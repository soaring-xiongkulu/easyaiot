package k8s

import (
	"context"
	"encoding/base64"
	"fmt"
	"net/http"
	"sync"
	"testing"
	"time"
)

func TestManagerConnectAndRequest(t *testing.T) {
	srv, ca := startTLSServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
		w.Write([]byte(`{"ok":true}`))
	}))
	defer srv.Close()

	caB64 := base64.StdEncoding.EncodeToString(ca)
	raw := []byte(fmt.Sprintf(`
apiVersion: v1
kind: Config
current-context: t
contexts:
- name: t
  context: {cluster: c, user: u}
clusters:
- name: c
  cluster: {server: %s, certificate-authority-data: %s}
users:
- name: u
  user: {token: xyz}
`, srv.URL, caB64))

	m := NewManager()
	m.SetEventEmitter(func(string, any) {}) // no-op

	connID, err := m.Connect(context.Background(), raw, "t")
	if err != nil {
		t.Fatalf("Connect: %v", err)
	}
	status, body, err := m.Request(context.Background(), connID, "GET", "/version", nil, "")
	if err != nil {
		t.Fatalf("Request: %v", err)
	}
	if status != 200 || string(body) != `{"ok":true}` {
		t.Errorf("status=%d body=%s", status, body)
	}
	m.Disconnect(connID)
	if _, _, err := m.Request(context.Background(), connID, "GET", "/", nil, ""); err == nil {
		t.Error("Request after Disconnect should fail")
	}
}

func TestManagerListContexts(t *testing.T) {
	raw := []byte(`
apiVersion: v1
kind: Config
current-context: a
contexts:
- name: a
  context: {cluster: c1, user: u1, namespace: ns-a}
- name: b
  context: {cluster: c2, user: u2}
`)
	m := NewManager()
	ctxs, err := m.ListContexts(raw)
	if err != nil {
		t.Fatal(err)
	}
	if len(ctxs) != 2 {
		t.Fatalf("len = %d", len(ctxs))
	}
}

func TestManagerWatchEmitsEvents(t *testing.T) {
	srv, ca := startTLSServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		flusher, _ := w.(http.Flusher)
		w.WriteHeader(200)
		fmt.Fprintln(w, `{"type":"ADDED","object":{"kind":"Pod"}}`)
		flusher.Flush()
		time.Sleep(20 * time.Millisecond)
	}))
	defer srv.Close()
	caB64 := base64.StdEncoding.EncodeToString(ca)
	raw := []byte(fmt.Sprintf(`
apiVersion: v1
kind: Config
current-context: t
contexts: [{name: t, context: {cluster: c, user: u}}]
clusters: [{name: c, cluster: {server: %s, certificate-authority-data: %s}}]
users: [{name: u, user: {token: x}}]
`, srv.URL, caB64))

	m := NewManager()
	var mu sync.Mutex
	var got []string
	m.SetEventEmitter(func(name string, payload any) {
		mu.Lock()
		defer mu.Unlock()
		got = append(got, name)
	})
	connID, _ := m.Connect(context.Background(), raw, "t")
	watchID, err := m.StartWatch(connID, "/api/v1/pods?watch=true")
	if err != nil {
		t.Fatal(err)
	}
	// 轮询等待首个事件到达（避免固定 sleep 造成的偶发 flake）
	deadline := time.Now().Add(time.Second)
	for time.Now().Before(deadline) {
		mu.Lock()
		n := len(got)
		mu.Unlock()
		if n > 0 {
			break
		}
		time.Sleep(5 * time.Millisecond)
	}
	m.StopWatch(watchID)
	m.Disconnect(connID)

	mu.Lock()
	defer mu.Unlock()
	if len(got) == 0 || got[0] != "k8s:watch:"+watchID {
		t.Errorf("events = %v", got)
	}
}
