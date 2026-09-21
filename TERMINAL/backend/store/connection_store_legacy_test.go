package store

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"easyaiot/terminal/backend/credentials"
	"easyaiot/terminal/backend/session"
)

// fakeLegacyKC is a LegacyPasswordSource keyed by connection ID, mimicking the
// pre-enc:v1 keychain (conn/<id>) holding plaintext passwords.
type fakeLegacyKC struct{ pw map[string]string }

func (f fakeLegacyKC) GetPassword(id string) (string, error)  { return f.pw[id], nil }
func (fakeLegacyKC) GetModelAPIKey(string) (string, error)    { return "", nil }

// TestLoadFallsBackToLegacyKeychain reproduces the upgrade regression: a
// connection saved under the old scheme has no enc:v1 field (the password
// lived in the keychain), and the one-shot migration never ran. Load() must
// recover the password from the legacy keychain and lazy-migrate it to enc:v1
// on the resulting save so it is not invisible.
func TestLoadFallsBackToLegacyKeychain(t *testing.T) {
	dir := t.TempDir()
	s := &ConnectionStore{configDir: dir, passwordStore: fakeCipherStore{}}
	s.SetLegacyKeychain(fakeLegacyKC{pw: map[string]string{"c1": "secret-pw"}})

	// JSON with no password field — exactly the old keychain-mode shape.
	mustWriteConnections(t, dir, session.ConnectionStoreData{
		Connections: []session.ConnectionConfig{
			{ID: "c1", Type: "ssh", AuthType: "password"},
		},
	})

	data, err := s.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if got := data.Connections[0].Password; got != "secret-pw" {
		t.Fatalf("password = %q, want %q (legacy keychain fallback)", got, "secret-pw")
	}

	// EnsurePassword recovers it too, without going through a full Load.
	s2 := &ConnectionStore{configDir: dir, passwordStore: fakeCipherStore{}}
	s2.SetLegacyKeychain(fakeLegacyKC{pw: map[string]string{"c1": "secret-pw"}})
	pw, err := s2.EnsurePassword("c1")
	if err != nil {
		t.Fatalf("EnsurePassword: %v", err)
	}
	if pw != "secret-pw" {
		t.Fatalf("EnsurePassword = %q, want %q", pw, "secret-pw")
	}
}

// TestLoadLegacyFallBackLazyMigrates verifies the recovered plaintext is
// written back as enc:v1 so subsequent loads don't depend on the keychain.
func TestLoadLegacyFallBackLazyMigrates(t *testing.T) {
	dir := t.TempDir()
	s := &ConnectionStore{configDir: dir, passwordStore: fakeCipherStore{}}
	s.SetLegacyKeychain(fakeLegacyKC{pw: map[string]string{"c1": "secret-pw"}})

	mustWriteConnections(t, dir, session.ConnectionStoreData{
		Connections: []session.ConnectionConfig{
			{ID: "c1", Type: "ssh", AuthType: "password"},
		},
	})
	if _, err := s.Load(); err != nil {
		t.Fatalf("Load: %v", err)
	}

	raw, _ := os.ReadFile(filepath.Join(dir, storeFileName))
	var d session.ConnectionStoreData
	if err := json.Unmarshal(raw, &d); err != nil {
		t.Fatalf("reparse: %v", err)
	}
	if !credentials.IsEncrypted(d.Connections[0].Password) {
		t.Fatalf("password not lazy-migrated to enc:v1: %q", d.Connections[0].Password)
	}
	// The legacy keychain entry must survive (we don't delete on recovery).
	if _, err := s.legacy.GetPassword("c1"); err != nil {
		t.Fatalf("legacy keychain entry deleted during migration: %v", err)
	}
}

// TestLoadEncV1PreferredOverLegacy ensures an existing enc:v1 field is used
// and the legacy keychain is never consulted for that connection.
func TestLoadEncV1PreferredOverLegacy(t *testing.T) {
	dir := t.TempDir()
	s := &ConnectionStore{configDir: dir, passwordStore: fakeCipherStore{}}
	enc, _ := fakeCipherStore{}.Encrypt("enc-pw")
	// Legacy holds a DIFFERENT value — it must be ignored.
	s.SetLegacyKeychain(fakeLegacyKC{pw: map[string]string{"c1": "stale-legacy"}})

	mustWriteConnections(t, dir, session.ConnectionStoreData{
		Connections: []session.ConnectionConfig{
			{ID: "c1", Type: "ssh", AuthType: "password", Password: enc},
		},
	})
	data, err := s.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if got := data.Connections[0].Password; got != "enc-pw" {
		t.Fatalf("password = %q, want enc:v1 value %q", got, "enc-pw")
	}
}

func mustWriteConnections(t *testing.T, dir string, data session.ConnectionStoreData) {
	t.Helper()
	s := &ConnectionStore{configDir: dir}
	if err := s.writeJSONLocked(data); err != nil {
		t.Fatalf("writeJSONLocked: %v", err)
	}
}
