package maplegacy

import (
	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/pipeline"
)

// ToAlertNotification maps pipeline pass context to sink-compatible JSON.
func ToAlertNotification(ctx *pipeline.Context) map[string]any {
	region := ctx.RegionLabel
	if region == "" {
		region = "全画面"
	}
	object := ""
	event := ctx.Task.AlertEvent
	if event == "" {
		event = "检测告警"
	}
	if patch, ok := ctx.Enrichment["default_pass"].(map[string]any); ok {
		if v, ok := patch["object"].(string); ok {
			object = v
		}
		if v, ok := patch["event"].(string); ok && v != "" {
			event = v
		}
	}
	if object == "" && len(ctx.Detections) > 0 {
		object = ctx.Detections[0].ClassName
	}

	regionFilter := "bypass"
	matched := []string{}
	if patch, ok := ctx.Enrichment["region_gate"].(map[string]any); ok {
		if v, ok := patch["region_filter"].(string); ok {
			regionFilter = v
		}
		if v, ok := patch["matched_regions"].([]string); ok {
			matched = v
		} else if v, ok := patch["matched_regions"].([]any); ok {
			for _, x := range v {
				if s, ok := x.(string); ok {
					matched = append(matched, s)
				}
			}
		}
	}

	gates := make([]string, 0)
	for k := range ctx.Enrichment {
		gates = append(gates, k)
	}

	info := map[string]any{
		"custom_post":      true,
		"gates_applied":    gates,
		"region_filter":    regionFilter,
		"matched_regions":  matched,
		"enrichment":       ctx.Enrichment,
		"drop_trace":       []any{},
		"task_type":        ctx.Task.TaskType,
		"detections":       ctx.Detections,
	}
	if ctx.Event.Hints != nil {
		info["hints"] = ctx.Event.Hints
	}

	taskName := ctx.Task.TaskName
	if taskName == "" {
		taskName = ctx.Event.TaskName
	}
	taskType := ctx.Task.TaskType
	if taskType == "" {
		taskType = ctx.Event.TaskType
	}
	deviceName := ctx.Event.DeviceName
	ts := ctx.Event.Timestamp
	if ts == "" {
		ts = contract.NowRFC3339()
	}

	return map[string]any{
		"taskId":        ctx.Event.TaskID,
		"task_id":       ctx.Event.TaskID,
		"taskName":      taskName,
		"task_name":     taskName,
		"deviceId":      ctx.Event.DeviceID,
		"device_id":     ctx.Event.DeviceID,
		"deviceName":    deviceName,
		"device_name":   deviceName,
		"correlationId": ctx.Event.CorrelationID,
		"correlation_id": ctx.Event.CorrelationID,
		"timestamp":     ts,
		"task_type":     taskType,
		"alert": map[string]any{
			"object":     object,
			"event":      event,
			"region":     region,
			"information": info,
			"imagePath":  ctx.Event.ImagePath,
			"image_path": ctx.Event.ImagePath,
			"time":       ts,
			"taskType":   taskType,
			"task_type":  taskType,
		},
		"shouldNotify": false,
	}
}

// ToAlertFinal builds internal alert_final shape (optional publish).
func ToAlertFinal(ctx *pipeline.Context) contract.AlertFinal {
	payload := ToAlertNotification(ctx)
	alert := payload["alert"].(map[string]any)
	info, _ := alert["information"].(map[string]any)
	return contract.AlertFinal{
		Schema:        contract.SchemaAlertFinal,
		CorrelationID: ctx.Event.CorrelationID,
		TaskID:        ctx.Event.TaskID,
		TaskName:      ctx.Task.TaskName,
		TaskType:      ctx.Task.TaskType,
		DeviceID:      ctx.Event.DeviceID,
		DeviceName:    ctx.Event.DeviceName,
		Region:        alert["region"].(string),
		Object:        alert["object"].(string),
		Event:         alert["event"].(string),
		Time:          alert["time"].(string),
		ImagePath:     ctx.Event.ImagePath,
		Detections:    ctx.Detections,
		Information:   info,
	}
}
