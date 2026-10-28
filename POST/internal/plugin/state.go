package plugin

import (
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/pipeline"
	"fmt"
	"strconv"
	"strings"
	"sync"
	"time"
)

const trackStateTTL = 10 * time.Minute

type trackState struct {
	lastSeen     time.Time
	lastAlert    time.Time
	lastDet      *contract.Detection
	lineSide     map[int64]int
	linePoint    map[int64][2]float64
	inRegion     map[int64]bool
	regionEnter  map[int64]time.Time
	dwellAlerted map[int64]bool
}

type trackStateStore struct {
	processMu sync.Mutex
	mu        sync.Mutex
	tracks    map[string]*trackState
}

var globalTrackState = &trackStateStore{tracks: map[string]*trackState{}}

func pluginTrackStateKey(ctx *pipeline.Context, det contract.Detection, name string) string {
	return fmt.Sprintf("%s:%v:%s", name, ctx.PluginParams["binding_state_scope"], trackStateKey(ctx.Event.TaskID, ctx.Event.DeviceID, det.ModelID, det.TrackID))
}

func trackStateKey(taskID int64, deviceID string, modelID *int64, trackID int) string {
	var mid int64
	if modelID != nil {
		mid = *modelID
	}
	return fmt.Sprintf("%d:%s:%d:%d", taskID, deviceID, mid, trackID)
}

func (s *trackStateStore) touch(key string, now time.Time) *trackState {
	s.mu.Lock()
	defer s.mu.Unlock()
	st, ok := s.tracks[key]
	if !ok || now.Sub(st.lastSeen) > trackStateTTL {
		st = &trackState{
			lineSide:     map[int64]int{},
			linePoint:    map[int64][2]float64{},
			inRegion:     map[int64]bool{},
			regionEnter:  map[int64]time.Time{},
			dwellAlerted: map[int64]bool{},
		}
		s.tracks[key] = st
	}
	st.lastSeen = now
	return st
}

// ExpiredTrackExit describes a track whose enter-state outlived its last
// observation; RegionEnterExit turns these into synthesized exit events.
type ExpiredTrackExit struct {
	TrackID int
	ModelID *int64
	Regions []int64
	LastDet *contract.Detection
}

// expireStaleEnter removes enter-state of tracks not observed for maxAge and
// returns the ones that were still inside a region. A vanished track (occlusion,
// sampling gap, leaving the frame) never produces a farewell observation, so
// headcount would drift upward forever without this reconciliation.
// prefix must cover "plugin:scope:taskID:deviceID:".
func (s *trackStateStore) expireStaleEnter(prefix string, maxAge time.Duration, now time.Time) []ExpiredTrackExit {
	s.mu.Lock()
	defer s.mu.Unlock()
	var expired []ExpiredTrackExit
	for k, st := range s.tracks {
		if !strings.HasPrefix(k, prefix) || now.Sub(st.lastSeen) <= maxAge {
			continue
		}
		delete(s.tracks, k)
		var regions []int64
		for rid, inside := range st.inRegion {
			if inside {
				regions = append(regions, rid)
			}
		}
		if len(regions) == 0 {
			continue
		}
		// Key tail is "{modelID}:{trackID}"; parse from the end so device IDs
		// containing ':' cannot shift the fields.
		parts := strings.Split(strings.TrimPrefix(k, prefix), ":")
		if len(parts) < 2 {
			continue
		}
		tid, errTrack := strconv.Atoi(parts[len(parts)-1])
		mid, errModel := strconv.ParseInt(parts[len(parts)-2], 10, 64)
		if errTrack != nil || errModel != nil {
			continue
		}
		expired = append(expired, ExpiredTrackExit{
			TrackID: tid,
			ModelID: &mid,
			Regions: regions,
			LastDet: st.lastDet,
		})
	}
	return expired
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
