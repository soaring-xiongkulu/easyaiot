package store

import (
	"encoding/base64"
	"os"
	"path/filepath"
	"testing"

	"easyaiot/terminal/backend/session"
)

// enc returns the fakeCipherStore encoding of pw (used to seed encrypted fields).
func enc(pw string) string {
	return "enc:v1:" + base64.StdEncoding.EncodeToString([]byte(pw))
}

func TestConnectionStore_SaveEncryptsPassword(t *testing.T) {
	dir := t.TempDir()
	s := &ConnectionStore{configDir: dir, passwordStore: fakeCipherStore{}}

	data := session.ConnectionStoreData{
		Groups:      []session.ConnectionGroup{},
		Connections: []session.ConnectionConfig{{ID: "c1", Type: "ssh", AuthType: "password", Password: "secret"}},
	}
	if err := s.Save(data); err != nil {
		t.Fatalf("Save: %v", err)
	}
	raw, err := os.ReadFile(filepath.Join(dir, storeFileName))
	if err != nil {
		t.Fatalf("read: %v", err)
	}
	if contains(string(raw), "secret") {
		t.Fatalf("plaintext leaked: %s", raw)
	}
	if !contains(string(raw), "enc:v1:") {
		t.Fatalf("expected encrypted field on disk, got %s", raw)
	}
}

func TestConnectionStore_LoadDecryptsPassword(t *testing.T) {
	dir := t.TempDir()
	s := &ConnectionStore{configDir: dir, passwordStore: fakeCipherStore{}}

	seed := session.ConnectionStoreData{
		Groups:      []session.ConnectionGroup{},
		Connections: []session.ConnectionConfig{{ID: "c1", Type: "ssh", AuthType: "password", Password: enc("secret")}},
	}
	if err := s.writeJSONLocked(seed); err != nil {
		t.Fatalf("seed: %v", err)
	}
	data, err := s.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if data.Connections[0].Password != "secret" {
		t.Fatalf("Load password = %q, want secret", data.Connections[0].Password)
	}
}

func TestConnectionStore_LoadMigratesLegacyPlaintext(t *testing.T) {
	dir := t.TempDir()
	s := &ConnectionStore{configDir: dir, passwordStore: fakeCipherStore{}}

	seed := session.ConnectionStoreData{
		Groups:      []session.ConnectionGroup{},
		Connections: []session.ConnectionConfig{{ID: "c1", Type: "ssh", AuthType: "password", Password: "legacy"}},
	}
	if err := s.writeJSONLocked(seed); err != nil {
		t.Fatalf("seed: %v", err)
	}
	data, err := s.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if data.Connections[0].Password != "legacy" {
		t.Fatalf("Load should return plaintext, got %q", data.Connections[0].Password)
	}
	raw, _ := os.ReadFile(filepath.Join(dir, storeFileName))
	if !contains(string(raw), "enc:v1:") {
		t.Fatalf("legacy plaintext not migrated to ciphertext: %s", raw)
	}
	if contains(string(raw), "\"password\": \"legacy\"") {
		t.Fatalf("legacy plaintext still on disk: %s", raw)
	}
}

func TestConnectionStore_EnsurePasswordCache(t *testing.T) {
	dir := t.TempDir()
	s := &ConnectionStore{configDir: dir, passwordStore: fakeCipherStore{}}
	seed := session.ConnectionStoreData{
		Groups:      []session.ConnectionGroup{},
		Connections: []session.ConnectionConfig{{ID: "c1", Type: "ssh", AuthType: "password", Password: enc("pw")}},
	}
	_ = s.writeJSONLocked(seed)
	if _, err := s.Load(); err != nil {
		t.Fatalf("Load: %v", err)
	}
	if got, _ := s.EnsurePassword("c1"); got != "pw" {
		t.Fatalf("EnsurePassword = %q, want pw", got)
	}
	if got, _ := s.EnsurePassword("missing"); got != "" {
		t.Fatalf("EnsurePassword(missing) = %q, want empty", got)
	}
}

// TestConnectionStore_SaveEncryptsKeyText and LoadDecryptsKeyText lock in that
// an inline private-key text (authType "keyText", KeyContent) is encrypted at
// rest in connections.json like a password, so plaintext keys can't leak to disk
// and are decrypted back on load (#720).
func TestConnectionStore_SaveEncryptsKeyText(t *testing.T) {
	dir := t.TempDir()
	s := &ConnectionStore{configDir: dir, passwordStore: fakeCipherStore{}}

	const keyText = "-----BEGIN OPENSSH PRIVATE KEY-----\nfake\n-----END OPENSSH PRIVATE KEY-----"
	data := session.ConnectionStoreData{
		Groups:      []session.ConnectionGroup{},
		Connections: []session.ConnectionConfig{{ID: "c1", Type: "ssh", AuthType: "keyText", KeyContent: keyText, Password: "pp"}},
	}
	if err := s.Save(data); err != nil {
		t.Fatalf("Save: %v", err)
	}
	raw, err := os.ReadFile(filepath.Join(dir, storeFileName))
	if err != nil {
		t.Fatalf("read: %v", err)
	}
	if contains(string(raw), keyText) {
		t.Fatalf("plaintext KeyContent leaked: %s", raw)
	}
	if !contains(string(raw), "enc:v1:") {
		t.Fatalf("expected encrypted KeyContent on disk: %s", raw)
	}
}

func TestConnectionStore_LoadDecryptsKeyText(t *testing.T) {
	dir := t.TempDir()
	s := &ConnectionStore{configDir: dir, passwordStore: fakeCipherStore{}}

	seed := session.ConnectionStoreData{
		Groups:      []session.ConnectionGroup{},
		Connections: []session.ConnectionConfig{{ID: "c1", Type: "ssh", AuthType: "keyText", KeyContent: enc("PEM-KEY"), Password: enc("pp")}},
	}
	if err := s.writeJSONLocked(seed); err != nil {
		t.Fatalf("seed: %v", err)
	}
	data, err := s.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if data.Connections[0].KeyContent != "PEM-KEY" {
		t.Fatalf("Load KeyContent = %q, want PEM-KEY", data.Connections[0].KeyContent)
	}
}
