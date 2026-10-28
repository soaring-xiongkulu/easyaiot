package plugin

import (
	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/pipeline"
	"testing"
	"time"
)

func TestHeadcountCooldownAfterEvaluation(t *testing.T) {
	resetTrackState()
	det := contract.Detection{ClassName: "person", BBox: [4]float64{100, 100, 200, 200}}
	params := map[string]any{"threshold": 1, "count_mode": "all", "cooldown_sec": 60}
	ctx := spatialCtx([]contract.Detection{det}, nil, params)
	base := time.Now().Truncate(time.Second)
	for i, seconds := range []int{0, 1, 61} {
		ctx.Event.Timestamp = base.Add(time.Duration(seconds) * time.Second).Format(time.RFC3339)
		delta, err := (HeadcountGate{}).Process(ctx)
		if err != nil {
			t.Fatal(err)
		}
		if i == 1 && delta.DropReason != "headcount_cooldown" {
			t.Fatalf("repeated alert: %+v", delta)
		}
		if i != 1 && delta.Decision != nil {
			t.Fatalf("expected reminder: %+v", delta)
		}
	}
}

func TestMissingRegionsDoNotProduceBusinessAlerts(t *testing.T) {
	for _, p := range []pipeline.Plugin{LineCross{}, RegionEnterExit{}, DwellTimer{}} {
		delta, err := p.Process(spatialCtx([]contract.Detection{{ClassName: "person", TrackID: 1}}, nil, nil))
		if err != nil || delta.Decision == nil || *delta.Decision != pipeline.DecisionDrop {
			t.Fatalf("%s should require configured geometry: %+v %v", p.Name(), delta, err)
		}
	}
}

func TestBoundRulesAreIndependentAndScoped(t *testing.T) {
	resetTrackState()
	regions := []config.Region{
		{ID: 10, RegionName: "出入口", RegionType: "line", IsEnabled: true, Points: []config.Point{{X: 0, Y: .5}, {X: 1, Y: .5}}},
		{ID: 20, RegionName: "等候区", RegionType: "polygon", IsEnabled: true, Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}, {X: 0, Y: 1}}},
	}
	task := config.TaskConfig{Pipeline: []config.PipelineStep{
		{Plugin: "region_gate"},
		{Plugin: "line_cross", Params: map[string]any{"region_ids": []any{float64(10)}}},
		{Plugin: "headcount_gate", Params: map[string]any{"region_ids": []any{float64(20)}, "threshold": 1}},
		{Plugin: "default_pass"},
	}}
	event := spatialCtx([]contract.Detection{{ClassName: "person", TrackID: 1, BBox: [4]float64{100, 200, 200, 400}}}, regions, nil).Event
	first := pipeline.Run(Builtin(), event, task, regions, true)
	if first.Decision != pipeline.DecisionPass {
		t.Fatal("headcount must pass even though no line crossed", first.DropReason)
	}
	rules := first.Context.Enrichment["business_rules"].([]map[string]any)
	if len(rules) != 1 || rules[0]["region_id"] != int64(20) {
		t.Fatalf("wrong binding: %+v", rules)
	}
	// A second instance of the SAME plugin binds another polygon without losing
	// either result, and a disabled shape must never turn into full-frame counting.
	regions = append(regions, config.Region{ID: 30, RegionType: "polygon", IsEnabled: false, Points: regions[1].Points})
	task.Pipeline = append(task.Pipeline[:3], config.PipelineStep{Plugin: "headcount_gate", Params: map[string]any{"region_ids": []any{float64(30)}, "threshold": 1}}, config.PipelineStep{Plugin: "default_pass"})
	result := pipeline.Run(Builtin(), event, task, regions, true)
	rules = result.Context.Enrichment["business_rules"].([]map[string]any)
	if len(rules) != 1 {
		t.Fatalf("disabled region produced results: %+v", rules)
	}
	regions[2].IsEnabled = true
	result = pipeline.Run(Builtin(), event, task, regions, true)
	rules = result.Context.Enrichment["business_rules"].([]map[string]any)
	if len(rules) != 2 {
		t.Fatalf("same plugin on two shapes lost a result: %+v", rules)
	}
}

func TestRemovingAllBindingsDoesNotEnableFullFrameAlerts(t *testing.T) {
	task := config.TaskConfig{Pipeline: []config.PipelineStep{{Plugin: "default_pass", Params: map[string]any{"monitoring_mode": "bound"}}}}
	event := spatialCtx([]contract.Detection{{ClassName: "person", BBox: [4]float64{1, 1, 20, 20}}}, nil, nil).Event
	result := pipeline.Run(Builtin(), event, task, nil, true)
	if result.Decision != pipeline.DecisionDrop {
		t.Fatal("removing the last rule enabled unrestricted alerts")
	}
}

func TestBoundAreaUsesGeometryMembershipControls(t *testing.T) {
	region := config.Region{ID: 50, RegionType: "polygon", IsEnabled: true, HitMode: "center", Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: .5}, {X: 0, Y: .5}}}
	task := config.TaskConfig{Pipeline: []config.PipelineStep{{Plugin: "headcount_gate", Params: map[string]any{"region_ids": []any{float64(50)}, "hit_mode": "bottom_center", "threshold": 1}}, {Plugin: "default_pass"}}}
	event := spatialCtx([]contract.Detection{{ClassName: "person", BBox: [4]float64{100, 400, 200, 650}}}, []config.Region{region}, nil).Event
	result := pipeline.Run(Builtin(), event, task, []config.Region{region}, true)
	if result.Decision != pipeline.DecisionPass {
		t.Fatal("visible center setting was overridden by plugin bottom-center default")
	}
	ratio := .9
	region.HitMode = "overlap_ratio"
	region.MinOverlapRatio = &ratio
	result = pipeline.Run(Builtin(), event, task, []config.Region{region}, true)
	if result.Decision != pipeline.DecisionDrop {
		t.Fatal("visible overlap ratio setting was ignored")
	}
}

func TestReversingBoundLineDoesNotInventStationaryCrossing(t *testing.T) {
	resetTrackState()
	r := config.Region{ID: 99, RegionType: "line", IsEnabled: true, Points: []config.Point{{X: 0, Y: .5}, {X: 1, Y: .5}}}
	task := config.TaskConfig{Pipeline: []config.PipelineStep{{Plugin: "line_cross", Params: map[string]any{"region_ids": []any{float64(99)}}}, {Plugin: "default_pass"}}}
	event := spatialCtx([]contract.Detection{{ClassName: "person", TrackID: 23, BBox: [4]float64{100, 200, 200, 400}}}, nil, nil).Event
	pipeline.Run(Builtin(), event, task, []config.Region{r}, true)
	r.Points[0], r.Points[1] = r.Points[1], r.Points[0]
	result := pipeline.Run(Builtin(), event, task, []config.Region{r}, true)
	if result.Decision != pipeline.DecisionDrop {
		t.Fatal("geometry edit created a phantom crossing for a stationary target")
	}
}

func TestBoundRulesKeepDistinctTracksWithOverlappingBoxes(t *testing.T) {
	r:=config.Region{ID:21,RegionType:"polygon",IsEnabled:true,Points:[]config.Point{{X:0,Y:0},{X:1,Y:0},{X:1,Y:1},{X:0,Y:1}}}
	dets:=[]contract.Detection{{ClassName:"person",TrackID:1,BBox:[4]float64{100,100,200,200}},{ClassName:"person",TrackID:2,BBox:[4]float64{100,100,200,200}}}
	task:=config.TaskConfig{Pipeline:[]config.PipelineStep{{Plugin:"headcount_gate",Params:map[string]any{"region_ids":[]any{float64(21)},"threshold":1}},{Plugin:"default_pass"}}}
	result:=pipeline.Run(Builtin(),spatialCtx(dets,nil,nil).Event,task,[]config.Region{r},true)
	if len(result.Context.Detections)!=2 { t.Fatal("distinct people were collapsed because their bounding boxes overlap") }
}

func TestDirectionUIValues(t *testing.T) {
	for _, tc := range []struct {
		name       string
		prev, curr int
		want       bool
	}{
		{"forward", 1, -1, true}, {"forward", -1, 1, false},
		{"backward", -1, 1, true}, {"backward", 1, -1, false},
	} {
		if got := crossedSide(tc.prev, tc.curr, tc.name); got != tc.want {
			t.Fatalf("%+v got %v", tc, got)
		}
	}
}

func TestLineCrossRetainsSideOnLine(t *testing.T) {
	resetTrackState()
	regions := []config.Region{{ID: 1, RegionType: "line", IsEnabled: true, Points: []config.Point{{X: 0, Y: .5}, {X: 1, Y: .5}}}}
	var delta pipeline.PluginDelta
	for _, y := range []float64{400, 540, 700} {
		ctx := spatialCtx([]contract.Detection{{TrackID: 1, ClassName: "person", BBox: [4]float64{900, y - 20, 1000, y + 20}}}, regions, map[string]any{"direction": "both"})
		delta, _ = (LineCross{}).Process(ctx)
	}
	if delta.Decision != nil {
		t.Fatalf("crossing after on-line sample was lost: %+v", delta)
	}
	events := delta.EnrichmentPatch["crossed"].([]map[string]any)
	if len(events) != 1 || events[0]["direction"] != "backward" {
		t.Fatalf("actual direction missing: %v", events)
	}
}

func TestRegionExitThroughDefaultHead(t *testing.T) {
	resetTrackState()
	regions := []config.Region{{ID: 1, RegionType: "polygon", IsEnabled: true, Points: []config.Point{{X: 0, Y: 0}, {X: .5, Y: 0}, {X: .5, Y: 1}, {X: 0, Y: 1}}}}
	task := config.TaskConfig{Pipeline: []config.PipelineStep{{Plugin: "region_gate"}, {Plugin: "region_enter_exit", Params: map[string]any{"event_type": "exit"}}, {Plugin: "default_pass"}}}
	var result pipeline.Result
	for _, x := range []float64{400, 1400} {
		ctx := spatialCtx([]contract.Detection{{TrackID: 1, ClassName: "person", BBox: [4]float64{x, 200, x + 100, 400}}}, regions, nil)
		result = pipeline.Run(Builtin(), ctx.Event, task, regions, true)
	}
	if result.Decision != pipeline.DecisionPass {
		t.Fatalf("outside observation lost: %+v", result)
	}
	events := result.Context.Enrichment["region_enter_exit"].(map[string]any)["events"].([]map[string]any)
	if len(events) != 1 || events[0]["event"] != "exit" {
		t.Fatalf("missing exit: %v", events)
	}
}

func TestRegionEnterExitSynthesizesExitAfterTrackVanishes(t *testing.T) {
	resetTrackState()
	regions := []config.Region{{ID: 7, RegionName: "大堂", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}, {X: 0, Y: 1}}}}
	task := config.TaskConfig{Pipeline: []config.PipelineStep{
		{Plugin: "region_gate"},
		{Plugin: "region_enter_exit", Params: map[string]any{"event_type": "both", "exit_timeout_sec": 15}},
		{Plugin: "default_pass"},
	}}
	base := time.Now().Truncate(time.Second)
	inside := spatialCtx([]contract.Detection{{TrackID: 5, ClassName: "person", BBox: [4]float64{400, 200, 500, 400}}}, regions, nil)
	inside.Event.Timestamp = base.Format(time.RFC3339)
	if first := pipeline.Run(Builtin(), inside.Event, task, regions, true); first.Decision != pipeline.DecisionPass {
		t.Fatal("enter observation lost:", first.DropReason)
	}

	// The tracker lost the target mid-region (occlusion/sampling gap/left the
	// frame); only a later empty observation frame arrives. The vanish must be
	// reconciled into an exit, otherwise headcount drifts up forever.
	later := spatialCtx(nil, regions, nil)
	later.Event.Timestamp = base.Add(30 * time.Second).Format(time.RFC3339)
	result := pipeline.Run(Builtin(), later.Event, task, regions, true)
	if result.Decision != pipeline.DecisionPass {
		t.Fatal("synthesized exit was dropped:", result.DropReason)
	}
	events := result.Context.Enrichment["region_enter_exit"].(map[string]any)["events"].([]map[string]any)
	if len(events) != 1 || events[0]["event"] != "exit" || events[0]["track_id"] != 5 || events[0]["synthesized"] != true {
		t.Fatalf("missing synthesized exit: %v", events)
	}
	if events[0]["region_name"] != "大堂" {
		t.Fatalf("synthesized exit lost region name: %v", events)
	}
}
