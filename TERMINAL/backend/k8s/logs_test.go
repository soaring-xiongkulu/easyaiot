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

func TestLogStreamDeliversLines(t *testing.T) {
	srv, ca := startTLSServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !strings.Contains(r.URL.Path, "/log") {
			t.Errorf("path missing /log: %q", r.URL.Path)
		}
		if !strings.Contains(r.URL.RawQuery, "follow=true") {
			t.Errorf("query missing follow=true: %q", r.URL.RawQuery)
		}
		flusher, _ := w.(http.Flusher)
		w.WriteHeader(200)
		for _, l := range []string{"line-1", "line-2", "line-3"} {
			fmt.Fprintln(w, l)
			flusher.Flush()
			time.Sleep(3 * time.Millisecond)
		}
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
		t.Fatalf("BuildClient: %v", err)
	}

	m := NewManager()
	// 直接注入一个连接，避开 kubeconfig->connection 的 YAML 编解码环节。
	m.mu.Lock()
	m.conns["c1conn"] = &connection{
		id:      "c1conn",
		client:  client,
		base:    base,
		watches: make(map[string]struct{}),
	}
	m.mu.Unlock()

	var mu sync.Mutex
	var got []string
	m.SetEventEmitter(func(name string, payload any) {
		mu.Lock()
		defer mu.Unlock()
		if strings.HasPrefix(name, "k8s:log:") {
			got = append(got, payload.(string))
		}
	})

	sid, err := m.StartLogStream("c1conn", "default", "p1", "c1", 100, false, false)
	if err != nil {
		t.Fatalf("StartLogStream: %v", err)
	}
	if sid == "" {
		t.Fatal("empty streamID")
	}
	time.Sleep(80 * time.Millisecond)
	mu.Lock()
	defer mu.Unlock()
	if len(got) != 3 {
		t.Fatalf("want 3 lines, got %d: %v", len(got), got)
	}
}

// TestLogReconnectDoesNotCallOnEnd (F-404): same contract as
// TestWatchReconnectDoesNotCallOnEnd but for the log stream — a
// transient pod log disconnect fires onReconnect and reopens the
// stream, onEnd is reserved for the terminal case.
func TestLogReconnectDoesNotCallOnEnd(t *testing.T) {
	var hits int
	srv, ca := startTLSServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		hits++
		flusher, _ := w.(http.Flusher)
		w.WriteHeader(200)
		if hits == 1 {
			fmt.Fprintln(w, "boot-line")
			flusher.Flush()
			hj, ok := w.(http.Hijacker)
			if ok {
				conn, _, _ := hj.Hijack()
				conn.Close()
			}
			return
		}
		for i := 0; ; i++ {
			select {
			case <-r.Context().Done():
				return
			default:
			}
			fmt.Fprintf(w, "line-%d\n", i)
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
		mu         sync.Mutex
		endCalls   int
		reconCalls int
	)
	ended := make(chan struct{})
	wrappedEnd := func(err error) {
		mu.Lock()
		endCalls++
		mu.Unlock()
		select {
		case <-ended:
			t.Errorf("onEnd called more than once (err=%v)", err)
		default:
			close(ended)
		}
	}
	onReconnect := func(err error) {
		mu.Lock()
		reconCalls++
		mu.Unlock()
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	if err := startLogStream(ctx, client, base, "/api/v1/namespaces/default/pods/p1/log?follow=true&container=c",
		func(string) {}, wrappedEnd, onReconnect, make(chan struct{})); err != nil {
		t.Fatalf("startLogStream: %v", err)
	}

	time.Sleep(1500 * time.Millisecond)
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
		t.Errorf("server saw %d requests, want >= 2", hits)
	}

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

func TestBuildLogPath(t *testing.T) {
	// follow 模式（previous=false）：follow=true & previous=false
	p := buildLogPath("default", "p1", "c1", 100, true, false)
	if !strings.HasPrefix(p, "/api/v1/namespaces/default/pods/p1/log?") {
		t.Errorf("bad prefix: %q", p)
	}
	if !strings.Contains(p, "container=c1") ||
		!strings.Contains(p, "follow=true") ||
		!strings.Contains(p, "previous=false") ||
		!strings.Contains(p, "tailLines=100") ||
		!strings.Contains(p, "timestamps=true") {
		t.Errorf("follow path wrong: %q", p)
	}

	// previous 模式：一次性，follow=false & previous=true
	p = buildLogPath("ns2", "p2", "", 50, false, true)
	if !strings.Contains(p, "follow=false") || !strings.Contains(p, "previous=true") {
		t.Errorf("previous path wrong: %q", p)
	}
}
