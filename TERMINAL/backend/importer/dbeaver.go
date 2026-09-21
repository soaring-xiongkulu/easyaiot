package importer

import (
	"crypto/aes"
	"crypto/cipher"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"

	"easyaiot/terminal/backend/session"
)

// FormatDBeaver imports DBeaver connections straight from a workspace's
// General/.dbeaver folder (data-sources.json + credentials-config.json).
const FormatDBeaver = "dbeaver"

// dbeaverAesKey is DBeaver's built-in local-encryption key (zero IV, first
// decrypted block discarded — the file's real IV is recovered that way).
var dbeaverAesKey, _ = hex.DecodeString("babb4a9f774ab853c96c2d653dfe544a")

// dbeaverConnType maps DBeaver providers directly onto uniterm database
// targets (config type + dbType + default port).
var dbeaverConnType = map[string]connTarget{
	"mysql":         {Type: "database", DBType: "mysql", Port: 3306},
	"mariadb":       {Type: "database", DBType: "mysql", Port: 3306},
	"postgresql":    {Type: "database", DBType: "postgres", Port: 5432},
	"postgres":      {Type: "database", DBType: "postgres", Port: 5432},
	"mssql":         {Type: "database", DBType: "sqlserver", Port: 1433},
	"sqlserver":     {Type: "database", DBType: "sqlserver", Port: 1433},
	"oracle":        {Type: "database", DBType: "oracle", Port: 1521},
	"redis":         {Type: "redis", Port: 6379},
	"mongodb":       {Type: "mongodb", Port: 27017},
	"elasticsearch": {Type: "elasticsearch", Port: 9200},
}

// dbeaverSource is one entry of data-sources.json's connections map.
type dbeaverSource struct {
	Name          string `json:"name"`
	Provider      string `json:"provider"`
	Folder        string `json:"folder"`
	Configuration struct {
		Host       string          `json:"host"`
		Port       json.RawMessage `json:"port"`
		Database   string          `json:"database"`
		User       string          `json:"user"`
		ServerType string          `json:"serverType"`
	} `json:"configuration"`
}

// dbeaverCredentials is the decrypted credentials-config.json payload keyed by
// connection id; #connection holds the main user/password pair.
type dbeaverCredentials struct {
	Conn struct {
		User     string `json:"user"`
		Password string `json:"password"`
	} `json:"#connection"`
}

// parseDBeaver imports connections from a DBeaver workspace. srcPath may be:
// empty (auto-detect the platform default), a .dbeaver dir, or a
// data-sources.json file. Passwords come from credentials-config.json; when it
// cannot be decrypted (e.g. DBeaver master password set) they are left empty
// with a warning.
func parseDBeaver(srcPath string, opts ParseOptions) (*ImportResult, error) {
	dir, err := dbeaverConfigDir(srcPath)
	if err != nil {
		return nil, err
	}

	raw, err := os.ReadFile(filepath.Join(dir, "data-sources.json"))
	if err != nil {
		return nil, fmt.Errorf("read data-sources.json: %w", err)
	}
	var doc struct {
		Connections map[string]dbeaverSource `json:"connections"`
		Folders     map[string]struct {
			Connections []string `json:"connections"`
		} `json:"folders"`
	}
	if err := json.Unmarshal(raw, &doc); err != nil {
		return nil, fmt.Errorf("parse data-sources.json: %w", err)
	}

	creds, credWarn := dbeaverLoadCredentials(dir)

	res := &ImportResult{}
	pathMap := map[string]string{}
	newGroup := func() string { return newGroupID() }
	newConn := newConnectionID

	for id, src := range doc.Connections {
		tgt, ok := dbeaverConnType[strings.ToLower(strings.TrimSpace(src.Provider))]
		if !ok {
			res.Warnings = append(res.Warnings, fmt.Sprintf("%s: unsupported provider %q, skipped", src.Name, src.Provider))
			continue
		}
		conn := session.ConnectionConfig{
			ID:       newConn(),
			Name:     firstNonEmpty(src.Name, id),
			Type:     tgt.Type,
			DBType:   tgt.DBType,
			Host:     src.Configuration.Host,
			DBName:   src.Configuration.Database,
			User:     src.Configuration.User,
			AuthType: "password",
		}
		conn.Port = dbeaverPortOf(src.Configuration.Port, tgt.Port)
		if creds != nil {
			if c, ok := creds[id]; ok {
				if conn.User == "" {
					conn.User = c.Conn.User
				}
				conn.Password = c.Conn.Password
			}
		}
		if src.Folder != "" {
			conn.GroupId = ensureGroupPath([]string{src.Folder}, pathMap, &res.Groups, newGroup)
		}
		res.Connections = append(res.Connections, conn)
	}
	if credWarn != "" {
		res.Warnings = append(res.Warnings, credWarn)
	}
	return res, nil
}

// dbeaverConfigDir resolves the .dbeaver config folder from srcPath or the
// platform default workspace location.
func dbeaverConfigDir(srcPath string) (string, error) {
	if srcPath != "" {
		info, err := os.Stat(srcPath)
		if err != nil {
			return "", err
		}
		dir := srcPath
		if !info.IsDir() {
			dir = filepath.Dir(srcPath)
		}
		if filepath.Base(dir) == ".dbeaver" {
			return dir, nil
		}
		// A workspace root: look for the standard General/.dbeaver below it.
		candidate := filepath.Join(dir, "General", ".dbeaver")
		if st, err := os.Stat(candidate); err == nil && st.IsDir() {
			return candidate, nil
		}
		return dir, nil
	}

	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	var candidates []string
	switch runtime.GOOS {
	case "darwin":
		candidates = []string{filepath.Join(home, "Library", "DBeaverData", "workspace6", "General", ".dbeaver")}
	case "windows":
		appdata := os.Getenv("APPDATA")
		if appdata == "" {
			appdata = filepath.Join(home, "AppData", "Roaming")
		}
		candidates = []string{filepath.Join(appdata, "DBeaverData", "workspace6", "General", ".dbeaver")}
	default:
		data := os.Getenv("XDG_DATA_HOME")
		if data == "" {
			data = filepath.Join(home, ".local", "share")
		}
		candidates = []string{
			filepath.Join(data, "DBeaverData", "workspace6", "General", ".dbeaver"),
			filepath.Join(home, ".local", "share", "DBeaverData", "workspace6", "General", ".dbeaver"),
		}
	}
	for _, c := range candidates {
		if st, err := os.Stat(c); err == nil && st.IsDir() {
			return c, nil
		}
	}
	return "", errors.New("DBeaver workspace not found; select data-sources.json manually")
}

// dbeaverLoadCredentials decrypts credentials-config.json (AES-128-CBC with
// DBeaver's built-in key; the first plaintext block is the file IV, skipped).
// Returns nil + a warning when the file is missing or undecryptable.
func dbeaverLoadCredentials(dir string) (map[string]dbeaverCredentials, string) {
	raw, err := os.ReadFile(filepath.Join(dir, "credentials-config.json"))
	if err != nil {
		return nil, "" // no credentials file: passwords simply absent
	}
	plain, err := dbeaverDecrypt(raw)
	if err != nil {
		return nil, "DBeaver credentials could not be decrypted (custom master password?); passwords left empty"
	}
	var creds map[string]dbeaverCredentials
	if err := json.Unmarshal(plain, &creds); err != nil {
		return nil, "DBeaver credentials file has unexpected format; passwords left empty"
	}
	return creds, ""
}

// dbeaverDecrypt reverses DBeaver's local credential encryption:
// AES-128-CBC, zero IV, where the first 16-byte plaintext block is the file's
// own random IV and the remainder is the PKCS#7-padded JSON payload.
func dbeaverDecrypt(data []byte) ([]byte, error) {
	block, err := aes.NewCipher(dbeaverAesKey)
	if err != nil {
		return nil, err
	}
	if len(data) < 2*block.BlockSize() || len(data)%block.BlockSize() != 0 {
		return nil, errors.New("unexpected credentials-config.json length")
	}
	plain := make([]byte, len(data))
	cipher.NewCBCDecrypter(block, make([]byte, block.BlockSize())).CryptBlocks(plain, data)
	return pkcs7Unpad(plain[block.BlockSize():], block.BlockSize())
}

// dbeaverPortOf parses DBeaver's port (string or number) with a per-dbType
// default fallback.
func dbeaverPortOf(raw json.RawMessage, fallback int) int {
	var n int
	if len(raw) > 0 {
		if err := json.Unmarshal(raw, &n); err == nil && n > 0 {
			return n
		}
		var s string
		if err := json.Unmarshal(raw, &s); err == nil {
			if v, err := strconv.Atoi(strings.TrimSpace(s)); err == nil && v > 0 {
				return v
			}
		}
	}
	return fallback
}

func firstNonEmpty(vals ...string) string {
	for _, v := range vals {
		if v != "" {
			return v
		}
	}
	return ""
}
