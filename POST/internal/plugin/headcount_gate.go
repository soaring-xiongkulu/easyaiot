package plugin

import (
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/pipeline"
)

// HeadcountGate passes only when detection count in regions meets threshold.
type HeadcountGate struct{}

func (HeadcountGate) Name() string { return "headcount_gate" }
func (HeadcountGate) Kinds() []pipeline.PluginKind {
	return []pipeline.PluginKind{pipeline.KindFilter, pipeline.KindDecide}
}

func (HeadcountGate) Process(ctx *pipeline.Context) (pipeline.PluginDelta, error) {
	hitMode := paramString(ctx.PluginParams, "hit_mode", "center")
	threshold := paramInt(ctx.PluginParams, "threshold", 1)
	operator := paramString(ctx.PluginParams, "operator", "gte")
	classes := paramStringSlice(ctx.PluginParams, "target_classes")
	countMode := paramString(ctx.PluginParams, "count_mode", "in_regions")

	fw := ctx.Event.FrameWidth
	fh := ctx.Event.FrameHeight
	regions := activePolygonRegions(ctx)

	var counted []contract.Detection
	if countMode == "all" || len(regions) == 0 {
		for _, det := range ctx.Detections {
			if classAllowed(det.ClassName, classes) {
				counted = append(counted, det)
			}
		}
	} else {
		seenTrack := map[string]struct{}{}
		for _, det := range ctx.Detections {
			if !classAllowed(det.ClassName, classes) {
				continue
			}
			if det.TrackID > 0 {
				key := trackStateKey(ctx.Event.TaskID, ctx.Event.DeviceID, det.ModelID, det.TrackID)
				if _, ok := seenTrack[key]; ok {
					continue
				}
			}
			for _, region := range activePolygonRegionsForDetection(ctx, det.ModelID) {
				if detectionInRegion(det, region, fw, fh, hitMode) {
					counted = append(counted, det)
					if det.TrackID > 0 {
						key := trackStateKey(ctx.Event.TaskID, ctx.Event.DeviceID, det.ModelID, det.TrackID)
						seenTrack[key] = struct{}{}
					}
					break
				}
			}
		}
	}

	count := len(counted)
	if !compareCount(count, threshold, operator) {
		empty := []contract.Detection{}
		drop := pipeline.DecisionDrop
		return pipeline.PluginDelta{
			Detections: &empty,
			Decision:   &drop,
			DropReason: "headcount_not_met",
			EnrichmentPatch: map[string]any{
				"headcount_gate": "applied",
				"count":          count,
				"threshold":      threshold,
				"operator":       operator,
			},
		}, nil
	}

	delta := pipeline.PluginDelta{
		Detections: &counted,
		EnrichmentPatch: map[string]any{
			"headcount_gate": "applied",
			"count":          count,
			"threshold":      threshold,
			"operator":       operator,
		},
	}
	if len(regions) > 0 {
		delta.RegionLabel = regions[0].RegionName
	}
	return delta, nil
}
