package config

import "encoding/json"

// PipelineStep is one plugin step in a task pipeline.
type PipelineStep struct {
	Plugin       string         `json:"plugin"`
	Version      string         `json:"version,omitempty"`
	Enabled      *bool          `json:"enabled,omitempty"`
	Params       map[string]any `json:"params,omitempty"`
	FailStrategy string         `json:"fail_strategy,omitempty"`
	Endpoint     string         `json:"endpoint,omitempty"`
}

// IsEnabled returns whether the step should run (default true).
func (s PipelineStep) IsEnabled() bool {
	if s.Enabled == nil {
		return true
	}
	return *s.Enabled
}

// TaskConfig is the task subset of a template snapshot.
type TaskConfig struct {
	ID                int64          `json:"id"`
	TaskName          string         `json:"task_name"`
	TaskType          string         `json:"task_type"`
	AlertEvent        string         `json:"alert_event,omitempty"`
	ModelIDs          []int64        `json:"model_ids,omitempty"`
	Pipeline          []PipelineStep `json:"pipeline,omitempty"`
	PostProcessScript string         `json:"post_process_script,omitempty"`
}

// Region is a detection region snapshot.
type Region struct {
	ID         int64   `json:"id"`
	DeviceID   string  `json:"device_id"`
	RegionName string  `json:"region_name"`
	RegionType string  `json:"region_type"`
	Points     []Point `json:"points"`
	IsEnabled  bool    `json:"is_enabled"`
	SortOrder  int     `json:"sort_order"`
	ModelIDs   []int64 `json:"model_ids,omitempty"`
}

// Point supports {x,y} and [x,y] JSON forms.
type Point struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

func (p *Point) UnmarshalJSON(data []byte) error {
	var obj map[string]any
	if err := json.Unmarshal(data, &obj); err == nil {
		if _, ok := obj["x"]; ok {
			p.X = asFloat(obj["x"])
			p.Y = asFloat(obj["y"])
			return nil
		}
	}
	var arr []float64
	if err := json.Unmarshal(data, &arr); err != nil {
		return err
	}
	if len(arr) >= 2 {
		p.X, p.Y = arr[0], arr[1]
	}
	return nil
}

func asFloat(v any) float64 {
	switch t := v.(type) {
	case float64:
		return t
	case int:
		return float64(t)
	case json.Number:
		f, _ := t.Float64()
		return f
	default:
		return 0
	}
}

// TaskTemplate is the full cache entry body.
type TaskTemplate struct {
	Schema  string     `json:"schema"`
	Task    TaskConfig `json:"task"`
	Regions []Region   `json:"regions"`
}

// DefaultPipeline returns region_gate → default_pass.
func DefaultPipeline() []PipelineStep {
	en := true
	return []PipelineStep{
		{Plugin: "region_gate", Enabled: &en, Params: map[string]any{"hit_mode": "center"}},
		{Plugin: "default_pass", Enabled: &en, Params: map[string]any{}},
	}
}

// EffectivePipeline returns configured pipeline or default.
// v1.9 §4.1.1: nil/omitted → default region_gate→default_pass;
// explicit [] or all disabled → pass-through (default_pass only).
func (t TaskConfig) EffectivePipeline() []PipelineStep {
	if t.Pipeline == nil {
		return DefaultPipeline()
	}
	en := true
	passOnly := []PipelineStep{{Plugin: "default_pass", Enabled: &en, Params: map[string]any{}}}
	if len(t.Pipeline) == 0 {
		return passOnly
	}
	anyEnabled := false
	hasDecide := false
	for _, s := range t.Pipeline {
		if !s.IsEnabled() {
			continue
		}
		anyEnabled = true
		if s.Plugin == "default_pass" {
			hasDecide = true
		}
	}
	if !anyEnabled {
		return passOnly
	}
	out := append([]PipelineStep(nil), t.Pipeline...)
	if !hasDecide {
		out = append(out, PipelineStep{Plugin: "default_pass", Enabled: &en, Params: map[string]any{}})
	}
	return out
}

// RegionsByDevice indexes regions by device_id (enabled polygon/rectangle only filtered at gate).
func RegionsByDevice(regions []Region) map[string][]Region {
	out := make(map[string][]Region)
	for _, r := range regions {
		out[r.DeviceID] = append(out[r.DeviceID], r)
	}
	return out
}
