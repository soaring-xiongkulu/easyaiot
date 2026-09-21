package importer

import (
	"bytes"
	"crypto/aes"
	"crypto/cipher"
	"encoding/base64"
	"os"
	"path/filepath"
	"testing"
)

// TestParseWindTermFlatKeys verifies the real WindTerm flat dotted-key layout
// (session.protocol, session.target, …) and the inline-JSON autoLogin string.
func TestParseWindTermFlatKeys(t *testing.T) {
	data := []byte(`[{
		"session.protocol": "SSH",
		"session.target": "deploy@192.168.1.10",
		"session.port": 2222,
		"session.label": "Prod web",
		"session.group": "prod>web",
		"session.autoLogin": "{\"Password\":\"secret\",\"PasswordEnabled\":true,\"session.user\":\"deploy\"}"
	}]`)
	res, err := parseWindTerm(data, "", ParseOptions{})
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if len(res.Connections) != 1 {
		t.Fatalf("expected 1 connection, got %d", len(res.Connections))
	}
	c := res.Connections[0]
	if c.Type != "ssh" || c.Host != "192.168.1.10" || c.Port != 2222 || c.User != "deploy" ||
		c.Password != "secret" || c.AuthType != "password" {
		t.Fatalf("mapping wrong: %+v", c)
	}
	if c.Name != "Prod web" {
		t.Fatalf("name %q", c.Name)
	}
	if len(res.Groups) != 2 || res.Groups[0].Name != "prod" || res.Groups[1].Name != "web" {
		t.Fatalf("groups: %+v", res.Groups)
	}
}

// TestParseWindTermEncryptedAutoLogin verifies AES-256-CBC decryption of the
// base64 autoLogin blob using the PBKDF2-SHA3-512-derived key (fingerprint salt).
func TestParseWindTermEncryptedAutoLogin(t *testing.T) {
	dir := t.TempDir()
	profile := filepath.Join(dir, "default.v10")
	terminal := filepath.Join(profile, "terminal")
	if err := os.MkdirAll(terminal, 0o755); err != nil {
		t.Fatal(err)
	}
	const fingerprint = "fp-salt"
	const master = "master-secret"

	encrypted := windTermTestEncrypt(`{"Password":"hunter2","PasswordEnabled":true,"session.user":"root"}`, deriveWindTermKey(fingerprint, master))

	if err := os.WriteFile(filepath.Join(profile, "user.config"),
		[]byte(`{"application.fingerprint":"`+fingerprint+`","application.masterPassword":true}`), 0o644); err != nil {
		t.Fatal(err)
	}
	sessions := `[{"session.protocol":"SSH","session.target":"10.0.0.4","session.port":22,"session.autoLogin":"` + encrypted + `"}]`
	srcPath := filepath.Join(terminal, "user.sessions")
	if err := os.WriteFile(srcPath, []byte(sessions), 0o644); err != nil {
		t.Fatal(err)
	}

	res, err := parseWindTerm([]byte(sessions), srcPath, ParseOptions{Password: master})
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	c := res.Connections[0]
	if c.Password != "hunter2" || c.User != "root" || c.AuthType != "password" {
		t.Fatalf("decrypt wrong: %+v", c)
	}
}

// TestParseWindTermRequiresMasterPassword verifies the master-password gate.
func TestParseWindTermRequiresMasterPassword(t *testing.T) {
	dir := t.TempDir()
	profile := filepath.Join(dir, "default.v10")
	terminal := filepath.Join(profile, "terminal")
	if err := os.MkdirAll(terminal, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(profile, "user.config"),
		[]byte(`{"application.fingerprint":"fp-salt","application.masterPassword":true}`), 0o644); err != nil {
		t.Fatal(err)
	}
	srcPath := filepath.Join(terminal, "user.sessions")
	if err := os.WriteFile(srcPath, []byte(`[]`), 0o644); err != nil {
		t.Fatal(err)
	}

	if _, err := parseWindTerm([]byte(`[]`), srcPath, ParseOptions{}); err == nil {
		t.Fatal("expected master-password-required error, got nil")
	}
}

// windTermTestEncrypt AES-256-CBC encrypts with PKCS#7 padding, returning base64
// — the inverse of windTermDecrypt for test fixtures.
func windTermTestEncrypt(plaintext string, k *windTermKey) string {
	block, _ := aes.NewCipher(k.key)
	bs := block.BlockSize()
	pad := bs - len(plaintext)%bs
	padded := append([]byte(plaintext), bytes.Repeat([]byte{byte(pad)}, pad)...)
	out := make([]byte, len(padded))
	cipher.NewCBCEncrypter(block, k.iv).CryptBlocks(out, padded)
	return base64.StdEncoding.EncodeToString(out)
}
