//go:build !android

package store

import (
	"os"
	"path/filepath"
	"testing"
)

func TestDefaultDataDir(t *testing.T) {
	dir, err := DefaultDataDir()
	if err != nil {
		t.Fatalf("DefaultDataDir: %v", err)
	}
	if dir == "" {
		t.Fatalf("empty default dir")
	}
}

func TestResolveDataDirUpgradeWhenConfigExists(t *testing.T) {
	// Cannot override UserConfigDir in-process; this test exercises the helper
	// hasConfigFiles used by ResolveDataDir.
	dir := t.TempDir()
	if hasConfigFiles(dir) {
		t.Fatalf("empty dir should not have config files")
	}
	_ = os.WriteFile(filepath.Join(dir, "connections.json"), []byte("{}"), 0600)
	if !hasConfigFiles(dir) {
		t.Fatalf("dir with connections.json should be detected")
	}
}
