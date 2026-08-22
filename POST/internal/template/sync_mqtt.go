package template

import (
	"encoding/json"
	"log/slog"
	"time"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/metrics"
	mqttbus "easyaiot/post/internal/mqtt"
)

// SyncMessage is multi-replica template sync payload.
type SyncMessage struct {
	Schema         string               `json:"schema"`
	Op             string               `json:"op"`
	TaskID         int64                `json:"task_id"`
	Template       *config.TaskTemplate `json:"template,omitempty"`
	TS             string               `json:"ts"`
	SourceInstance string               `json:"source_instance"`
}

// SyncPublisher publishes task sync after local HTTP mutations.
type SyncPublisher struct {
	Bus        *mqttbus.Bus
	Topic      string
	InstanceID string
}

func (s *SyncPublisher) PublishUpsert(tpl config.TaskTemplate) {
	if s == nil || s.Bus == nil {
		return
	}
	msg := SyncMessage{
		Schema: contract.SchemaTaskSync, Op: "upsert", TaskID: tpl.Task.ID,
		Template: &tpl, TS: time.Now().Format(time.RFC3339), SourceInstance: s.InstanceID,
	}
	if err := s.Bus.PublishJSON(s.Topic, 1, msg); err != nil {
		slog.Error("task_sync_publish_failed", "op", "upsert", "task_id", tpl.Task.ID, "err", err)
	}
}

func (s *SyncPublisher) PublishDelete(taskID int64) {
	if s == nil || s.Bus == nil {
		return
	}
	msg := SyncMessage{
		Schema: contract.SchemaTaskSync, Op: "delete", TaskID: taskID,
		TS: time.Now().Format(time.RFC3339), SourceInstance: s.InstanceID,
	}
	if err := s.Bus.PublishJSON(s.Topic, 1, msg); err != nil {
		slog.Error("task_sync_publish_failed", "op", "delete", "task_id", taskID, "err", err)
	}
}

func (s *SyncPublisher) PublishTouch(taskID int64) {
	if s == nil || s.Bus == nil {
		return
	}
	msg := SyncMessage{
		Schema: contract.SchemaTaskSync, Op: "touch", TaskID: taskID,
		TS: time.Now().Format(time.RFC3339), SourceInstance: s.InstanceID,
	}
	if err := s.Bus.PublishJSON(s.Topic, 1, msg); err != nil {
		slog.Error("task_sync_publish_failed", "op", "touch", "task_id", taskID, "err", err)
	}
}

// ApplySync applies remote sync (no rebroadcast).
func ApplySync(cache *Cache, instanceID string, payload []byte) {
	var msg SyncMessage
	if err := json.Unmarshal(payload, &msg); err != nil {
		slog.Warn("task_sync_bad_json", "err", err)
		return
	}
	if msg.SourceInstance == instanceID {
		return
	}
	switch msg.Op {
	case "upsert":
		if msg.Template == nil {
			return
		}
		if msg.Template.Task.ID == 0 {
			msg.Template.Task.ID = msg.TaskID
		}
		cache.Upsert(*msg.Template)
		metrics.SyncApply.WithLabelValues("upsert", instanceID).Inc()
	case "delete":
		cache.Delete(msg.TaskID)
		metrics.SyncApply.WithLabelValues("delete", instanceID).Inc()
	case "touch":
		if cache.Touch(msg.TaskID) {
			metrics.SyncApply.WithLabelValues("touch", instanceID).Inc()
		}
		// 无模板则忽略（不回源）
	default:
		slog.Warn("task_sync_unknown_op", "op", msg.Op)
	}
}
