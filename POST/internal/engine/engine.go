package engine

import (
	"encoding/json"
	"log/slog"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/maplegacy"
	"easyaiot/post/internal/metrics"
	mqttbus "easyaiot/post/internal/mqtt"
	"easyaiot/post/internal/pipeline"
	"easyaiot/post/internal/plugin"
	"easyaiot/post/internal/template"
)

// Engine processes InferEvents.
type Engine struct {
	Cfg      config.Config
	Cache    *template.Cache
	Registry pipeline.Registry
	Resolve  pipeline.Resolver
	Bus      *mqttbus.Bus
	Sync     *template.SyncPublisher
}

func New(cfg config.Config, cache *template.Cache, bus *mqttbus.Bus) *Engine {
	reg := plugin.NewRegistry(cfg)
	timeout := cfg.PluginHTTPTimeout
	return &Engine{
		Cfg: cfg, Cache: cache, Registry: reg, Bus: bus,
		Resolve: func(step config.PipelineStep) pipeline.Plugin {
			return plugin.Resolve(reg, step, timeout)
		},
	}
}

// HandleInferJSON parses and processes one InferEvent payload.
func (e *Engine) HandleInferJSON(payload []byte) {
	var ev contract.InferEvent
	if err := json.Unmarshal(payload, &ev); err != nil {
		slog.Warn("invalid_infer_event", "err", err)
		return
	}
	if err := ev.Validate(); err != nil {
		slog.Warn("invalid_infer_event", "err", err, "task_id", ev.TaskID)
		return
	}
	e.Handle(ev)
}

// Handle runs cache + pipeline + optional publish.
func (e *Engine) Handle(ev contract.InferEvent) (result string, dropReason string, alertPayload map[string]any) {
	kind := ev.EventKind
	if kind == "" {
		kind = "infer"
	}
	metrics.InferTotal.WithLabelValues(kind, e.Cfg.InstanceID).Inc()

	entry, ok := e.Cache.Get(ev.TaskID)
	if !ok {
		metrics.CacheMiss.WithLabelValues(e.Cfg.InstanceID).Inc()
		metrics.DropTotal.WithLabelValues("task_cache_miss", e.Cfg.InstanceID).Inc()
		slog.Info("post_drop",
			"correlation_id", ev.CorrelationID, "task_id", ev.TaskID, "device_id", ev.DeviceID,
			"instance_id", e.Cfg.InstanceID, "result", "drop", "drop_reason", "task_cache_miss",
			"detections_in", len(ev.Detections), "detections_out", 0)
		return "drop", "task_cache_miss", nil
	}
	e.Cache.Touch(ev.TaskID)
	// v1.9：多节点滑动 TTL —— 本地 Touch 后广播，其它副本只 Touch 不回环
	if e.Sync != nil {
		e.Sync.PublishTouch(ev.TaskID)
	}

	if !e.Cfg.Enabled {
		metrics.DropTotal.WithLabelValues("gate_disabled", e.Cfg.InstanceID).Inc()
		return "drop", "gate_disabled", nil
	}

	regions := entry.ByDevice[ev.DeviceID]
	task := entry.Template.Task
	if reason := normalizeDetectionModelIDs(&ev, task, regions); reason != "" {
		metrics.DropTotal.WithLabelValues(reason, e.Cfg.InstanceID).Inc()
		slog.Info("post_drop",
			"correlation_id", ev.CorrelationID, "task_id", ev.TaskID, "device_id", ev.DeviceID,
			"template_revision", entry.Template.Revision,
			"instance_id", e.Cfg.InstanceID, "result", "drop", "drop_reason", reason,
			"detections_in", len(ev.Detections), "detections_out", 0)
		return "drop", reason, nil
	}
	res := pipeline.RunWith(pipeline.Options{
		Registry: e.Registry,
		Resolve:  e.Resolve,
		Debug:    e.Cfg.Debug,
	}, ev, task, regions)
	if res.Context != nil {
		res.Context.Enrichment["template_revision"] = entry.Template.Revision
		if regionInfo, ok := res.Context.Enrichment["region_gate"].(map[string]any); ok {
			regionInfo["region_revision"] = entry.Template.Revision
		}
	}

	inN := len(ev.Detections)
	outN := 0
	if res.Context != nil {
		outN = len(res.Context.Detections)
	}

	if res.Decision == pipeline.DecisionDrop {
		metrics.DropTotal.WithLabelValues(res.DropReason, e.Cfg.InstanceID).Inc()
		slog.Info("post_drop",
			"correlation_id", ev.CorrelationID, "task_id", ev.TaskID, "device_id", ev.DeviceID,
			"template_revision", entry.Template.Revision,
			"instance_id", e.Cfg.InstanceID, "result", "drop", "drop_reason", res.DropReason,
			"detections_in", inN, "detections_out", outN)
		if e.Cfg.Debug && e.Bus != nil {
			_ = e.Bus.PublishJSON(e.Cfg.TopicTrace, 0, map[string]any{
				"correlation_id": ev.CorrelationID, "result": "drop",
				"drop_reason": res.DropReason, "trace": res.Trace,
			})
		}
		return "drop", res.DropReason, nil
	}

	alert := maplegacy.ToAlertNotification(res.Context)
	metrics.PassTotal.WithLabelValues(e.Cfg.InstanceID).Inc()
	slog.Info("post_pass",
		"correlation_id", ev.CorrelationID, "task_id", ev.TaskID, "device_id", ev.DeviceID,
		"template_revision", entry.Template.Revision,
		"instance_id", e.Cfg.InstanceID, "result", "pass",
		"detections_in", inN, "detections_out", outN)

	if e.Bus != nil {
		topic := e.Cfg.TopicLegacyAlert
		tt := stringsEqualFoldAny(ev.TaskType, "snap", "snapshot")
		if tt {
			topic = e.Cfg.TopicSnapshotAlert
		}
		if err := e.Bus.PublishJSON(topic, 1, alert); err != nil {
			slog.Error("publish_alert_failed", "err", err, "topic", topic)
		}
		if e.Cfg.PublishOptionalFinal {
			_ = e.Bus.PublishJSON(e.Cfg.TopicAlertFinal, 0, maplegacy.ToAlertFinal(res.Context))
		}
		if e.Cfg.Debug {
			_ = e.Bus.PublishJSON(e.Cfg.TopicTrace, 0, map[string]any{
				"correlation_id": ev.CorrelationID, "result": "pass", "trace": res.Trace,
			})
		}
	}
	return "pass", "", alert
}

func normalizeDetectionModelIDs(ev *contract.InferEvent, task config.TaskConfig, regions []config.Region) string {
	taskModels := make(map[int64]struct{}, len(task.ModelIDs))
	for _, id := range task.ModelIDs {
		taskModels[id] = struct{}{}
	}
	var fallback *int64
	if len(ev.ModelIDs) == 1 {
		id := ev.ModelIDs[0]
		fallback = &id
	} else if len(task.ModelIDs) == 1 {
		id := task.ModelIDs[0]
		fallback = &id
	}
	hasModelSpecificRegion := false
	for _, r := range regions {
		if !r.IsEnabled {
			continue
		}
		if len(r.ModelIDs) > 0 {
			hasModelSpecificRegion = true
		}
	}
	requiresFrameSize := false
	for i := range ev.Detections {
		det := &ev.Detections[i]
		if det.ModelID == nil && fallback != nil {
			id := *fallback
			det.ModelID = &id
		}
		if det.ModelID == nil {
			if hasModelSpecificRegion {
				return "missing_detection_model_id"
			}
		} else if _, ok := taskModels[*det.ModelID]; !ok {
			return "foreign_detection_model_id"
		}
		for _, region := range regions {
			if !region.IsEnabled || !regionAppliesToDetectionModel(region.ModelIDs, det.ModelID) {
				continue
			}
			if region.RegionType == "" || region.RegionType == "polygon" ||
				region.RegionType == "rectangle" || region.RegionType == "line" {
				requiresFrameSize = true
				break
			}
		}
	}
	if requiresFrameSize && (ev.FrameWidth <= 0 || ev.FrameHeight <= 0) {
		return "invalid_frame_size"
	}
	return ""
}

func regionAppliesToDetectionModel(regionModelIDs []int64, detectionModelID *int64) bool {
	if len(regionModelIDs) == 0 {
		return true
	}
	if detectionModelID == nil {
		return false
	}
	for _, id := range regionModelIDs {
		if id == *detectionModelID {
			return true
		}
	}
	return false
}

func stringsEqualFoldAny(s string, opts ...string) bool {
	for _, o := range opts {
		if equalFold(s, o) {
			return true
		}
	}
	return false
}

func equalFold(a, b string) bool {
	if len(a) != len(b) {
		return false
	}
	for i := 0; i < len(a); i++ {
		ca, cb := a[i], b[i]
		if ca >= 'A' && ca <= 'Z' {
			ca += 'a' - 'A'
		}
		if cb >= 'A' && cb <= 'Z' {
			cb += 'a' - 'A'
		}
		if ca != cb {
			return false
		}
	}
	return true
}
