package k8s

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"strings"
	"testing"
)

func TestDoGet(t *testing.T) {
	srv, ca := startTLSServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/v1/namespaces/default/pods" {
			t.Errorf("path = %q", r.URL.Path)
		}
		if r.Header.Get("Authorization") != "Bearer x" {
			t.Errorf("auth missing")
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(200)
		json.NewEncoder(w).Encode(map[string]any{"kind": "PodList", "items": []any{}})
	}))
	defer srv.Close()

	kc := &Kubeconfig{
		CurrentContext: "t",
		Contexts:       map[string]contextEntry{"t": {Cluster: "c", User: "u"}},
		Clusters:       map[string]clusterEntry{"c": {Server: srv.URL, CertificateAuthorityData: ca}},
		Users:          map[string]userEntry{"u": {Token: "x"}},
	}
	client, base, err := BuildClient(kc, "t")
	if err != nil {
		t.Fatal(err)
	}
	status, body, err := Do(context.Background(), client, base, "GET", "/api/v1/namespaces/default/pods", nil, "")
	if err != nil {
		t.Fatalf("Do: %v", err)
	}
	if status != 200 {
		t.Errorf("status = %d", status)
	}
	if !strings.Contains(string(body), `"kind":"PodList"`) {
		t.Errorf("body = %s", body)
	}
}

func TestDoPatchWithContentType(t *testing.T) {
	var gotCT string
	var gotBody []byte
	srv, ca := startTLSServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotCT = r.Header.Get("Content-Type")
		gotBody, _ = io.ReadAll(r.Body)
		w.WriteHeader(200)
	}))
	defer srv.Close()
	kc := &Kubeconfig{
		CurrentContext: "t",
		Contexts:       map[string]contextEntry{"t": {Cluster: "c", User: "u"}},
		Clusters:       map[string]clusterEntry{"c": {Server: srv.URL, CertificateAuthorityData: ca}},
		Users:          map[string]userEntry{"u": {Token: "x"}},
	}
	client, base, _ := BuildClient(kc, "t")
	body := []byte(`{"kind":"Pod"}`)
	_, _, err := Do(context.Background(), client, base, "PATCH",
		"/api/v1/namespaces/default/pods/p1?fieldManager=terminal",
		body, "application/apply-patch+yaml")
	if err != nil {
		t.Fatal(err)
	}
	if gotCT != "application/apply-patch+yaml" {
		t.Errorf("content-type = %q", gotCT)
	}
	if string(gotBody) != `{"kind":"Pod"}` {
		t.Errorf("body = %s", gotBody)
	}
}

// TestDoBodySizeLimit (K8S-05): a response body above maxK8sResponseBytes
// must surface a clear error and not stream a giant slice back to the
// caller. We exercise the cap via a fake RoundTripper so the test stays
// O(1) in memory — no 64 MiB allocation, no real TLS handshake.
func TestDoBodySizeLimit(t *testing.T) {
	fake := &fakeTripper{resp: &http.Response{
		StatusCode: 200,
		Header:     http.Header{"Content-Type": []string{"application/json"}},
		Body:       io.NopCloser(bytes.NewReader(make([]byte, maxK8sResponseBytes+1))),
	}}
	client := &http.Client{Transport: fake}

	status, body, err := Do(context.Background(), client, "http://example.invalid", "GET", "/huge", nil, "")
	if err == nil {
		t.Fatalf("expected oversize error, got nil (status=%d body=%d bytes)", status, len(body))
	}
	if !strings.Contains(err.Error(), "64 MiB") && !strings.Contains(err.Error(), "limit") {
		t.Errorf("error = %v; want message mentioning the 64 MiB limit", err)
	}
	if len(body) != 0 {
		t.Errorf("body should be nil on oversize, got %d bytes", len(body))
	}
	if status != 200 {
		t.Errorf("status = %d, want 200 (response was received, just too big)", status)
	}
}

// fakeTripper returns a canned response without touching the network.
type fakeTripper struct{ resp *http.Response }

func (f *fakeTripper) RoundTrip(req *http.Request) (*http.Response, error) {
	return f.resp, nil
}