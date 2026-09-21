package store

import (
	"os"
	"path/filepath"
	"testing"
)

func TestFavoriteStore_SaveAndGetAll_PreservesOrder(t *testing.T) {
	dir := t.TempDir()
	s := NewFavoriteStore(dir)

	err := s.Save([]string{"conn-3", "conn-1", "conn-2"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	ids := s.GetAll()
	if len(ids) != 3 {
		t.Fatalf("expected 3 ids, got %v", ids)
	}
	if ids[0] != "conn-3" || ids[1] != "conn-1" || ids[2] != "conn-2" {
		t.Errorf("expected saved order preserved, got %v", ids)
	}
}

func TestFavoriteStore_Save_Deduplicates(t *testing.T) {
	dir := t.TempDir()
	s := NewFavoriteStore(dir)

	s.Save([]string{"a", "b", "a", "c", "b"})

	ids := s.GetAll()
	if len(ids) != 3 {
		t.Fatalf("expected 3 unique ids, got %v", ids)
	}
	if ids[0] != "a" || ids[1] != "b" || ids[2] != "c" {
		t.Errorf("expected first occurrence order kept, got %v", ids)
	}
}

func TestFavoriteStore_Load_MissingFile(t *testing.T) {
	dir := t.TempDir()
	s := NewFavoriteStore(dir)

	ids, err := s.Load()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(ids) != 0 {
		t.Errorf("expected empty list, got %v", ids)
	}
}

func TestFavoriteStore_Load_CorruptedFile(t *testing.T) {
	dir := t.TempDir()
	filePath := filepath.Join(dir, "favorites.json")
	os.WriteFile(filePath, []byte("not valid json"), 0644)

	s := NewFavoriteStore(dir)
	ids, err := s.Load()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(ids) != 0 {
		t.Errorf("expected empty list for corrupted file, got %v", ids)
	}
}

func TestFavoriteStore_Persistence(t *testing.T) {
	dir := t.TempDir()
	s := NewFavoriteStore(dir)

	s.Save([]string{"conn-1", "conn-2"})

	// Create a new store pointing to same dir — should read persisted data
	s2 := NewFavoriteStore(dir)
	ids, err := s2.Load()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if len(ids) != 2 {
		t.Fatalf("expected 2 ids loaded from disk, got %d: %v", len(ids), ids)
	}
	if ids[0] != "conn-1" || ids[1] != "conn-2" {
		t.Errorf("expected persisted order preserved, got %v", ids)
	}
}

func TestFavoriteStore_Persistence_EmptyList(t *testing.T) {
	dir := t.TempDir()
	s := NewFavoriteStore(dir)

	// Save a non-empty list first, then clear it — the empty list must
	// overwrite the file rather than being skipped.
	s.Save([]string{"a"})
	if err := s.Save([]string{}); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	s2 := NewFavoriteStore(dir)
	ids, err := s2.Load()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(ids) != 0 {
		t.Errorf("expected empty list after clearing, got %v", ids)
	}
}
