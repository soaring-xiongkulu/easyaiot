package plugin

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/pipeline"
)

func TestUserScriptUsesConfiguredEndpoint(t *testing.T) {
	var requestPath string
	var requestBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestPath = r.URL.Path
		if err := json.NewDecoder(r.Body).Decode(&requestBody); err != nil {
			t.Fatalf("decode request: %v", err)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{
			"schema":           SchemaPluginDelta,
			"enrichment_patch": map[string]any{"script_ok": true},
		})
	}))
	defer srv.Close()

	ctx := &pipeline.Context{
		Event:        sampleEvent(),
		Task:         config.TaskConfig{ID: 1},
		Enrichment:   map[string]any{},
		Decision:     pipeline.DecisionContinue,
		PluginParams: map[string]any{"mode": "regression"},
	}
	delta, err := (UserScript{URL: srv.URL, Timeout: time.Second}).Process(ctx)
	if err != nil {
		t.Fatal(err)
	}
	if requestPath != "/v1/process" {
		t.Fatalf("request path=%q", requestPath)
	}
	if requestBody["plugin_id"] != "user_script" {
		t.Fatalf("plugin_id=%v", requestBody["plugin_id"])
	}
	if delta.EnrichmentPatch["script_ok"] != true {
		t.Fatalf("patch=%v", delta.EnrichmentPatch)
	}
}

func TestUserScriptRequiresEndpoint(t *testing.T) {
	t.Setenv("USER_SCRIPT_URL", "")
	_, err := (UserScript{}).Process(&pipeline.Context{})
	if err == nil || !strings.Contains(err.Error(), "USER_SCRIPT_URL not configured") {
		t.Fatalf("err=%v", err)
	}
}
