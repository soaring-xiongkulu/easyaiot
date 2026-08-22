package plugin

import (
	"math"
	"sort"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/pipeline"
)

// RegionGate filters detections by device detection regions.
type RegionGate struct{}

func (RegionGate) Name() string { return "region_gate" }
func (RegionGate) Kinds() []pipeline.PluginKind {
	return []pipeline.PluginKind{pipeline.KindFilter}
}

func (RegionGate) Process(ctx *pipeline.Context) (pipeline.PluginDelta, error) {
	hitMode := "center"
	if ctx.PluginParams != nil {
		if v, ok := ctx.PluginParams["hit_mode"].(string); ok && v != "" {
			hitMode = v
		}
	}

	fw := ctx.Event.FrameWidth
	fh := ctx.Event.FrameHeight
	modelSet := unionModelIDs(ctx.Event.ModelIDs, ctx.Task.ModelIDs)

	var active []config.Region
	for _, r := range ctx.Regions {
		if !r.IsEnabled {
			continue
		}
		rt := r.RegionType
		if rt == "" {
			rt = "polygon"
		}
		if rt == "line" {
			continue
		}
		if rt != "polygon" && rt != "rectangle" {
			continue
		}
		if len(r.Points) < 3 {
			continue
		}
		if len(r.ModelIDs) > 0 && !intersects(r.ModelIDs, modelSet) {
			continue
		}
		active = append(active, r)
	}

	if len(active) == 0 {
		return pipeline.PluginDelta{
			EnrichmentPatch: map[string]any{
				"region_filter":    "bypass",
				"matched_regions":  []string{},
				"matched_region_ids": []int64{},
			},
			RegionLabel: "全画面",
		}, nil
	}

	sort.SliceStable(active, func(i, j int) bool {
		return active[i].SortOrder < active[j].SortOrder
	})

	var kept []contract.Detection
	matchedNames := map[string]struct{}{}
	var matchedIDs []int64
	primaryName := ""
	primaryOrder := math.MaxInt32

	for _, det := range ctx.Detections {
		hitRegions := regionsContaining(det, active, fw, fh, hitMode)
		if len(hitRegions) == 0 {
			continue
		}
		kept = append(kept, det)
		for _, hr := range hitRegions {
			matchedNames[hr.RegionName] = struct{}{}
			matchedIDs = appendUniqueID(matchedIDs, hr.ID)
			if hr.SortOrder < primaryOrder {
				primaryOrder = hr.SortOrder
				primaryName = hr.RegionName
			}
		}
	}

	names := make([]string, 0, len(matchedNames))
	for n := range matchedNames {
		names = append(names, n)
	}
	sort.Strings(names)

	if len(kept) == 0 {
		drop := pipeline.DecisionDrop
		return pipeline.PluginDelta{
			Detections: &kept,
			Decision:   &drop,
			DropReason: "region_miss",
			EnrichmentPatch: map[string]any{
				"region_filter":      "applied",
				"matched_regions":    names,
				"matched_region_ids": matchedIDs,
			},
		}, nil
	}

	return pipeline.PluginDelta{
		Detections:  &kept,
		RegionLabel: primaryName,
		EnrichmentPatch: map[string]any{
			"region_filter":      "applied",
			"matched_regions":    names,
			"matched_region_ids": matchedIDs,
		},
	}, nil
}

func regionsContaining(det contract.Detection, regions []config.Region, fw, fh int, hitMode string) []config.Region {
	var hits []config.Region
	points := samplePoints(det.BBox, hitMode)
	for _, r := range regions {
		poly := scalePoints(r.Points, fw, fh)
		for _, pt := range points {
			if pointInPolygon(pt[0], pt[1], poly) {
				hits = append(hits, r)
				break
			}
		}
	}
	return hits
}

func samplePoints(bbox [4]float64, hitMode string) [][2]float64 {
	x1, y1, x2, y2 := bbox[0], bbox[1], bbox[2], bbox[3]
	cx, cy := (x1+x2)/2, (y1+y2)/2
	if hitMode == "any_corner" {
		return [][2]float64{
			{x1, y1}, {x2, y1}, {x2, y2}, {x1, y2}, {cx, cy},
		}
	}
	return [][2]float64{{cx, cy}}
}

func scalePoints(pts []config.Point, fw, fh int) [][2]float64 {
	if len(pts) == 0 {
		return nil
	}
	normalized := true
	for _, p := range pts {
		if p.X < 0 || p.X > 1 || p.Y < 0 || p.Y > 1 {
			normalized = false
			break
		}
	}
	out := make([][2]float64, len(pts))
	for i, p := range pts {
		if normalized && fw > 0 && fh > 0 {
			out[i] = [2]float64{p.X * float64(fw), p.Y * float64(fh)}
		} else {
			out[i] = [2]float64{p.X, p.Y}
		}
	}
	return out
}

// pointInPolygon uses ray casting; boundary counts as inside.
func pointInPolygon(x, y float64, poly [][2]float64) bool {
	if len(poly) < 3 {
		return false
	}
	if onBoundary(x, y, poly) {
		return true
	}
	inside := false
	n := len(poly)
	j := n - 1
	for i := 0; i < n; i++ {
		xi, yi := poly[i][0], poly[i][1]
		xj, yj := poly[j][0], poly[j][1]
		if ((yi > y) != (yj > y)) && (x < (xj-xi)*(y-yi)/(yj-yi+1e-12)+xi) {
			inside = !inside
		}
		j = i
	}
	return inside
}

func onBoundary(x, y float64, poly [][2]float64) bool {
	const eps = 1e-6
	n := len(poly)
	j := n - 1
	for i := 0; i < n; i++ {
		if pointOnSegment(x, y, poly[j][0], poly[j][1], poly[i][0], poly[i][1], eps) {
			return true
		}
		j = i
	}
	return false
}

func pointOnSegment(px, py, x1, y1, x2, y2, eps float64) bool {
	cross := (px-x1)*(y2-y1) - (py-y1)*(x2-x1)
	if math.Abs(cross) > eps*math.Max(1, math.Hypot(x2-x1, y2-y1)) {
		return false
	}
	dot := (px-x1)*(x2-x1) + (py-y1)*(y2-y1)
	if dot < -eps {
		return false
	}
	len2 := (x2-x1)*(x2-x1) + (y2-y1)*(y2-y1)
	return dot <= len2+eps
}

func unionModelIDs(a, b []int64) map[int64]struct{} {
	out := map[int64]struct{}{}
	for _, id := range a {
		out[id] = struct{}{}
	}
	for _, id := range b {
		out[id] = struct{}{}
	}
	return out
}

func intersects(regionIDs []int64, set map[int64]struct{}) bool {
	if len(set) == 0 {
		// no model ids on event/task → treat as match-all for empty set semantics:
		// design: region model_ids non-empty must intersect Event∪Task model_ids.
		// if both event and task empty, no intersection → skip region.
		return false
	}
	for _, id := range regionIDs {
		if _, ok := set[id]; ok {
			return true
		}
	}
	return false
}

func appendUniqueID(ids []int64, id int64) []int64 {
	for _, x := range ids {
		if x == id {
			return ids
		}
	}
	return append(ids, id)
}
