package store

import (
	"os"
	"path/filepath"
	"testing"
)

func TestRecentStore_Record_Deduplicates(t *testing.T) {
	dir := t.TempDir()
	s := NewRecentStore(dir)

	s.Record("a")
	s.Record("b")
	s.Record("a") // duplicate — should move to front

	ids := s.GetAll()
	if len(ids) != 2 {
		t.Fatalf("expected 2 unique ids, got %d: %v", len(ids), ids)
	}
	if ids[0] != "a" {
		t.Errorf("expected 'a' first (most recent), got %v", ids)
	}
	if ids[1] != "b" {
		t.Errorf("expected 'b' second, got %v", ids)
	}
}

func TestRecentStore_Record_TrimsToMax(t *testing.T) {
	dir := t.TempDir()
	s := NewRecentStore(dir)

	for i := 0; i < 25; i++ {
		s.Record(string(rune('a' + i)))
	}

	ids := s.GetAll()
	if len(ids) != 20 {
		t.Fatalf("expected 20 ids (maxRecent), got %d", len(ids))
	}
}

func TestRecentStore_Load_MissingFile(t *testing.T) {
	dir := t.TempDir()
	s := NewRecentStore(dir)

	ids, err := s.Load()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(ids) != 0 {
		t.Errorf("expected empty list, got %v", ids)
	}
}

func TestRecentStore_Load_CorruptedFile(t *testing.T) {
	dir := t.TempDir()
	filePath := filepath.Join(dir, "recent.json")
	os.WriteFile(filePath, []byte("not valid json"), 0644)

	s := NewRecentStore(dir)
	ids, err := s.Load()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(ids) != 0 {
		t.Errorf("expected empty list for corrupted file, got %v", ids)
	}
}

func TestRecentStore_Persistence(t *testing.T) {
	dir := t.TempDir()
	s := NewRecentStore(dir)

	s.Record("conn-1")
	s.Record("conn-2")
	// Record is debounced; flush via Close before reading from a fresh store.
	s.Close()

	// Create a new store pointing to same dir — should read persisted data
	s2 := NewRecentStore(dir)
	ids, _ := s2.Load()

	if len(ids) != 2 {
		t.Fatalf("expected 2 ids loaded from disk, got %d: %v", len(ids), ids)
	}
	if ids[0] != "conn-2" {
		t.Errorf("expected 'conn-2' first, got %v", ids)
	}
}
