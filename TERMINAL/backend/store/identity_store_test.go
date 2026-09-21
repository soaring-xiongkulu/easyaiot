package store

import (
	"os"
	"path/filepath"
	"testing"

	"easyaiot/terminal/backend/session"
)

type fakePasswordStore struct{ prefix string }

func (f fakePasswordStore) Encrypt(p string) (string, error) { return f.prefix + p, nil }
func (f fakePasswordStore) Decrypt(e string) (string, error) { return e[len(f.prefix):], nil }

// readFileString returns the raw contents of path as a string.
func readFileString(path string) (string, error) {
	b, err := os.ReadFile(path)
	return string(b), err
}

func TestIdentityStoreRoundTrip(t *testing.T) {
	dir := t.TempDir()
	s, err := NewIdentityStore(dir)
	if err != nil {
		t.Fatalf("new store: %v", err)
	}
	ps := fakePasswordStore{prefix: "enc:v1:"}
	s.SetPasswordStore(ps)

	in := session.IdentityStoreData{Identities: []session.Identity{
		{ID: "i1", Name: "prod", Username: "root", AuthType: "password", Password: "pw"},
		{ID: "i2", Name: "git", Username: "git", AuthType: "key", KeyPath: "/k", Password: "pp"},
	}}
	if err := s.Save(in); err != nil {
		t.Fatalf("save: %v", err)
	}
	// 落盘后 password 字段应为密文，KeyPath 保持明文
	raw, err := readFileString(filepath.Join(dir, "identities.json"))
	if err != nil {
		t.Fatalf("read: %v", err)
	}
	if contains(raw, `"password": "pw"`) {
		t.Fatal("password was not encrypted on disk")
	}

	out, err := s.Load()
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	if len(out.Identities) != 2 || out.Identities[0].Password != "pw" || out.Identities[1].KeyPath != "/k" {
		t.Fatalf("bad round-trip: %+v", out)
	}
}

// TestIdentityStoreKeyTextRoundTrip locks in that an inline private-key text
// (authType "keyText", KeyContent) is encrypted at rest like the password and
// decrypted back on load — the same treatment any secret gets (#720).
func TestIdentityStoreKeyTextRoundTrip(t *testing.T) {
	dir := t.TempDir()
	s, err := NewIdentityStore(dir)
	if err != nil {
		t.Fatalf("new store: %v", err)
	}
	s.SetPasswordStore(fakePasswordStore{prefix: "enc:v1:"})

	const keyText = "-----BEGIN OPENSSH PRIVATE KEY-----\n...fake-key...\n-----END OPENSSH PRIVATE KEY-----"
	in := session.IdentityStoreData{Identities: []session.Identity{
		{ID: "i1", Name: "inline", Username: "git", AuthType: "keyText", KeyContent: keyText, Password: "pp"},
	}}
	if err := s.Save(in); err != nil {
		t.Fatalf("save: %v", err)
	}

	raw, err := readFileString(filepath.Join(dir, "identities.json"))
	if err != nil {
		t.Fatalf("read: %v", err)
	}
	if contains(raw, keyText) {
		t.Fatal("KeyContent was not encrypted on disk")
	}
	if !contains(raw, "enc:v1:") {
		t.Fatal("KeyContent should be stored with the enc:v1: prefix")
	}

	out, err := s.Load()
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	if len(out.Identities) != 1 || out.Identities[0].KeyContent != keyText || out.Identities[0].Password != "pp" {
		t.Fatalf("bad keyText round-trip: %+v", out)
	}
}

func TestIdentityStoreEmpty(t *testing.T) {
	s, _ := NewIdentityStore(t.TempDir())
	out, err := s.Load()
	if err != nil {
		t.Fatalf("load empty: %v", err)
	}
	if out.Identities == nil || len(out.Identities) != 0 {
		t.Fatalf("expected empty, got %+v", out)
	}
}
