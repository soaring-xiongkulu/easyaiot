package contract

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestSharedInferEventFixtures(t *testing.T) {
	paths, err := filepath.Glob(filepath.Join("..", "..", "..", "testdata", "contracts", "infer_*.json"))
	if err != nil {
		t.Fatal(err)
	}
	if len(paths) != 5 {
		t.Fatalf("expected 5 shared fixtures, got %d (%#v)", len(paths), paths)
	}
	for _, path := range paths {
		t.Run(filepath.Base(path), func(t *testing.T) {
			raw, err := os.ReadFile(path)
			if err != nil {
				t.Fatal(err)
			}
			var event InferEvent
			if err := json.Unmarshal(raw, &event); err != nil {
				t.Fatal(err)
			}
			if err := event.Validate(); err != nil {
				t.Fatal(err)
			}
			for _, det := range event.Detections {
				if det.BBox[2] < det.BBox[0] || det.BBox[3] < det.BBox[1] {
					t.Fatalf("invalid pixel bbox: %#v", det.BBox)
				}
			}
		})
	}
}

func TestSharedFixturePreservesNegativeAndMissingModelIdentity(t *testing.T) {
	read := func(name string) InferEvent {
		raw, err := os.ReadFile(filepath.Join("..", "..", "..", "testdata", "contracts", name))
		if err != nil {
			t.Fatal(err)
		}
		var event InferEvent
		if err := json.Unmarshal(raw, &event); err != nil {
			t.Fatal(err)
		}
		return event
	}
	negative := read("infer_negative_default.json")
	if len(negative.ModelIDs) != 1 || negative.ModelIDs[0] != -1 ||
		negative.Detections[0].ModelID == nil || *negative.Detections[0].ModelID != -1 {
		t.Fatalf("negative business model identity lost: %#v", negative)
	}
	missing := read("infer_missing_detection_model.json")
	if missing.Detections[0].ModelID != nil {
		t.Fatalf("missing model_id became a numeric value: %#v", missing.Detections[0].ModelID)
	}
}

func TestSharedFixturePreservesDetectionRegionMatches(t *testing.T) {
	raw, err := os.ReadFile(filepath.Join("..", "..", "..", "testdata", "contracts", "infer_multi_region_output.json"))
	if err != nil {
		t.Fatal(err)
	}
	var event InferEvent
	if err := json.Unmarshal(raw, &event); err != nil {
		t.Fatal(err)
	}
	det := event.Detections[0]
	if len(det.MatchedRegionIDs) != 2 || len(det.MatchedRegionNames) != 2 {
		t.Fatalf("matched regions lost: %#v", det)
	}
}
