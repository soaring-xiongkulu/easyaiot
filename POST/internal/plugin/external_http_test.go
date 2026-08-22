package plugin

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/pipeline"
)

func sampleEvent() contract.InferEvent {
	return contract.InferEvent{
		Schema:        contract.SchemaInferEvent,
		EventKind:     "infer",
		CorrelationID: "c1",
		TaskID:        1,
		TaskType:      "realtime",
		DeviceID:      "cam1",
		Timestamp:     "2026-01-01T00:00:00Z",
		FrameWidth:    1920,
		FrameHeight:   1080,
		Detections: []contract.Detection{
			{BBox: [4]float64{0.1, 0.1, 0.2, 0.2}, ClassName: "person", Confidence: 0.9},
		},
	}
}

func TestExternalHTTP_Enrich(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/process" {
			http.NotFound(w, r)
			return
		}
		_ = json.NewEncoder(w).Encode(map[string]any{
			"schema":           SchemaPluginDelta,
			"enrichment_patch": map[string]any{"echo": true},
			"decision":         nil,
		})
	}))
	defer srv.Close()

	ext := NewExternalFromStep("acme.echo", srv.URL, "1.0.0", time.Second)
	ctx := &pipeline.Context{
		Event: sampleEvent(), Task: config.TaskConfig{ID: 1},
		Detections: append([]contract.Detection{}, sampleEvent().Detections...),
		Enrichment: map[string]any{}, Decision: pipeline.DecisionContinue,
		PluginParams: map[string]any{"k": 1},
	}
	delta, err := ext.Process(ctx)
	if err != nil {
		t.Fatal(err)
	}
	if delta.EnrichmentPatch["echo"] != true {
		t.Fatalf("patch=%v", delta.EnrichmentPatch)
	}
}

func TestPipeline_ExternalFailOpenClosed(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Error(w, "boom", http.StatusInternalServerError)
	}))
	defer srv.Close()

	reg := Builtin()
	resolve := func(step config.PipelineStep) pipeline.Plugin {
		return Resolve(reg, step, time.Second)
	}
	en := true
	ev := sampleEvent()
	taskOpen := config.TaskConfig{
		ID: 1, TaskType: "realtime",
		Pipeline: []config.PipelineStep{
			{Plugin: "acme.bad", Enabled: &en, Endpoint: srv.URL, FailStrategy: "fail_open"},
			{Plugin: "default_pass", Enabled: &en},
		},
	}
	res := pipeline.RunWith(pipeline.Options{Resolve: resolve, Debug: true}, ev, taskOpen, nil)
	if res.Decision != pipeline.DecisionPass {
		t.Fatalf("fail_open want pass got %s/%s", res.Decision, res.DropReason)
	}

	taskClosed := config.TaskConfig{
		ID: 1, TaskType: "realtime",
		Pipeline: []config.PipelineStep{
			{Plugin: "acme.bad", Enabled: &en, Endpoint: srv.URL, FailStrategy: "fail_closed"},
			{Plugin: "default_pass", Enabled: &en},
		},
	}
	res2 := pipeline.RunWith(pipeline.Options{Resolve: resolve, Debug: true}, ev, taskClosed, nil)
	if res2.Decision != pipeline.DecisionDrop || res2.DropReason != "plugin_error" {
		t.Fatalf("fail_closed want drop/plugin_error got %s/%s", res2.Decision, res2.DropReason)
	}
}

func TestPipeline_ExternalEndpointEnrich(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_ = json.NewEncoder(w).Encode(map[string]any{
			"schema":           SchemaPluginDelta,
			"enrichment_patch": map[string]any{"n": 42},
		})
	}))
	defer srv.Close()

	reg := Builtin()
	resolve := func(step config.PipelineStep) pipeline.Plugin {
		return Resolve(reg, step, time.Second)
	}
	en := true
	ev := sampleEvent()
	task := config.TaskConfig{
		ID: 1, TaskType: "realtime",
		Pipeline: []config.PipelineStep{
			{Plugin: "acme.echo", Enabled: &en, Endpoint: srv.URL},
			{Plugin: "default_pass", Enabled: &en},
		},
	}
	res := pipeline.RunWith(pipeline.Options{Resolve: resolve, Debug: true}, ev, task, nil)
	if res.Decision != pipeline.DecisionPass {
		t.Fatalf("got %s/%s", res.Decision, res.DropReason)
	}
	if res.Context.Enrichment["acme.echo"] == nil {
		t.Fatalf("missing enrichment: %v", res.Context.Enrichment)
	}
}
