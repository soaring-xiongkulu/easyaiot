package store

import (
	"os"
	"path/filepath"
	"testing"
)

func TestResolveAndroidDataDirCreatesDir(t *testing.T) {
	base := t.TempDir()
	dd, err := resolveAndroidDataDir(base)
	if err != nil {
		t.Fatalf("resolveAndroidDataDir: %v", err)
	}
	want := filepath.Join(base, "Terminal")
	if dd.Path != want {
		t.Errorf("Path = %q, want %q", dd.Path, want)
	}
	if dd.Type != "default" || dd.FirstRun || dd.Upgrade {
		t.Errorf("DataDir flags wrong: %+v", dd)
	}
	if info, err := os.Stat(want); err != nil || !info.IsDir() {
		t.Errorf("dir %q not created: %v", want, err)
	}
}

func TestResolveAndroidDataDirEmptyBaseErrors(t *testing.T) {
	dd, err := resolveAndroidDataDir("")
	if err == nil {
		t.Fatal("resolveAndroidDataDir(\"\") = nil error, want error")
	}
	if dd != (DataDir{}) {
		t.Errorf("DataDir = %+v, want zero value", dd)
	}
}
