package store

import (
	"encoding/json"
	"os"
	"path/filepath"
)

const localStateFileName = "local_state.json"

type LocalState struct {
	SidebarVisible    bool     `json:"sidebarVisible"`
	AISidebarVisible  bool     `json:"aiSidebarVisible"`
	CollapsedGroupIds []string `json:"collapsedGroupIds"`
	// Collapsed quick-command group ids (plus "__ungrouped__"). Local-only
	// UI state, never synced; groups absent from the list stay expanded.
	CollapsedQuickCommandGroupIds []string `json:"collapsedQuickCommandGroupIds"`
	WindowX                       int      `json:"windowX"`
	WindowY                       int      `json:"windowY"`
	WindowWidth                   int      `json:"windowWidth"`
	WindowHeight                  int      `json:"windowHeight"`
	WindowMaximised               bool     `json:"windowMaximised"`
	// Background image — local-only appearance, never synced.
	BackgroundEnabled bool   `json:"backgroundEnabled"`
	BackgroundImage   string `json:"backgroundImage"`
	BackgroundOpacity int    `json:"backgroundOpacity"`
	BackgroundBlur    int    `json:"backgroundBlur"`
	BackgroundFit     string `json:"backgroundFit"`
	// SystemTitleBar switches the window to the OS native frame instead of
	// the built-in one. Read at startup only — changing it needs a restart.
	SystemTitleBar bool `json:"systemTitleBar"`
	// ExternalEditor command used to open remote files in an external editor
	// (SFTP "edit externally"). Local-only preference, never synced.
	ExternalEditor string `json:"externalEditor"`
	// SftpHiddenColumns lists SFTP file-list columns hidden via the header
	// context menu (type/modTime/size/permission/owner/group). Local-only UI
	// state, never synced; columns absent from the list stay visible.
	SftpHiddenColumns []string `json:"sftpHiddenColumns,omitempty"`
}

type LocalStateStore struct {
	configDir string
}

func NewLocalStateStore(configDir string) *LocalStateStore {
	return &LocalStateStore{configDir: configDir}
}

func (s *LocalStateStore) filePath() string {
	return filepath.Join(s.configDir, localStateFileName)
}

func (s *LocalStateStore) Save(state LocalState) error {
	bytes, err := json.MarshalIndent(state, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(s.filePath(), bytes, 0600)
}

func defaultLocalState() LocalState {
	return LocalState{
		SidebarVisible:                true,
		AISidebarVisible:              true,
		CollapsedQuickCommandGroupIds: []string{},
		BackgroundOpacity:             60,
		BackgroundBlur:                3,
		BackgroundFit:                 "cover",
	}
}

func (s *LocalStateStore) Load() (LocalState, error) {
	bytes, err := os.ReadFile(s.filePath())
	if err != nil {
		if os.IsNotExist(err) {
			return defaultLocalState(), nil
		}
		return LocalState{}, err
	}
	// Start from defaults so fields missing in older configs keep their
	// intended values instead of Go zero values (e.g. opacity/blur = 0).
	state := defaultLocalState()
	if err := json.Unmarshal(bytes, &state); err != nil {
		return defaultLocalState(), nil
	}
	return state, nil
}
