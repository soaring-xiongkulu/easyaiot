package engine

import (
	"testing"
	"time"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/template"
)

func engineWithTemplate(task config.TaskConfig, regions []config.Region) *Engine {
	cache := template.NewCache(time.Minute)
	cache.Upsert(config.TaskTemplate{
		Schema: "post_task_template.v1",
		Task:   task, Regions: regions,
	})
	return New(config.Config{Enabled: true, InstanceID: "test"}, cache, nil)
}

func baseEvent(dets []contract.Detection) contract.InferEvent {
	return contract.InferEvent{
		Schema: contract.SchemaInferEvent, EventKind: "infer", CorrelationID: "c1",
		TaskID: 1, TaskType: "realtime", DeviceID: "cam", Timestamp: "2026-01-01T00:00:00Z",
		FrameWidth: 1920, FrameHeight: 1080, Detections: dets,
	}
}

func TestHandleRejectsMissingModelIDForMultiModelSpecificRegion(t *testing.T) {
	eng := engineWithTemplate(
		config.TaskConfig{ID: 1, TaskType: "realtime", ModelIDs: []int64{1, 2}},
		[]config.Region{{
			ID: 1, DeviceID: "cam", RegionName: "m1", RegionType: "polygon", IsEnabled: true,
			ModelIDs: []int64{1},
			Points:   []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}},
		}},
	)
	ev := baseEvent([]contract.Detection{{BBox: [4]float64{10, 10, 20, 20}, ClassName: "person"}})
	result, reason, _ := eng.Handle(ev)
	if result != "drop" || reason != "missing_detection_model_id" {
		t.Fatalf("got %s/%s", result, reason)
	}
}

func TestHandleFillsSingleEventModelID(t *testing.T) {
	eng := engineWithTemplate(
		config.TaskConfig{ID: 1, TaskType: "realtime", ModelIDs: []int64{1, 2}}, nil,
	)
	ev := baseEvent([]contract.Detection{{BBox: [4]float64{10, 10, 20, 20}, ClassName: "person"}})
	ev.ModelIDs = []int64{2}
	result, reason, _ := eng.Handle(ev)
	if result != "pass" || reason != "" {
		t.Fatalf("got %s/%s", result, reason)
	}
}

func TestHandleRejectsForeignDetectionModelID(t *testing.T) {
	eng := engineWithTemplate(
		config.TaskConfig{ID: 1, TaskType: "realtime", ModelIDs: []int64{1}}, nil,
	)
	foreign := int64(2)
	ev := baseEvent([]contract.Detection{{ModelID: &foreign, BBox: [4]float64{10, 10, 20, 20}, ClassName: "person"}})
	result, reason, _ := eng.Handle(ev)
	if result != "drop" || reason != "foreign_detection_model_id" {
		t.Fatalf("got %s/%s", result, reason)
	}
}

func TestHandleAllowsMissingFrameSizeWhenDetectionModelHasNoRegions(t *testing.T) {
	eng := engineWithTemplate(
		config.TaskConfig{ID: 1, TaskType: "realtime", ModelIDs: []int64{1, 2}},
		[]config.Region{{
			ID: 1, DeviceID: "cam", RegionName: "m1", RegionType: "polygon", IsEnabled: true,
			ModelIDs: []int64{1},
			Points:   []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}},
		}},
	)
	m2 := int64(2)
	ev := baseEvent([]contract.Detection{{ModelID: &m2, BBox: [4]float64{10, 10, 20, 20}, ClassName: "person"}})
	ev.FrameWidth = 0
	ev.FrameHeight = 0
	result, reason, _ := eng.Handle(ev)
	if result != "pass" || reason != "" {
		t.Fatalf("got %s/%s", result, reason)
	}
}

func TestHandleFillsSingleTaskModelID(t *testing.T) {
	eng := engineWithTemplate(
		config.TaskConfig{ID: 1, TaskType: "realtime", ModelIDs: []int64{-1}}, nil,
	)
	ev := baseEvent([]contract.Detection{{BBox: [4]float64{10, 10, 20, 20}, ClassName: "person"}})
	result, reason, _ := eng.Handle(ev)
	if result != "pass" || reason != "" {
		t.Fatalf("got %s/%s", result, reason)
	}
}

func TestHandleAllowsUnknownDetectionModelWithOnlyAllModelRegions(t *testing.T) {
	eng := engineWithTemplate(
		config.TaskConfig{ID: 1, TaskType: "realtime", ModelIDs: []int64{1, 2}},
		[]config.Region{{
			ID: 1, DeviceID: "cam", RegionName: "all", RegionType: "polygon", IsEnabled: true,
			Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}, {X: 0, Y: 1}},
		}},
	)
	ev := baseEvent([]contract.Detection{{BBox: [4]float64{10, 10, 20, 20}, ClassName: "person"}})
	result, reason, _ := eng.Handle(ev)
	if result != "pass" || reason != "" {
		t.Fatalf("got %s/%s", result, reason)
	}
}

func TestHandleRejectsMissingFrameSizeWhenAllModelRegionApplies(t *testing.T) {
	eng := engineWithTemplate(
		config.TaskConfig{ID: 1, TaskType: "realtime", ModelIDs: []int64{1, 2}},
		[]config.Region{{
			ID: 1, DeviceID: "cam", RegionName: "all", RegionType: "polygon", IsEnabled: true,
			Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}},
		}},
	)
	one := int64(1)
	ev := baseEvent([]contract.Detection{{ModelID: &one, BBox: [4]float64{10, 10, 20, 20}}})
	ev.FrameWidth, ev.FrameHeight = 0, 0
	result, reason, _ := eng.Handle(ev)
	if result != "drop" || reason != "invalid_frame_size" {
		t.Fatalf("got %s/%s", result, reason)
	}
}

func TestHandleUsesEventModelFallbackBeforeForeignValidation(t *testing.T) {
	eng := engineWithTemplate(
		config.TaskConfig{ID: 1, TaskType: "realtime", ModelIDs: []int64{1, 2}}, nil,
	)
	ev := baseEvent([]contract.Detection{{BBox: [4]float64{10, 10, 20, 20}}})
	ev.ModelIDs = []int64{99}
	result, reason, _ := eng.Handle(ev)
	if result != "drop" || reason != "foreign_detection_model_id" {
		t.Fatalf("got %s/%s", result, reason)
	}
}

func TestRegionHitModeHotUpdateIsTaskScopedAndNeedsNoEngineRestart(t *testing.T) {
	cache := template.NewCache(time.Minute)
	region := config.Region{
		ID: 1, DeviceID: "cam", RegionName: "left", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 140, Y: 0}, {X: 140, Y: 400}, {X: 0, Y: 400}},
	}
	pipeline := func(mode string) []config.PipelineStep {
		enabled := true
		return []config.PipelineStep{
			{Plugin: "region_gate", Enabled: &enabled, Params: map[string]any{"hit_mode": mode}},
			{Plugin: "default_pass", Enabled: &enabled, Params: map[string]any{}},
		}
	}
	for _, taskID := range []int64{1, 2} {
		cache.Upsert(config.TaskTemplate{
			Schema: "post_task_template.v1", Revision: 1,
			Task: config.TaskConfig{
				ID: taskID, TaskName: "task", TaskType: "realtime",
				ModelIDs: []int64{1}, Pipeline: pipeline("center"),
			},
			Regions: []config.Region{region},
		})
	}
	eng := New(config.Config{Enabled: true, InstanceID: "test"}, cache, nil)
	one := int64(1)
	event := baseEvent([]contract.Detection{{
		ModelID: &one, BBox: [4]float64{100, 100, 200, 200}, ClassName: "person",
	}})

	result, reason, _ := eng.Handle(event)
	if result != "drop" || reason != "region_miss" {
		t.Fatalf("center before update=%s/%s", result, reason)
	}

	cache.Upsert(config.TaskTemplate{
		Schema: "post_task_template.v1", Revision: 2,
		Task: config.TaskConfig{
			ID: 1, TaskName: "task", TaskType: "realtime",
			ModelIDs: []int64{1}, Pipeline: pipeline("any_intersection"),
		},
		Regions: []config.Region{region},
	})
	result, reason, _ = eng.Handle(event)
	if result != "pass" || reason != "" {
		t.Fatalf("task 1 did not use hot-updated mode: %s/%s", result, reason)
	}

	event.TaskID = 2
	result, reason, _ = eng.Handle(event)
	if result != "drop" || reason != "region_miss" {
		t.Fatalf("task 2 configuration leaked after task 1 update: %s/%s", result, reason)
	}
}
