package sync

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"fmt"

	"golang.org/x/crypto/pbkdf2"
)

const keychainService = "Terminal"

const (
	pbkdf2Iterations = 600000
	keyLength        = 32
	saltLength       = 16
)

type Keychain struct{}

func NewKeychain() *Keychain { return &Keychain{} }

func (k *Keychain) Get(key string) (string, error) {
	return keychainGet(keychainService, key)
}

func (k *Keychain) Set(key, value string) error {
	return keychainSet(keychainService, key, value)
}

func (k *Keychain) Delete(key string) error {
	return keychainDelete(keychainService, key)
}

// GetEncryptionKey retrieves the derived encryption key from OS keychain.
func (k *Keychain) GetEncryptionKey() ([]byte, error) {
	const keyName = "encryption-key"
	hexKey, err := k.Get(keyName)
	if err != nil {
		return nil, fmt.Errorf("encryption key not found: %w", err)
	}
	return hex.DecodeString(hexKey)
}

// StoreEncryptionKey stores the derived encryption key in OS keychain.
func (k *Keychain) StoreEncryptionKey(key []byte) error {
	return k.Set("encryption-key", hex.EncodeToString(key))
}

func (k *Keychain) GetGitToken() (string, error) {
	token, err := k.Get("git-token")
	if err != nil {
		return "", nil
	}
	return token, nil
}

func (k *Keychain) SetGitToken(token string) error {
	if token == "" {
		return k.Delete("git-token")
	}
	return k.Set("git-token", token)
}
func (k *Keychain) GetPassword(connID string) (string, error) {
	password, err := k.Get("conn/" + connID)
	if err != nil {
		return "", nil
	}
	return password, nil
}

func (k *Keychain) SetPassword(connID, password string) error {
	if password == "" {
		return k.Delete("conn/" + connID)
	}
	return k.Set("conn/"+connID, password)
}

func (k *Keychain) DeletePassword(connID string) error {
	return k.Delete("conn/" + connID)
}

// DeriveKey derives a 32-byte AES-256 key from a password and salt using PBKDF2-SHA256.
func DeriveKey(password string, salt []byte) []byte {
	return pbkdf2.Key([]byte(password), salt, pbkdf2Iterations, keyLength, sha256.New)
}

// GenerateSalt generates a random 16-byte salt.
func GenerateSalt() ([]byte, error) {
	salt := make([]byte, saltLength)
	if _, err := rand.Read(salt); err != nil {
		return nil, fmt.Errorf("generate salt: %w", err)
	}
	return salt, nil
}
