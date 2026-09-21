package store

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
	"time"
)

const terminalHistoryFileName = "terminal-history.json"
const maxHistorySize = 500
const terminalHistoryDebounce = 500 * time.Millisecond

type TerminalHistoryStore struct {
	configDir string

	mu      sync.Mutex
	pending []HistoryEntry // latest snapshot from the most recent Save call
	timer   *time.Timer
	stop    chan struct{}
	done    chan struct{}
	closed  bool
	closeOnce sync.Once
}

type HistoryEntry struct {
	ID      string `json:"id"`
	Command string `json:"command"`
}

type TerminalHistoryData struct {
	Entries []HistoryEntry `json:"entries"`
}

func NewTerminalHistoryStore(configDir string) *TerminalHistoryStore {
	s := &TerminalHistoryStore{
		configDir: configDir,
		stop:      make(chan struct{}),
		done:      make(chan struct{}),
	}
	go s.flushLoop()
	return s
}

func (s *TerminalHistoryStore) filePath() string {
	return filepath.Join(s.configDir, terminalHistoryFileName)
}

// Save records the latest snapshot and arms a 500ms debounce timer. Concurrent
// calls coalesce: only the most recent entries list is written. Use Close or
// Flush to force a synchronous write.
//
// Fixes: F-101.
func (s *TerminalHistoryStore) Save(entries []HistoryEntry) error {
	s.mu.Lock()
	if s.closed {
		s.mu.Unlock()
		return nil
	}
	s.pending = entries
	if s.timer == nil {
		s.timer = time.AfterFunc(terminalHistoryDebounce, s.fire)
	} else {
		s.timer.Reset(terminalHistoryDebounce)
	}
	s.mu.Unlock()
	return nil
}

// fire is the timer callback; it triggers a flush.
func (s *TerminalHistoryStore) fire() {
	s.flush(false)
}

// Flush forces an immediate synchronous write of any pending entries. Safe to
// call concurrently with Save; subsequent timer-fired writes within the
// debounce window are coalesced as usual.
func (s *TerminalHistoryStore) Flush() error {
	return s.flush(true)
}

// flush performs the actual write. If sync is true it runs in the caller
// goroutine (used by Flush); otherwise it runs in the timer goroutine (or
// the shutdown goroutine for Close).
func (s *TerminalHistoryStore) flush(sync bool) error {
	s.mu.Lock()
	if sync {
		// Cancel any pending timer so a concurrent fire doesn't double-write.
		if s.timer != nil {
			s.timer.Stop()
		}
	}
	if len(s.pending) == 0 {
		s.mu.Unlock()
		return nil
	}
	entries := s.pending
	s.pending = nil
	s.mu.Unlock()
	return s.writeAtomic(entries)
}

// writeAtomic dedups, trims, marshals, and writes via tmp+rename.
func (s *TerminalHistoryStore) writeAtomic(entries []HistoryEntry) error {
	seen := make(map[string]bool)
	result := make([]HistoryEntry, 0, len(entries))
	for i := len(entries) - 1; i >= 0; i-- {
		entry := entries[i]
		if entry.Command == "" || seen[entry.Command] {
			continue
		}
		seen[entry.Command] = true
		result = append([]HistoryEntry{entry}, result...)
	}
	if len(result) > maxHistorySize {
		result = result[len(result)-maxHistorySize:]
	}
	data := TerminalHistoryData{Entries: result}
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}
	return atomicWriteFile(s.filePath(), jsonData, 0600)
}

// flushLoop waits for Close.
func (s *TerminalHistoryStore) flushLoop() {
	defer close(s.done)
	<-s.stop
	s.mu.Lock()
	s.closed = true
	if s.timer != nil {
		s.timer.Stop()
	}
	s.mu.Unlock()
	// Final synchronous flush before signaling shutdown. Bounded so a hung
	// disk cannot block app shutdown forever.
	done := make(chan struct{})
	go func() { _ = s.flush(false); close(done) }()
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		// disk is hung — let the app exit anyway
	}
}

// Close stops the debounce loop. Idempotent and bounded — a hung flushLoop
// (e.g. blocked on disk I/O or a stuck timer callback) cannot block shutdown
// for more than 2 s. Subsequent calls return immediately.
func (s *TerminalHistoryStore) Close() error {
	s.closeOnce.Do(func() {
		s.mu.Lock()
		closed := s.closed
		s.mu.Unlock()
		if !closed {
			close(s.stop)
		}
	})
	select {
	case <-s.done:
	case <-time.After(3 * time.Second):
		// flushLoop never finished — abandon and let the process exit
	}
	return nil
}

func (s *TerminalHistoryStore) Load() ([]HistoryEntry, error) {
	fileData, err := os.ReadFile(s.filePath())
	if err != nil {
		if os.IsNotExist(err) {
			return []HistoryEntry{}, nil
		}
		return nil, err
	}
	var data TerminalHistoryData
	if err := json.Unmarshal(fileData, &data); err != nil {
		_ = os.Remove(s.filePath())
		return []HistoryEntry{}, nil
	}
	if len(data.Entries) == 0 && len(fileData) > 10 {
		var oldFormat struct {
			Commands []string `json:"commands"`
		}
		if err := json.Unmarshal(fileData, &oldFormat); err == nil && len(oldFormat.Commands) > 0 {
			_ = os.Remove(s.filePath())
			return []HistoryEntry{}, nil
		}
	}
	return data.Entries, nil
}

func (s *TerminalHistoryStore) DeleteByIDs(ids []string) error {
	if err := s.Flush(); err != nil {
		return err
	}
	entries, err := s.Load()
	if err != nil {
		return err
	}
	idSet := make(map[string]bool)
	for _, id := range ids {
		idSet[id] = true
	}
	filtered := make([]HistoryEntry, 0, len(entries))
	for _, entry := range entries {
		if !idSet[entry.ID] {
			filtered = append(filtered, entry)
		}
	}
	if err := s.writeAtomic(filtered); err != nil {
		return err
	}
	s.mu.Lock()
	s.pending = nil
	if s.timer != nil {
		s.timer.Stop()
	}
	s.mu.Unlock()
	return nil
}