package k8s

import (
	"context"
	"crypto/sha256"
	"crypto/tls"
	"fmt"
	"net/http"
	"net/url"
	"sync"
	"sync/atomic"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/websocket"
)

// EventEmitter 是 Manager 用来推送 watch 事件的抽象；
// 上层（App）把它接到 Wails runtime.EventsEmit。
type EventEmitter func(name string, payload any)

type Manager struct {
	mu      sync.RWMutex
	conns   map[string]*connection
	watches map[string]*watchHandle
	logs    map[string]*logHandle
	// emit is set once in startup via SetEventEmitter and never changes,
	// so we store it in atomic.Value to let StartWatch/StartLogStream
	// capture it without grabbing the manager mutex (F-413).
	emit atomic.Value // EventEmitter

	// kubeconfigCache memoizes ParseBytes results keyed on sha256 of the
	// raw YAML bytes — kubeconfigs are re-parsed on every tab open, and
	// a 20-context config pays a full yaml.Unmarshal + per-cluster base64
	// decode + per-user X509KeyPair parse each time (F-405).
	kubeconfigCache sync.Map // map[string]*Kubeconfig (sha256 hex → *Kubeconfig)
}

type connection struct {
	id           string
	client       *http.Client
	base         string
	token        string      // exec 等 WebSocket 场景复用的 bearer token
	tlsConfig    *tls.Config // 复用 REST client 的 TLS 配置
	dialOverride DialFunc    // 可选的 dial 劫持（SSH 隧道）
	watches      map[string]struct{} // 属于本 conn 的 watchID 集合，Disconnect 时统一停
	onClose      func()              // Disconnect 时触发（例如拆 SSH 隧道）；只调一次
}

type watchHandle struct {
	connID string
	cancel context.CancelFunc
	// done is closed by runWatchLoop when the goroutine exits (terminal
	// onEnd). The sweeper uses this to prune handles whose backing
	// goroutine has exited without anyone calling StopWatch / Disconnect
	// (e.g. Wails frontend HMR reload leaks — F-413).
	done chan struct{}
}

type logHandle struct {
	connID string
	cancel context.CancelFunc
	done   chan struct{}
}

func NewManager() *Manager {
	m := &Manager{
		conns:   make(map[string]*connection),
		watches: make(map[string]*watchHandle),
		logs:    make(map[string]*logHandle),
	}
	m.emit.Store(EventEmitter(func(string, any) {}))
	go m.sweepLoop()
	return m
}

// sweepLoop periodically prunes watchHandles / logHandles whose backing
// goroutine has exited but were never explicitly stopped (e.g. Wails
// frontend HMR reload in dev left the handles behind). Each handle's
// `done` channel is closed by runWatchLoop / runLogLoop when the
// goroutine returns; we use that as the exit signal (F-413).
func (m *Manager) sweepLoop() {
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()
	for range ticker.C {
		m.sweepOnce()
	}
}

func (m *Manager) sweepOnce() {
	m.mu.Lock()
	defer m.mu.Unlock()
	for id, wh := range m.watches {
		select {
		case <-wh.done:
			delete(m.watches, id)
			if c, ok := m.conns[wh.connID]; ok {
				delete(c.watches, id)
			}
		default:
		}
	}
	for id, lh := range m.logs {
		select {
		case <-lh.done:
			delete(m.logs, id)
		default:
		}
	}
}

func (m *Manager) SetEventEmitter(e EventEmitter) {
	m.emit.Store(e)
}

// cachedParseBytes returns a cached *Kubeconfig for the given raw YAML,
// or parses it on miss. Cache key is the sha256 of the raw bytes so
// identical kubeconfigs share a parse result (F-405).
func (m *Manager) cachedParseBytes(raw []byte) (*Kubeconfig, error) {
	key := sha256Hex(raw)
	if v, ok := m.kubeconfigCache.Load(key); ok {
		return v.(*Kubeconfig), nil
	}
	kc, err := ParseBytes(raw)
	if err != nil {
		return nil, err
	}
	actual, _ := m.kubeconfigCache.LoadOrStore(key, kc)
	return actual.(*Kubeconfig), nil
}

func sha256Hex(b []byte) string {
	sum := sha256.Sum256(b)
	const hex = "0123456789abcdef"
	out := make([]byte, len(sum)*2)
	for i, s := range sum {
		out[i*2] = hex[s>>4]
		out[i*2+1] = hex[s&0x0f]
	}
	return string(out)
}

// ListContexts parses the given kubeconfig YAML and returns context metadata.
func (m *Manager) ListContexts(kubeconfigYAML []byte) ([]ContextInfo, error) {
	kc, err := m.cachedParseBytes(kubeconfigYAML)
	if err != nil {
		return nil, err
	}
	return kc.ListContexts(), nil
}

func (m *Manager) Connect(_ context.Context, kubeconfigYAML []byte, contextName string) (string, error) {
	return m.ConnectWith(kubeconfigYAML, contextName, ConnectOptions{})
}

// ConnectOptions 是可选的建连参数：
//   - PresetID: 若非空则用作 connID，方便上层把 K8s 连接和外部资源（例如 SSH 隧道）
//     用同一个 key 关联；为空则内部生成 UUID。
//   - DialOverride: 透传给 BuildClientWithDial 的 dial 劫持。
//   - OnClose: Disconnect 时触发一次，用于拆隧道等外部资源清理。
type ConnectOptions struct {
	PresetID     string
	DialOverride DialFunc
	OnClose      func()
}

// ConnectWith 是 Connect 的可选参数版本，供 app.go 在需要 dial 劫持 / 生命周期回调时使用。
func (m *Manager) ConnectWith(kubeconfigYAML []byte, contextName string, opts ConnectOptions) (string, error) {
	kc, err := m.cachedParseBytes(kubeconfigYAML)
	if err != nil {
		return "", fmt.Errorf("kubeconfig: %w", err)
	}
	if contextName == "" {
		contextName = kc.CurrentContext
	}
	client, base, token, tlsCfg, err := BuildClientWithDial(kc, contextName, opts.DialOverride)
	if err != nil {
		return "", fmt.Errorf("build client: %w", err)
	}
	id := opts.PresetID
	if id == "" {
		id = uuid.New().String()
	}
	m.mu.Lock()
	if _, exists := m.conns[id]; exists {
		m.mu.Unlock()
		return "", fmt.Errorf("k8s connection %q already exists", id)
	}
	m.conns[id] = &connection{
		id:           id,
		client:       client,
		base:         base,
		token:        token,
		tlsConfig:    tlsCfg,
		dialOverride: opts.DialOverride,
		watches:      make(map[string]struct{}),
		onClose:      opts.OnClose,
	}
	m.mu.Unlock()
	return id, nil
}

func (m *Manager) Disconnect(connID string) {
	m.mu.Lock()
	conn, ok := m.conns[connID]
	if !ok {
		m.mu.Unlock()
		return
	}
	// 停掉所有属于本 conn 的 watch
	toStop := make([]string, 0, len(conn.watches))
	for wid := range conn.watches {
		toStop = append(toStop, wid)
	}
	// 停掉所有属于本 conn 的 log stream
	var logsToStop []string
	for sid, lh := range m.logs {
		if lh.connID == connID {
			logsToStop = append(logsToStop, sid)
		}
	}
	onClose := conn.onClose
	delete(m.conns, connID)
	m.mu.Unlock()

	for _, wid := range toStop {
		m.StopWatch(wid)
	}
	for _, sid := range logsToStop {
		m.StopLogStream(sid)
	}
	if onClose != nil {
		onClose()
	}
}

func (m *Manager) Request(ctx context.Context, connID, method, path string, body []byte, contentType string) (int, []byte, error) {
	m.mu.RLock()
	conn, ok := m.conns[connID]
	m.mu.RUnlock()
	if !ok {
		return 0, nil, fmt.Errorf("connection %q not found", connID)
	}
	return Do(ctx, conn.client, conn.base, method, path, body, contentType)
}

func (m *Manager) StartWatch(connID, path string) (string, error) {
	watchID := uuid.New().String()
	eventName := "k8s:watch:" + watchID
	endName := "k8s:watch-end:" + watchID
	reconnectingName := "k8s:watch-reconnecting:" + watchID
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan struct{})

	// 先注册再启流：避免 stream 立即 EOF 时 onEnd 抢在注册之前跑，导致句柄泄漏。
	m.mu.Lock()
	conn, ok := m.conns[connID]
	if !ok {
		m.mu.Unlock()
		cancel()
		return "", fmt.Errorf("connection %q not found", connID)
	}
	client := conn.client
	base := conn.base
	m.watches[watchID] = &watchHandle{connID: connID, cancel: cancel, done: done}
	conn.watches[watchID] = struct{}{}
	m.mu.Unlock()

	// emit is set once at startup and never changes; load via atomic
	// instead of grabbing the manager mutex (F-413).
	emit := m.emit.Load().(EventEmitter)

	err := startWatchStream(ctx, client, base, path,
		func(ev WatchEvent) { emit(eventName, ev) },
		func(err error) {
			// 终端结束（ctx 取消 / 干净 EOF）才走这里：emit 终态事件并清 map。
			payload := map[string]any{"error": ""}
			if err != nil {
				payload["error"] = err.Error()
			}
			emit(endName, payload)
			m.mu.Lock()
			delete(m.watches, watchID)
			if c, ok := m.conns[connID]; ok {
				delete(c.watches, watchID)
			}
			m.mu.Unlock()
		},
		func(err error) {
			// 重连退避前仅发轻量 reconnecting 事件，不动 maps — 防止 apiserver 抖动时
			// 每 1s/2s/4s/… 都抢 mutex + EventsEmit (F-404)。
			emit(reconnectingName, map[string]any{"error": err.Error()})
		},
		done,
	)
	if err != nil {
		m.mu.Lock()
		delete(m.watches, watchID)
		if c, ok := m.conns[connID]; ok {
			delete(c.watches, watchID)
		}
		m.mu.Unlock()
		cancel()
		return "", err
	}
	return watchID, nil
}

func (m *Manager) StopWatch(watchID string) {
	m.mu.Lock()
	wh, ok := m.watches[watchID]
	if !ok {
		m.mu.Unlock()
		return
	}
	delete(m.watches, watchID)
	if c, ok := m.conns[wh.connID]; ok {
		delete(c.watches, watchID)
	}
	m.mu.Unlock()
	wh.cancel()
}

func (m *Manager) StartLogStream(connID, ns, pod, container string, tailLines int, timestamps, previous bool) (string, error) {
	streamID := uuid.New().String()
	eventName := "k8s:log:" + streamID
	endName := "k8s:log-end:" + streamID
	reconnectingName := "k8s:log-reconnecting:" + streamID
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan struct{})

	m.mu.Lock()
	conn, ok := m.conns[connID]
	if !ok {
		m.mu.Unlock()
		cancel()
		return "", fmt.Errorf("connection %q not found", connID)
	}
	client, base := conn.client, conn.base
	m.logs[streamID] = &logHandle{connID: connID, cancel: cancel, done: done}
	m.mu.Unlock()

	// emit is set once at startup and never changes; load via atomic
	// instead of grabbing the manager mutex (F-413).
	emit := m.emit.Load().(EventEmitter)

	path := buildLogPath(ns, pod, container, tailLines, timestamps, previous)
	err := startLogStream(ctx, client, base, path,
		func(line string) { emit(eventName, line) },
		func(err error) {
			payload := map[string]any{"error": ""}
			if err != nil {
				payload["error"] = err.Error()
			}
			emit(endName, payload)
			m.mu.Lock()
			delete(m.logs, streamID)
			m.mu.Unlock()
		},
		func(err error) {
			emit(reconnectingName, map[string]any{"error": err.Error()})
		},
		done,
	)
	if err != nil {
		m.mu.Lock()
		delete(m.logs, streamID)
		m.mu.Unlock()
		cancel()
		return "", err
	}
	return streamID, nil
}

func (m *Manager) StopLogStream(streamID string) {
	m.mu.Lock()
	lh, ok := m.logs[streamID]
	if !ok {
		m.mu.Unlock()
		return
	}
	delete(m.logs, streamID)
	m.mu.Unlock()
	lh.cancel()
}

// DialExec 打开一个到 Pod exec 端点的 WebSocket，复用连接的 TLS/auth/dial 配置。
// cols/rows 供上层建立终端后通过 resize 通道下发，这里仅负责建连。
func (m *Manager) DialExec(connID, ns, pod, container string, cols, rows int) (*websocket.Conn, error) {
	m.mu.RLock()
	conn, ok := m.conns[connID]
	m.mu.RUnlock()
	if !ok {
		return nil, fmt.Errorf("connection %q not found", connID)
	}

	u, err := url.Parse(conn.base)
	if err != nil {
		return nil, err
	}
	if u.Scheme == "https" {
		u.Scheme = "wss"
	} else {
		u.Scheme = "ws"
	}
	u.Path = fmt.Sprintf("/api/v1/namespaces/%s/pods/%s/exec", ns, pod)
	// k9s 风格的 shell 自动探测：优先 bash，其次 ash，最后退回 /bin/sh。
	shellCmd := "exec $(command -v bash || command -v ash || echo /bin/sh)"
	q := url.Values{}
	q.Set("container", container)
	q.Set("stdin", "true")
	q.Set("stdout", "true")
	q.Set("stderr", "true")
	q.Set("tty", "true")
	q.Add("command", "/bin/sh")
	q.Add("command", "-c")
	q.Add("command", shellCmd)
	u.RawQuery = q.Encode()

	dialer := websocket.Dialer{
		TLSClientConfig: conn.tlsConfig,
		Subprotocols:    []string{"v4.channel.k8s.io"},
	}
	if conn.dialOverride != nil {
		dialer.NetDialContext = conn.dialOverride
	}
	header := http.Header{}
	if conn.token != "" {
		header.Set("Authorization", "Bearer "+conn.token)
	}
	c, _, err := dialer.Dial(u.String(), header)
	if err != nil {
		return nil, fmt.Errorf("exec dial: %w", err)
	}
	return c, nil
}
