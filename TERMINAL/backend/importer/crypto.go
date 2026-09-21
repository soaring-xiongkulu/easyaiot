package importer

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"

	"easyaiot/terminal/backend/credentials"
	"golang.org/x/crypto/pbkdf2"
)

const (
	kdfAlgo       = "pbkdf2-sha256"
	kdfIterations = 100000
	keyLen        = 32 // AES-256
	saltLen       = 16
)

func newSalt() ([]byte, error) {
	s := make([]byte, saltLen)
	if _, err := rand.Read(s); err != nil {
		return nil, err
	}
	return s, nil
}

func deriveKey(passphrase string, salt []byte, iterations int) []byte {
	return pbkdf2.Key([]byte(passphrase), salt, iterations, keyLen, sha256.New)
}

func encryptField(plaintext, passphrase string, salt []byte) (string, error) {
	return credentials.EncryptField(plaintext, deriveKey(passphrase, salt, kdfIterations))
}

func decryptField(encoded, passphrase string, salt []byte) (string, error) {
	return credentials.DecryptField(encoded, deriveKey(passphrase, salt, kdfIterations))
}

func encodeSalt(salt []byte) string { return base64.StdEncoding.EncodeToString(salt) }
func decodeSalt(s string) ([]byte, error) { return base64.StdEncoding.DecodeString(s) }
