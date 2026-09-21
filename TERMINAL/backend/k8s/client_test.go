package k8s

import (
	"crypto/x509"
	"encoding/pem"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func startTLSServer(t *testing.T, handler http.Handler) (*httptest.Server, []byte) {
	t.Helper()
	srv := httptest.NewTLSServer(handler)
	cert := srv.Certificate()
	ca := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: cert.Raw})
	pool := x509.NewCertPool()
	if !pool.AppendCertsFromPEM(ca) {
		t.Fatal("cannot append test CA")
	}
	return srv, ca
}

func TestClientBearerToken(t *testing.T) {
	var gotAuth string
	srv, ca := startTLSServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotAuth = r.Header.Get("Authorization")
		w.WriteHeader(200)
		w.Write([]byte(`{"kind":"APIVersions"}`))
	}))
	defer srv.Close()

	kc := &Kubeconfig{
		CurrentContext: "t",
		Contexts:       map[string]contextEntry{"t": {Cluster: "c", User: "u"}},
		Clusters:       map[string]clusterEntry{"c": {Server: srv.URL, CertificateAuthorityData: ca}},
		Users:          map[string]userEntry{"u": {Token: "abc123"}},
	}
	client, base, err := BuildClient(kc, "t")
	if err != nil {
		t.Fatalf("BuildClient: %v", err)
	}
	if base != srv.URL {
		t.Errorf("base = %q want %q", base, srv.URL)
	}
	req, _ := http.NewRequest("GET", base+"/api", nil)
	resp, err := client.Do(req)
	if err != nil {
		t.Fatalf("Do: %v", err)
	}
	defer resp.Body.Close()
	io.ReadAll(resp.Body)
	if gotAuth != "Bearer abc123" {
		t.Errorf("Authorization = %q", gotAuth)
	}
}

func TestClientInsecureSkip(t *testing.T) {
	srv, _ := startTLSServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
	}))
	defer srv.Close()

	kc := &Kubeconfig{
		CurrentContext: "t",
		Contexts:       map[string]contextEntry{"t": {Cluster: "c", User: "u"}},
		Clusters:       map[string]clusterEntry{"c": {Server: srv.URL, InsecureSkipTLSVerify: true}},
		Users:          map[string]userEntry{"u": {Token: "x"}},
	}
	client, base, err := BuildClient(kc, "t")
	if err != nil {
		t.Fatal(err)
	}
	req, _ := http.NewRequest("GET", base+"/", nil)
	resp, err := client.Do(req)
	if err != nil {
		t.Fatalf("insecure Do: %v", err)
	}
	defer resp.Body.Close()
	io.ReadAll(resp.Body)
	if resp.StatusCode != 200 {
		t.Errorf("StatusCode = %d want 200", resp.StatusCode)
	}
}

func TestClientMissingCARejectsUntrustedServer(t *testing.T) {
	srv, _ := startTLSServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
	}))
	defer srv.Close()

	kc := &Kubeconfig{
		CurrentContext: "t",
		Contexts:       map[string]contextEntry{"t": {Cluster: "c", User: "u"}},
		Clusters:       map[string]clusterEntry{"c": {Server: srv.URL}}, // 无 CA，不 skip verify
		Users:          map[string]userEntry{"u": {}},
	}
	client, base, err := BuildClient(kc, "t")
	if err != nil {
		t.Fatalf("BuildClient: %v", err)
	}
	req, _ := http.NewRequest("GET", base+"/", nil)
	resp, err := client.Do(req)
	if err == nil {
		resp.Body.Close()
		t.Fatal("expected TLS verification error, got nil")
	}
}

// TestAuthRoundTripperRetriesOn401 verifies K8S-01: on 401 the
// roundtripper refreshes the token via refreshTok and retries exactly
// once. The original 401 must surface if refresh fails. Also exercises
// K8S-09: the caller's request headers must never be mutated — otherwise
// the second pass (after retry setup) would have nothing left to clone.
func TestAuthRoundTripperRetriesOn401(t *testing.T) {
	var hits int
	var gotAuths []string
	srv, ca := startTLSServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		hits++
		gotAuths = append(gotAuths, r.Header.Get("Authorization"))
		if hits == 1 {
			w.WriteHeader(http.StatusUnauthorized)
			return
		}
		w.WriteHeader(200)
		w.Write([]byte(`{"ok":true}`))
	}))
	defer srv.Close()

	kc := &Kubeconfig{
		CurrentContext: "t",
		Contexts:       map[string]contextEntry{"t": {Cluster: "c", User: "u"}},
		Clusters:       map[string]clusterEntry{"c": {Server: srv.URL, CertificateAuthorityData: ca}},
		Users:          map[string]userEntry{"u": {Token: "old"}},
	}
	client, base, err := BuildClient(kc, "t")
	if err != nil {
		t.Fatalf("BuildClient: %v", err)
	}

	// Splice a refreshTok into the transport; BuildClient doesn't expose it.
	rt, ok := client.Transport.(*authRoundTripper)
	if !ok {
		t.Fatalf("transport type = %T", client.Transport)
	}
	var refreshCalls int
	rt.refreshTok = func() (string, error) {
		refreshCalls++
		return "fresh", nil
	}

	// Caller-supplied headers — clone() under the hood must preserve them.
	req, _ := http.NewRequest("GET", base+"/api", nil)
	req.Header.Set("X-Trace", "abc")

	// Snapshot the caller's header map so we can prove nothing was mutated.
	wantTrace := req.Header.Get("X-Trace")

	resp, err := client.Do(req)
	if err != nil {
		t.Fatalf("Do: %v", err)
	}
	defer resp.Body.Close()
	io.ReadAll(resp.Body)

	if hits != 2 {
		t.Errorf("server hits = %d, want 2 (initial + retry)", hits)
	}
	if refreshCalls != 1 {
		t.Errorf("refreshTok calls = %d, want 1", refreshCalls)
	}
	if resp.StatusCode != 200 {
		t.Errorf("status = %d, want 200", resp.StatusCode)
	}
	if len(gotAuths) != 2 ||
		gotAuths[0] != "Bearer old" ||
		gotAuths[1] != "Bearer fresh" {
		t.Errorf("auth headers seen = %v, want [Bearer old Bearer fresh]", gotAuths)
	}
	if req.Header.Get("X-Trace") != wantTrace {
		t.Errorf("caller header mutated: X-Trace = %q", req.Header.Get("X-Trace"))
	}
}

// TestAuthRoundTripperSurfaces401OnRefreshFail: when refreshTok returns
// an error, the roundtripper must not silently swallow the original 401 —
// the caller still needs to know the credential was rejected.
func TestAuthRoundTripperSurfaces401OnRefreshFail(t *testing.T) {
	srv, ca := startTLSServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusUnauthorized)
	}))
	defer srv.Close()

	kc := &Kubeconfig{
		CurrentContext: "t",
		Contexts:       map[string]contextEntry{"t": {Cluster: "c", User: "u"}},
		Clusters:       map[string]clusterEntry{"c": {Server: srv.URL, CertificateAuthorityData: ca}},
		Users:          map[string]userEntry{"u": {Token: "stale"}},
	}
	client, base, err := BuildClient(kc, "t")
	if err != nil {
		t.Fatal(err)
	}
	rt := client.Transport.(*authRoundTripper)
	rt.refreshTok = func() (string, error) {
		return "", fmt.Errorf("kubelogin: idp timeout")
	}

	req, _ := http.NewRequest("GET", base+"/api", nil)
	resp, err := client.Do(req)
	if err != nil {
		t.Fatalf("Do: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusUnauthorized {
		t.Errorf("status = %d, want 401 surfaced", resp.StatusCode)
	}
}

func TestClientClientCertRequiresBoth(t *testing.T) {
	kc := &Kubeconfig{
		CurrentContext: "t",
		Contexts:       map[string]contextEntry{"t": {Cluster: "c", User: "u"}},
		Clusters:       map[string]clusterEntry{"c": {Server: "https://example.invalid", InsecureSkipTLSVerify: true}},
		Users:          map[string]userEntry{"u": {ClientCertificateData: []byte("-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----\n")}},
	}
	_, _, err := BuildClient(kc, "t")
	if err == nil {
		t.Fatal("expected error for missing client key, got nil")
	}
	if !strings.Contains(err.Error(), "both") {
		t.Errorf("error = %v; want message containing \"both\"", err)
	}
}
