package store

import (
	"errors"
	"os"
	"path/filepath"
)

// resolveAndroidDataDir maps the Android app files dir (from the wails
// bridge) to the Terminal data dir. Kept untagged so it is unit-testable on
// desktop hosts; it is only called by bootstrap_android.go. An empty base
// means the wails bridge was not attached yet (getStoragePath returned ""),
// which is treated as an error rather than silently redirecting persistent
// storage somewhere ephemeral.
func resolveAndroidDataDir(base string) (DataDir, error) {
	if base == "" {
		return DataDir{}, errors.New("android: storage path unavailable (bridge not attached)")
	}
	dir := filepath.Join(base, "Terminal")
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return DataDir{}, err
	}
	return DataDir{Path: dir, Type: "default"}, nil
}
