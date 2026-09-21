package store

import (
	"os"
	"path/filepath"
	"testing"

	"easyaiot/terminal/backend/session"
)

type fakeLegacy struct {
	pw map[string]string
	ak map[string]string
}

func (f fakeLegacy) GetPassword(id string) (string, error)    { return f.pw[id], nil }
func (f fakeLegacy) GetModelAPIKey(id string) (string, error) { return f.ak[id], nil }

func TestMigrateLegacyKeychainToInPlace(t *testing.T) {
	dir := t.TempDir()
	// Seed connections.json with an empty password (legacy: password in keychain).
	cs := &ConnectionStore{configDir: dir}
	_ = cs.writeJSONLocked(session.ConnectionStoreData{
		Groups:      []session.ConnectionGroup{},
		Connections: []session.ConnectionConfig{{ID: "c1", Type: "ssh", AuthType: "password", Password: ""}},
	})
	// Seed settings.json with an empty apiKey.
	ss := &SettingsStore{configDir: dir}
	_ = ss.Save(AppSettings{AI: AISettings{Models: []AIModelConfig{{ID: "m1", APIKey: ""}}}})

	legacy := fakeLegacy{pw: map[string]string{"c1": "pw1"}, ak: map[string]string{"m1": "ak1"}}
	n, err := MigrateLegacyKeychainToInPlace(dir, legacy, fakeCipherStore{})
	if err != nil {
		t.Fatalf("MigrateLegacyKeychainToInPlace: %v", err)
	}
	if n != 2 {
		t.Fatalf("migrated %d secrets, want 2", n)
	}
	// connections.json now holds ciphertext.
	raw, _ := os.ReadFile(filepath.Join(dir, storeFileName))
	wantPW, _ := fakeCipherStore{}.Encrypt("pw1")
	if !contains(string(raw), wantPW) {
		t.Fatalf("connection password not migrated: %s", raw)
	}
	rawS, _ := os.ReadFile(filepath.Join(dir, settingsFileName))
	wantAK, _ := fakeCipherStore{}.Encrypt("ak1")
	if !contains(string(rawS), wantAK) {
		t.Fatalf("apiKey not migrated: %s", rawS)
	}
}
