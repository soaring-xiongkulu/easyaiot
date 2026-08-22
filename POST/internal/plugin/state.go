package plugin

import (
	"fmt"
	"sync"
	"time"
)

const trackStateTTL = 10 * time.Minute

type trackState struct {
	lastSeen    time.Time
	lineSide    map[int64]int
	inRegion    map[int64]bool
	regionEnter map[int64]time.Time
}

type trackStateStore struct {
	mu     sync.Mutex
	tracks map[string]*trackState
}

var globalTrackState = &trackStateStore{tracks: map[string]*trackState{}}

func trackStateKey(taskID int64, deviceID string, trackID int) string {
	return fmt.Sprintf("%d:%s:%d", taskID, deviceID, trackID)
}

func (s *trackStateStore) touch(key string, now time.Time) *trackState {
	s.mu.Lock()
	defer s.mu.Unlock()
	st, ok := s.tracks[key]
	if !ok {
		st = &trackState{
			lineSide:    map[int64]int{},
			inRegion:    map[int64]bool{},
			regionEnter: map[int64]time.Time{},
		}
		s.tracks[key] = st
	}
	st.lastSeen = now
	return st
}

func (s *trackStateStore) sweep(maxAge time.Duration) {
	if maxAge <= 0 {
		maxAge = trackStateTTL
	}
	cutoff := time.Now().Add(-maxAge)
	s.mu.Lock()
	defer s.mu.Unlock()
	for k, st := range s.tracks {
		if st.lastSeen.Before(cutoff) {
			delete(s.tracks, k)
		}
	}
}

// SweepTrackState removes stale per-track plugin state (call periodically from main).
func SweepTrackState() {
	globalTrackState.sweep(trackStateTTL)
}
