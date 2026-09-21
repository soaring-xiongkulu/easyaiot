package store

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"easyaiot/terminal/backend/session"
)

// LegacyPasswordSource reads secrets from the legacy keychain entries
// (conn/<id>, ai-model/<id>). *sync.Keychain satisfies this interface.
type LegacyPasswordSource interface {
	GetPassword(connID string) (string, error)
	GetModelAPIKey(modelID string) (string, error)
}

// MigrateLegacyKeychainToInPlace reads plaintext secrets from legacy keychain
// entries and writes them encrypted into connections.json / settings.json.
// Legacy keychain entries are NOT deleted (rollback safety).
func MigrateLegacyKeychainToInPlace(configDir string, legacy LegacyPasswordSource, cred PasswordStore) (int, error) {
	count := 0

	// connections.json
	connPath := filepath.Join(configDir, storeFileName)
	if data, err := os.ReadFile(connPath); err == nil {
		var d session.ConnectionStoreData
		if err := json.Unmarshal(data, &d); err != nil {
			// Previously swallowed — surface it so a malformed file doesn't
			// silently leave every connection's password unmigrated.
			return count, fmt.Errorf("parse connections for migration: %w", err)
		}
		changed := false
		for i := range d.Connections {
			conn := &d.Connections[i]
			if conn.AuthType != "password" || conn.Password != "" {
				continue
			}
			if pw, err := legacy.GetPassword(conn.ID); err == nil && pw != "" {
				enc, err := cred.Encrypt(pw)
				if err != nil {
					return count, err
				}
				conn.Password = enc
				count++
				changed = true
			}
		}
		if changed {
			out, _ := json.MarshalIndent(d, "", "  ")
			if err := atomicWriteFile(connPath, out, 0600); err != nil {
				return count, err
			}
		}
	}

	// settings.json
	setPath := filepath.Join(configDir, settingsFileName)
	if data, err := os.ReadFile(setPath); err == nil {
		var s AppSettings
		if err := json.Unmarshal(data, &s); err != nil {
			return count, fmt.Errorf("parse settings for migration: %w", err)
		}
		changed := false
		for i := range s.AI.Models {
			m := &s.AI.Models[i]
			if m.APIKey != "" {
				continue
			}
			if ak, err := legacy.GetModelAPIKey(m.ID); err == nil && ak != "" {
				enc, err := cred.Encrypt(ak)
				if err != nil {
					return count, err
				}
				m.APIKey = enc
				count++
				changed = true
			}
		}
		if changed {
			out, _ := json.Marshal(s)
			if err := atomicWriteFile(setPath, out, 0600); err != nil {
				return count, err
			}
		}
	}

	return count, nil
}
