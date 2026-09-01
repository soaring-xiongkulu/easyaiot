package config

import (
	"encoding/json"
	"fmt"
	"math"
	"strings"
)

const (
	RegionHitModeCenter          = "center"
	RegionHitModeBottomCenter    = "bottom_center"
	RegionHitModeAnyIntersection = "any_intersection"
	RegionHitModeOverlapRatio    = "overlap_ratio"
	RegionHitModeFullyInside     = "fully_inside"

	DefaultMinOverlapRatio = 0.5
	MinOverlapRatio        = 0.01
	MaxOverlapRatio        = 1.0
)

var supportedRegionHitModes = map[string]struct{}{
	RegionHitModeCenter:          {},
	RegionHitModeBottomCenter:    {},
	RegionHitModeAnyIntersection: {},
	RegionHitModeOverlapRatio:    {},
	RegionHitModeFullyInside:     {},
	"any_corner":                 {},
	"any":                        {},
	"all":                        {},
	"bottom":                     {},
}

// ValidateTaskTemplate performs defensive validation at every POST template ingress.
func ValidateTaskTemplate(tpl TaskTemplate) error {
	for index, step := range tpl.Task.Pipeline {
		if step.Plugin != "region_gate" {
			continue
		}
		mode := RegionHitModeCenter
		if raw, ok := step.Params["hit_mode"]; ok {
			value, ok := raw.(string)
			if !ok || strings.TrimSpace(value) == "" {
				return fmt.Errorf("pipeline[%d].region_gate.hit_mode must be a non-empty string", index)
			}
			mode = strings.TrimSpace(value)
		}
		if _, ok := supportedRegionHitModes[mode]; !ok {
			return fmt.Errorf("pipeline[%d].region_gate.hit_mode unsupported: %s", index, mode)
		}
		if raw, ok := step.Params["min_overlap_ratio"]; ok {
			ratio, ok := numericFloat(raw)
			if !ok || math.IsNaN(ratio) || math.IsInf(ratio, 0) {
				return fmt.Errorf("pipeline[%d].region_gate.min_overlap_ratio must be numeric", index)
			}
			if ratio < MinOverlapRatio || ratio > MaxOverlapRatio {
				return fmt.Errorf(
					"pipeline[%d].region_gate.min_overlap_ratio must be between %.2f and %.2f",
					index, MinOverlapRatio, MaxOverlapRatio,
				)
			}
		}
	}
	for index, region := range tpl.Regions {
		if region.HitMode != "" {
			mode := strings.TrimSpace(region.HitMode)
			if mode == "" {
				return fmt.Errorf("regions[%d].hit_mode must be a non-empty string", index)
			}
			if _, ok := supportedRegionHitModes[mode]; !ok {
				return fmt.Errorf("regions[%d].hit_mode unsupported: %s", index, mode)
			}
		}
		if region.MinOverlapRatio != nil {
			ratio := *region.MinOverlapRatio
			if math.IsNaN(ratio) || math.IsInf(ratio, 0) ||
				ratio < MinOverlapRatio || ratio > MaxOverlapRatio {
				return fmt.Errorf(
					"regions[%d].min_overlap_ratio must be between %.2f and %.2f",
					index, MinOverlapRatio, MaxOverlapRatio,
				)
			}
		}
	}
	return nil
}

func numericFloat(value any) (float64, bool) {
	switch typed := value.(type) {
	case float64:
		return typed, true
	case float32:
		return float64(typed), true
	case int:
		return float64(typed), true
	case int32:
		return float64(typed), true
	case int64:
		return float64(typed), true
	case json.Number:
		result, err := typed.Float64()
		return result, err == nil
	default:
		return 0, false
	}
}
