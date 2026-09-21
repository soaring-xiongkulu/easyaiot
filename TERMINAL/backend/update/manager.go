package update

import (
	"os"
	"sync"
)

// Manager holds in-memory state for one in-progress update (download → apply).
type Manager struct {
	mu      sync.Mutex
	pending *PendingUpdate
}

// PendingUpdate is a downloaded, verified, staged update ready to apply.
type PendingUpdate struct {
	Asset     UpdateAsset
	Kind      string // classifyAsset(name): "installer" | "portable" | "binary-tar.gz"
	StageDir  string // staging directory holding the downloaded artifact + extracted payload
	FilePath  string // the downloaded artifact itself
	NewBinary string // extracted replacement executable (empty for "installer")
}

// NewManager returns an empty update Manager.
func NewManager() *Manager { return &Manager{} }

// Pending returns the currently staged update, or nil.
func (m *Manager) Pending() *PendingUpdate {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.pending
}

// Clear discards the staged update and removes its staging directory.
func (m *Manager) Clear() {
	m.mu.Lock()
	defer m.mu.Unlock()
	if m.pending != nil && m.pending.StageDir != "" {
		// Installer payloads are kept for the detached updater script; only
		// extraction dirs are removed here.
		if m.pending.Kind != "installer" {
			_ = os.RemoveAll(m.pending.StageDir)
		}
	}
	m.pending = nil
}

func (m *Manager) setPending(p *PendingUpdate) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.pending = p
}
