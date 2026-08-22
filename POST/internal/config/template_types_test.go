package config

import "testing"

func TestEffectivePipelineNilUsesDefault(t *testing.T) {
	var tc TaskConfig
	steps := tc.EffectivePipeline()
	if len(steps) != 2 || steps[0].Plugin != "region_gate" || steps[1].Plugin != "default_pass" {
		t.Fatalf("nil pipeline want default region_gate→default_pass, got %#v", steps)
	}
}

func TestEffectivePipelineEmptyIsPassThrough(t *testing.T) {
	tc := TaskConfig{Pipeline: []PipelineStep{}}
	steps := tc.EffectivePipeline()
	if len(steps) != 1 || steps[0].Plugin != "default_pass" {
		t.Fatalf("[] pipeline want default_pass only, got %#v", steps)
	}
}

func TestEffectivePipelineAllDisabledIsPassThrough(t *testing.T) {
	off := false
	tc := TaskConfig{Pipeline: []PipelineStep{
		{Plugin: "region_gate", Enabled: &off},
	}}
	steps := tc.EffectivePipeline()
	if len(steps) != 1 || steps[0].Plugin != "default_pass" {
		t.Fatalf("all-disabled want default_pass only, got %#v", steps)
	}
}

func TestEffectivePipelineImplicitDefaultPass(t *testing.T) {
	on := true
	tc := TaskConfig{Pipeline: []PipelineStep{
		{Plugin: "region_gate", Enabled: &on},
	}}
	steps := tc.EffectivePipeline()
	if len(steps) != 2 || steps[1].Plugin != "default_pass" {
		t.Fatalf("no decide want trailing default_pass, got %#v", steps)
	}
}
