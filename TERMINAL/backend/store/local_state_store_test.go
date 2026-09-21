package store

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLocalStateRoundtrip(t *testing.T) {
	s := NewLocalStateStore(t.TempDir())

	loaded, err := s.Load()
	if err != nil {
		t.Fatalf("initial load: %v", err)
	}
	if loaded.CollapsedQuickCommandGroupIds == nil {
		t.Fatalf("default LocalState should init CollapsedQuickCommandGroupIds, got nil")
	}
	if len(loaded.CollapsedQuickCommandGroupIds) != 0 {
		t.Fatalf("default CollapsedQuickCommandGroupIds should be empty, got %v", loaded.CollapsedQuickCommandGroupIds)
	}

	loaded.CollapsedQuickCommandGroupIds = []string{"qcg-1", "__ungrouped__"}
	if err := s.Save(loaded); err != nil {
		t.Fatalf("save: %v", err)
	}

	again, err := s.Load()
	if err != nil {
		t.Fatalf("reload: %v", err)
	}
	if len(again.CollapsedQuickCommandGroupIds) != 2 ||
		again.CollapsedQuickCommandGroupIds[0] != "qcg-1" ||
		again.CollapsedQuickCommandGroupIds[1] != "__ungrouped__" {
		t.Fatalf("roundtrip mismatch: got %v", again.CollapsedQuickCommandGroupIds)
	}

	// Defaults must survive: older configs lack the new key entirely.
	if err := os.WriteFile(filepath.Join(s.configDir, localStateFileName), []byte(`{"sidebarVisible":false}`), 0600); err != nil {
		t.Fatalf("write legacy config: %v", err)
	}
	legacy, err := s.Load()
	if err != nil {
		t.Fatalf("load legacy: %v", err)
	}
	if legacy.CollapsedQuickCommandGroupIds == nil || len(legacy.CollapsedQuickCommandGroupIds) != 0 {
		t.Fatalf("legacy config should yield empty CollapsedQuickCommandGroupIds, got %v", legacy.CollapsedQuickCommandGroupIds)
	}
}

func TestLocalStateSftpHiddenColumns(t *testing.T) {
	s := NewLocalStateStore(t.TempDir())

	loaded, err := s.Load()
	if err != nil {
		t.Fatalf("initial load: %v", err)
	}
	if loaded.SftpHiddenColumns != nil {
		t.Fatalf("default SftpHiddenColumns should be nil (all visible), got %v", loaded.SftpHiddenColumns)
	}

	loaded.SftpHiddenColumns = []string{"permission", "owner", "group"}
	if err := s.Save(loaded); err != nil {
		t.Fatalf("save: %v", err)
	}

	again, err := s.Load()
	if err != nil {
		t.Fatalf("reload: %v", err)
	}
	if len(again.SftpHiddenColumns) != 3 || again.SftpHiddenColumns[0] != "permission" {
		t.Fatalf("roundtrip mismatch: got %v", again.SftpHiddenColumns)
	}

	// Older configs lack the key entirely; columns stay visible (nil set).
	if err := os.WriteFile(filepath.Join(s.configDir, localStateFileName), []byte(`{"sidebarVisible":true}`), 0600); err != nil {
		t.Fatalf("write legacy config: %v", err)
	}
	legacy, err := s.Load()
	if err != nil {
		t.Fatalf("load legacy: %v", err)
	}
	if legacy.SftpHiddenColumns != nil {
		t.Fatalf("legacy config should yield nil SftpHiddenColumns, got %v", legacy.SftpHiddenColumns)
	}
}
