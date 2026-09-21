package importer

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/sha3"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"hash"
	"os"
	"path/filepath"
	"strings"

	"easyaiot/terminal/backend/session"
	"golang.org/x/crypto/pbkdf2"
)

const (
	windTermPBKDF2Iterations = 100000
	windTermDerivedLength    = 48
	windTermAESKeyLength     = 32
	windTermAESIVLength      = 16
)

// windTermSession models one entry of WindTerm's user.sessions JSON. WindTerm
// uses FLAT dotted keys (session.protocol, session.target, …), not nested
// objects — porting this wrong (nested "protocol"/"target"/…) parses nothing.
type windTermSession struct {
	Protocol  string `json:"session.protocol"`
	Target    string `json:"session.target"`
	Port      *int   `json:"session.port"`
	Label     string `json:"session.label"`
	Group     string `json:"session.group"`
	AutoLogin string `json:"session.autoLogin"` // JSON-object string, or AES-256-CBC base64
	SSH       struct {
		IdentityFilePath string `json:"identityFilePath.windows"`
	} `json:"ssh"`
}

// windTermAutoLogin is the (possibly decrypted) payload of session.autoLogin.
// It uses its own flat keys, e.g. "session.user" and "Public Key".
type windTermAutoLogin struct {
	PasswordEnabled bool   `json:"PasswordEnabled"`
	Password        string `json:"Password"`
	SessionUser     string `json:"session.user"`
	PublicKey       struct {
		WindowsPath string `json:"windows.path"`
		WindowsPass string `json:"windows.pass"`
	} `json:"Public Key"`
}

// windTermKey is the AES-256-CBC key/IV derived from WindTerm's master password.
type windTermKey struct {
	key []byte
	iv  []byte
}

// parseWindTerm imports WindTerm's user.sessions. srcPath locates the sibling
// user.config (profile dir = parent of the sessions dir), and opts.Password is
// the master password required to decrypt autoLogin when masterPassword is on.
func parseWindTerm(data []byte, srcPath string, opts ParseOptions) (*ImportResult, error) {
	var sessions []windTermSession
	if err := json.Unmarshal(data, &sessions); err != nil {
		return nil, fmt.Errorf("parse windterm json: %w", err)
	}

	crypto, err := windTermCrypto(srcPath, opts.Password)
	if err != nil {
		return nil, err
	}

	res := &ImportResult{}
	pathMap := map[string]string{}
	for _, s := range sessions {
		if !strings.EqualFold(s.Protocol, "SSH") {
			res.Warnings = append(res.Warnings, "skipped WindTerm protocol "+s.Protocol)
			continue
		}
		host, targetUser := windTermTarget(s.Target)
		if host == "" {
			continue
		}
		var port int
		switch {
		case s.Port == nil:
			port = 22
		case *s.Port < 1 || *s.Port > 65535:
			continue
		default:
			port = *s.Port
		}

		al, err := windTermAutoLoginFor(s.AutoLogin, crypto)
		if err != nil {
			return nil, err
		}

		name := strings.TrimSpace(s.Label)
		if name == "" {
			name = host
		}

		user := targetUser
		if al != nil && strings.TrimSpace(al.SessionUser) != "" {
			user = strings.TrimSpace(al.SessionUser)
		}

		conn := session.ConnectionConfig{
			ID: newConnectionID(), Name: name, Type: "ssh", Host: host, Port: port, User: user,
		}
		keyPath := windTermKeyPath(al, s.SSH.IdentityFilePath)
		switch {
		case al != nil && al.PasswordEnabled && al.Password != "":
			conn.AuthType = "password"
			conn.Password = al.Password
		case keyPath != "":
			conn.AuthType = "key"
			conn.KeyPath = windTermResolveKeyPath(keyPath)
			if al != nil {
				conn.Password = al.PublicKey.WindowsPass
			}
		default:
			conn.AuthType = "agent"
		}

		segs := splitNonEmpty(strings.ReplaceAll(s.Group, ">", "/"), "/")
		if gid := ensureGroupPath(segs, pathMap, &res.Groups, newGroupID); gid != nil {
			conn.GroupId = gid
		}
		res.Connections = append(res.Connections, conn)
	}
	return res, nil
}

// windTermTarget splits "user@host" on the LAST '@'; no '@' (or empty halves)
// falls back to host with a "root" user.
func windTermTarget(target string) (host, user string) {
	target = strings.TrimSpace(target)
	if i := strings.LastIndex(target, "@"); i > 0 && i < len(target)-1 {
		return target[i+1:], target[:i]
	}
	return target, "root"
}

// windTermKeyPath returns the first non-empty key path across the autoLogin
// "Public Key.windows.path" and the session's ssh.identityFilePath.windows.
func windTermKeyPath(al *windTermAutoLogin, identity string) string {
	if al != nil && strings.TrimSpace(al.PublicKey.WindowsPath) != "" {
		return strings.TrimSpace(al.PublicKey.WindowsPath)
	}
	return strings.TrimSpace(identity)
}

// windTermResolveKeyPath expands WindTerm's $(HomeDir)/~ placeholders so the
// path can be handed to os.ReadFile at connect time.
func windTermResolveKeyPath(p string) string {
	home, _ := os.UserHomeDir()
	if home == "" {
		return p
	}
	p = strings.ReplaceAll(p, "$(HomeDir)", home)
	p = strings.ReplaceAll(p, "${HomeDir}", home)
	if p == "~" {
		return home
	}
	if strings.HasPrefix(p, "~/") {
		return filepath.Join(home, p[2:])
	}
	if strings.HasPrefix(p, `~\`) {
		return filepath.Join(home, p[2:])
	}
	return p
}

// windTermCrypto loads the profile's user.config next to the sessions file and,
// if masterPassword is enabled, derives the AES key/IV. Returns (nil, nil) when
// there is no user.config or masterPassword is off (autoLogin stays plaintext).
func windTermCrypto(sessionsPath, masterPassword string) (*windTermKey, error) {
	configPath := filepath.Join(filepath.Dir(filepath.Dir(sessionsPath)), "user.config")
	content, err := os.ReadFile(configPath)
	if err != nil {
		return nil, nil
	}
	var cfg struct {
		Fingerprint    string `json:"application.fingerprint"`
		MasterPassword bool   `json:"application.masterPassword"`
	}
	if err := json.Unmarshal(content, &cfg); err != nil {
		return nil, fmt.Errorf("parse windterm user.config: %w", err)
	}
	if cfg.Fingerprint == "" {
		return nil, fmt.Errorf("windterm user.config missing application.fingerprint")
	}
	if !cfg.MasterPassword {
		return nil, nil
	}
	if masterPassword == "" {
		return nil, fmt.Errorf("windterm master password is required")
	}
	return deriveWindTermKey(cfg.Fingerprint, masterPassword), nil
}

// deriveWindTermKey derives PBKDF2-HMAC-SHA3-512 with 100k iterations,
// 48-byte material (fingerprint as salt) split into a 32-byte key + 16-byte IV.
func deriveWindTermKey(fingerprint, masterPassword string) *windTermKey {
	material := pbkdf2.Key(
		[]byte(masterPassword),
		[]byte(fingerprint),
		windTermPBKDF2Iterations,
		windTermDerivedLength,
		func() hash.Hash { return sha3.New512() },
	)
	return &windTermKey{
		key: material[:windTermAESKeyLength],
		iv:  material[windTermAESKeyLength:windTermDerivedLength],
	}
}

// windTermAutoLoginFor returns the autoLogin payload: plaintext inline JSON if
// it decodes, otherwise AES-256-CBC base64 decrypted with the derived key.
func windTermAutoLoginFor(raw string, k *windTermKey) (*windTermAutoLogin, error) {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return nil, nil
	}
	var al windTermAutoLogin
	if err := json.Unmarshal([]byte(raw), &al); err == nil {
		return &al, nil
	}
	if k == nil {
		return nil, fmt.Errorf("windterm session.autoLogin is encrypted but no master password is available")
	}
	ciphertext, err := base64.StdEncoding.DecodeString(raw)
	if err != nil {
		return nil, fmt.Errorf("decode windterm autoLogin: %w", err)
	}
	plain, err := windTermDecrypt(ciphertext, k)
	if err != nil {
		return nil, fmt.Errorf("decrypt windterm autoLogin: %w", err)
	}
	if err := json.Unmarshal(plain, &al); err != nil {
		return nil, fmt.Errorf("parse decrypted windterm autoLogin: %w", err)
	}
	return &al, nil
}

// windTermDecrypt decrypts AES-256-CBC ciphertext with PKCS#7 padding.
func windTermDecrypt(ciphertext []byte, k *windTermKey) ([]byte, error) {
	block, err := aes.NewCipher(k.key)
	if err != nil {
		return nil, err
	}
	if len(ciphertext) == 0 || len(ciphertext)%block.BlockSize() != 0 {
		return nil, fmt.Errorf("invalid windterm ciphertext length")
	}
	plain := make([]byte, len(ciphertext))
	cipher.NewCBCDecrypter(block, k.iv).CryptBlocks(plain, ciphertext)
	n := len(plain)
	if n == 0 {
		return nil, fmt.Errorf("empty plaintext")
	}
	pad := int(plain[n-1])
	if pad < 1 || pad > block.BlockSize() || pad > n {
		return nil, fmt.Errorf("invalid pkcs7 padding")
	}
	for i := 0; i < pad; i++ {
		if plain[n-1-i] != byte(pad) {
			return nil, fmt.Errorf("invalid pkcs7 padding")
		}
	}
	return plain[:n-pad], nil
}
