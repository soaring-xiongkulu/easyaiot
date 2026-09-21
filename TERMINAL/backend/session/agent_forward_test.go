package session

import (
	"encoding/json"
	"strings"
	"testing"
)

func TestConnectionConfigAgentForwardingJSON(t *testing.T) {
	b, err := json.Marshal(ConnectionConfig{AgentForwarding: true})
	if err != nil {
		t.Fatalf("json.Marshal() error = %v", err)
	}
	if !strings.Contains(string(b), `"agentForwarding":true`) {
		t.Fatalf("json.Marshal() = %s, want agentForwarding=true", b)
	}

	var cfg ConnectionConfig
	if err := json.Unmarshal([]byte(`{"agentForwarding":true}`), &cfg); err != nil {
		t.Fatalf("json.Unmarshal() error = %v", err)
	}
	if !cfg.AgentForwarding {
		t.Fatal("json.Unmarshal() did not restore agentForwarding")
	}
}

func boolPtr(b bool) *bool { return &b }

// Shell integration defaults to ENABLED: a nil field (historical configs and
// fresh JSON) means startup injection runs, and only an explicit false opts
// out. All three states must round-trip through JSON.
func TestConnectionConfigShellIntegrationDefaultsOnAndRoundTrips(t *testing.T) {
	var defaultConfig ConnectionConfig
	if err := json.Unmarshal([]byte(`{}`), &defaultConfig); err != nil {
		t.Fatalf("json.Unmarshal() error = %v", err)
	}
	if !defaultConfig.shellIntegrationEnabled() {
		t.Fatal("absent shellIntegration must default to enabled")
	}

	var disabled ConnectionConfig
	if err := json.Unmarshal([]byte(`{"shellIntegration":false}`), &disabled); err != nil {
		t.Fatalf("json.Unmarshal() error = %v", err)
	}
	if disabled.shellIntegrationEnabled() {
		t.Fatal("explicit shellIntegration=false must stay disabled")
	}

	var enabled ConnectionConfig
	if err := json.Unmarshal([]byte(`{"shellIntegration":true}`), &enabled); err != nil {
		t.Fatalf("json.Unmarshal() error = %v", err)
	}
	if !enabled.shellIntegrationEnabled() {
		t.Fatal("explicit shellIntegration=true must stay enabled")
	}

	b, err := json.Marshal(ConnectionConfig{ShellIntegration: boolPtr(true)})
	if err != nil {
		t.Fatalf("json.Marshal() error = %v", err)
	}
	if !strings.Contains(string(b), `"shellIntegration":true`) {
		t.Fatalf("json.Marshal() = %s, want shellIntegration=true", b)
	}
	b, err = json.Marshal(ConnectionConfig{ShellIntegration: boolPtr(false)})
	if err != nil {
		t.Fatalf("json.Marshal() error = %v", err)
	}
	if !strings.Contains(string(b), `"shellIntegration":false`) {
		t.Fatalf("json.Marshal() = %s, want shellIntegration=false", b)
	}
	b, err = json.Marshal(ConnectionConfig{})
	if err != nil {
		t.Fatalf("json.Marshal() error = %v", err)
	}
	if strings.Contains(string(b), "shellIntegration") {
		t.Fatalf("json.Marshal() = %s, want shellIntegration omitted for nil", b)
	}
}
