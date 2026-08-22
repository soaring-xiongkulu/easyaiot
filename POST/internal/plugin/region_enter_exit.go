package plugin

import (
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/pipeline"
)

// RegionEnterExit fires when a tracked target enters or exits a polygon region.
type RegionEnterExit struct{}

func (RegionEnterExit) Name() string { return "region_enter_exit" }
func (RegionEnterExit) Kinds() []pipeline.PluginKind {
	return []pipeline.PluginKind{pipeline.KindFilter, pipeline.KindDecide}
}

func (RegionEnterExit) Process(ctx *pipeline.Context) (pipeline.PluginDelta, error) {
	regions := activePolygonRegions(ctx)
	if len(regions) == 0 {
		return pipeline.PluginDelta{
			EnrichmentPatch: map[string]any{
				"region_enter_exit": "bypass",
				"events":            []any{},
			},
		}, nil
	}

	eventType := paramString(ctx.PluginParams, "event_type", "both")
	hitMode := paramString(ctx.PluginParams, "hit_mode", "center")
	classes := paramStringSlice(ctx.PluginParams, "target_classes")

	fw := ctx.Event.FrameWidth
	fh := ctx.Event.FrameHeight
	now := parseEventTime(ctx.Event.Timestamp)

	var events []map[string]any
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
			prev, known := st.inRegion[region.ID]
			st.inRegion[region.ID] = inside

			var ev string
			switch {
			case inside && (!known || !prev):
				ev = "enter"
			case !inside && known && prev:
				ev = "exit"
			}
			if ev == "" {
				continue
			}
			if eventType != "both" && eventType != ev {
				continue
			}
			events = append(events, map[string]any{
				"event":       ev,
				"track_id":    det.TrackID,
				"region_id":   region.ID,
				"region_name": region.RegionName,
				"class_name":  det.ClassName,
			})
			kept = appendUniqueDetection(kept, det)
			if primaryRegion == "" {
				primaryRegion = region.RegionName
			}
		}
	}

	if len(events) == 0 {
		empty := []contract.Detection{}
		drop := pipeline.DecisionDrop
		return pipeline.PluginDelta{
			Detections: &empty,
			Decision:   &drop,
			DropReason: "no_region_transition",
			EnrichmentPatch: map[string]any{
				"region_enter_exit": "applied",
				"events":            events,
			},
		}, nil
	}

	delta := pipeline.PluginDelta{
		Detections: &kept,
		EnrichmentPatch: map[string]any{
			"region_enter_exit": "applied",
			"events":            events,
		},
	}
	if primaryRegion != "" {
		delta.RegionLabel = primaryRegion
	}
	return delta, nil
}
