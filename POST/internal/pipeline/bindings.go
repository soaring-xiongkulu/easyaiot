package pipeline

import (
	"crypto/sha256"
	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
	"encoding/json"
	"fmt"
)

// Bound business rules are independent subscriptions to specific geometry,
// rather than consecutive filters of the previous rule's detections.
func boundRegionIDs(step config.PipelineStep) []int64 {
	switch step.Plugin {
	case "line_cross", "region_enter_exit", "dwell_timer", "headcount_gate":
	default:
		return nil
	}
	var ids []int64
	switch values := step.Params["region_ids"].(type) {
	case []any:
		for _, v := range values {
			switch n := v.(type) {
			case float64:
				ids = append(ids, int64(n))
			case int:
				ids = append(ids, int64(n))
			case int64:
				ids = append(ids, n)
			}
		}
	case []int64:
		ids = values
	case []int:
		for _, n := range values {
			ids = append(ids, int64(n))
		}
	}
	return ids
}

func runBindings(opt Options, event contract.InferEvent, task config.TaskConfig, regions []config.Region) Result {
	var common []config.PipelineStep
	var matched []contract.Detection
	enrichment := map[string]any{}
	var rules []map[string]any
	var traces []StepTrace
	label := ""
	for _, step := range task.EffectivePipeline() {
		ids := boundRegionIDs(step)
		if len(ids) == 0 {
			if step.Plugin != "region_gate" {
				if step.Plugin == "default_pass" {
					params := map[string]any{}
					for k, v := range step.Params {
						if k != "monitoring_mode" {
							params[k] = v
						}
					}
					step.Params = params
				}
				common = append(common, step)
			}
			continue
		}
		if !step.IsEnabled() {
			continue
		}
		// One invocation per bound region keeps timers, cooldowns, and counters local.
		for _, id := range ids {
			var scope []config.Region
			for _, r := range regions {
				if r.ID == id && r.IsEnabled {
					scope = append(scope, r)
				}
			}
			if len(scope) == 0 {
				continue
			}
			params := map[string]any{}
			for k, v := range step.Params {
				if k != "region_ids" {
					params[k] = v
				}
			}
			params["binding_region_id"] = id
			// The geometry editor owns area membership; do not silently override
			// its visible controls with a hidden plugin default.
			if step.Plugin != "line_cross" && scope[0].HitMode != "" {
				params["hit_mode"] = scope[0].HitMode
			}
			if step.Plugin == "headcount_gate" {
				params["count_mode"] = "in_regions"
			}
			stateConfig, _ := json.Marshal(map[string]any{"points": scope[0].Points, "models": scope[0].ModelIDs, "mode": scope[0].HitMode, "ratio": scope[0].MinOverlapRatio, "params": params})
			params["binding_state_scope"] = fmt.Sprintf("%x", sha256.Sum256(stateConfig))
			branchStep := step
			branchStep.Params = params
			branchTask := task
			branchTask.Pipeline = []config.PipelineStep{branchStep, {Plugin: "default_pass"}}
			res := RunWith(opt, event, branchTask, scope)
			traces = append(traces, res.Trace...)
			if res.Decision != DecisionPass {
				continue
			}
			for _, det := range res.Context.Detections {
				exists := false
				for _, old := range matched {
					sameTarget := old.TrackID > 0 && det.TrackID > 0 && old.TrackID == det.TrackID
					if old.TrackID <= 0 && det.TrackID <= 0 { sameTarget = old.BBox == det.BBox && old.ClassName == det.ClassName }
					if sameTarget && sameDetectionModel(old, det) {
						exists = true
						break
					}
				}
				if !exists {
					matched = append(matched, det)
				}
			}
			patch, _ := res.Context.Enrichment[step.Plugin].(map[string]any)
			if patch != nil {
				patch["region_id"] = id
				rules = append(rules, map[string]any{"plugin": step.Plugin, "region_id": id, "result": patch})
				merged, _ := enrichment[step.Plugin].(map[string]any)
				if merged == nil {
					merged = map[string]any{}
				}
				for k, v := range patch {
					if events, ok := v.([]map[string]any); ok {
						prior, _ := merged[k].([]map[string]any)
						merged[k] = append(prior, events...)
					} else {
						merged[k] = v
					}
				}
				enrichment[step.Plugin] = merged
			}
			if label == "" {
				label = res.Context.RegionLabel
			}
		}
	}
	commonTask := task
	commonTask.Pipeline = common
	commonEvent := event
	commonEvent.Detections = matched
	res := RunWith(opt, commonEvent, commonTask, regions)
	for k, v := range enrichment {
		res.Context.Enrichment[k] = v
	}
	res.Context.Enrichment["business_rules"] = rules
	if label != "" {
		res.Context.RegionLabel = label
	}
	res.Trace = append(traces, res.Trace...)
	res.Context.Trace = res.Trace
	return res
}

func sameDetectionModel(a, b contract.Detection) bool {
	if a.ModelID == nil || b.ModelID == nil {
		return a.ModelID == nil && b.ModelID == nil
	}
	return *a.ModelID == *b.ModelID
}
