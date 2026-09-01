package plugin

import (
	"testing"
	"time"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/pipeline"
)

func resetTrackState() {
	globalTrackState.mu.Lock()
	globalTrackState.tracks = map[string]*trackState{}
	globalTrackState.mu.Unlock()
}

func spatialCtx(dets []contract.Detection, regions []config.Region, params map[string]any) *pipeline.Context {
	return &pipeline.Context{
		Event: contract.InferEvent{
			TaskID:      1,
			DeviceID:    "cam1",
			Timestamp:   time.Now().Format(time.RFC3339),
			FrameWidth:  1920,
			FrameHeight: 1080,
			Detections:  dets,
			ModelIDs:    []int64{1},
		},
		Task:         config.TaskConfig{ID: 1, ModelIDs: []int64{1}},
		Regions:      regions,
		Detections:   dets,
		Enrichment:   map[string]any{},
		Decision:     pipeline.DecisionContinue,
		PluginParams: params,
	}
}

func TestLineCross_DetectsCrossing(t *testing.T) {
	resetTrackState()
	// horizontal line y=500 from (0,500) to (1920,500)
	lines := []config.Region{{
		ID: 10, DeviceID: "cam1", RegionName: "警戒线", RegionType: "line", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 500.0 / 1080}, {X: 1, Y: 500.0 / 1080}},
	}}
	params := map[string]any{"direction": "both", "sample_point": "center"}

	// frame 1: above line (y center ~300) — 尚未越线，应丢弃
	d1 := contract.Detection{BBox: [4]float64{900, 200, 1000, 400}, ClassName: "person", TrackID: 1, Confidence: 0.9}
	ctx1 := spatialCtx([]contract.Detection{d1}, lines, params)
	delta1, err := (LineCross{}).Process(ctx1)
	if err != nil {
		t.Fatal(err)
	}
	if delta1.Decision == nil || *delta1.Decision != pipeline.DecisionDrop {
		t.Fatalf("first frame should drop before cross, got %+v", delta1)
	}

	// frame 2: below line (y center ~700) → cross
	d2 := contract.Detection{BBox: [4]float64{900, 600, 1000, 800}, ClassName: "person", TrackID: 1, Confidence: 0.9}
	ctx2 := spatialCtx([]contract.Detection{d2}, lines, params)
	delta2, err := (LineCross{}).Process(ctx2)
	if err != nil {
		t.Fatal(err)
	}
	if delta2.Decision != nil || delta2.Detections == nil || len(*delta2.Detections) != 1 {
		t.Fatalf("expected cross pass, delta=%+v", delta2)
	}
}

func TestLineCross_NoCrossDrops(t *testing.T) {
	resetTrackState()
	lines := []config.Region{{
		ID: 10, RegionName: "线", RegionType: "line", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0.5}, {X: 1, Y: 0.5}},
	}}
	d := contract.Detection{BBox: [4]float64{900, 200, 1000, 400}, ClassName: "person", TrackID: 2, Confidence: 0.9}
	ctx := spatialCtx([]contract.Detection{d}, lines, map[string]any{})
	delta, _ := (LineCross{}).Process(ctx)
	if delta.Decision == nil || *delta.Decision != pipeline.DecisionDrop {
		t.Fatal("expected drop when no cross")
	}
}

func TestRegionEnterExit_Enter(t *testing.T) {
	resetTrackState()
	regions := []config.Region{{
		ID: 1, RegionName: "禁区", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 0.5, Y: 0}, {X: 0.5, Y: 0.5}, {X: 0, Y: 0.5}},
	}}
	params := map[string]any{"event_type": "enter", "hit_mode": "center"}

	outside := contract.Detection{BBox: [4]float64{1400, 500, 1600, 700}, ClassName: "person", TrackID: 3, Confidence: 0.9}
	ctx1 := spatialCtx([]contract.Detection{outside}, regions, params)
	delta1, _ := (RegionEnterExit{}).Process(ctx1)
	if delta1.Decision == nil || *delta1.Decision != pipeline.DecisionDrop {
		t.Fatal("outside should drop on enter-only")
	}

	inside := contract.Detection{BBox: [4]float64{400, 200, 560, 400}, ClassName: "person", TrackID: 3, Confidence: 0.9}
	ctx2 := spatialCtx([]contract.Detection{inside}, regions, params)
	delta2, _ := (RegionEnterExit{}).Process(ctx2)
	if delta2.Detections == nil || len(*delta2.Detections) != 1 {
		t.Fatalf("enter expected pass, got %+v", delta2)
	}
}

func TestRegionEnterExit_Exit(t *testing.T) {
	resetTrackState()
	regions := []config.Region{{
		ID: 1, RegionName: "禁区", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 0.5, Y: 0}, {X: 0.5, Y: 0.5}, {X: 0, Y: 0.5}},
	}}
	params := map[string]any{"event_type": "exit"}

	inside := contract.Detection{BBox: [4]float64{400, 200, 560, 400}, ClassName: "person", TrackID: 4, Confidence: 0.9}
	_, _ = (RegionEnterExit{}).Process(spatialCtx([]contract.Detection{inside}, regions, params))

	outside := contract.Detection{BBox: [4]float64{1400, 500, 1600, 700}, ClassName: "person", TrackID: 4, Confidence: 0.9}
	delta, _ := (RegionEnterExit{}).Process(spatialCtx([]contract.Detection{outside}, regions, params))
	if delta.Detections == nil || len(*delta.Detections) != 1 {
		t.Fatalf("exit expected pass, got %+v", delta)
	}
}

func TestDwellTimer_Timeout(t *testing.T) {
	resetTrackState()
	regions := []config.Region{{
		ID: 1, RegionName: "通道", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}, {X: 0, Y: 1}},
	}}
	params := map[string]any{"min_dwell_sec": 2.0}

	d := contract.Detection{BBox: [4]float64{400, 200, 560, 400}, ClassName: "person", TrackID: 5, Confidence: 0.9}
	ts := time.Now().Add(-3 * time.Second).Format(time.RFC3339)

	ctx1 := spatialCtx([]contract.Detection{d}, regions, params)
	ctx1.Event.Timestamp = ts
	_, _ = (DwellTimer{}).Process(ctx1)

	ctx2 := spatialCtx([]contract.Detection{d}, regions, params)
	delta, _ := (DwellTimer{}).Process(ctx2)
	if delta.Detections == nil || len(*delta.Detections) != 1 {
		t.Fatalf("dwell timeout expected pass, got %+v", delta)
	}
}

func TestDwellTimer_NotYet(t *testing.T) {
	resetTrackState()
	regions := []config.Region{{
		ID: 1, RegionName: "通道", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}, {X: 0, Y: 1}},
	}}
	params := map[string]any{"min_dwell_sec": 60.0}
	d := contract.Detection{BBox: [4]float64{400, 200, 560, 400}, ClassName: "person", TrackID: 6, Confidence: 0.9}
	delta, _ := (DwellTimer{}).Process(spatialCtx([]contract.Detection{d}, regions, params))
	if delta.Decision == nil || *delta.Decision != pipeline.DecisionDrop {
		t.Fatal("expected drop before dwell met")
	}
}

func TestHeadcountGate_MeetsThreshold(t *testing.T) {
	regions := []config.Region{{
		ID: 1, RegionName: "大厅", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}, {X: 0, Y: 1}},
	}}
	dets := []contract.Detection{
		{BBox: [4]float64{100, 100, 200, 300}, ClassName: "person", TrackID: 1, Confidence: 0.9},
		{BBox: [4]float64{300, 100, 400, 300}, ClassName: "person", TrackID: 2, Confidence: 0.9},
		{BBox: [4]float64{500, 100, 600, 300}, ClassName: "person", TrackID: 3, Confidence: 0.9},
	}
	params := map[string]any{"threshold": 3, "operator": "gte"}
	delta, _ := (HeadcountGate{}).Process(spatialCtx(dets, regions, params))
	if delta.Detections == nil || len(*delta.Detections) != 3 {
		t.Fatalf("expected 3 detections, got %+v", delta)
	}
}

func TestHeadcountGate_BelowThreshold(t *testing.T) {
	regions := []config.Region{{
		ID: 1, RegionName: "大厅", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}, {X: 0, Y: 1}},
	}}
	dets := []contract.Detection{
		{BBox: [4]float64{100, 100, 200, 300}, ClassName: "person", TrackID: 1, Confidence: 0.9},
	}
	params := map[string]any{"threshold": 5, "operator": "gte"}
	delta, _ := (HeadcountGate{}).Process(spatialCtx(dets, regions, params))
	if delta.DropReason != "headcount_not_met" {
		t.Fatalf("expected headcount_not_met, got %s", delta.DropReason)
	}
}

func TestLineCross_ModelSpecificLineDoesNotConsumeOtherModelState(t *testing.T) {
	resetTrackState()
	lines := []config.Region{{
		ID: 10, RegionName: "模型1警戒线", RegionType: "line", IsEnabled: true, ModelIDs: []int64{1},
		Points: []config.Point{{X: 0, Y: 0.5}, {X: 1, Y: 0.5}},
	}}
	params := map[string]any{"direction": "both"}
	above := [4]float64{900, 200, 1000, 400}
	below := [4]float64{900, 600, 1000, 800}

	// 同 track_id 的模型2不能为模型1预热越线状态。
	for _, bbox := range [][4]float64{above, below} {
		det := contract.Detection{ModelID: modelID(2), BBox: bbox, TrackID: 9}
		delta, _ := (LineCross{}).Process(spatialCtx([]contract.Detection{det}, lines, params))
		if delta.DropReason != "no_line_cross" {
			t.Fatalf("model2 should not use model1 line: %#v", delta)
		}
	}

	first := contract.Detection{ModelID: modelID(1), BBox: above, TrackID: 9}
	second := contract.Detection{ModelID: modelID(1), BBox: below, TrackID: 9}
	_, _ = (LineCross{}).Process(spatialCtx([]contract.Detection{first}, lines, params))
	delta, _ := (LineCross{}).Process(spatialCtx([]contract.Detection{second}, lines, params))
	if delta.Detections == nil || len(*delta.Detections) != 1 {
		t.Fatalf("model1 crossing not detected: %#v", delta)
	}
}

func TestTrackStateKeySeparatesTaskDeviceModelAndTrack(t *testing.T) {
	keys := map[string]struct{}{
		trackStateKey(1, "cam-a", modelID(1), 7): {},
		trackStateKey(2, "cam-a", modelID(1), 7): {},
		trackStateKey(1, "cam-b", modelID(1), 7): {},
		trackStateKey(1, "cam-a", modelID(2), 7): {},
		trackStateKey(1, "cam-a", modelID(1), 8): {},
	}
	if len(keys) != 5 {
		t.Fatalf("track state key collision: %#v", keys)
	}
}

func TestHeadcountGateSameTrackFromDifferentModelsCountsIndependently(t *testing.T) {
	regions := []config.Region{
		{ID: 1, RegionName: "模型1区", RegionType: "polygon", IsEnabled: true, ModelIDs: []int64{1},
			Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}, {X: 0, Y: 1}}},
		{ID: 2, RegionName: "模型2区", RegionType: "polygon", IsEnabled: true, ModelIDs: []int64{2},
			Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}, {X: 0, Y: 1}}},
	}
	dets := []contract.Detection{
		{ModelID: modelID(1), BBox: [4]float64{100, 100, 200, 200}, TrackID: 5, ClassName: "person"},
		{ModelID: modelID(2), BBox: [4]float64{100, 100, 200, 200}, TrackID: 5, ClassName: "person"},
	}
	delta, _ := (HeadcountGate{}).Process(spatialCtx(dets, regions, map[string]any{
		"threshold": 2, "operator": "gte",
	}))
	if delta.Detections == nil || len(*delta.Detections) != 2 {
		t.Fatalf("same track from two models was deduplicated: %#v", delta)
	}
}

func TestSpatialPluginsSkipMissingTrackID(t *testing.T) {
	resetTrackState()
	line := []config.Region{{
		ID: 1, RegionName: "线", RegionType: "line", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0.5}, {X: 1, Y: 0.5}},
	}}
	polygon := []config.Region{{
		ID: 2, RegionName: "区", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}, {X: 0, Y: 1}},
	}}
	det := contract.Detection{ModelID: modelID(1), BBox: [4]float64{100, 100, 200, 200}, TrackID: 0}
	cases := []struct {
		name string
		run  func() pipeline.PluginDelta
	}{
		{"line", func() pipeline.PluginDelta {
			d, _ := (LineCross{}).Process(spatialCtx([]contract.Detection{det}, line, nil))
			return d
		}},
		{"enter_exit", func() pipeline.PluginDelta {
			d, _ := (RegionEnterExit{}).Process(spatialCtx([]contract.Detection{det}, polygon, nil))
			return d
		}},
		{"dwell", func() pipeline.PluginDelta {
			d, _ := (DwellTimer{}).Process(spatialCtx([]contract.Detection{det}, polygon, nil))
			return d
		}},
	}
	for _, tc := range cases {
		with := tc.run()
		if with.Decision == nil || *with.Decision != pipeline.DecisionDrop {
			t.Fatalf("%s should skip track_id=0: %#v", tc.name, with)
		}
	}
}
