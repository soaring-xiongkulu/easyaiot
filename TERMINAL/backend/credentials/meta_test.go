package credentials

import (
	"path/filepath"
	"testing"
)

func TestMetaRoundTripMasterPassword(t *testing.T) {
	dir := t.TempDir()
	salt := []byte("0123456789abcdef")
	if err := WriteMeta(dir, &Meta{Mode: ModeMasterPassword, Salt: salt}); err != nil {
		t.Fatalf("WriteMeta: %v", err)
	}
	m, err := ReadMeta(dir)
	if err != nil {
		t.Fatalf("ReadMeta: %v", err)
	}
	if m.Mode != ModeMasterPassword {
		t.Fatalf("mode = %q", m.Mode)
	}
	if string(m.Salt) != string(salt) {
		t.Fatalf("salt = %q, want %q", m.Salt, salt)
	}
}

func TestMetaRoundTripKeychainNoSalt(t *testing.T) {
	dir := t.TempDir()
	if err := WriteMeta(dir, &Meta{Mode: ModeKeychain}); err != nil {
		t.Fatalf("WriteMeta: %v", err)
	}
	m, err := ReadMeta(dir)
	if err != nil {
		t.Fatalf("ReadMeta: %v", err)
	}
	if m.Mode != ModeKeychain {
		t.Fatalf("mode = %q", m.Mode)
	}
	if m.Salt != nil {
		t.Fatalf("salt should be nil for keychain mode, got %v", m.Salt)
	}
}

func TestReadMetaAbsentReturnsNil(t *testing.T) {
	m, err := ReadMeta(t.TempDir())
	if err != nil {
		t.Fatalf("ReadMeta: %v", err)
	}
	if m != nil {
		t.Fatalf("expected nil for missing file, got %+v", m)
	}
}

func TestMetaPath(t *testing.T) {
	if got := MetaPath("/data"); got != filepath.Join("/data", "credentials.meta") {
		t.Fatalf("MetaPath = %q", got)
	}
}
