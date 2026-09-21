package store

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestTerminalHistoryDebounceCoalesces(t *testing.T) {
	dir := t.TempDir()
	s := NewTerminalHistoryStore(dir)
	defer s.Close()

	if err := s.Save([]HistoryEntry{{ID: "1", Command: "ls"}}); err != nil {
		t.Fatalf("Save 1: %v", err)
	}
	if err := s.Save([]HistoryEntry{{ID: "1", Command: "ls"}, {ID: "2", Command: "pwd"}}); err != nil {
		t.Fatalf("Save 2: %v", err)
	}
	if err := s.Save([]HistoryEntry{{ID: "1", Command: "ls"}, {ID: "2", Command: "pwd"}, {ID: "3", Command: "cat"}}); err != nil {
		t.Fatalf("Save 3: %v", err)
	}

	// Before debounce window, the file must not exist yet.
	if _, err := os.Stat(s.filePath()); !os.IsNotExist(err) {
		t.Fatalf("file should not exist before debounce window, got err=%v", err)
	}

	if err := s.Flush(); err != nil {
		t.Fatalf("Flush: %v", err)
	}

	entries, err := s.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if len(entries) != 3 {
		t.Fatalf("expected 3 entries after coalesced save, got %d", len(entries))
	}
}

func TestTerminalHistoryDebounceTimer(t *testing.T) {
	dir := t.TempDir()
	s := NewTerminalHistoryStore(dir)
	defer s.Close()

	if err := s.Save([]HistoryEntry{{ID: "1", Command: "echo"}}); err != nil {
		t.Fatalf("Save: %v", err)
	}

	// Wait past the debounce window for the timer goroutine to fire.
	time.Sleep(terminalHistoryDebounce + 200*time.Millisecond)

	entries, err := s.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if len(entries) != 1 || entries[0].Command != "echo" {
		t.Fatalf("expected one entry 'echo', got %+v", entries)
	}
}

func TestTerminalHistoryCloseFlushesPending(t *testing.T) {
	dir := t.TempDir()
	s := NewTerminalHistoryStore(dir)

	if err := s.Save([]HistoryEntry{{ID: "1", Command: "ls -la"}}); err != nil {
		t.Fatalf("Save: %v", err)
	}
	// Close without an explicit Flush must still persist the entry.
	if err := s.Close(); err != nil {
		t.Fatalf("Close: %v", err)
	}

	if _, err := os.Stat(filepath.Join(dir, terminalHistoryFileName)); err != nil {
		t.Fatalf("file should exist after Close, got err=%v", err)
	}
	entries, err := s.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if len(entries) != 1 || entries[0].Command != "ls -la" {
		t.Fatalf("expected 'ls -la' after Close flush, got %+v", entries)
	}
}

func TestTerminalHistorySaveAfterCloseNoop(t *testing.T) {
	dir := t.TempDir()
	s := NewTerminalHistoryStore(dir)
	if err := s.Close(); err != nil {
		t.Fatalf("Close: %v", err)
	}
	if err := s.Save([]HistoryEntry{{ID: "1", Command: "noop"}}); err != nil {
		t.Fatalf("Save after Close should not error, got %v", err)
	}
	if _, err := os.Stat(filepath.Join(dir, terminalHistoryFileName)); !os.IsNotExist(err) {
		t.Fatalf("Save after Close must not write file, got err=%v", err)
	}
}

func TestTerminalHistoryDeleteByIDs(t *testing.T) {
	dir := t.TempDir()
	s := NewTerminalHistoryStore(dir)
	defer s.Close()

	if err := s.Save([]HistoryEntry{{ID: "1", Command: "a"}, {ID: "2", Command: "b"}}); err != nil {
		t.Fatalf("Save: %v", err)
	}
	if err := s.DeleteByIDs([]string{"1"}); err != nil {
		t.Fatalf("DeleteByIDs: %v", err)
	}
	entries, err := s.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if len(entries) != 1 || entries[0].ID != "2" {
		t.Fatalf("expected only id=2 after delete, got %+v", entries)
	}
}