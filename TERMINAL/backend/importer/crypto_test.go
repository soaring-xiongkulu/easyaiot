package importer

import (
	"strings"
	"testing"
)

func TestEncryptDecryptRoundTrip(t *testing.T) {
	salt, err := newSalt()
	if err != nil {
		t.Fatalf("newSalt: %v", err)
	}
	enc, err := encryptField("hunter2", "correct horse", salt)
	if err != nil {
		t.Fatalf("encryptField: %v", err)
	}
	if strings.Contains(enc, "hunter2") {
		t.Fatalf("ciphertext leaks plaintext: %q", enc)
	}
	got, err := decryptField(enc, "correct horse", salt)
	if err != nil {
		t.Fatalf("decryptField: %v", err)
	}
	if got != "hunter2" {
		t.Fatalf("round trip mismatch: got %q", got)
	}
}

func TestDecryptWrongPasswordFails(t *testing.T) {
	salt, _ := newSalt()
	enc, _ := encryptField("secret", "right", salt)
	if _, err := decryptField(enc, "wrong", salt); err == nil {
		t.Fatalf("expected error decrypting with wrong password")
	}
}

func TestNewIDsUnique(t *testing.T) {
	seen := map[string]bool{}
	for i := 0; i < 1000; i++ {
		id := newConnectionID()
		if seen[id] {
			t.Fatalf("duplicate id %q", id)
		}
		seen[id] = true
		if !strings.HasPrefix(id, "conn-") {
			t.Fatalf("bad prefix: %q", id)
		}
	}
}
