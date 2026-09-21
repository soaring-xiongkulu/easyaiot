package k8s

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"testing"
	"time"
)

func TestWatchDeliversEvents(t *testing.T) {
	srv, ca := startTLSServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !strings.Contains(r.URL.RawQuery, "watch=true") {
			t.Errorf("query missing watch=true: %q", r.URL.RawQuery)
		}
		flusher, _ := w.(http.Flusher)
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("Transfer-Encoding", "chunked")
		w.WriteHeader(200)
		lines := []string{
			`{"type":"ADDED","object":{"kind":"Pod","metadata":{"name":"p1","uid":"u1","resourceVersion":"1"}}}`,
			`{"type":"MODIFIED","object":{"kind":"Pod","metadata":{"name":"p1","uid":"u1","resourceVersion":"2"}}}`,
			`{"type":"DELETED","object":{"kind":"Pod","metadata":{"name":"p1","uid":"u1","resourceVersion":"3"}}}`,
		}
		for _, l := range lines {
			fmt.Fprintln(w, l)
			flusher.Flush()
			time.Sleep(5 * time.Millisecond)
		}
	}))
	defer srv.Close()

	kc := &Kubeconfig{
		CurrentContext: "t",
		Contexts:       map[string]contextEntry{"t": {Cluster: "c", User: "u"}},
		Clusters:       map[string]clusterEntry{"c": {Server: srv.URL, CertificateAuthorityData: ca}},
		Users:          map[string]userEntry{"u": {Token: "x"}},
	}
	client, base, _ := BuildClient(kc, "t")

	var mu sync.Mutex
	var got []string
	done := make(chan struct{})
	cb := func(ev WatchEvent) {
		mu.Lock()
		got = append(got, ev.Type)
		mu.Unlock()
	}
	onEnd := func(err error) {
		close(done)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	err := startWatchStream(ctx, client, base, "/api/v1/namespaces/default/pods?watch=true", cb, onEnd, nil, make(chan struct{}))
	if err != nil {
		t.Fatalf("startWatchStream: %v", err)
	}

	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("watch timeout")
	}
	mu.Lock()
	defer mu.Unlock()
	if len(got) != 3 || got[0] != "ADDED" || got[2] != "DELETED" {
		t.Errorf("got = %v", got)
	}
}

// TestWatchReconnectDoesNotCallOnEnd (F-404): when the apiserver drops
// the connection mid-stream, the watch loop must fire onReconnect, NOT
// onEnd. onEnd is reserved for the terminal case (ctx cancel, clean EOF)
// — otherwise the manager would drop the watch handle on every retry
// attempt and the UI would never see new events.
func TestWatchReconnectDoesNotCallOnEnd(t *testing.T) {
	var hits int
	srv, ca := startTLSServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		hits++
		flusher, _ := w.(http.Flusher)
		w.Header().Set("Transfer-Encoding", "chunked")
		w.WriteHeader(200)
		// First attempt: send 1 event then drop the connection — simulates
		// apiserver bounce mid-stream.
		if hits == 1 {
			fmt.Fprintln(w, `{"type":"ADDED","object":{"metadata":{"resourceVersion":"1"}}}`)
			flusher.Flush()
			// Hijack & close so the scanner sees an EOF, not a clean stream
			// end. Hijacker is httptest.Server safe.
			hj, ok := w.(http.Hijacker)
			if ok {
				conn, _, _ := hj.Hijack()
				conn.Close()
			}
			return
		}
		// Subsequent attempts: keep the connection alive with events so
		// the loop has to back off + retry but never reaches onEnd.
		for i := 0; ; i++ {
			select {
			case <-r.Context().Done():
				return
			default:
			}
			fmt.Fprintf(w, `{"type":"MODIFIED","object":{"metadata":{"resourceVersion":"%d"}}}`+"\n", i+2)
			flusher.Flush()
			time.Sleep(20 * time.Millisecond)
		}
	}))
	defer srv.Close()

	kc := &Kubeconfig{
		CurrentContext: "t",
		Contexts:       map[string]contextEntry{"t": {Cluster: "c", User: "u"}},
		Clusters:       map[string]clusterEntry{"c": {Server: srv.URL, CertificateAuthorityData: ca}},
		Users:          map[string]userEntry{"u": {Token: "x"}},
	}
	client, base, _ := BuildClient(kc, "t")

	var (
		mu          sync.Mutex
		endCalls    int
		reconCalls  int
	)
	endName := "ended"
	reconName := "reconnect"
	onEnd := func(err error) {
		mu.Lock()
		endCalls++
		mu.Unlock()
	}
	onReconnect := func(err error) {
		mu.Lock()
		reconCalls++
		mu.Unlock()
	}
	// Wrap to assert onEnd is called exactly once at terminal cancel.
	ended := make(chan struct{})
	wrappedEnd := func(err error) {
		onEnd(err)
		select {
		case <-ended:
			t.Errorf("onEnd called more than once (err=%v)", err)
		default:
			close(ended)
		}
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	if err := startWatchStream(ctx, client, base, "/api/v1/pods?watch=true",
		func(WatchEvent) {}, wrappedEnd, onReconnect, make(chan struct{})); err != nil {
		t.Fatalf("startWatchStream: %v", err)
	}

	// Give the loop time for at least one reconnect attempt.
	time.Sleep(1500 * time.Millisecond)

	// At this point the loop has had one transport failure → at least
	// one reconnect, but should NOT have called onEnd.
	mu.Lock()
	preEnd := endCalls
	preRecon := reconCalls
	mu.Unlock()
	if preEnd != 0 {
		t.Errorf("onEnd called %d times during reconnect (want 0)", preEnd)
	}
	if preRecon == 0 {
		t.Errorf("onReconnect called %d times (want >= 1)", preRecon)
	}
	if hits < 2 {
		t.Errorf("server saw %d requests, want >= 2 (initial + reconnect)", hits)
	}
	_ = endName
	_ = reconName

	// Now cancel — onEnd must fire exactly once.
	cancel()
	select {
	case <-ended:
	case <-time.After(2 * time.Second):
		t.Fatal("onEnd never called after ctx cancel")
	}
	mu.Lock()
	defer mu.Unlock()
	if endCalls != 1 {
		t.Errorf("onEnd calls = %d, want exactly 1", endCalls)
	}
}

func TestWatchContextCancel(t *testing.T) {
	srv, ca := startTLSServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		flusher, _ := w.(http.Flusher)
		w.WriteHeader(200)
		for i := 0; ; i++ {
			_, err := fmt.Fprintf(w, `{"type":"ADDED","object":{"metadata":{"resourceVersion":"%d"}}}`+"\n", i)
			if err != nil {
				return
			}
			flusher.Flush()
			time.Sleep(10 * time.Millisecond)
		}
	}))
	defer srv.Close()

	kc := &Kubeconfig{
		CurrentContext: "t",
		Contexts:       map[string]contextEntry{"t": {Cluster: "c", User: "u"}},
		Clusters:       map[string]clusterEntry{"c": {Server: srv.URL, CertificateAuthorityData: ca}},
		Users:          map[string]userEntry{"u": {Token: "x"}},
	}
	client, base, _ := BuildClient(kc, "t")
	ctx, cancel := context.WithCancel(context.Background())
	ended := make(chan struct{})
	err := startWatchStream(ctx, client, base, "/api/v1/pods?watch=true",
		func(WatchEvent) {},
		func(err error) { close(ended) },
		nil, make(chan struct{}))
	if err != nil {
		t.Fatal(err)
	}
	time.Sleep(50 * time.Millisecond)
	cancel()
	select {
	case <-ended:
	case <-time.After(1 * time.Second):
		t.Fatal("cancel did not stop watch")
	}
}
