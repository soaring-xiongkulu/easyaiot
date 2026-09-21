package credentials

import (
	"encoding/base64"
	"strings"
	"testing"
)

func TestEncryptDecryptRoundTrip(t *testing.T) {
	key := make([]byte, 32)
	for i := range key {
		key[i] = byte(i)
	}
	enc, err := EncryptField("hunter2", key)
	if err != nil {
		t.Fatalf("EncryptField: %v", err)
	}
	if !IsEncrypted(enc) {
		t.Fatalf("expected %q prefix, got %q", Prefix, enc)
	}
	if enc == "hunter2" {
		t.Fatalf("ciphertext equals plaintext")
	}
	got, err := DecryptField(enc, key)
	if err != nil {
		t.Fatalf("DecryptField: %v", err)
	}
	if got != "hunter2" {
		t.Fatalf("round trip = %q, want hunter2", got)
	}
}

func TestEncryptFieldUsesFreshNonce(t *testing.T) {
	key := make([]byte, 32)
	a, _ := EncryptField("same", key)
	b, _ := EncryptField("same", key)
	if a == b {
		t.Fatalf("same plaintext produced identical ciphertext")
	}
}

func TestDecryptFieldWrongKeyFails(t *testing.T) {
	k1 := make([]byte, 32)
	k2 := make([]byte, 32)
	k2[0] = 1
	enc, _ := EncryptField("secret", k1)
	if _, err := DecryptField(enc, k2); err == nil {
		t.Fatalf("decrypt with wrong key should fail")
	}
}

func TestDecryptFieldRejectsMalformed(t *testing.T) {
	key := make([]byte, 32)
	badNonce := "enc:v1:" + base64.StdEncoding.EncodeToString([]byte("12345678")) + ":AAAA"
	for _, bad := range []string{"", "not-encrypted", "enc:v1:", "enc:v1:abc", badNonce} {
		if _, err := DecryptField(bad, key); err == nil {
			t.Fatalf("DecryptField(%q) should fail", bad)
		}
	}
	if IsEncrypted("plain") {
		t.Fatalf("IsEncrypted should be false for plaintext")
	}
	if !strings.HasPrefix("enc:v1:x:y", Prefix) {
		t.Fatalf("prefix constant mismatch")
	}
}
