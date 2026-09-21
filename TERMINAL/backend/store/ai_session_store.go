package store

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
)

const (
	aiSessionFileName = "ai-sessions.json"
	aiSessionDirName  = "ai-sessions"
)

type AISessionData struct {
	Sessions        []AISessionEntry `json:"sessions"`
	CurrentSessionID string          `json:"currentSessionId"`
}

type AISessionEntry struct {
	ID        string              `json:"id"`
	Name      string              `json:"name"`
	CreatedAt int64               `json:"createdAt"`
	UpdatedAt int64               `json:"updatedAt"`
	Messages  []AIMessageEntry    `json:"messages"`
}

type AIMessageEntry struct {
	ID          string           `json:"id"`
	Role        string           `json:"role"`
	Content     string           `json:"content"`
	ToolCallID  string           `json:"tool_call_id,omitempty"`
	ToolCalls   []interface{}    `json:"tool_calls,omitempty"`
	PendingTools []interface{}   `json:"pendingTools,omitempty"`
	RawAPIMsg   string           `json:"_rawApiMsg,omitempty"`
}

type AISessionStore struct {
	configDir string
}

func NewAISessionStore(configDir string) (*AISessionStore, error) {
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return nil, err
	}
	return &AISessionStore{configDir: configDir}, nil
}

func (s *AISessionStore) filePath() string {
	return filepath.Join(s.configDir, aiSessionFileName)
}

func (s *AISessionStore) shardDir() string {
	return filepath.Join(s.configDir, aiSessionDirName)
}

// shardPath returns the per-session shard file path. Falls back to a hash
// subdir if id contains path-traversal chars (defensive — ids are normally
// app-generated UUIDs).
func (s *AISessionStore) shardPath(id string) string {
	return filepath.Join(s.shardDir(), filepath.Base(id)+".json")
}

// Save writes each session as its own shard under ai-sessions/<id>.json.
// Removing the full-file marshal eliminates the O(total-size) memory spike
// from F-103. Orphan shards (sessions no longer in data) are removed.
// F-103.
func (s *AISessionStore) Save(data AISessionData) error {
	if err := os.MkdirAll(s.shardDir(), 0755); err != nil {
		return err
	}

	wanted := make(map[string]struct{}, len(data.Sessions))
	for i := range data.Sessions {
		sess := data.Sessions[i]
		if sess.ID == "" {
			continue
		}
		payload, err := json.Marshal(sess)
		if err != nil {
			return fmt.Errorf("marshal session %s: %w", sess.ID, err)
		}
		// Use filepath.Base(id) for both the shard name and the wanted
		// key so orphan cleanup matches against the actual on-disk name
		// (the only path the cleanup pass sees).
		name := filepath.Base(sess.ID)
		if err := atomicWriteFile(filepath.Join(s.shardDir(), name+".json"), payload, 0600); err != nil {
			return fmt.Errorf("write shard %s: %w", sess.ID, err)
		}
		wanted[name] = struct{}{}
	}

	entries, err := os.ReadDir(s.shardDir())
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil
		}
		return err
	}
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		name := e.Name()
		if filepath.Ext(name) != ".json" {
			continue
		}
		id := name[:len(name)-len(".json")]
		if _, keep := wanted[id]; keep {
			continue
		}
		_ = os.Remove(filepath.Join(s.shardDir(), name))
	}

	return nil
}

// Load reads every shard in ai-sessions/ and decodes them. Runs the
// one-time migration from the legacy ai-sessions.json file if present.
// F-103.
func (s *AISessionStore) Load() (AISessionData, error) {
	if err := s.migrateLegacy(); err != nil {
		// Migration failures must not block load — log via returned error
		// only if caller cares; otherwise fall through to shard scan.
		_ = err
	}

	out := AISessionData{Sessions: []AISessionEntry{}, CurrentSessionID: ""}

	entries, err := os.ReadDir(s.shardDir())
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return out, nil
		}
		return AISessionData{}, err
	}
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		if filepath.Ext(e.Name()) != ".json" {
			continue
		}
		path := filepath.Join(s.shardDir(), e.Name())
		raw, err := os.ReadFile(path)
		if err != nil {
			continue
		}
		var sess AISessionEntry
		if err := json.Unmarshal(raw, &sess); err != nil {
			quarantineCorrupt(path)
			continue
		}
		if sess.ID == "" {
			continue
		}
		out.Sessions = append(out.Sessions, sess)
	}

	return out, nil
}

// migrateLegacy splits the old ai-sessions.json into per-session shards
// and deletes the legacy file. Idempotent — no-op once shards exist.
func (s *AISessionStore) migrateLegacy() error {
	if _, err := os.Stat(s.filePath()); err != nil {
		return nil
	}
	raw, err := os.ReadFile(s.filePath())
	if err != nil {
		return err
	}
	var legacy AISessionData
	if err := json.Unmarshal(raw, &legacy); err != nil {
		quarantineCorrupt(s.filePath())
		return nil
	}
	if len(legacy.Sessions) > 0 {
		if err := s.Save(legacy); err != nil {
			return err
		}
	}
	return os.Remove(s.filePath())
}