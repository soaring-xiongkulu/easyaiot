package sync

import (
	"bytes"
	"testing"
)

// TestEncryptDecryptWithAAD_RoundTrip verifies that encryptBytesWithAAD +
// decryptBytesWithAAD round-trip when the same AAD is provided.
func TestEncryptDecryptWithAAD_RoundTrip(t *testing.T) {
	key := []byte("0123456789abcdef0123456789abcdef") // 32 bytes — AES-256
	plaintext := []byte(`{"theme":"dark"}`)
	aad := []byte("connections.json")

	encoded, err := encryptBytesWithAAD(plaintext, key, aad)
	if err != nil {
		t.Fatalf("encrypt: %v", err)
	}
	got, err := decryptBytesWithAAD(encoded, key, aad)
	if err != nil {
		t.Fatalf("decrypt: %v", err)
	}
	if !bytes.Equal(got, plaintext) {
		t.Fatalf("round-trip mismatch:\n got %q\nwant %q", got, plaintext)
	}
}

// TestEncryptBytesWithAAD_AADMismatchRejected is the cross-file swap guard
// (SYNC-P1-1): an attacker who can paste ciphertext from one file over
// another (e.g. settings.json.enc → connections.json.enc) must fail the
// AAD check on decryption.
func TestEncryptBytesWithAAD_AADMismatchRejected(t *testing.T) {
	key := []byte("0123456789abcdef0123456789abcdef")
	plaintext := []byte(`{"password":"s3cret"}`)
	connAAD := []byte("connections.json")
	settingsAAD := []byte("settings.json")

	// Encrypt under connections.json AAD.
	encoded, err := encryptBytesWithAAD(plaintext, key, connAAD)
	if err != nil {
		t.Fatalf("encrypt: %v", err)
	}

	// Attempt to decrypt under settings.json AAD — must fail.
	if _, err := decryptBytesWithAAD(encoded, key, settingsAAD); err == nil {
		t.Fatalf("AAD mismatch was accepted — cross-file ciphertext swap is undetected")
	}

	// Sanity: decrypting under the correct AAD still works.
	got, err := decryptBytesWithAAD(encoded, key, connAAD)
	if err != nil {
		t.Fatalf("decrypt with correct AAD: %v", err)
	}
	if !bytes.Equal(got, plaintext) {
		t.Fatalf("plaintext mismatch")
	}
}

func TestIsEncryptedField(t *testing.T) {
	cases := []struct {
		in   string
		want bool
	}{
		{"", false},
		{"plaintext", false},
		{"enc:v1:AAAA:BBBB", true},
		{"enc:v1:", true},        // malformed prefix — still treated as opaque by design
		{"ENC:v1:AAAA", false},   // case-sensitive
		{"xenc:v1:AAAA", false},  // prefix must be at the start
	}
	for _, c := range cases {
		if got := isEncryptedField(c.in); got != c.want {
			t.Errorf("isEncryptedField(%q) = %v, want %v", c.in, got, c.want)
		}
	}
}

// TestEncryptBytes_NilAADStillWorks ensures backward compat: existing
// callers using encryptBytes (which pass nil AAD internally) continue to
// round-trip unchanged.
func TestEncryptBytes_NilAADStillWorks(t *testing.T) {
	key := []byte("0123456789abcdef0123456789abcdef")
	plaintext := []byte(`{"theme":"dark"}`)

	encoded, err := encryptBytes(plaintext, key)
	if err != nil {
		t.Fatalf("encrypt: %v", err)
	}
	got, err := decryptBytes(encoded, key)
	if err != nil {
		t.Fatalf("decrypt: %v", err)
	}
	if !bytes.Equal(got, plaintext) {
		t.Fatalf("round-trip mismatch:\n got %q\nwant %q", got, plaintext)
	}
}