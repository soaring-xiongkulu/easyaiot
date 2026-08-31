package plugin

import (
	"testing"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/pipeline"
)

func modelID(id int64) *int64 { return &id }

func baseCtx(dets []contract.Detection, regions []config.Region) *pipeline.Context {
	return &pipeline.Context{
		Event: contract.InferEvent{
			FrameWidth: 1920, FrameHeight: 1080,
			Detections: dets, ModelIDs: []int64{1},
		},
		Task:         config.TaskConfig{ModelIDs: []int64{1}},
		Regions:      regions,
		Detections:   dets,
		Enrichment:   map[string]any{},
		Decision:     pipeline.DecisionContinue,
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

func TestRegionGate_R9_PerDetectionModelRegions(t *testing.T) {
	regions := []config.Region{
		{ID: 1, DeviceID: "cam", RegionName: "模型1左区", RegionType: "polygon", IsEnabled: true, ModelIDs: []int64{1},
			Points: []config.Point{{X: 0, Y: 0}, {X: 0.5, Y: 0}, {X: 0.5, Y: 1}, {X: 0, Y: 1}}},
		{ID: 2, DeviceID: "cam", RegionName: "模型2右区", RegionType: "polygon", IsEnabled: true, ModelIDs: []int64{2},
			Points: []config.Point{{X: 0.5, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}, {X: 0.5, Y: 1}}},
	}
	dets := []contract.Detection{
		{ModelID: modelID(1), BBox: [4]float64{100, 100, 200, 200}, ClassName: "person", Confidence: 0.9},
		{ModelID: modelID(2), BBox: [4]float64{1500, 100, 1600, 200}, ClassName: "car", Confidence: 0.9},
		{ModelID: modelID(1), BBox: [4]float64{1500, 100, 1600, 200}, ClassName: "outside", Confidence: 0.9},
	}
	ctx := baseCtx(dets, regions)
	delta, err := (RegionGate{}).Process(ctx)
	if err != nil {
		t.Fatal(err)
	}
	if delta.Detections == nil || len(*delta.Detections) != 2 {
		t.Fatalf("kept=%v", delta.Detections)
	}
	if (*delta.Detections)[0].MatchedRegionIDs[0] != 1 || (*delta.Detections)[1].MatchedRegionIDs[0] != 2 {
		t.Fatalf("wrong per-model matches: %#v", *delta.Detections)
	}
}

func TestRegionGate_R10_ModelWithoutRegionsBypasses(t *testing.T) {
	regions := []config.Region{{
		ID: 1, DeviceID: "cam", RegionName: "模型1区", RegionType: "polygon", IsEnabled: true,
		ModelIDs: []int64{1},
		Points:   []config.Point{{X: 0, Y: 0}, {X: 50, Y: 0}, {X: 50, Y: 50}, {X: 0, Y: 50}},
	}}
	dets := []contract.Detection{{
		ModelID: modelID(2), BBox: [4]float64{100, 100, 200, 200}, ClassName: "car", Confidence: 0.9,
	}}
	ctx := baseCtx(dets, regions)
	delta, err := (RegionGate{}).Process(ctx)
	if err != nil {
		t.Fatal(err)
	}
	if delta.Detections == nil || len(*delta.Detections) != 1 {
		t.Fatalf("model without regions must bypass, got %#v", delta)
	}
	if delta.EnrichmentPatch["region_filter"] != "bypass" {
		t.Fatalf("filter=%v", delta.EnrichmentPatch["region_filter"])
	}
}

func TestRegionGate_R11_AllModelRegionAppliesAlongsideModelSpecificRegion(t *testing.T) {
	regions := []config.Region{
		{ID: 1, DeviceID: "cam", RegionName: "全模型左区", RegionType: "polygon", IsEnabled: true,
			Points: []config.Point{{X: 0, Y: 0}, {X: 0.5, Y: 0}, {X: 0.5, Y: 1}, {X: 0, Y: 1}}},
		{ID: 2, DeviceID: "cam", RegionName: "模型2右区", RegionType: "polygon", IsEnabled: true, ModelIDs: []int64{2},
			Points: []config.Point{{X: 0.5, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}, {X: 0.5, Y: 1}}},
	}
	dets := []contract.Detection{
		{ModelID: modelID(1), BBox: [4]float64{100, 100, 200, 200}, ClassName: "m1-left"},
		{ModelID: modelID(2), BBox: [4]float64{100, 100, 200, 200}, ClassName: "m2-left"},
		{ModelID: modelID(2), BBox: [4]float64{1500, 100, 1600, 200}, ClassName: "m2-right"},
		{ModelID: modelID(1), BBox: [4]float64{1500, 100, 1600, 200}, ClassName: "m1-right-miss"},
	}
	delta, err := (RegionGate{}).Process(baseCtx(dets, regions))
	if err != nil {
		t.Fatal(err)
	}
	if delta.Detections == nil || len(*delta.Detections) != 3 {
		t.Fatalf("expected three detections, got %#v", delta.Detections)
	}
}

func TestRegionGate_R12_MultipleMatchesPopulateDetectionAndEventEnrichment(t *testing.T) {
	regions := []config.Region{
		{ID: 20, RegionName: "后区", RegionType: "polygon", IsEnabled: true, SortOrder: 2,
			Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}, {X: 0, Y: 1}}},
		{ID: 10, RegionName: "先区", RegionType: "rectangle", IsEnabled: true, SortOrder: 1,
			Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}, {X: 0, Y: 1}}},
	}
	dets := []contract.Detection{{ModelID: modelID(1), BBox: [4]float64{100, 100, 200, 200}}}
	delta, err := (RegionGate{}).Process(baseCtx(dets, regions))
	if err != nil {
		t.Fatal(err)
	}
	if delta.RegionLabel != "先区" {
		t.Fatalf("primary region=%q", delta.RegionLabel)
	}
	if delta.Detections == nil || len(*delta.Detections) != 1 {
		t.Fatalf("detections=%#v", delta.Detections)
	}
	got := (*delta.Detections)[0]
	if len(got.MatchedRegionIDs) != 2 || got.MatchedRegionIDs[0] != 10 || got.MatchedRegionIDs[1] != 20 {
		t.Fatalf("detection matches=%#v", got.MatchedRegionIDs)
	}
	ids, ok := delta.EnrichmentPatch["matched_region_ids"].([]int64)
	if !ok || len(ids) != 2 || ids[0] != 10 || ids[1] != 20 {
		t.Fatalf("event matches=%#v", delta.EnrichmentPatch["matched_region_ids"])
	}
}

func TestRegionGate_R13_MixedAppliedAndBypassIsPartial(t *testing.T) {
	regions := []config.Region{{
		ID: 1, RegionName: "模型1左区", RegionType: "polygon", IsEnabled: true, ModelIDs: []int64{1},
		Points: []config.Point{{X: 0, Y: 0}, {X: 0.5, Y: 0}, {X: 0.5, Y: 1}, {X: 0, Y: 1}},
	}}
	dets := []contract.Detection{
		{ModelID: modelID(1), BBox: [4]float64{1500, 100, 1600, 200}, ClassName: "m1-miss"},
		{ModelID: modelID(2), BBox: [4]float64{1500, 100, 1600, 200}, ClassName: "m2-bypass"},
	}
	delta, err := (RegionGate{}).Process(baseCtx(dets, regions))
	if err != nil {
		t.Fatal(err)
	}
	if delta.EnrichmentPatch["region_filter"] != "partial" || delta.RegionLabel != "全画面" {
		t.Fatalf("unexpected partial result: %#v", delta)
	}
	if delta.Detections == nil || len(*delta.Detections) != 1 || (*delta.Detections)[0].ClassName != "m2-bypass" {
		t.Fatalf("wrong kept detections: %#v", delta.Detections)
	}
}

func TestRegionGate_R14_LineAndInvalidRegionsDoNotEnterOrdinaryGate(t *testing.T) {
	regions := []config.Region{
		{ID: 1, RegionName: "线", RegionType: "line", IsEnabled: true,
			Points: []config.Point{{X: 0, Y: 0.5}, {X: 1, Y: 0.5}}},
		{ID: 2, RegionName: "坏多边形", RegionType: "polygon", IsEnabled: true,
			Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}}},
		{ID: 3, RegionName: "禁用", RegionType: "polygon", IsEnabled: false,
			Points: []config.Point{{X: 0, Y: 0}, {X: 1, Y: 0}, {X: 1, Y: 1}}},
	}
	delta, _ := (RegionGate{}).Process(baseCtx(
		[]contract.Detection{{ModelID: modelID(1), BBox: [4]float64{100, 100, 200, 200}}}, regions,
	))
	if delta.EnrichmentPatch["region_filter"] != "bypass" || delta.RegionLabel != "全画面" {
		t.Fatalf("ordinary gate should bypass line/invalid regions: %#v", delta)
	}
}

func TestRegionGate_R15_HitModesAndLegacyAliases(t *testing.T) {
	bbox := [4]float64{100, 100, 300, 300}
	if got := samplePoints(bbox, "bottom_center"); len(got) != 1 || got[0] != [2]float64{200, 300} {
		t.Fatalf("bottom_center=%#v", got)
	}
	if got := samplePoints(bbox, "bottom"); len(got) != 1 || got[0] != [2]float64{200, 300} {
		t.Fatalf("legacy bottom=%#v", got)
	}
	for _, mode := range []string{"any_corner", "any"} {
		if got := samplePoints(bbox, mode); len(got) != 5 {
			t.Fatalf("%s points=%#v", mode, got)
		}
	}
}

func TestRegionGate_R16_NewHitModes(t *testing.T) {
	region := config.Region{
		ID: 1, RegionName: "左侧", RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 140, Y: 0}, {X: 140, Y: 400}, {X: 0, Y: 400}},
	}
	det := contract.Detection{ModelID: modelID(1), BBox: [4]float64{100, 100, 200, 200}}
	for _, tc := range []struct {
		name      string
		mode      string
		threshold float64
		want      bool
	}{
		{name: "center outside", mode: "center", threshold: 0.5, want: false},
		{name: "any intersection", mode: "any_intersection", threshold: 0.5, want: true},
		{name: "40 percent reaches threshold", mode: "overlap_ratio", threshold: 0.4, want: true},
		{name: "40 percent misses higher threshold", mode: "overlap_ratio", threshold: 0.41, want: false},
		{name: "not fully inside", mode: "fully_inside", threshold: 0.5, want: false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			got := detectionMatchesRegion(det, region, 1920, 1080, tc.mode, tc.threshold)
			if got != tc.want {
				t.Fatalf("mode=%s threshold=%v got=%v want=%v", tc.mode, tc.threshold, got, tc.want)
			}
		})
	}
}

func TestRegionGate_R17_BottomCenterAndFullyInside(t *testing.T) {
	det := contract.Detection{BBox: [4]float64{100, 100, 300, 300}}
	bottomStrip := config.Region{
		RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 250}, {X: 400, Y: 250}, {X: 400, Y: 400}, {X: 0, Y: 400}},
	}
	if detectionMatchesRegion(det, bottomStrip, 1920, 1080, "center", 0.5) {
		t.Fatal("center must remain outside the bottom strip")
	}
	if !detectionMatchesRegion(det, bottomStrip, 1920, 1080, "bottom_center", 0.5) {
		t.Fatal("bottom center must hit the bottom strip")
	}
	outer := config.Region{
		RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 400, Y: 0}, {X: 400, Y: 400}, {X: 0, Y: 400}},
	}
	if !detectionMatchesRegion(det, outer, 1920, 1080, "fully_inside", 0.5) {
		t.Fatal("bbox is fully inside the region")
	}
}

func TestRegionGate_R18_ConcavePolygonOverlapRatio(t *testing.T) {
	// L shape. The bbox has 75% of its area inside the region.
	region := config.Region{
		RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{
			{X: 0, Y: 0}, {X: 200, Y: 0}, {X: 200, Y: 100},
			{X: 100, Y: 100}, {X: 100, Y: 200}, {X: 0, Y: 200},
		},
	}
	det := contract.Detection{BBox: [4]float64{50, 50, 150, 150}}
	if !detectionMatchesRegion(det, region, 1920, 1080, "overlap_ratio", 0.75) {
		t.Fatal("concave overlap must reach 75 percent")
	}
	if detectionMatchesRegion(det, region, 1920, 1080, "overlap_ratio", 0.751) {
		t.Fatal("concave overlap must remain below 75.1 percent")
	}
}

func TestRegionGate_R19_AnyIntersectionIncludesBoundaryTouch(t *testing.T) {
	region := config.Region{
		RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{{X: 0, Y: 0}, {X: 100, Y: 0}, {X: 100, Y: 100}, {X: 0, Y: 100}},
	}
	det := contract.Detection{BBox: [4]float64{100, 20, 200, 80}}
	if !detectionMatchesRegion(det, region, 1920, 1080, "any_intersection", 0.5) {
		t.Fatal("shared boundary must count as any intersection")
	}
	if detectionMatchesRegion(det, region, 1920, 1080, "overlap_ratio", 0.01) {
		t.Fatal("boundary-only contact must have zero overlap area")
	}
}

func TestRegionGate_R20_FullyInsideRejectsConcaveNotch(t *testing.T) {
	// All four bbox corners are inside this U-shaped polygon, but its middle crosses the notch.
	region := config.Region{
		RegionType: "polygon", IsEnabled: true,
		Points: []config.Point{
			{X: 0, Y: 0}, {X: 300, Y: 0}, {X: 300, Y: 300}, {X: 200, Y: 300},
			{X: 200, Y: 100}, {X: 100, Y: 100}, {X: 100, Y: 300}, {X: 0, Y: 300},
		},
	}
	det := contract.Detection{BBox: [4]float64{50, 50, 250, 250}}
	if detectionMatchesRegion(det, region, 1920, 1080, "fully_inside", 0.5) {
		t.Fatal("bbox crossing a concave notch is not fully inside")
	}
}

func TestRegionGate_R21_UsesIndependentRegionRulesWithORSemantics(t *testing.T) {
	ratio := 0.4
	regions := []config.Region{
		{
			ID: 1, RegionName: "中心点严格区", RegionType: "polygon", IsEnabled: true,
			HitMode: "center",
			Points:  []config.Point{{X: 0, Y: 0}, {X: 140, Y: 0}, {X: 140, Y: 400}, {X: 0, Y: 400}},
		},
		{
			ID: 2, RegionName: "面积比例区", RegionType: "polygon", IsEnabled: true,
			HitMode: "overlap_ratio", MinOverlapRatio: &ratio,
			Points: []config.Point{{X: 0, Y: 0}, {X: 140, Y: 0}, {X: 140, Y: 400}, {X: 0, Y: 400}},
		},
	}
	det := contract.Detection{ModelID: modelID(1), BBox: [4]float64{100, 100, 200, 200}}
	hits := regionsContaining(det, regions, 1920, 1080, "fully_inside", 0.9)
	if len(hits) != 1 || hits[0].ID != 2 {
		t.Fatalf("per-region OR match got %#v", hits)
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
