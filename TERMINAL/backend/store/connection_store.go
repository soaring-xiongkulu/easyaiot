package store

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"sync"

	"easyaiot/terminal/backend/credentials"
	"easyaiot/terminal/backend/session"
)

const storeFileName = "connections.json"

// PasswordStore encrypts/decrypts individual secret field values in-place.
// Implementations own the master key (OS keychain or master-password derived).
type PasswordStore interface {
	Encrypt(plaintext string) (string, error)
	Decrypt(encoded string) (string, error)
}

type ConnectionStore struct {
	configDir     string
	passwordStore PasswordStore       // nil = passwords kept in JSON (backward compat)
	legacy         LegacyPasswordSource // optional fallback to pre-enc:v1 keychain entries
	mu            sync.Mutex    // serializes Save + populatePasswords writes (STORE-05/06).
	pwdMu         sync.RWMutex  // guards pwdCache for F-110 async keychain fill.
	pwdCache      map[string]string
	lastSavedHash string // F-105: skip no-op rewrites keyed by canonical content hash.
}

func NewConnectionStore(configDir string) (*ConnectionStore, error) {
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return nil, err
	}
	return &ConnectionStore{configDir: configDir}, nil
}

// SetPasswordStore sets the external password store. Once set, passwords
// are written to the store and cleared from the JSON file on save.
func (s *ConnectionStore) SetPasswordStore(ps PasswordStore) {
	s.passwordStore = ps
}

// SetLegacyKeychain wires the pre-enc:v1 keychain so a connection that lacks
// an enc:v1 field can still recover its password from the legacy conn/<id>
// entry. Lazy-migrates the value into enc:v1 on the next save.
func (s *ConnectionStore) SetLegacyKeychain(kc LegacyPasswordSource) {
	s.legacy = kc
}

func (s *ConnectionStore) filePath() string {
	return filepath.Join(s.configDir, storeFileName)
}

func (s *ConnectionStore) Save(data session.ConnectionStoreData) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Deep-copy connections so we don't mutate the caller's backing array
	connections := make([]session.ConnectionConfig, len(data.Connections))
	copy(connections, data.Connections)

	// Encrypt password fields in place before writing JSON.
	for i := range connections {
		conn := &connections[i]
		if conn.AuthType == "identity" {
			// Identity connections obtain both username and credentials solely
			// from the referenced identity (MaterializeIdentity overrides User
			// and Password at connect time). A stale password/user left when
			// switching away from another auth mode is unused — and, if it still
			// holds an enc:v1: field, would be carried verbatim into cloud sync
			// (sync normalization only cleans authType=="password" connections),
			// surfacing as a literal enc:v1: on other devices (issue #711).
			conn.Password = ""
			conn.User = ""
			continue
		}
		// keyText connections carry the inline private-key text in KeyContent —
		// a secret like passwords — so encrypt it before it lands in
		// connections.json. "key" references a path on disk and carries no
		// inline secret here, so it (and everything else) falls through to the
		// plain continue.
		if conn.AuthType == "keyText" {
			if err := encryptSecretField(&conn.KeyContent, s.passwordStore); err != nil {
				return err
			}
			continue
		}
		if conn.AuthType != "password" {
			continue
		}
		if conn.Password == "" {
			// Password cleared — drop cached plaintext so EnsurePassword can't
			// resurrect a deleted password.
			s.pwdMu.Lock()
			delete(s.pwdCache, conn.ID)
			s.pwdMu.Unlock()
			continue
		}
		if s.passwordStore == nil {
			// Fail closed: never write plaintext when no cipher is available.
			return errors.New("passwordStore not initialized; refusing to save plaintext password")
		}
		enc, err := s.passwordStore.Encrypt(conn.Password)
		if err != nil {
			return err
		}
		s.pwdMu.Lock()
		if s.pwdCache == nil {
			s.pwdCache = map[string]string{}
		}
		s.pwdCache[conn.ID] = conn.Password
		s.pwdMu.Unlock()
		conn.Password = enc
	}

	saveData := session.ConnectionStoreData{
		Groups:      data.Groups,
		Connections: connections,
	}
	return s.writeJSONLocked(saveData)
}

// writeJSONLocked serializes data to the connections file atomically.
// F-105: uses json.NewEncoder to stream directly to the temp file (no
// intermediate buffer the size of the output), and skips the temp+sync+rename
// cycle when the canonical content hash matches the last successful save.
// Caller must hold s.mu.
func (s *ConnectionStore) writeJSONLocked(data session.ConnectionStoreData) error {
	preview, err := json.Marshal(data)
	if err != nil {
		return err
	}
	sum := sha256.Sum256(preview)
	hashHex := hex.EncodeToString(sum[:])
	if hashHex == s.lastSavedHash {
		return nil
	}

	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}
	if err := atomicWriteFile(s.filePath(), jsonData, 0600); err != nil {
		return err
	}
	s.lastSavedHash = hashHex
	return nil
}

func (s *ConnectionStore) Load() (session.ConnectionStoreData, error) {
	fileData, err := os.ReadFile(s.filePath())
	if err != nil {
		if os.IsNotExist(err) {
			return session.ConnectionStoreData{
				Groups:      []session.ConnectionGroup{},
				Connections: []session.ConnectionConfig{},
			}, nil
		}
		return session.ConnectionStoreData{}, err
	}

	// Try new format first: {"groups": [...], "connections": [...]}
	var data session.ConnectionStoreData
	if err := json.Unmarshal(fileData, &data); err == nil && (data.Groups != nil || data.Connections != nil) {
		if data.Groups == nil {
			data.Groups = []session.ConnectionGroup{}
		}
		if data.Connections == nil {
			data.Connections = []session.ConnectionConfig{}
		}
		if err := s.populatePasswords(&data); err != nil {
			return session.ConnectionStoreData{}, err
		}
		return data, nil
	}

	// Fallback: old format — plain array of connections
	var connections []session.ConnectionConfig
	if err := json.Unmarshal(fileData, &connections); err != nil {
		// STORE-09: rename corrupt JSON aside before re-attempting.
		quarantineCorrupt(s.filePath())
		return session.ConnectionStoreData{}, err
	}
	data = session.ConnectionStoreData{
		Groups:      []session.ConnectionGroup{},
		Connections: connections,
	}
	if err := s.populatePasswords(&data); err != nil {
		return session.ConnectionStoreData{}, err
	}
	return data, nil
}

func (s *ConnectionStore) populatePasswords(data *session.ConnectionStoreData) error {
	needsSave := false

	for i := range data.Connections {
		conn := &data.Connections[i]
		if conn.AuthType == "keyText" && conn.KeyContent != "" && credentials.IsEncrypted(conn.KeyContent) && s.passwordStore != nil {
			dec, err := s.passwordStore.Decrypt(conn.KeyContent)
			if err != nil {
				return err
			}
			conn.KeyContent = dec
		}
		if conn.AuthType != "password" {
			continue
		}
		if conn.Password == "" {
			// No enc:v1 field. Under the pre-enc:v1 scheme the password lived
			// in the keychain under conn/<id> and the JSON field was omitted;
			// recover it here so the value stays visible without a manual
			// re-entry. Falls back to "" when neither source has it.
			if s.legacy != nil {
				if pw, err := s.legacy.GetPassword(conn.ID); err == nil && pw != "" {
					s.pwdMu.Lock()
					if s.pwdCache == nil {
						s.pwdCache = map[string]string{}
					}
					s.pwdCache[conn.ID] = pw
					s.pwdMu.Unlock()
					conn.Password = pw
					needsSave = true // lazy-migrate into enc:v1 on next save
				}
			}
			continue
		}
		if s.passwordStore == nil {
			continue // no cipher wired — leave as-is (backward compat)
		}
		if credentials.IsEncrypted(conn.Password) {
			pw, err := s.passwordStore.Decrypt(conn.Password)
			if err != nil {
				return err
			}
			s.pwdMu.Lock()
			if s.pwdCache == nil {
				s.pwdCache = map[string]string{}
			}
			s.pwdCache[conn.ID] = pw
			s.pwdMu.Unlock()
			conn.Password = pw
		} else {
			// Legacy plaintext on disk (never migrated to keychain). Keep the
			// plaintext for the caller but re-save so it lands encrypted.
			needsSave = true
		}
	}

	if needsSave {
		clean := *data
		clean.Connections = make([]session.ConnectionConfig, len(data.Connections))
		copy(clean.Connections, data.Connections)
		s.mu.Lock()
		defer s.mu.Unlock()
		return s.writeJSONLocked(s.encryptForSaveLocked(clean))
	}
	return nil
}

// encryptForSaveLocked returns a copy of data with plaintext password fields
// encrypted. Caller must hold s.mu.
func (s *ConnectionStore) encryptForSaveLocked(data session.ConnectionStoreData) session.ConnectionStoreData {
	out := data
	out.Connections = make([]session.ConnectionConfig, len(data.Connections))
	copy(out.Connections, data.Connections)
	for i := range out.Connections {
		conn := &out.Connections[i]
		if conn.AuthType != "password" || conn.Password == "" || credentials.IsEncrypted(conn.Password) {
			continue
		}
		if s.passwordStore == nil {
			continue
		}
		enc, err := s.passwordStore.Encrypt(conn.Password)
		if err != nil {
			continue // best-effort; the plaintext remains, encrypted on next Save
		}
		conn.Password = enc
	}
	return out
}

// EnsurePassword returns the cached decrypted password for a connection ID.
// Load() fills the cache synchronously from encrypted fields, so this is a
// defensive fallback for callers that construct configs without going through
// Load. On a cache miss it tries the legacy keychain (conn/<id>) so a connect
// attempt can still recover a password that was never migrated into enc:v1.
// Returns "" when there is no cached entry and no legacy keychain value.
func (s *ConnectionStore) EnsurePassword(connID string) (string, error) {
	s.pwdMu.RLock()
	pw, ok := s.pwdCache[connID]
	s.pwdMu.RUnlock()
	if ok {
		return pw, nil
	}
	if s.legacy == nil {
		return "", nil
	}
	pw, err := s.legacy.GetPassword(connID)
	if err != nil {
		return "", nil
	}
	if pw != "" {
		s.pwdMu.Lock()
		if s.pwdCache == nil {
			s.pwdCache = map[string]string{}
		}
		s.pwdCache[connID] = pw
		s.pwdMu.Unlock()
	}
	return pw, nil
}
