package plugin

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"easyaiot/post/internal/contract"
	"easyaiot/post/internal/pipeline"
)

const (
	SchemaPluginInvoke = "post_plugin_invoke.v1"
	SchemaPluginDelta  = "post_plugin_delta.v1"
)

// ExternalHTTP calls an HTTP sidecar implementing /v1/process.
type ExternalHTTP struct {
	ID      string
	BaseURL string
	Path    string
	Timeout time.Duration
	Client  *http.Client
	Version string
}

func (e ExternalHTTP) Name() string { return e.ID }
func (e ExternalHTTP) Kinds() []pipeline.PluginKind {
	return []pipeline.PluginKind{pipeline.KindEnrich, pipeline.KindFilter}
}

func (e ExternalHTTP) processURL() string {
	base := strings.TrimSpace(e.BaseURL)
	if base == "" {
		return ""
	}
	// Full URL that already points at a process path.
	if strings.Contains(base, "://") {
		trimmed := strings.TrimRight(base, "/")
		if strings.HasSuffix(trimmed, "/v1/process") || strings.Contains(trimmed, "/v1/") {
			return trimmed
		}
		path := e.Path
		if path == "" {
			path = "/v1/process"
		}
		if !strings.HasPrefix(path, "/") {
			path = "/" + path
		}
		return trimmed + path
	}
	path := e.Path
	if path == "" {
		path = "/v1/process"
	}
	if !strings.HasPrefix(path, "/") {
		path = "/" + path
	}
	return strings.TrimRight(base, "/") + path
}

func (e ExternalHTTP) Process(ctx *pipeline.Context) (pipeline.PluginDelta, error) {
	if strings.TrimSpace(e.BaseURL) == "" {
		return pipeline.PluginDelta{}, fmt.Errorf("external plugin %s: empty endpoint", e.ID)
	}
	timeout := e.Timeout
	if timeout <= 0 {
		timeout = 2 * time.Second
	}
	client := e.Client
	if client == nil {
		client = &http.Client{Timeout: timeout}
	} else if client.Timeout == 0 {
		// copy with timeout
		c := *client
		c.Timeout = timeout
		client = &c
	}

	body := map[string]any{
		"schema":         SchemaPluginInvoke,
		"plugin_id":      e.ID,
		"plugin_version": e.Version,
		"params":         ctx.PluginParams,
		"context": map[string]any{
			"event":      ctx.Event,
			"task":       ctx.Task,
			"regions":    ctx.Regions,
			"detections": ctx.Detections,
			"enrichment": ctx.Enrichment,
			"decision":   string(ctx.Decision),
		},
	}
	raw, err := json.Marshal(body)
	if err != nil {
		return pipeline.PluginDelta{}, err
	}
	req, err := http.NewRequest(http.MethodPost, e.processURL(), bytes.NewReader(raw))
	if err != nil {
		return pipeline.PluginDelta{}, err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := client.Do(req)
	if err != nil {
		return pipeline.PluginDelta{}, err
	}
	defer resp.Body.Close()
	respBody, err := io.ReadAll(io.LimitReader(resp.Body, 4<<20))
	if err != nil {
		return pipeline.PluginDelta{}, err
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return pipeline.PluginDelta{}, fmt.Errorf("external plugin %s: HTTP %d: %s", e.ID, resp.StatusCode, truncate(string(respBody), 200))
	}
	return parsePluginDelta(respBody)
}

type deltaWire struct {
	Schema          string                `json:"schema"`
	Detections      *[]contract.Detection `json:"detections"`
	EnrichmentPatch map[string]any        `json:"enrichment_patch"`
	LayersAppend    []contract.DrawLayer  `json:"layers_append"`
	Decision        *string               `json:"decision"`
	DropReason      string                `json:"drop_reason"`
	SkipRest        bool                  `json:"skip_rest"`
	RegionLabel     string                `json:"region_label"`
}

func parsePluginDelta(raw []byte) (pipeline.PluginDelta, error) {
	var w deltaWire
	if err := json.Unmarshal(raw, &w); err != nil {
		return pipeline.PluginDelta{}, fmt.Errorf("invalid plugin delta: %w", err)
	}
	if w.Schema != "" && w.Schema != SchemaPluginDelta {
		return pipeline.PluginDelta{}, fmt.Errorf("unsupported delta schema %q", w.Schema)
	}
	out := pipeline.PluginDelta{
		Detections:      w.Detections,
		EnrichmentPatch: w.EnrichmentPatch,
		LayersAppend:    w.LayersAppend,
		DropReason:      w.DropReason,
		SkipRest:        w.SkipRest,
		RegionLabel:     w.RegionLabel,
	}
	if w.Decision != nil {
		d := pipeline.Decision(strings.ToLower(strings.TrimSpace(*w.Decision)))
		out.Decision = &d
	}
	return out, nil
}

func truncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "..."
}

// NewExternalFromStep builds an ExternalHTTP plugin from a pipeline step endpoint.
func NewExternalFromStep(pluginID, endpoint, version string, timeout time.Duration) ExternalHTTP {
	base := strings.TrimSpace(endpoint)
	path := "/v1/process"
	// If endpoint already includes path after host, keep as BaseURL full URL.
	return ExternalHTTP{
		ID:      pluginID,
		BaseURL: base,
		Path:    path,
		Timeout: timeout,
		Version: version,
	}
}
