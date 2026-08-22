package contract

import (
	"encoding/json"
	"fmt"
	"time"
)

const SchemaInferEvent = "infer_event.v1"
const SchemaAlertFinal = "alert_final.v1"
const SchemaTaskTemplate = "post_task_template.v1"
const SchemaTaskSync = "post_task_sync.v1"

// Detection is a single bbox detection.
type Detection struct {
	BBox       [4]float64 `json:"bbox"`
	ClassID    int        `json:"class_id,omitempty"`
	ClassName  string     `json:"class_name"`
	Confidence float64    `json:"confidence"`
	TrackID    int        `json:"track_id,omitempty"`
}

// InferEvent is the Infer → POST input contract.
type InferEvent struct {
	Schema         string                 `json:"schema"`
	EventKind      string                 `json:"event_kind"`
	CorrelationID  string                 `json:"correlation_id"`
	TaskID         int64                  `json:"task_id"`
	TaskName       string                 `json:"task_name,omitempty"`
	TaskType       string                 `json:"task_type"`
	DeviceID       string                 `json:"device_id"`
	DeviceName     string                 `json:"device_name,omitempty"`
	Timestamp      string                 `json:"timestamp"`
	FrameNumber    int64                  `json:"frame_number,omitempty"`
	FrameWidth     int                    `json:"frame_width"`
	FrameHeight    int                    `json:"frame_height"`
	ImagePath      string                 `json:"image_path,omitempty"`
	Detections     []Detection            `json:"detections"`
	ModelIDs       []int64                `json:"model_ids,omitempty"`
	Hints          map[string]any         `json:"hints,omitempty"`
}

// Validate checks required InferEvent fields.
func (e *InferEvent) Validate() error {
	if e.Schema != "" && e.Schema != SchemaInferEvent {
		return fmt.Errorf("unsupported schema %q", e.Schema)
	}
	if e.CorrelationID == "" {
		return fmt.Errorf("correlation_id required")
	}
	if e.TaskID == 0 {
		return fmt.Errorf("task_id required")
	}
	if e.DeviceID == "" {
		return fmt.Errorf("device_id required")
	}
	if e.TaskType == "" {
		return fmt.Errorf("task_type required")
	}
	if e.Timestamp == "" {
		return fmt.Errorf("timestamp required")
	}
	if e.EventKind == "" {
		e.EventKind = "infer"
	}
	if e.Detections == nil {
		e.Detections = []Detection{}
	}
	return nil
}

// IsHeartbeat reports whether this is a cache-touch heartbeat.
func (e *InferEvent) IsHeartbeat() bool {
	return e.EventKind == "heartbeat"
}

// DrawLayer is an optional overlay instruction (Phase1: carry only).
type DrawLayer struct {
	Kind   string         `json:"kind"`
	Params map[string]any `json:"params,omitempty"`
}

// AlertFinal is the internal pass result before legacy mapping.
type AlertFinal struct {
	Schema        string         `json:"schema"`
	CorrelationID string         `json:"correlation_id"`
	TaskID        int64          `json:"task_id"`
	TaskName      string         `json:"task_name"`
	TaskType      string         `json:"task_type"`
	DeviceID      string         `json:"device_id"`
	DeviceName    string         `json:"device_name"`
	Region        string         `json:"region"`
	Object        string         `json:"object"`
	Event         string         `json:"event"`
	Time          string         `json:"time"`
	ImagePath     string         `json:"image_path,omitempty"`
	Detections    []Detection    `json:"detections"`
	Information   map[string]any `json:"information"`
}

// Point is a 2D coordinate (pixel or normalized).
type Point struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

// UnmarshalJSON accepts {x,y} or [x,y].
func (p *Point) UnmarshalJSON(data []byte) error {
	var obj struct {
		X float64 `json:"x"`
		Y float64 `json:"y"`
	}
	if err := json.Unmarshal(data, &obj); err == nil && (obj.X != 0 || obj.Y != 0 || string(data) == `{"x":0,"y":0}` || looksLikeObject(data)) {
		if looksLikeObject(data) {
			p.X, p.Y = obj.X, obj.Y
			return nil
		}
	}
	var arr []float64
	if err := json.Unmarshal(data, &arr); err != nil {
		return err
	}
	if len(arr) < 2 {
		return fmt.Errorf("point needs 2 numbers")
	}
	p.X, p.Y = arr[0], arr[1]
	return nil
}

func looksLikeObject(data []byte) bool {
	for _, b := range data {
		if b == '{' {
			return true
		}
		if b == '[' {
			return false
		}
	}
	return false
}

// NowRFC3339 returns current time in RFC3339.
func NowRFC3339() string {
	return time.Now().Format(time.RFC3339)
}
