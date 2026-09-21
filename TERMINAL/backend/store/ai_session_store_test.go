package store

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sort"
	"testing"
)

// F-103: shard-based persistence must be a drop-in replacement for the legacy
// single-file format, including the one-time migration from ai-sessions.json.

func newAISessionStoreAt(t *testing.T, dir string) *AISessionStore {
	t.Helper()
	return &AISessionStore{configDir: dir}
}

func sampleAISessions() AISessionData {
	return AISessionData{
		Sessions: []AISessionEntry{
			{
				ID:        "sess-1",
				Name:      "first",
				CreatedAt: 1,
				UpdatedAt: 2,
				Messages:  []AIMessageEntry{{ID: "m1", Role: "user", Content: "hi"}},
			},
			{
				ID:        "sess-2",
				Name:      "second",
				CreatedAt: 3,
				UpdatedAt: 4,
				Messages:  []AIMessageEntry{{ID: "m2", Role: "assistant", Content: "hello"}},
			},
		},
		CurrentSessionID: "sess-1",
	}
}

func TestAISessionStore_SaveLoadRoundTrip(t *testing.T) {
	dir := t.TempDir()
	s := newAISessionStoreAt(t, dir)

	want := sampleAISessions()
	if err := s.Save(want); err != nil {
		t.Fatalf("Save: %v", err)
	}

	got, err := s.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if len(got.Sessions) != len(want.Sessions) {
		t.Fatalf("session count: got %d want %d", len(got.Sessions), len(want.Sessions))
	}
	// Save iterates by index; preserve order.
	for i := range got.Sessions {
		if got.Sessions[i].ID != want.Sessions[i].ID {
			t.Errorf("session[%d].ID: got %q want %q", i, got.Sessions[i].ID, want.Sessions[i].ID)
		}
		if got.Sessions[i].Name != want.Sessions[i].Name {
			t.Errorf("session[%d].Name: got %q want %q", i, got.Sessions[i].Name, want.Sessions[i].Name)
		}
		if len(got.Sessions[i].Messages) != len(want.Sessions[i].Messages) {
			t.Errorf("session[%d].Messages: got %d want %d", i, len(got.Sessions[i].Messages), len(want.Sessions[i].Messages))
		}
	}
}

func TestAISessionStore_LoadNoDirReturnsEmpty(t *testing.T) {
	dir := t.TempDir()
	s := newAISessionStoreAt(t, dir)

	got, err := s.Load()
	if err != nil {
		t.Fatalf("Load on empty dir: %v", err)
	}
	if len(got.Sessions) != 0 {
		t.Errorf("expected zero sessions, got %d", len(got.Sessions))
	}
}

func TestAISessionStore_ShardsArePerSession(t *testing.T) {
	dir := t.TempDir()
	s := newAISessionStoreAt(t, dir)

	want := sampleAISessions()
	if err := s.Save(want); err != nil {
		t.Fatalf("Save: %v", err)
	}

	for _, sess := range want.Sessions {
		shard := filepath.Join(dir, aiSessionDirName, sess.ID+".json")
		if _, err := os.Stat(shard); err != nil {
			t.Errorf("expected shard %s: %v", shard, err)
		}
	}
}

func TestAISessionStore_SaveRemovesOrphans(t *testing.T) {
	dir := t.TempDir()
	s := newAISessionStoreAt(t, dir)

	// Seed three shards.
	full := AISessionData{Sessions: []AISessionEntry{
		{ID: "a", Name: "a"},
		{ID: "b", Name: "b"},
		{ID: "c", Name: "c"},
	}}
	if err := s.Save(full); err != nil {
		t.Fatalf("initial Save: %v", err)
	}

	// Save only "b" — "a" and "c" must be removed.
	trimmed := AISessionData{Sessions: []AISessionEntry{{ID: "b", Name: "b"}}}
	if err := s.Save(trimmed); err != nil {
		t.Fatalf("trimmed Save: %v", err)
	}

	for _, id := range []string{"a", "c"} {
		path := filepath.Join(dir, aiSessionDirName, id+".json")
		if _, err := os.Stat(path); !os.IsNotExist(err) {
			t.Errorf("orphan %s should be removed (err=%v)", id, err)
		}
	}
	if _, err := os.Stat(filepath.Join(dir, aiSessionDirName, "b.json")); err != nil {
		t.Errorf("kept shard missing: %v", err)
	}
}

// F-103: the legacy ai-sessions.json file must be migrated to shards on first
// Load. The migration is idempotent — running it a second time must not
// duplicate shards or re-create the legacy file.
func TestAISessionStore_MigrateLegacyToShards(t *testing.T) {
	dir := t.TempDir()
	s := newAISessionStoreAt(t, dir)

	want := sampleAISessions()
	raw, err := json.Marshal(want)
	if err != nil {
		t.Fatalf("marshal legacy: %v", err)
	}
	legacyPath := filepath.Join(dir, aiSessionFileName)
	if err := os.WriteFile(legacyPath, raw, 0600); err != nil {
		t.Fatalf("write legacy: %v", err)
	}

	got, err := s.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if len(got.Sessions) != len(want.Sessions) {
		t.Fatalf("session count: got %d want %d", len(got.Sessions), len(want.Sessions))
	}
	for i := range got.Sessions {
		if got.Sessions[i].ID != want.Sessions[i].ID {
			t.Errorf("session[%d].ID: got %q want %q", i, got.Sessions[i].ID, want.Sessions[i].ID)
		}
	}

	// Legacy file must be gone.
	if _, err := os.Stat(legacyPath); !os.IsNotExist(err) {
		t.Errorf("legacy file should be removed, got err=%v", err)
	}
	// Each session must have its shard.
	for _, sess := range want.Sessions {
		shard := filepath.Join(dir, aiSessionDirName, sess.ID+".json")
		if _, err := os.Stat(shard); err != nil {
			t.Errorf("missing shard %s: %v", shard, err)
		}
	}
}

// F-103: idempotency — calling Load twice on the same dir must produce the
// same data and must not multiply shards or re-introduce the legacy file.
func TestAISessionStore_MigrationIdempotent(t *testing.T) {
	dir := t.TempDir()
	s := newAISessionStoreAt(t, dir)

	want := sampleAISessions()
	raw, _ := json.Marshal(want)
	legacyPath := filepath.Join(dir, aiSessionFileName)
	if err := os.WriteFile(legacyPath, raw, 0600); err != nil {
		t.Fatalf("write legacy: %v", err)
	}

	first, err := s.Load()
	if err != nil {
		t.Fatalf("first Load: %v", err)
	}
	// Migration already removed the legacy file. Running Load again must
	// not re-migrate (legacy gone) and must not corrupt the shards.
	second, err := s.Load()
	if err != nil {
		t.Fatalf("second Load: %v", err)
	}

	if len(first.Sessions) != len(second.Sessions) {
		t.Errorf("session count differs: first=%d second=%d", len(first.Sessions), len(second.Sessions))
	}

	entries, err := os.ReadDir(filepath.Join(dir, aiSessionDirName))
	if err != nil {
		t.Fatalf("ReadDir: %v", err)
	}
	shards := 0
	for _, e := range entries {
		if filepath.Ext(e.Name()) == ".json" {
			shards++
		}
	}
	if shards != len(want.Sessions) {
		t.Errorf("shard count after idempotent load: got %d want %d", shards, len(want.Sessions))
	}
}

// F-103: reversibility — if the legacy file is re-introduced (e.g. user
// downgrade to a pre-shard build) after a successful migration, re-running
// Load must recover the data into shards and remove the legacy file again.
func TestAISessionStore_MigrationReversible(t *testing.T) {
	dir := t.TempDir()
	s := newAISessionStoreAt(t, dir)

	original := sampleAISessions()
	raw, _ := json.Marshal(original)

	// First migration: legacy -> shards.
	if err := os.WriteFile(filepath.Join(dir, aiSessionFileName), raw, 0600); err != nil {
		t.Fatalf("write legacy: %v", err)
	}
	if _, err := s.Load(); err != nil {
		t.Fatalf("first Load: %v", err)
	}

	// User downgrades then upgrades: legacy file comes back with the same
	// content. Load must migrate again (shards overwritten identically).
	if err := os.WriteFile(filepath.Join(dir, aiSessionFileName), raw, 0600); err != nil {
		t.Fatalf("re-write legacy: %v", err)
	}
	got, err := s.Load()
	if err != nil {
		t.Fatalf("second Load: %v", err)
	}
	if len(got.Sessions) != len(original.Sessions) {
		t.Errorf("session count after re-migration: got %d want %d", len(got.Sessions), len(original.Sessions))
	}
	if _, err := os.Stat(filepath.Join(dir, aiSessionFileName)); !os.IsNotExist(err) {
		t.Errorf("legacy file should be removed again, got err=%v", err)
	}

	// Shard content must still match.
	for _, sess := range original.Sessions {
		shard := filepath.Join(dir, aiSessionDirName, sess.ID+".json")
		data, err := os.ReadFile(shard)
		if err != nil {
			t.Errorf("missing shard %s: %v", shard, err)
			continue
		}
		var roundtripped AISessionEntry
		if err := json.Unmarshal(data, &roundtripped); err != nil {
			t.Errorf("unmarshal shard %s: %v", shard, err)
			continue
		}
		if roundtripped.ID != sess.ID || roundtripped.Name != sess.Name {
			t.Errorf("shard %s: got {%s,%s} want {%s,%s}", shard,
				roundtripped.ID, roundtripped.Name, sess.ID, sess.Name)
		}
	}
}

// F-103: a corrupt legacy file must be quarantined, not crash the load path,
// and must not leak into shards.
func TestAISessionStore_CorruptLegacyQuarantined(t *testing.T) {
	dir := t.TempDir()
	s := newAISessionStoreAt(t, dir)

	legacyPath := filepath.Join(dir, aiSessionFileName)
	if err := os.WriteFile(legacyPath, []byte("not json"), 0600); err != nil {
		t.Fatalf("write corrupt legacy: %v", err)
	}

	got, err := s.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if len(got.Sessions) != 0 {
		t.Errorf("expected no sessions, got %d", len(got.Sessions))
	}

	if _, err := os.Stat(legacyPath); !os.IsNotExist(err) {
		t.Errorf("corrupt legacy file should be quarantined (renamed away), err=%v", err)
	}
	corruptMatches, _ := filepath.Glob(filepath.Join(dir, aiSessionFileName+".corrupt-*"))
	if len(corruptMatches) == 0 {
		t.Errorf("expected quarantined legacy file (.corrupt-*), found none")
	}
	if _, err := os.Stat(filepath.Join(dir, aiSessionDirName)); !os.IsNotExist(err) {
		t.Errorf("shard dir should not exist for empty corrupt legacy, err=%v", err)
	}
}

// F-103: a legacy file with zero sessions must be removed without leaving
// empty shards behind.
func TestAISessionStore_EmptyLegacyRemoved(t *testing.T) {
	dir := t.TempDir()
	s := newAISessionStoreAt(t, dir)

	empty := AISessionData{Sessions: []AISessionEntry{}}
	raw, _ := json.Marshal(empty)
	if err := os.WriteFile(filepath.Join(dir, aiSessionFileName), raw, 0600); err != nil {
		t.Fatalf("write empty legacy: %v", err)
	}

	got, err := s.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if len(got.Sessions) != 0 {
		t.Errorf("expected no sessions, got %d", len(got.Sessions))
	}
	if _, err := os.Stat(filepath.Join(dir, aiSessionFileName)); !os.IsNotExist(err) {
		t.Errorf("empty legacy file should be removed, err=%v", err)
	}
	shardDir := filepath.Join(dir, aiSessionDirName)
	if _, err := os.Stat(shardDir); !os.IsNotExist(err) {
		t.Errorf("shard dir should not exist for empty legacy, err=%v", err)
	}
}

// F-103: Save must skip sessions with empty IDs (defensive — UUIDs are
// always set in practice) rather than writing junk shard files.
func TestAISessionStore_SaveSkipsEmptyID(t *testing.T) {
	dir := t.TempDir()
	s := newAISessionStoreAt(t, dir)

	data := AISessionData{Sessions: []AISessionEntry{
		{ID: "", Name: "should be dropped"},
		{ID: "real", Name: "real one"},
	}}
	if err := s.Save(data); err != nil {
		t.Fatalf("Save: %v", err)
	}

	got, err := s.Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if len(got.Sessions) != 1 || got.Sessions[0].ID != "real" {
		t.Errorf("expected one session with ID=real, got %+v", got.Sessions)
	}
}

// F-103: shard filenames must use filepath.Base(id) to neutralise any
// traversal characters in the ID. The test verifies the on-disk layout.
func TestAISessionStore_ShardPathUsesBase(t *testing.T) {
	dir := t.TempDir()
	s := newAISessionStoreAt(t, dir)

	id := "../escape-attempt"
	data := AISessionData{Sessions: []AISessionEntry{{ID: id, Name: "x"}}}
	if err := s.Save(data); err != nil {
		t.Fatalf("Save: %v", err)
	}

	// The shard must live under the shard dir, not anywhere outside.
	shardDir := filepath.Join(dir, aiSessionDirName)
	entries, err := os.ReadDir(shardDir)
	if err != nil {
		t.Fatalf("ReadDir(%s): %v", shardDir, err)
	}
	names := make([]string, 0, len(entries))
	for _, e := range entries {
		names = append(names, e.Name())
	}
	sort.Strings(names)
	if len(names) != 1 || names[0] != "escape-attempt.json" {
		t.Errorf("expected shard name [escape-attempt.json], got %v", names)
	}
}