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

const proxyStoreFileName = "proxies.json"

type ProxyStore struct {
	configDir     string
	passwordStore PasswordStore // nil = refuse to write plaintext passwords
	mu            sync.Mutex    // serializes Save + Load password rewrites
}

func NewProxyStore(configDir string) (*ProxyStore, error) {
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return nil, err
	}
	return &ProxyStore{configDir: configDir}, nil
}

func (s *ProxyStore) SetPasswordStore(ps PasswordStore) { s.passwordStore = ps }

func (s *ProxyStore) filePath() string {
	return filepath.Join(s.configDir, proxyStoreFileName)
}

// Save writes data to proxies.json, encrypting only the Pass field. It fails
// closed rather than persisting a plaintext password when no passwordStore is
// wired. Values already prefixed (credentials.IsEncrypted) are skipped so a
// save doesn't double-encrypt previously encrypted data.
func (s *ProxyStore) Save(data session.ProxyStoreData) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Deep-copy proxies so we don't mutate the caller's backing array.
	proxies := make([]session.Proxy, len(data.Proxies))
	copy(proxies, data.Proxies)

	for i := range proxies {
		p := &proxies[i]
		if p.Pass == "" || credentials.IsEncrypted(p.Pass) {
			continue
		}
		if s.passwordStore == nil {
			return errors.New("passwordStore not initialized; refusing to save plaintext password")
		}
		enc, err := s.passwordStore.Encrypt(p.Pass)
		if err != nil {
			return err
		}
		p.Pass = enc
	}

	jsonData, err := json.MarshalIndent(session.ProxyStoreData{Proxies: proxies}, "", "  ")
	if err != nil {
		return err
	}
	return atomicWriteFile(s.filePath(), jsonData, 0600)
}

// Load reads proxies.json, returning an empty store when the file does not
// exist, quarantining+erroring on corrupt JSON, and decrypting the Pass field
// of each proxy.
func (s *ProxyStore) Load() (session.ProxyStoreData, error) {
	data, err := os.ReadFile(s.filePath())
	if err != nil {
		if os.IsNotExist(err) {
			return session.ProxyStoreData{Proxies: []session.Proxy{}}, nil
		}
		return session.ProxyStoreData{}, err
	}
	var out session.ProxyStoreData
	if err := json.Unmarshal(data, &out); err != nil {
		quarantineCorrupt(s.filePath())
		return session.ProxyStoreData{}, err
	}
	if out.Proxies == nil {
		out.Proxies = []session.Proxy{}
	}
	for i := range out.Proxies {
		p := &out.Proxies[i]
		if p.Pass != "" && credentials.IsEncrypted(p.Pass) && s.passwordStore != nil {
			pw, err := s.passwordStore.Decrypt(p.Pass)
			if err != nil {
				return session.ProxyStoreData{}, err
			}
			p.Pass = pw
		}
	}
	return out, nil
}
