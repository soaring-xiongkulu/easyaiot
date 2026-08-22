package plugin

import (
	"fmt"
	"strings"

	"easyaiot/post/internal/pipeline"
)

// DefaultPass finalizes a custom-post pass decision.
type DefaultPass struct{}

func (DefaultPass) Name() string { return "default_pass" }
func (DefaultPass) Kinds() []pipeline.PluginKind {
	return []pipeline.PluginKind{pipeline.KindDecide}
}

func (DefaultPass) Process(ctx *pipeline.Context) (pipeline.PluginDelta, error) {
	if ctx.Decision == pipeline.DecisionDrop {
		return pipeline.PluginDelta{}, nil
	}
	if len(ctx.Detections) == 0 {
		drop := pipeline.DecisionDrop
		return pipeline.PluginDelta{
			Decision:   &drop,
			DropReason: "empty_detections",
		}, nil
	}
	pass := pipeline.DecisionPass
	delta := pipeline.PluginDelta{Decision: &pass}

	if ctx.RegionLabel == "" {
		delta.RegionLabel = "全画面"
	}

	// Assemble display object/event into enrichment for maplegacy.
	objCounts := map[string]int{}
	for _, d := range ctx.Detections {
		name := d.ClassName
		if name == "" {
			name = "unknown"
		}
		objCounts[name]++
	}
	parts := make([]string, 0, len(objCounts))
	for k, v := range objCounts {
		if v > 1 {
			parts = append(parts, fmt.Sprintf("%s×%d", k, v))
		} else {
			parts = append(parts, k)
		}
	}
	object := strings.Join(parts, ",")
	event := ctx.Task.AlertEvent
	if event == "" {
		event = "检测告警"
	}
	delta.EnrichmentPatch = map[string]any{
		"object": object,
		"event":  event,
	}
	return delta, nil
}
