package plugin

import (
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/pipeline"
)

// DwellTimer alerts when a tracked target stays inside a region longer than min_dwell_sec.
type DwellTimer struct{}

func (DwellTimer) Name() string { return "dwell_timer" }
func (DwellTimer) Kinds() []pipeline.PluginKind {
	return []pipeline.PluginKind{pipeline.KindFilter, pipeline.KindDecide}
}

func (DwellTimer) Process(ctx *pipeline.Context) (pipeline.PluginDelta, error) {
	regions := activePolygonRegions(ctx)
	if len(regions) == 0 {
		return pipeline.PluginDelta{
			EnrichmentPatch: map[string]any{
				"dwell_timer": "bypass",
				"dwells":      []any{},
			},
		}, nil
	}

	minDwellSec := paramFloat(ctx.PluginParams, "min_dwell_sec", 5)
	hitMode := paramString(ctx.PluginParams, "hit_mode", "center")
	classes := paramStringSlice(ctx.PluginParams, "target_classes")

	fw := ctx.Event.FrameWidth
	fh := ctx.Event.FrameHeight
	now := parseEventTime(ctx.Event.Timestamp)
	minDwell := minDwellSec

	var dwells []map[string]any
	var kept []contract.Detection
	primaryRegion := ""

	for _, det := range ctx.Detections {
		if !classAllowed(det.ClassName, classes) {
			continue
		}
		if det.TrackID <= 0 {
			continue
		}
		key := trackStateKey(ctx.Event.TaskID, ctx.Event.DeviceID, det.TrackID)
		st := globalTrackState.touch(key, now)

		for _, region := range regions {
			inside := detectionInRegion(det, region, fw, fh, hitMode)
			prevInside := st.inRegion[region.ID]
			st.inRegion[region.ID] = inside

			if inside {
				if !prevInside {
					st.regionEnter[region.ID] = now
				}
				enterAt, ok := st.regionEnter[region.ID]
				if !ok {
					st.regionEnter[region.ID] = now
					enterAt = now
				}
				elapsed := now.Sub(enterAt).Seconds()
				if elapsed < minDwell {
					continue
				}
				dwells = append(dwells, map[string]any{
					"track_id":     det.TrackID,
					"region_id":    region.ID,
					"region_name":  region.RegionName,
					"class_name":   det.ClassName,
					"dwell_sec":    elapsed,
					"min_dwell_sec": minDwell,
				})
				kept = appendUniqueDetection(kept, det)
				if primaryRegion == "" {
					primaryRegion = region.RegionName
				}
			} else if prevInside {
				delete(st.regionEnter, region.ID)
			}
		}
	}

	if len(dwells) == 0 {
		empty := []contract.Detection{}
		drop := pipeline.DecisionDrop
		return pipeline.PluginDelta{
			Detections: &empty,
			Decision:   &drop,
			DropReason: "dwell_not_met",
			EnrichmentPatch: map[string]any{
				"dwell_timer": "applied",
				"dwells":      dwells,
			},
		}, nil
	}

	delta := pipeline.PluginDelta{
		Detections: &kept,
		EnrichmentPatch: map[string]any{
			"dwell_timer": "applied",
			"dwells":      dwells,
		},
	}
	if primaryRegion != "" {
		delta.RegionLabel = primaryRegion
	}
	return delta, nil
}
