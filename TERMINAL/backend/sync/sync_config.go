package sync

import (
	"encoding/json"
	"os"
	"path/filepath"
	"time"
)

const syncConfigFileName = "sync-config.json"

type SyncConfig struct {
	RepoURL        string    `json:"repoUrl"`
	Branch         string    `json:"branch"`
	Username       string    `json:"username"`
	AutoSync       bool      `json:"autoSync"`
	LastSyncAt     time.Time `json:"lastSyncAt"`
	LastSyncStatus string    `json:"lastSyncStatus"`
	LastSyncError  string    `json:"lastSyncError"`
}

type SyncConfigStore struct {
	configDir string
}

func NewSyncConfigStore(configDir string) *SyncConfigStore {
	return &SyncConfigStore{configDir: configDir}
}

func (s *SyncConfigStore) filePath() string {
	return filepath.Join(s.configDir, syncConfigFileName)
}

func (s *SyncConfigStore) Save(config SyncConfig) error {
	data, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(s.filePath(), data, 0600)
}

func (s *SyncConfigStore) Load() (SyncConfig, error) {
	data, err := os.ReadFile(s.filePath())
	if err != nil {
		if os.IsNotExist(err) {
			return SyncConfig{Branch: "main"}, nil
		}
		return SyncConfig{}, err
	}
	var config SyncConfig
	if err := json.Unmarshal(data, &config); err != nil {
		return SyncConfig{Branch: "main"}, nil
	}
	if config.Branch == "" {
		config.Branch = "main"
	}
	return config, nil
}
