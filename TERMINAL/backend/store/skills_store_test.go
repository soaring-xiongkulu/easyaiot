package store

import (
	"os"
	"path/filepath"
	"sync/atomic"
	"testing"
	"time"
)

// writeSkill creates a skill directory under configDir/skills/<dir>/SKILL.md
// with the given frontmatter. Returns the directory name used.
func writeSkill(t *testing.T, configDir, name, description, body string) {
	t.Helper()
	dir := filepath.Join(configDir, "skills", name)
	if err := os.MkdirAll(dir, 0755); err != nil {
		t.Fatalf("MkdirAll(%s): %v", dir, err)
	}
	content := "---\nname: " + name + "\ndescription: " + description + "\n---\n\n" + body + "\n"
	mdPath := filepath.Join(dir, "SKILL.md")
	if err := os.WriteFile(mdPath, []byte(content), 0644); err != nil {
		t.Fatalf("WriteFile(%s): %v", mdPath, err)
	}
}

// F-107: verify SkillsStore.List cache actually works. The cache is intended
// to coalesce rapid re-reads (per-token AI / terminal code) by reusing the
// merged result for up to skillsListCacheTTL, but only as long as no mutator
// invalidates it.
func TestSkillsStore_List_CachesAndInvalidates(t *testing.T) {
	dir := t.TempDir()
	s := NewSkillsStore(dir)

	writeSkill(t, dir, "alpha", "first skill", "alpha body")
	writeSkill(t, dir, "beta", "second skill", "beta body")

	// First call: populates the cache.
	first, err := s.List()
	if err != nil {
		t.Fatalf("first List: %v", err)
	}
	if len(first) != 2 {
		t.Fatalf("expected 2 skills, got %d", len(first))
	}

	// Cache populated — should not be nil and should be within TTL.
	s.listMu.Lock()
	populated := s.listCache != nil && time.Since(s.listCachedAt) < skillsListCacheTTL
	s.listMu.Unlock()
	if !populated {
		t.Fatalf("expected cache populated after first List, got cache=%v cachedAt=%v",
			s.listCache == nil, s.listCachedAt)
	}

	// Second call: serves from cache. We verify by adding a new skill
	// to disk AFTER the cache is populated — the cached result must NOT
	// see it (this is the correctness property of the cache).
	writeSkill(t, dir, "gamma", "third skill", "gamma body")
	second, err := s.List()
	if err != nil {
		t.Fatalf("second List: %v", err)
	}
	if len(second) != 2 {
		t.Fatalf("expected cached slice to keep 2 skills (gamma not yet visible), got %d", len(second))
	}

	// Mutator invalidates the cache; the next List picks up the new skill.
	s.invalidateListCache()
	third, err := s.List()
	if err != nil {
		t.Fatalf("third List: %v", err)
	}
	if len(third) != 3 {
		t.Fatalf("expected 3 skills after cache invalidation, got %d", len(third))
	}
}

// F-107: SetEnabled (and the other setPref mutators) must invalidate the
// cache so the next List reflects the change. Without invalidation the UI
// would show stale enabled state until the 2s TTL expired.
func TestSkillsStore_List_MutatorsInvalidate(t *testing.T) {
	dir := t.TempDir()
	s := NewSkillsStore(dir)

	writeSkill(t, dir, "delta", "fourth skill", "delta body")

	if _, err := s.List(); err != nil {
		t.Fatalf("seed List: %v", err)
	}
	s.listMu.Lock()
	cacheBefore := s.listCache != nil
	s.listMu.Unlock()
	if !cacheBefore {
		t.Fatalf("cache not populated before mutate")
	}

	if err := s.SetEnabled("delta", false); err != nil {
		t.Fatalf("SetEnabled: %v", err)
	}
	s.listMu.Lock()
	cacheAfter := s.listCache != nil
	s.listMu.Unlock()
	if cacheAfter {
		t.Fatalf("cache should be invalidated after SetEnabled")
	}

	out, err := s.List()
	if err != nil {
		t.Fatalf("post-mutate List: %v", err)
	}
	if len(out) != 1 || out[0].Enabled {
		t.Fatalf("expected disabled delta, got %+v", out)
	}
}

// F-107: repeated concurrent List calls must not corrupt the cache or
// return inconsistent results. The cache mutex serialises cache reads and
// store writes; List should be safe to call from many goroutines.
func TestSkillsStore_List_ConcurrentReads(t *testing.T) {
	dir := t.TempDir()
	s := NewSkillsStore(dir)

	for i := 0; i < 5; i++ {
		writeSkill(t, dir, "skill"+string(rune('a'+i)), "desc", "body")
	}

	var calls atomic.Int64
	const goroutines = 16
	done := make(chan struct{}, goroutines)
	for i := 0; i < goroutines; i++ {
		go func() {
			defer func() { done <- struct{}{} }()
			for j := 0; j < 8; j++ {
				out, err := s.List()
				if err != nil {
					t.Errorf("List: %v", err)
					return
				}
				if len(out) != 5 {
					t.Errorf("expected 5 skills, got %d", len(out))
					return
				}
				calls.Add(1)
			}
		}()
	}
	for i := 0; i < goroutines; i++ {
		<-done
	}
	if got := calls.Load(); got != goroutines*8 {
		t.Fatalf("expected %d List calls, got %d", goroutines*8, got)
	}
}
