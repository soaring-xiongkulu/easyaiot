package debug

import (
	"encoding/json"
	"net/http"
	"strings"
	"time"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/engine"
	"easyaiot/post/internal/maplegacy"
	"easyaiot/post/internal/pipeline"
	"easyaiot/post/internal/plugin"
	"easyaiot/post/internal/template"
)

// Handler serves /debug/* endpoints.
type Handler struct {
	Engine *engine.Engine
	Cache  *template.Cache
}

type pipelineReq struct {
	Event            contract.InferEvent   `json:"event"`
	PipelineOverride []config.PipelineStep `json:"pipeline_override"`
	UntilPlugin      string                `json:"until_plugin"`
	Task             *config.TaskConfig    `json:"task"`
	Regions          []config.Region       `json:"regions"`
}

func (h *Handler) Register(mux *http.ServeMux) {
	mux.HandleFunc("/debug/pipeline", h.pipeline)
	mux.HandleFunc("/debug/plugin", h.plugin)
}

func (h *Handler) resolver() pipeline.Resolver {
	reg := plugin.Builtin()
	timeout := time.Duration(0)
	if h.Engine != nil {
		if h.Engine.Resolve != nil {
			return h.Engine.Resolve
		}
		if h.Engine.Registry != nil {
			reg = h.Engine.Registry
		}
		timeout = h.Engine.Cfg.PluginHTTPTimeout
	}
	return func(step config.PipelineStep) pipeline.Plugin {
		return plugin.Resolve(reg, step, timeout)
	}
}

func (h *Handler) pipeline(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req pipelineReq
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	_ = req.Event.Validate()

	task := config.TaskConfig{ID: req.Event.TaskID, TaskType: req.Event.TaskType, TaskName: req.Event.TaskName}
	regions := req.Regions
	if req.Task != nil {
		task = *req.Task
	} else if entry, ok := h.Cache.Get(req.Event.TaskID); ok {
		task = entry.Template.Task
		if regions == nil {
			regions = entry.ByDevice[req.Event.DeviceID]
		}
	}
	if len(req.PipelineOverride) > 0 {
		task.Pipeline = req.PipelineOverride
	}
	if req.UntilPlugin != "" {
		var steps []config.PipelineStep
		for _, s := range task.EffectivePipeline() {
			steps = append(steps, s)
			if s.Plugin == req.UntilPlugin {
				break
			}
		}
		task.Pipeline = steps
	}

	res := pipeline.RunWith(pipeline.Options{
		Registry: h.Engine.Registry,
		Resolve:  h.resolver(),
		Debug:    true,
	}, req.Event, task, regions)
	out := map[string]any{
		"result":      string(res.Decision),
		"drop_reason": res.DropReason,
		"trace":       res.Trace,
	}
	if res.Decision == pipeline.DecisionPass && res.Context != nil {
		out["alert_payload"] = maplegacy.ToAlertNotification(res.Context)
	} else {
		out["alert_payload"] = nil
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(out)
}

type pluginReq struct {
	Plugin   string              `json:"plugin"`
	Endpoint string              `json:"endpoint"`
	Event    contract.InferEvent `json:"event"`
	Params   map[string]any      `json:"params"`
	Task     *config.TaskConfig  `json:"task"`
	Regions  []config.Region     `json:"regions"`
}

func (h *Handler) plugin(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req pluginReq
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	step := config.PipelineStep{Plugin: req.Plugin, Endpoint: req.Endpoint, Params: req.Params}
	p := h.resolver()(step)
	if p == nil {
		http.Error(w, "unknown plugin", http.StatusBadRequest)
		return
	}
	_ = req.Event.Validate()
	task := config.TaskConfig{}
	if req.Task != nil {
		task = *req.Task
	}
	dets := make([]contract.Detection, len(req.Event.Detections))
	copy(dets, req.Event.Detections)
	params := req.Params
	if params == nil {
		params = map[string]any{}
	}
	ctx := &pipeline.Context{
		Event: req.Event, Task: task, Regions: req.Regions,
		Detections: dets, Enrichment: map[string]any{},
		Decision: pipeline.DecisionContinue, PluginParams: params,
	}
	delta, err := p.Process(ctx)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if delta.Detections != nil {
		ctx.Detections = *delta.Detections
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]any{
		"delta":      delta,
		"detections": ctx.Detections,
		"region":     delta.RegionLabel,
		"plugin":     strings.TrimSpace(req.Plugin),
	})
}
