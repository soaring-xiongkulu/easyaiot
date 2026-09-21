package store

import (
	"encoding/json"
	"os"
	"path/filepath"

	"easyaiot/terminal/backend/session"
)

const tunnelsFileName = "tunnels.json"

// TunnelStore persists the user's SSH tunnel definitions to tunnels.json in the
// app config dir, mirroring QuickCommandsStore.
type TunnelStore struct {
	configDir string
}

func NewTunnelStore(configDir string) *TunnelStore {
	return &TunnelStore{configDir: configDir}
}

func (s *TunnelStore) filePath() string {
	return filepath.Join(s.configDir, tunnelsFileName)
}

func (s *TunnelStore) Save(data session.TunnelStoreData) error {
	bytes, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(s.filePath(), bytes, 0600)
}

func (s *TunnelStore) Load() (session.TunnelStoreData, error) {
	bytes, err := os.ReadFile(s.filePath())
	if err != nil {
		if os.IsNotExist(err) {
			return session.TunnelStoreData{Version: 1, Groups: []session.TunnelGroup{}, Tunnels: []session.Tunnel{}}, nil
		}
		return session.TunnelStoreData{}, err
	}
	var data session.TunnelStoreData
	if err := json.Unmarshal(bytes, &data); err != nil {
		return session.TunnelStoreData{}, err
	}
	if data.Version == 0 {
		data.Version = 1
	}
	return data, nil
}
