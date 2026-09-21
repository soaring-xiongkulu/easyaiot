package store

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"sync"

	"easyaiot/terminal/backend/credentials"
)

const aiConfigFileName = "ai.json"

// AIStoreData is the syncable slice of the AI settings: the model catalog and
// the agent turn limit. It lives in its own ai.json file so it can ride the
// cloud sync while the rest of settings.json stays device-local. The active
// model choice deliberately stays in settings.json — it is per-device
// "current selection" state, not a shareable asset.
type AIStoreData struct {
	MaxTurns *int            `json:"maxTurns"`
	Models   []AIModelConfig `json:"models"`
}

type AIConfigStore struct {
	configDir     string
	passwordStore PasswordStore
	mu            sync.Mutex
}

func NewAIConfigStore(configDir string) (*AIConfigStore, error) {
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return nil, err
	}
	return &AIConfigStore{configDir: configDir}, nil
}

func (s *AIConfigStore) SetPasswordStore(ps PasswordStore) {
	s.passwordStore = ps
}

func (s *AIConfigStore) filePath() string {
	return filepath.Join(s.configDir, aiConfigFileName)
}

// Exists reports whether ai.json is on disk yet. The one-shot settings→ai
// migration uses this to stay idempotent.
func (s *AIConfigStore) Exists() bool {
	_, err := os.Stat(s.filePath())
	return err == nil
}

// Save writes ai.json, encrypting model apiKeys in place (same policy as
// settings.json: best-effort — when no passwordStore is wired the values
// are kept as-is rather than failing the save).
func (s *AIConfigStore) Save(cfg AIStoreData) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	models := make([]AIModelConfig, len(cfg.Models))
	copy(models, cfg.Models)
	for i := range models {
		m := &models[i]
		if m.APIKey == "" || credentials.IsEncrypted(m.APIKey) {
			continue
		}
		if s.passwordStore == nil {
			continue
		}
		enc, err := s.passwordStore.Encrypt(m.APIKey)
		if err != nil {
			return err
		}
		m.APIKey = enc
	}
	cfg.Models = models
	if cfg.Models == nil {
		cfg.Models = []AIModelConfig{}
	}

	var buf bytes.Buffer
	if err := json.NewEncoder(&buf).Encode(cfg); err != nil {
		return err
	}
	return atomicWriteFile(s.filePath(), buf.Bytes(), 0600)
}

// Load reads ai.json. A missing file yields the default config; a corrupt
// file is quarantined before falling back, matching SettingsStore's
// STORE-09 behaviour.
func (s *AIConfigStore) Load() (AIStoreData, error) {
	data, err := os.ReadFile(s.filePath())
	if err != nil {
		if os.IsNotExist(err) {
			return defaultAIConfig(), nil
		}
		return AIStoreData{}, err
	}
	var cfg AIStoreData
	if err := json.Unmarshal(data, &cfg); err != nil {
		s.mu.Lock()
		quarantineCorrupt(s.filePath())
		s.mu.Unlock()
		return defaultAIConfig(), nil
	}

	s.mu.Lock()
	ps := s.passwordStore
	s.mu.Unlock()

	needsSave := false
	for i := range cfg.Models {
		m := &cfg.Models[i]
		if m.APIKey == "" || ps == nil {
			continue
		}
		if credentials.IsEncrypted(m.APIKey) {
			ak, err := ps.Decrypt(m.APIKey)
			if err != nil {
				return AIStoreData{}, err
			}
			m.APIKey = ak
		} else {
			needsSave = true
		}
	}
	if cfg.MaxTurns == nil {
		cfg.MaxTurns = intPtr(defaultMaxTurns)
		needsSave = true
	}
	if needsSave {
		_ = s.Save(cfg)
	}
	return cfg, nil
}

// MigrateFromSettings seeds ai.json from the AI block of settings.json on
// first run after the split. The settings copy is deliberately left intact
// so a user rolling back to a build without ai.json still finds their
// models there. Idempotent: skipped once ai.json exists.
func (s *AIConfigStore) MigrateFromSettingsIfNeeded(settings AppSettings) error {
	if s.Exists() {
		return nil
	}
	if len(settings.AI.Models) == 0 && settings.AI.MaxTurns == nil {
		return nil
	}
	maxTurns := settings.AI.MaxTurns
	if maxTurns == nil {
		t := defaultMaxTurns
		maxTurns = &t
	}
	return s.Save(AIStoreData{MaxTurns: maxTurns, Models: settings.AI.Models})
}
