package plugin

import (
	"strings"
	"time"
)

func paramString(params map[string]any, key, def string) string {
	if params == nil {
		return def
	}
	v, ok := params[key].(string)
	if !ok || strings.TrimSpace(v) == "" {
		return def
	}
	return strings.TrimSpace(v)
}

func paramFloat(params map[string]any, key string, def float64) float64 {
	if params == nil {
		return def
	}
	switch t := params[key].(type) {
	case float64:
		return t
	case int:
		return float64(t)
	case int64:
		return float64(t)
	default:
		return def
	}
}

func paramInt(params map[string]any, key string, def int) int {
	if params == nil {
		return def
	}
	switch t := params[key].(type) {
	case float64:
		return int(t)
	case int:
		return t
	case int64:
		return int(t)
	default:
		return def
	}
}

func paramStringSlice(params map[string]any, key string) []string {
	if params == nil {
		return nil
	}
	raw, ok := params[key]
	if !ok || raw == nil {
		return nil
	}
	switch t := raw.(type) {
	case []string:
		return t
	case []any:
		out := make([]string, 0, len(t))
		for _, x := range t {
			if s, ok := x.(string); ok && s != "" {
				out = append(out, s)
			}
		}
		return out
	default:
		return nil
	}
}

func parseEventTime(ts string) time.Time {
	if ts == "" {
		return time.Now()
	}
	t, err := time.Parse(time.RFC3339, ts)
	if err != nil {
		return time.Now()
	}
	return t
}

func compareCount(count, threshold int, op string) bool {
	switch op {
	case "gt":
		return count > threshold
	case "eq":
		return count == threshold
	case "lt":
		return count < threshold
	case "lte":
		return count <= threshold
	default: // gte
		return count >= threshold
	}
}
