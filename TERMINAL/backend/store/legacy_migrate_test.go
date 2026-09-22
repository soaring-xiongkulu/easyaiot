package store

import (
	"os"
	"path/filepath"
	"testing"

	"easyaiot/terminal/backend/session"
)

type fakeLegacy struct {
	pw map[string]string
}

func (f fakeLegacy) GetPassword(id string) (string, error) { return f.pw[id], nil }

func TestMigrateLegacyKeychainToInPlace(t *testing.T) {
	dir := t.TempDir()
	// Seed connections.json with an empty password (legacy: password in keychain).
	cs := &ConnectionStore{configDir: dir}
	_ = cs.writeJSONLocked(session.ConnectionStoreData{
		Groups:      []session.ConnectionGroup{},
		Connections: []session.ConnectionConfig{{ID: "c1", Type: "ssh", AuthType: "password", Password: ""}},
	})

	legacy := fakeLegacy{pw: map[string]string{"c1": "pw1"}}
	n, err := MigrateLegacyKeychainToInPlace(dir, legacy, fakeCipherStore{})
	if err != nil {
		t.Fatalf("MigrateLegacyKeychainToInPlace: %v", err)
	}
	if n != 1 {
		t.Fatalf("migrated %d secrets, want 1", n)
	}
	// connections.json now holds ciphertext.
	raw, _ := os.ReadFile(filepath.Join(dir, storeFileName))
	wantPW, _ := fakeCipherStore{}.Encrypt("pw1")
	if !contains(string(raw), wantPW) {
		t.Fatalf("connection password not migrated: %s", raw)
	}
}
