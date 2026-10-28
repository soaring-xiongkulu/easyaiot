package plugin

import (
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/pipeline"
	"fmt"
	"time"
)

// RegionEnterExit fires when a tracked target enters or exits a polygon region.
type RegionEnterExit struct{}

func (RegionEnterExit) Name() string { return "region_enter_exit" }
func (RegionEnterExit) Kinds() []pipeline.PluginKind {
	return []pipeline.PluginKind{pipeline.KindFilter, pipeline.KindDecide}
}

func (RegionEnterExit) Process(ctx *pipeline.Context) (pipeline.PluginDelta, error) {
	globalTrackState.processMu.Lock()
	defer globalTrackState.processMu.Unlock()
	if len(activePolygonRegions(ctx)) == 0 {
		drop := pipeline.DecisionDrop
		return pipeline.PluginDelta{
			Decision: &drop, DropReason: "missing_polygon_region",
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
		regions := activePolygonRegionsForDetection(ctx, det.ModelID)
		if len(regions) == 0 {
			continue
		}
		key := pluginTrackStateKey(ctx, det, "region_enter_exit")
		st := globalTrackState.touch(key, now)
		detCopy := det
		st.lastDet = &detCopy

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

	events, kept = appendSynthesizedExits(ctx, events, kept, now, eventType)

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

// appendSynthesizedExits closes enter-state of tracks that stopped being
// observed (tracker lost them or they left the frame mid-region). Without it a
// store visitor is counted on every re-detection and "exit" stays at zero.
func appendSynthesizedExits(ctx *pipeline.Context, events []map[string]any, kept []contract.Detection, now time.Time, eventType string) ([]map[string]any, []contract.Detection) {
	timeout := paramFloat(ctx.PluginParams, "exit_timeout_sec", 15)
	if timeout <= 0 {
		return events, kept
	}
	if eventType == "enter" {
		return events, kept
	}
	prefix := fmt.Sprintf("region_enter_exit:%v:%d:%s:", ctx.PluginParams["binding_state_scope"], ctx.Event.TaskID, ctx.Event.DeviceID)
	for _, ex := range globalTrackState.expireStaleEnter(prefix, time.Duration(timeout*float64(time.Second)), now) {
		for _, rid := range ex.Regions {
			className := ""
			if ex.LastDet != nil {
				className = ex.LastDet.ClassName
			}
			events = append(events, map[string]any{
				"event":       "exit",
				"track_id":    ex.TrackID,
				"region_id":   rid,
				"region_name": regionNameByID(ctx, rid),
				"class_name":  className,
				"synthesized": true,
			})
		}
		// The branch pipeline drops on empty detections; replay the last known
		// detection so the exit event survives the pass gate.
		if ex.LastDet != nil {
			kept = appendUniqueDetection(kept, *ex.LastDet)
		}
	}
	return events, kept
}

func regionNameByID(ctx *pipeline.Context, regionID int64) string {
	for _, r := range ctx.Regions {
		if r.ID == regionID {
			return r.RegionName
		}
	}
	return fmt.Sprintf("region-%d", regionID)
}
