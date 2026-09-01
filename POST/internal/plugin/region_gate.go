package plugin

import (
	"math"
	"sort"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/metrics"
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
	minOverlapRatio := paramFloat(ctx.PluginParams, "min_overlap_ratio", 0.5)

	fw := ctx.Event.FrameWidth
	fh := ctx.Event.FrameHeight
	if len(activePolygonRegions(ctx)) == 0 {
		metrics.RegionDetection.WithLabelValues("pass", "bypass").Inc()
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
	primaryID := int64(math.MaxInt64)
	appliedCount := 0
	bypassCount := 0

	for _, det := range ctx.Detections {
		active := activePolygonRegionsForDetection(ctx, det.ModelID)
		if len(active) == 0 {
			bypassCount++
			kept = append(kept, det)
			continue
		}
		appliedCount++
		hitRegions := regionsContaining(det, active, fw, fh, hitMode, minOverlapRatio)
		if len(hitRegions) == 0 {
			continue
		}
		det.MatchedRegionIDs = nil
		det.MatchedRegionNames = nil
		for _, hr := range hitRegions {
			det.MatchedRegionIDs = appendUniqueID(det.MatchedRegionIDs, hr.ID)
			det.MatchedRegionNames = appendUniqueStr(det.MatchedRegionNames, hr.RegionName)
			matchedNames[hr.RegionName] = struct{}{}
			matchedIDs = appendUniqueID(matchedIDs, hr.ID)
			if hr.SortOrder < primaryOrder || (hr.SortOrder == primaryOrder && hr.ID < primaryID) {
				primaryOrder = hr.SortOrder
				primaryID = hr.ID
				primaryName = hr.RegionName
			}
		}
		sort.Strings(det.MatchedRegionNames)
		kept = append(kept, det)
	}

	names := make([]string, 0, len(matchedNames))
	for n := range matchedNames {
		names = append(names, n)
	}
	sort.Strings(names)
	sort.Slice(matchedIDs, func(i, j int) bool { return matchedIDs[i] < matchedIDs[j] })

	filterState := "applied"
	if appliedCount == 0 {
		filterState = "bypass"
		primaryName = "全画面"
	} else if bypassCount > 0 {
		filterState = "partial"
		if primaryName == "" {
			primaryName = "全画面"
		}
	}

	if len(kept) == 0 {
		metrics.RegionDetection.WithLabelValues("drop", filterState).Inc()
		drop := pipeline.DecisionDrop
		return pipeline.PluginDelta{
			Detections: &kept,
			Decision:   &drop,
			DropReason: "region_miss",
			EnrichmentPatch: map[string]any{
				"region_filter":      filterState,
				"matched_regions":    names,
				"matched_region_ids": matchedIDs,
			},
		}, nil
	}

	metrics.RegionDetection.WithLabelValues("pass", filterState).Inc()
	return pipeline.PluginDelta{
		Detections:  &kept,
		RegionLabel: primaryName,
		EnrichmentPatch: map[string]any{
			"region_filter":      filterState,
			"matched_regions":    names,
			"matched_region_ids": matchedIDs,
		},
	}, nil
}

func regionsContaining(
	det contract.Detection,
	regions []config.Region,
	fw, fh int,
	hitMode string,
	minOverlapRatio float64,
) []config.Region {
	var hits []config.Region
	for _, r := range regions {
		regionHitMode := r.HitMode
		if regionHitMode == "" {
			regionHitMode = hitMode
		}
		regionMinOverlapRatio := minOverlapRatio
		if r.MinOverlapRatio != nil {
			regionMinOverlapRatio = *r.MinOverlapRatio
		}
		if detectionMatchesRegion(
			det, r, fw, fh, regionHitMode, regionMinOverlapRatio,
		) {
			hits = append(hits, r)
		}
	}
	return hits
}
