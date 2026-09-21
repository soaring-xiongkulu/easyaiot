package store

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"sync"

	"easyaiot/terminal/backend/credentials"
	"easyaiot/terminal/backend/session"
)

const identityStoreFileName = "identities.json"

type IdentityStore struct {
	configDir     string
	passwordStore PasswordStore // nil = refuse to write plaintext passwords
	mu            sync.Mutex    // serializes Save + Load password rewrites
}

func NewIdentityStore(configDir string) (*IdentityStore, error) {
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return nil, err
	}
	return &IdentityStore{configDir: configDir}, nil
}

// SetPasswordStore sets the external password store used to encrypt the
// Password field on save and decrypt it on load.
func (s *IdentityStore) SetPasswordStore(ps PasswordStore) {
	s.passwordStore = ps
}

func (s *IdentityStore) filePath() string {
	return filepath.Join(s.configDir, identityStoreFileName)
}

// Save writes data to identities.json, encrypting only the Password field.
// It fails closed rather than persisting a plaintext password when no
// passwordStore is wired. Values already prefixed (credentials.IsEncrypted)
// are skipped so a save doesn't double-encrypt previously encrypted data.
func (s *IdentityStore) Save(data session.IdentityStoreData) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Deep-copy identities so we don't mutate the caller's backing array.
	identities := make([]session.Identity, len(data.Identities))
	copy(identities, data.Identities)

	for i := range identities {
		id := &identities[i]
		// Both the password/passphrase and the inline key text (keyText) are
		// secrets; encrypt whichever is present, leaving empty values alone.
		for _, field := range []*string{&id.Password, &id.KeyContent} {
			if err := encryptSecretField(field, s.passwordStore); err != nil {
				return err
			}
		}
	}

	jsonData, err := json.MarshalIndent(session.IdentityStoreData{Identities: identities}, "", "  ")
	if err != nil {
		return err
	}
	return atomicWriteFile(s.filePath(), jsonData, 0600)
}

// Load reads identities.json, returning an empty store when the file does not
// exist, quarantining+erroring on corrupt JSON, and decrypting the Password
// field of each identity.
func (s *IdentityStore) Load() (session.IdentityStoreData, error) {
	data, err := os.ReadFile(s.filePath())
	if err != nil {
		if os.IsNotExist(err) {
			return session.IdentityStoreData{Identities: []session.Identity{}}, nil
		}
		return session.IdentityStoreData{}, err
	}
	var out session.IdentityStoreData
	if err := json.Unmarshal(data, &out); err != nil {
		quarantineCorrupt(s.filePath())
		return session.IdentityStoreData{}, err
	}
	if out.Identities == nil {
		out.Identities = []session.Identity{}
	}
	for i := range out.Identities {
		id := &out.Identities[i]
		for _, field := range []*string{&id.Password, &id.KeyContent} {
			if *field == "" || !credentials.IsEncrypted(*field) || s.passwordStore == nil {
				continue
			}
			dec, err := s.passwordStore.Decrypt(*field)
			if err != nil {
				return session.IdentityStoreData{}, err
			}
			*field = dec
		}
	}
	return out, nil
}

// encryptSecretField encrypts a secret field in place using the password store,
// skipping empty and already-encrypted values. Returns an error (failing
// closed) when a plaintext secret would be persisted with no cipher wired.
func encryptSecretField(field *string, ps PasswordStore) error {
	if *field == "" || credentials.IsEncrypted(*field) {
		return nil
	}
	if ps == nil {
		return errors.New("passwordStore not initialized; refusing to save plaintext secret")
	}
	enc, err := ps.Encrypt(*field)
	if err != nil {
		return err
	}
	*field = enc
	return nil
}
