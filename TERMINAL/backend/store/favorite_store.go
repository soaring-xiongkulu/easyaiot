package store

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
)

const favoriteFileName = "favorites.json"

// FavoriteStore persists the user's ordered list of favorite connection ids.
// The array order is the display order (drag & drop rewrites the whole list).
type FavoriteStore struct {
	filePath string

	mu  sync.Mutex
	ids []string
}

func NewFavoriteStore(configDir string) *FavoriteStore {
	return &FavoriteStore{
		filePath: filepath.Join(configDir, favoriteFileName),
		ids:      make([]string, 0),
	}
}

// Load reads favorites.json into memory and returns a copy. A missing or
// corrupted file resets to an empty list (same tolerate-missing policy as
// RecentStore).
func (s *FavoriteStore) Load() ([]string, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	data, err := os.ReadFile(s.filePath)
	if err != nil {
		if os.IsNotExist(err) {
			s.ids = make([]string, 0)
			return make([]string, 0), nil
		}
		return nil, err
	}

	var ids []string
	if err := json.Unmarshal(data, &ids); err != nil {
		// Corrupted file — reset
		s.ids = make([]string, 0)
		return make([]string, 0), nil
	}
	s.ids = ids
	result := make([]string, len(s.ids))
	copy(result, s.ids)
	return result, nil
}

// Save replaces the favorite list with ids (deduplicated, first occurrence
// order kept) and writes the file synchronously. Favorites change rarely
// (toggle / drag reorder), so an immediate atomic write needs no debouncing.
func (s *FavoriteStore) Save(ids []string) error {
	s.mu.Lock()
	seen := make(map[string]struct{}, len(ids))
	deduped := make([]string, 0, len(ids))
	for _, id := range ids {
		if id == "" {
			continue
		}
		if _, ok := seen[id]; ok {
			continue
		}
		seen[id] = struct{}{}
		deduped = append(deduped, id)
	}
	s.ids = deduped
	current := make([]string, len(s.ids))
	copy(current, s.ids)
	s.mu.Unlock()

	data, err := json.Marshal(current)
	if err != nil {
		return err
	}
	return atomicWriteFile(s.filePath, data, 0644)
}

func (s *FavoriteStore) GetAll() []string {
	s.mu.Lock()
	defer s.mu.Unlock()

	result := make([]string, len(s.ids))
	copy(result, s.ids)
	return result
}
