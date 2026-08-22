package pipeline

import (
	"log/slog"
	"strings"
	"time"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/metrics"
)

type Decision string

const (
	DecisionContinue Decision = "continue"
	DecisionDrop     Decision = "drop"
	DecisionPass     Decision = "pass"
)

type PluginKind string

const (
	KindFilter PluginKind = "filter"
	KindEnrich PluginKind = "enrich"
	KindRender PluginKind = "render"
	KindDecide PluginKind = "decide"
)

// Plugin is a custom post-process step.
type Plugin interface {
	Name() string
	Kinds() []PluginKind
	Process(ctx *Context) (PluginDelta, error)
}

// Resolver maps a pipeline step to a Plugin implementation.
// If nil, Run looks up Registry by step.Plugin only.
type Resolver func(step config.PipelineStep) Plugin

// Context is the mutable pipeline state.
type Context struct {
	Event        contract.InferEvent
	Task         config.TaskConfig
	Regions      []config.Region
	Detections   []contract.Detection
	Enrichment   map[string]any
	Layers       []contract.DrawLayer
	Decision     Decision
	DropReason   string
	PluginParams map[string]any
	Trace        []StepTrace
	RegionLabel  string
	Debug        bool
}

// PluginDelta is the mutation returned by a plugin.
type PluginDelta struct {
	Detections      *[]contract.Detection
	EnrichmentPatch map[string]any
	LayersAppend    []contract.DrawLayer
	Decision        *Decision
	DropReason      string
	SkipRest        bool
	RegionLabel     string
}

// StepTrace records one plugin invocation for debug.
type StepTrace struct {
	Plugin          string         `json:"plugin"`
	DetectionsIn    int            `json:"detections_in"`
	DetectionsOut   int            `json:"detections_out"`
	Decision        string         `json:"decision"`
	DropReason      string         `json:"drop_reason,omitempty"`
	EnrichmentPatch map[string]any `json:"enrichment_patch,omitempty"`
	LatencyMs       float64        `json:"latency_ms"`
}

// Registry maps plugin id → implementation.
type Registry map[string]Plugin

// Result is the pipeline outcome.
type Result struct {
	Decision   Decision
	DropReason string
	Context    *Context
	Trace      []StepTrace
}

// Options configures a pipeline run.
type Options struct {
	Debug    bool
	Resolve  Resolver
	Registry Registry
}

// Run executes the task pipeline (compat: registry-only resolve).
func Run(reg Registry, event contract.InferEvent, task config.TaskConfig, regions []config.Region, debug bool) Result {
	return RunWith(Options{Registry: reg, Debug: debug}, event, task, regions)
}

// RunWith executes with optional external resolver (endpoint-aware).
func RunWith(opt Options, event contract.InferEvent, task config.TaskConfig, regions []config.Region) Result {
	dets := make([]contract.Detection, len(event.Detections))
	copy(dets, event.Detections)

	ctx := &Context{
		Event:      event,
		Task:       task,
		Regions:    regions,
		Detections: dets,
		Enrichment: map[string]any{},
		Decision:   DecisionContinue,
		Debug:      opt.Debug,
	}

	for _, step := range task.EffectivePipeline() {
		if !step.IsEnabled() {
			continue
		}
		var p Plugin
		if opt.Resolve != nil {
			p = opt.Resolve(step)
		} else if opt.Registry != nil {
			p = opt.Registry[step.Plugin]
		}
		if p == nil {
			slog.Warn("unknown_plugin", "plugin", step.Plugin, "task_id", task.ID)
			continue
		}
		ctx.PluginParams = step.Params
		if ctx.PluginParams == nil {
			ctx.PluginParams = map[string]any{}
		}
		in := len(ctx.Detections)
		t0 := time.Now()
		delta, err := p.Process(ctx)
		lat := float64(time.Since(t0).Microseconds()) / 1000.0
		metrics.PluginLatency.WithLabelValues(step.Plugin).Observe(lat)
		if err != nil {
			strategy := strings.ToLower(strings.TrimSpace(step.FailStrategy))
			if strategy == "" {
				strategy = "fail_open"
			}
			slog.Error("plugin_error", "plugin", step.Plugin, "err", err, "task_id", task.ID, "fail_strategy", strategy)
			if strategy == "fail_closed" {
				ctx.Decision = DecisionDrop
				ctx.DropReason = "plugin_error"
				if opt.Debug {
					ctx.Trace = append(ctx.Trace, StepTrace{
						Plugin: step.Plugin, DetectionsIn: in, DetectionsOut: len(ctx.Detections),
						Decision: string(ctx.Decision), DropReason: ctx.DropReason, LatencyMs: lat,
					})
				}
				break
			}
			// fail_open: skip step, continue pipeline
			if opt.Debug {
				ctx.Trace = append(ctx.Trace, StepTrace{
					Plugin: step.Plugin, DetectionsIn: in, DetectionsOut: len(ctx.Detections),
					Decision: string(ctx.Decision), DropReason: "plugin_error_skipped", LatencyMs: lat,
				})
			}
			continue
		}
		applyDelta(ctx, p.Name(), delta)
		out := len(ctx.Detections)
		if opt.Debug {
			ctx.Trace = append(ctx.Trace, StepTrace{
				Plugin: step.Plugin, DetectionsIn: in, DetectionsOut: out,
				Decision: string(ctx.Decision), DropReason: ctx.DropReason,
				EnrichmentPatch: delta.EnrichmentPatch, LatencyMs: lat,
			})
		}
		if ctx.Decision == DecisionDrop {
			break
		}
		if delta.SkipRest {
			break
		}
	}

	if ctx.Decision == DecisionDrop {
		return Result{Decision: DecisionDrop, DropReason: ctx.DropReason, Context: ctx, Trace: ctx.Trace}
	}
	if len(ctx.Detections) == 0 {
		ctx.Decision = DecisionDrop
		if ctx.DropReason == "" {
			ctx.DropReason = "empty_detections"
		}
		return Result{Decision: DecisionDrop, DropReason: ctx.DropReason, Context: ctx, Trace: ctx.Trace}
	}
	if ctx.Decision != DecisionPass {
		ctx.Decision = DecisionPass
	}
	return Result{Decision: DecisionPass, Context: ctx, Trace: ctx.Trace}
}

func applyDelta(ctx *Context, pluginName string, d PluginDelta) {
	if d.Detections != nil {
		ctx.Detections = *d.Detections
	}
	if d.EnrichmentPatch != nil {
		ctx.Enrichment[pluginName] = d.EnrichmentPatch
	}
	if len(d.LayersAppend) > 0 {
		ctx.Layers = append(ctx.Layers, d.LayersAppend...)
	}
	if d.Decision != nil {
		ctx.Decision = *d.Decision
	}
	if d.DropReason != "" {
		ctx.DropReason = d.DropReason
	}
	if d.RegionLabel != "" {
		ctx.RegionLabel = d.RegionLabel
	}
}
