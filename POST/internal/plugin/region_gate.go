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
	hitMode := paramString(ctx.PluginParams, "hit_mode", "center")

	fw := ctx.Event.FrameWidth
	fh := ctx.Event.FrameHeight
	active := activePolygonRegions(ctx)

	if len(active) == 0 {
		return pipeline.PluginDelta{
			EnrichmentPatch: map[string]any{
				"region_filter":      "bypass",
				"matched_regions":    []string{},
				"matched_region_ids": []int64{},
			},
			RegionLabel: "全画面",
		}, nil
	}

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
