package main

import (
	"net/http"
	"testing"
)

// TestLLMProxyEnvFallback verifies that llmProxy resolves proxies declared
// via the HTTP_PROXY/HTTPS_PROXY environment variables (go-ieproxy prefers
// explicit env vars over the OS system proxy config).
//
// Direct-connection and system-proxy branches are intentionally not unit
// tested: they depend on the host's real system proxy state and on net/http's
// process-wide env-proxy cache, so they cannot be made hermetic.
func TestLLMProxyEnvFallback(t *testing.T) {
	t.Setenv("HTTP_PROXY", "127.0.0.1:7890")
	t.Setenv("HTTPS_PROXY", "127.0.0.1:7891")
	t.Setenv("NO_PROXY", "")

	// Force a fresh resolution so the cached func sees the test env.
	llmProxyMu.Lock()
	llmProxyFn = nil
	llmProxyMu.Unlock()

	req, err := http.NewRequest("GET", "https://api.openai.com/models", nil)
	if err != nil {
		t.Fatal(err)
	}
	u, err := llmProxy(req)
	if err != nil {
		t.Fatal(err)
	}
	if u == nil || u.Host != "127.0.0.1:7891" {
		t.Fatalf("want https proxy 127.0.0.1:7891, got %v", u)
	}

	req, err = http.NewRequest("GET", "http://example.com/models", nil)
	if err != nil {
		t.Fatal(err)
	}
	u, err = llmProxy(req)
	if err != nil {
		t.Fatal(err)
	}
	if u == nil || u.Host != "127.0.0.1:7890" {
		t.Fatalf("want http proxy 127.0.0.1:7890, got %v", u)
	}
}
