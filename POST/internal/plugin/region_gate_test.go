package plugin

import (
	"testing"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/pipeline"
)

func baseCtx(dets []contract.Detection, regions []config.Region) *pipeline.Context {
	return &pipeline.Context{
		Event: contract.InferEvent{
			FrameWidth: 1920, FrameHeight: 1080,
			Detections: dets, ModelIDs: []int64{1},
		},
		Task:       config.TaskConfig{ModelIDs: []int64{1}},
		Regions:    regions,
		Detections: dets,
		Enrichment: map[string]any{},
		Decision:   pipeline.DecisionContinue,
		PluginParams: map[string]any{"hit_mode": "center"},
	}
}

func TestRegionGate_R1_NoRegionsBypass(t *testing.T) {
	dets := []contract.Detection{{BBox: [4]float64{100, 100, 200, 200}, ClassName: "person", Confidence: 0.9}}
	ctx := baseCtx(dets, nil)
	delta, err := (RegionGate{}).Process(ctx)
	if err != nil {
		t.Fatal(err)
	}
	if delta.RegionLabel != "全画面" {
		t.Fatalf("region=%q", delta.RegionLabel)
	}
	if delta.EnrichmentPatch["region_filter"] != "bypass" {
		t.Fatalf("filter=%v", delta.EnrichmentPatch["region_filter"])
	}
	if delta.Detections != nil {
		t.Fatal("detections should be unchanged (nil delta)")
	}
}

func TestRegionGate_R2_CenterInside(t *testing.T) {
	// square covering center of bbox (150,150)
	regions := []config.Region{{
		ID: 1, DeviceID: "cam", RegionName: "区A", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 300, Y: 0}, {X: 300, Y: 300}, {X: 0, Y: 300}},
	}}
	dets := []contract.Detection{{BBox: [4]float64{100, 100, 200, 200}, ClassName: "person", Confidence: 0.9}}
	ctx := baseCtx(dets, regions)
	delta, err := (RegionGate{}).Process(ctx)
	if err != nil {
		t.Fatal(err)
	}
	if delta.Detections == nil || len(*delta.Detections) != 1 {
		t.Fatalf("kept=%v", delta.Detections)
	}
	if delta.RegionLabel != "区A" {
		t.Fatalf("region=%q", delta.RegionLabel)
	}
}

func TestRegionGate_R3_CenterOutside(t *testing.T) {
	regions := []config.Region{{
		ID: 1, DeviceID: "cam", RegionName: "区A", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 50, Y: 0}, {X: 50, Y: 50}, {X: 0, Y: 50}},
	}}
	dets := []contract.Detection{{BBox: [4]float64{100, 100, 200, 200}, ClassName: "person", Confidence: 0.9}}
	ctx := baseCtx(dets, regions)
	delta, err := (RegionGate{}).Process(ctx)
	if err != nil {
		t.Fatal(err)
	}
	if delta.Decision == nil || *delta.Decision != pipeline.DecisionDrop {
		t.Fatal("expected drop")
	}
	if delta.DropReason != "region_miss" {
		t.Fatalf("reason=%s", delta.DropReason)
	}
}

func TestRegionGate_R4_XYObjectPoints(t *testing.T) {
	// same as R2 but ensure Point unmarshaling path via constructed points
	regions := []config.Region{{
		ID: 1, DeviceID: "cam", RegionName: "区A", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 300, Y: 0}, {X: 300, Y: 300}, {X: 0, Y: 300}},
	}}
	dets := []contract.Detection{{BBox: [4]float64{100, 100, 200, 200}, ClassName: "person", Confidence: 0.9}}
	ctx := baseCtx(dets, regions)
	delta, _ := (RegionGate{}).Process(ctx)
	if delta.RegionLabel != "区A" {
		t.Fatalf("region=%q", delta.RegionLabel)
	}
}

func TestRegionGate_R5_NormalizedPoints(t *testing.T) {
	// normalized square left half; bbox center at (480,540) → inside
	regions := []config.Region{{
		ID: 1, DeviceID: "cam", RegionName: "左半", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 0.5, Y: 0}, {X: 0.5, Y: 1}, {X: 0, Y: 1}},
	}}
	dets := []contract.Detection{{BBox: [4]float64{400, 500, 560, 580}, ClassName: "person", Confidence: 0.9}}
	ctx := baseCtx(dets, regions)
	delta, _ := (RegionGate{}).Process(ctx)
	if delta.Detections == nil || len(*delta.Detections) != 1 {
		t.Fatal("expected keep")
	}
	// outside right half
	dets2 := []contract.Detection{{BBox: [4]float64{1400, 500, 1600, 580}, ClassName: "person", Confidence: 0.9}}
	ctx2 := baseCtx(dets2, regions)
	delta2, _ := (RegionGate{}).Process(ctx2)
	if delta2.DropReason != "region_miss" {
		t.Fatalf("expected region_miss got %s", delta2.DropReason)
	}
}

func TestRegionGate_R6_SortOrder(t *testing.T) {
	regions := []config.Region{
		{ID: 2, DeviceID: "cam", RegionName: "后", RegionType: "polygon", IsEnabled: true, SortOrder: 10,
			Points: []config.Point{{X: 0, Y: 0}, {X: 300, Y: 0}, {X: 300, Y: 300}, {X: 0, Y: 300}}},
		{ID: 1, DeviceID: "cam", RegionName: "先", RegionType: "polygon", IsEnabled: true, SortOrder: 1,
			Points: []config.Point{{X: 0, Y: 0}, {X: 300, Y: 0}, {X: 300, Y: 300}, {X: 0, Y: 300}}},
	}
	dets := []contract.Detection{{BBox: [4]float64{100, 100, 200, 200}, ClassName: "person", Confidence: 0.9}}
	ctx := baseCtx(dets, regions)
	delta, _ := (RegionGate{}).Process(ctx)
	if delta.RegionLabel != "先" {
		t.Fatalf("region=%q", delta.RegionLabel)
	}
}

func TestRegionGate_R7_ModelIDsNoIntersect(t *testing.T) {
	regions := []config.Region{{
		ID: 1, DeviceID: "cam", RegionName: "区A", RegionType: "polygon", IsEnabled: true,
		ModelIDs: []int64{99},
		Points:   []config.Point{{X: 0, Y: 0}, {X: 300, Y: 0}, {X: 300, Y: 300}, {X: 0, Y: 300}},
	}}
	dets := []contract.Detection{{BBox: [4]float64{100, 100, 200, 200}, ClassName: "person", Confidence: 0.9}}
	ctx := baseCtx(dets, regions)
	delta, _ := (RegionGate{}).Process(ctx)
	// region skipped → bypass
	if delta.RegionLabel != "全画面" {
		t.Fatalf("expected bypass, got %q", delta.RegionLabel)
	}
}

func TestRegionGate_R8_UsesContextRegionsOnly(t *testing.T) {
	// caller filters by device; gate just uses Context.Regions
	regions := []config.Region{{
		ID: 1, DeviceID: "cam_b", RegionName: "B区", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 50, Y: 0}, {X: 50, Y: 50}, {X: 0, Y: 50}},
	}}
	dets := []contract.Detection{{BBox: [4]float64{100, 100, 200, 200}, ClassName: "person", Confidence: 0.9}}
	ctx := baseCtx(dets, regions)
	delta, _ := (RegionGate{}).Process(ctx)
	if delta.DropReason != "region_miss" {
		t.Fatalf("expected miss on wrong-device regions passed in, got %s", delta.DropReason)
	}
}

func TestDefaultPipeline_InsidePass(t *testing.T) {
	regions := []config.Region{{
		ID: 1, DeviceID: "cam", RegionName: "东门", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 300, Y: 0}, {X: 300, Y: 300}, {X: 0, Y: 300}},
	}}
	event := contract.InferEvent{
		Schema: contract.SchemaInferEvent, EventKind: "infer", CorrelationID: "c1",
		TaskID: 1, TaskType: "realtime", DeviceID: "cam", Timestamp: "2026-01-01T00:00:00Z",
		FrameWidth: 1920, FrameHeight: 1080,
		Detections: []contract.Detection{{BBox: [4]float64{100, 100, 200, 200}, ClassName: "person", Confidence: 0.9}},
		ModelIDs:   []int64{1},
	}
	task := config.TaskConfig{ID: 1, TaskName: "t", TaskType: "realtime", AlertEvent: "入侵", ModelIDs: []int64{1}}
	res := pipeline.Run(Builtin(), event, task, regions, true)
	if res.Decision != pipeline.DecisionPass {
		t.Fatalf("decision=%s reason=%s", res.Decision, res.DropReason)
	}
	if res.Context.RegionLabel != "东门" {
		t.Fatalf("region=%s", res.Context.RegionLabel)
	}
	if len(res.Trace) != 2 {
		t.Fatalf("trace len=%d", len(res.Trace))
	}
}

func TestDefaultPipeline_OutsideDrop(t *testing.T) {
	regions := []config.Region{{
		ID: 1, DeviceID: "cam", RegionName: "东门", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 50, Y: 0}, {X: 50, Y: 50}, {X: 0, Y: 50}},
	}}
	event := contract.InferEvent{
		Schema: contract.SchemaInferEvent, EventKind: "infer", CorrelationID: "c1",
		TaskID: 1, TaskType: "realtime", DeviceID: "cam", Timestamp: "2026-01-01T00:00:00Z",
		FrameWidth: 1920, FrameHeight: 1080,
		Detections: []contract.Detection{{BBox: [4]float64{100, 100, 200, 200}, ClassName: "person", Confidence: 0.9}},
		ModelIDs:   []int64{1},
	}
	task := config.TaskConfig{ID: 1, TaskName: "t", TaskType: "realtime", ModelIDs: []int64{1}}
	res := pipeline.Run(Builtin(), event, task, regions, false)
	if res.Decision != pipeline.DecisionDrop || res.DropReason != "region_miss" {
		t.Fatalf("got %s/%s", res.Decision, res.DropReason)
	}
}
