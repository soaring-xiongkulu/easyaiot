package credentials

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"io"
	"strings"
)

// Prefix is the wire-format marker for an in-place encrypted field value.
const Prefix = "enc:v1:"

// IsEncrypted reports whether s is an in-place encrypted field value.
func IsEncrypted(s string) bool { return strings.HasPrefix(s, Prefix) }

// EncryptField encrypts plaintext under key, returning "enc:v1:<nonce>:<ciphertext>".
// A fresh random nonce is used per call.
func EncryptField(plaintext string, key []byte) (string, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return "", fmt.Errorf("create cipher: %w", err)
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", fmt.Errorf("create gcm: %w", err)
	}
	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return "", fmt.Errorf("generate nonce: %w", err)
	}
	sealed := gcm.Seal(nil, nonce, []byte(plaintext), nil)
	return Prefix +
		base64.StdEncoding.EncodeToString(nonce) + ":" +
		base64.StdEncoding.EncodeToString(sealed), nil
}

// DecryptField decrypts an EncryptField value. It errors on a malformed
// value or a wrong key (GCM tag mismatch).
func DecryptField(encoded string, key []byte) (string, error) {
	if !strings.HasPrefix(encoded, Prefix) {
		return "", fmt.Errorf("not an encrypted field")
	}
	body := strings.TrimPrefix(encoded, Prefix)
	parts := strings.SplitN(body, ":", 2)
	if len(parts) != 2 {
		return "", fmt.Errorf("malformed encrypted field")
	}
	nonce, err := base64.StdEncoding.DecodeString(parts[0])
	if err != nil {
		return "", fmt.Errorf("decode nonce: %w", err)
	}
	sealed, err := base64.StdEncoding.DecodeString(parts[1])
	if err != nil {
		return "", fmt.Errorf("decode ciphertext: %w", err)
	}
	block, err := aes.NewCipher(key)
	if err != nil {
		return "", fmt.Errorf("create cipher: %w", err)
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", fmt.Errorf("create gcm: %w", err)
	}
	if len(nonce) != gcm.NonceSize() {
		return "", fmt.Errorf("invalid nonce length %d", len(nonce))
	}
	plain, err := gcm.Open(nil, nonce, sealed, nil)
	if err != nil {
		return "", fmt.Errorf("decrypt: %w", err)
	}
	return string(plain), nil
}
