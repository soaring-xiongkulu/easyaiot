//go:build !android

package store

import (
	"encoding/json"
	"os"
	"path/filepath"

	"easyaiot/terminal/backend/log"
)

const bootstrapFileName = "bootstrap.json"

type bootstrap struct {
	Type    string `json:"type"`
	DataDir string `json:"dataDir,omitempty"`
}

// DefaultDataDir returns the OS user-config data dir (<UserConfigDir>/Terminal).
func DefaultDataDir() (string, error) {
	cfg, err := os.UserConfigDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(cfg, "Terminal"), nil
}

func exeDir() (string, error) {
	exe, err := os.Executable()
	if err != nil {
		return "", err
	}
	return filepath.Dir(exe), nil
}

func bootstrapPath() (string, error) {
	dir, err := exeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(dir, "data", bootstrapFileName), nil
}

// userConfigBootstrapPath returns the bootstrap path in the user config dir
// (<UserConfigDir>/Terminal/bootstrap.json). Unlike the exe/data location it is
// writable for installs under a read-only Program Files / Applications, which
// is where default and custom data dirs (and their bootstrap pointer) belong.
func userConfigBootstrapPath() (string, error) {
	def, err := DefaultDataDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(def, bootstrapFileName), nil
}

// bootstrapTargetPaths decides where a bootstrap of the given kind is written
// and which stale location to remove afterwards.
//
//	portable → lives with the exe (exe/data) so it follows a USB stick.
//	everything else → lives in the user config dir (writable even from a
//	read-only install dir).
//
// To keep only one valid pointer on disk (a mode switch must not silently
// shadow one another at read time) the stale location is the other one.
func bootstrapTargetPaths(kind, exe, userCfg string) (primary, stale string) {
	exePath := filepath.Join(exe, "data", bootstrapFileName)
	userPath := filepath.Join(userCfg, bootstrapFileName)
	if kind == "portable" {
		return exePath, userPath
	}
	return userPath, exePath
}

// bootstrapSearchOrder returns the candidate paths read at startup, newest
// preference first: the user-config bootstrap (authoritative for installs),
// then the exe/data one (portable fallback). Each is validated as it is read.
func bootstrapSearchOrder(exe, userCfg string) []string {
	exePath := filepath.Join(exe, "data", bootstrapFileName)
	userPath := filepath.Join(userCfg, bootstrapFileName)
	if exePath == userPath {
		return []string{exePath}
	}
	return []string{userPath, exePath}
}

// ResolveDataDir determines where config files live.
//   - Valid bootstrap.json in (user-config, then exe/data) → resolve its path.
//   - No valid bootstrap + default dir has config files → Upgrade (existing user).
//   - Otherwise → FirstRun.
func ResolveDataDir() (DataDir, error) {
	exe, err := exeDir()
	if err != nil {
		return DataDir{}, err
	}
	userCfg, err := userConfigBootstrapPath()
	if err != nil {
		return DataDir{}, err
	}
	for _, bp := range bootstrapSearchOrder(exe, userCfg) {
		if b, err := readBootstrap(bp); err == nil && b != nil {
			if dir, err := resolvePath(b); err == nil && dir != "" && pathExists(dir) {
				return DataDir{Path: dir, Type: b.Type}, nil
			}
			// Invalid or missing path → try next location.
		}
	}
	def, err := DefaultDataDir()
	if err != nil {
		return DataDir{}, err
	}
	if hasConfigFiles(def) {
		log.Writef("no valid bootstrap; default dir has config → upgrade dataDir=%s", def)
		return DataDir{Path: def, Type: "default", Upgrade: true}, nil
	}
	log.Writef("no valid bootstrap and no config in default dir → first run")
	return DataDir{FirstRun: true}, nil
}

func readBootstrap(path string) (*bootstrap, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var b bootstrap
	if err := json.Unmarshal(data, &b); err != nil {
		return nil, err
	}
	return &b, nil
}

func resolvePath(b *bootstrap) (string, error) {
	switch b.Type {
	case "default":
		return DefaultDataDir()
	case "portable":
		dir, err := exeDir()
		if err != nil {
			return "", err
		}
		return filepath.Join(dir, "data"), nil
	case "custom":
		if b.DataDir == "" {
			return "", nil
		}
		return b.DataDir, nil
	default:
		return "", nil
	}
}

// WriteBootstrap writes the bootstrap pointer for the given kind to the
// canonical location (user config dir for default/custom, exe/data for
// portable) and removes the stale location so only one pointer exists.
func WriteBootstrap(kind, customDir string) error {
	exe, err := exeDir()
	if err != nil {
		return err
	}
	userCfg, err := userConfigBootstrapPath()
	if err != nil {
		return err
	}
	primary, stale := bootstrapTargetPaths(kind, exe, userCfg)

	b := bootstrap{Type: kind}
	if kind == "custom" {
		b.DataDir = customDir
	}
	data, err := json.Marshal(b)
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(primary), 0755); err != nil {
		return err
	}
	if err := atomicWriteFile(primary, data, 0600); err != nil {
		return err
	}
	// A mode switch must not leave a second, shadowing pointer behind.
	if stale != primary {
		_ = os.Remove(stale)
	}
	return nil
}

func pathExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func hasConfigFiles(dir string) bool {
	for _, name := range []string{"connections.json", "settings.json"} {
		if _, err := os.Stat(filepath.Join(dir, name)); err == nil {
			return true
		}
	}
	return false
}
