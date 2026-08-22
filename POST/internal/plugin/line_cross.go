package plugin

import (
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/pipeline"
)

// LineCross detects track crossing over configured line regions.
type LineCross struct{}

func (LineCross) Name() string { return "line_cross" }
func (LineCross) Kinds() []pipeline.PluginKind {
	return []pipeline.PluginKind{pipeline.KindFilter, pipeline.KindDecide}
}

func (LineCross) Process(ctx *pipeline.Context) (pipeline.PluginDelta, error) {
	lines := activeLineRegions(ctx)
	if len(lines) == 0 {
		return pipeline.PluginDelta{
			EnrichmentPatch: map[string]any{
				"line_cross": "bypass",
				"crossed":    []any{},
			},
		}, nil
	}

	direction := paramString(ctx.PluginParams, "direction", "both")
	samplePoint := paramString(ctx.PluginParams, "sample_point", "center")
	classes := paramStringSlice(ctx.PluginParams, "target_classes")

	fw := ctx.Event.FrameWidth
	fh := ctx.Event.FrameHeight
	now := parseEventTime(ctx.Event.Timestamp)

	var crossedEvents []map[string]any
	var kept []contract.Detection
	primaryRegion := ""

	for _, det := range ctx.Detections {
		if !classAllowed(det.ClassName, classes) {
			continue
		}
		if det.TrackID <= 0 {
			continue
		}
		pt := detectionPoint(det, samplePoint)
		key := trackStateKey(ctx.Event.TaskID, ctx.Event.DeviceID, det.TrackID)
		st := globalTrackState.touch(key, now)

		for _, line := range lines {
			scaled := scalePoints(line.Points, fw, fh)
			if len(scaled) < 2 {
				continue
			}
			p0, p1 := scaled[0], scaled[1]
			curr := lineSide(pt[0], pt[1], p0[0], p0[1], p1[0], p1[1])
			prev := st.lineSide[line.ID]
			st.lineSide[line.ID] = curr

			if crossedSide(prev, curr, direction) {
				crossedEvents = append(crossedEvents, map[string]any{
					"track_id":    det.TrackID,
					"region_id":   line.ID,
					"region_name": line.RegionName,
					"direction":   direction,
					"class_name":  det.ClassName,
				})
				kept = appendUniqueDetection(kept, det)
				if primaryRegion == "" {
					primaryRegion = line.RegionName
				}
			}
		}
	}

	if len(crossedEvents) == 0 {
		empty := []contract.Detection{}
		drop := pipeline.DecisionDrop
		return pipeline.PluginDelta{
			Detections: &empty,
			Decision:   &drop,
			DropReason: "no_line_cross",
			EnrichmentPatch: map[string]any{
				"line_cross": "applied",
				"crossed":    crossedEvents,
			},
		}, nil
	}

	delta := pipeline.PluginDelta{
		Detections: &kept,
		EnrichmentPatch: map[string]any{
			"line_cross": "applied",
			"crossed":    crossedEvents,
		},
	}
	if primaryRegion != "" {
		delta.RegionLabel = primaryRegion
	}
	return delta, nil
}

func appendUniqueDetection(dets []contract.Detection, det contract.Detection) []contract.Detection {
	for _, d := range dets {
		if d.TrackID > 0 && d.TrackID == det.TrackID {
			return dets
		}
		if d.TrackID == 0 && d.ClassName == det.ClassName && d.BBox == det.BBox {
			return dets
		}
	}
	return append(dets, det)
}
