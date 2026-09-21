package store

import (
	"encoding/json"
	"os"
	"path/filepath"
)

const quickCommandsFileName = "quickCommands.json"

type QuickCommand struct {
	ID        string `json:"id"`
	Name      string `json:"name,omitempty"`
	Remark    string `json:"remark,omitempty"`
	Command   string `json:"command"`
	GroupID   string `json:"groupId,omitempty"`
	SortOrder int    `json:"sortOrder"`
}

type QuickCommandGroup struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	SortOrder int    `json:"sortOrder"`
}

type QuickCommandData struct {
	Version  int                 `json:"version"`
	Groups   []QuickCommandGroup `json:"groups"`
	Commands []QuickCommand      `json:"commands"`
}

type QuickCommandsStore struct {
	configDir string
}

func NewQuickCommandsStore(configDir string) *QuickCommandsStore {
	return &QuickCommandsStore{configDir: configDir}
}

func (s *QuickCommandsStore) filePath() string {
	return filepath.Join(s.configDir, quickCommandsFileName)
}

func (s *QuickCommandsStore) Save(data QuickCommandData) error {
	bytes, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(s.filePath(), bytes, 0600)
}

func (s *QuickCommandsStore) Load() (QuickCommandData, error) {
	bytes, err := os.ReadFile(s.filePath())
	if err != nil {
		if os.IsNotExist(err) {
			return QuickCommandData{Version: 1, Groups: []QuickCommandGroup{}, Commands: []QuickCommand{}}, nil
		}
		return QuickCommandData{}, err
	}
	var data QuickCommandData
	if err := json.Unmarshal(bytes, &data); err != nil {
		return QuickCommandData{}, err
	}
	if data.Version == 0 {
		data.Version = 1
	}
	return data, nil
}
