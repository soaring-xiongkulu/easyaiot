package template

import (
	"encoding/json"
	"testing"
	"time"

	"easyaiot/post/internal/config"
)

func TestApplySyncRejectsInvalidRegionHitModeWithoutReplacingCache(t *testing.T) {
	cache := NewCache(time.Minute)
	cache.UpsertVersioned(testTemplate(7, 4))
	message := SyncMessage{
		Op: "upsert", TaskID: 7, Revision: 5, SourceInstance: "peer",
		Template: &config.TaskTemplate{
			Revision: 5,
			Task: config.TaskConfig{
				ID: 7,
				Pipeline: []config.PipelineStep{{
					Plugin: "region_gate",
					Params: map[string]any{"hit_mode": "unknown"},
				}},
			},
		},
	}
	payload, err := json.Marshal(message)
	if err != nil {
		t.Fatal(err)
	}
	ApplySync(cache, "local", payload)
	entry, ok := cache.Get(7)
	if !ok || entry.Template.Revision != 4 {
		t.Fatalf("invalid sync replaced cache: %#v", entry)
	}
}
