package main

import (
	"context"
	"fmt"
	"net"
	"os"
	"path/filepath"

	"github.com/google/uuid"

	"easyaiot/terminal/backend/container"
	"easyaiot/terminal/backend/k8s"
	"easyaiot/terminal/backend/session"
)

// K8sContextInfo 是前端可见的 context 元信息。
type K8sContextInfo = k8s.ContextInfo

// K8sListContexts 解析给定 kubeconfig 内容并返回 context 列表。
// source 为文件路径或 YAML 内联字符串；根据 sourceIsPath 区分。
func (a *App) K8sListContexts(source string, sourceIsPath bool) ([]K8sContextInfo, error) {
	raw, err := readKubeconfigSource(source, sourceIsPath)
	if err != nil {
		return nil, err
	}
	return a.k8sManager.ListContexts(raw)
}

// K8sConnect 建立到 kubeconfig 中指定 context 的连接，返回 connID。
// 若 tunnelSSHConnID 非空，会先起一条 SSH 隧道，把到 apiserver 的 TCP 拨号
// 劫持到本地 loopback；TLS 校验仍按 kubeconfig 里的原 hostname 走。
func (a *App) K8sConnect(source string, sourceIsPath bool, contextName string,
	tunnelSSHConnID, tunnelSSHUser, tunnelSSHPassword string) (string, error) {
	raw, err := readKubeconfigSource(source, sourceIsPath)
	if err != nil {
		return "", err
	}

	if tunnelSSHConnID == "" {
		return a.k8sManager.Connect(a.ctx, raw, contextName)
	}

	// ── SSH Tunnel for K8s (reuses the shared jump-host tunnel logic) ──
	// 从 kubeconfig 解出 apiserver host/port 作为隧道目标
	kc, err := k8s.ParseBytes(raw)
	if err != nil {
		return "", fmt.Errorf("kubeconfig: %w", err)
	}
	ctxName := contextName
	if ctxName == "" {
		ctxName = kc.CurrentContext
	}
	ctxEntry, ok := kc.Contexts[ctxName]
	if !ok {
		return "", fmt.Errorf("context %q not found", ctxName)
	}
	cluster, ok := kc.Clusters[ctxEntry.Cluster]
	if !ok {
		return "", fmt.Errorf("cluster %q not found", ctxEntry.Cluster)
	}
	targetHost, targetPort, err := k8s.ParseServerAddr(cluster.Server)
	if err != nil {
		return "", fmt.Errorf("parse apiserver url: %w", err)
	}

	// 用同一个 key 既做 K8s connID 也做 TunnelService 的 sessionID，
	// 方便 Disconnect 时的 onClose 回调直接 Stop 同名隧道。
	tunnelKey := uuid.New().String()
	tunnelConfig := session.ConnectionConfig{
		TunnelSSHConnID:   tunnelSSHConnID,
		TunnelSSHUser:     tunnelSSHUser,
		TunnelSSHPassword: tunnelSSHPassword,
		Host:              targetHost,
		Port:              targetPort,
	}
	// 与其它连接类型共享同一段隧道逻辑：按认证类型解析跳板机凭据并拉起隧道。
	if err := a.setupJumpHostTunnel(tunnelKey, "k8s", &tunnelConfig); err != nil {
		return "", err
	}
	localPort := tunnelConfig.Port

	var dialer net.Dialer
	dialOverride := func(ctx context.Context, _ /*network*/, _ /*addr*/ string) (net.Conn, error) {
		return dialer.DialContext(ctx, "tcp", k8s.LocalAddr(localPort))
	}
	onClose := func() {
		a.tunnelService.Stop(tunnelKey)
	}

	connID, err := a.k8sManager.ConnectWith(raw, contextName, k8s.ConnectOptions{
		PresetID:     tunnelKey,
		DialOverride: dialOverride,
		OnClose:      onClose,
	})
	if err != nil {
		a.tunnelService.Stop(tunnelKey)
		return "", err
	}
	return connID, nil
}

func (a *App) K8sDisconnect(connID string) {
	a.k8sManager.Disconnect(connID)
}

// K8sResponse 是前端可见的 REST 响应。Body 为 JSON 原文字符串。
type K8sResponse struct {
	Status int    `json:"status"`
	Body   string `json:"body"`
}

func (a *App) K8sRequest(connID, method, path, body, contentType string) (K8sResponse, error) {
	status, out, err := a.k8sManager.Request(a.ctx, connID, method, path, []byte(body), contentType)
	if err != nil {
		return K8sResponse{}, err
	}
	return K8sResponse{Status: status, Body: string(out)}, nil
}

func (a *App) K8sStartWatch(connID, path string) (string, error) {
	return a.k8sManager.StartWatch(connID, path)
}

func (a *App) K8sStopWatch(watchID string) {
	a.k8sManager.StopWatch(watchID)
}

func (a *App) K8sStartLogStream(connID, namespace, pod, container string, tailLines int, timestamps, previous bool) (string, error) {
	return a.k8sManager.StartLogStream(connID, namespace, pod, container, tailLines, timestamps, previous)
}

func (a *App) K8sStopLogStream(streamID string) {
	a.k8sManager.StopLogStream(streamID)
}

func (a *App) K8sExecSession(connID, namespace, pod, container string) (*session.SessionInfo, error) {
	if a.k8sManager == nil {
		return nil, fmt.Errorf("k8s manager not initialized")
	}
	// initial size fallback; real size arrives via Resize after the frontend mounts xterm
	wsConn, err := a.k8sManager.DialExec(connID, namespace, pod, container, 80, 24)
	if err != nil {
		return nil, err
	}
	id := uuid.New().String()
	sess := session.NewK8sExecSession(id, wsConn)
	sess.SetOnDataCallback(func(data []byte) {
		a.emit("session:data", map[string]interface{}{
			"id":   sess.ID(),
			"data": string(data),
		})
	})
	sess.SetOnStatusChangeCallback(func(status session.SessionStatus) {
		a.emit("session:status", map[string]interface{}{
			"id":     sess.ID(),
			"status": status,
		})
	})
	a.sessionManager.Add(sess)
	return &session.SessionInfo{ID: id, Type: "k8s-exec", Title: pod, Status: session.StatusConnected}, nil
}

func readKubeconfigSource(source string, sourceIsPath bool) ([]byte, error) {
	if !sourceIsPath {
		return []byte(source), nil
	}
	if len(source) > 1 && source[0] == '~' {
		home, err := os.UserHomeDir()
		if err == nil {
			source = filepath.Join(home, source[1:])
		}
	}
	return os.ReadFile(source)
}

// ContainerConnect 打开容器连接：解析配置、按 transport 建 Local 或 SSH runner。
// SSH 传输时若被引用连接配了跳板机（TunnelSSHConnID），先起本地转发隧道，
// 与 CreateSession 的单层隧道行为一致。
func (a *App) ContainerConnect(connectionID string) error {
	if a.containerManager == nil || a.connectionStore == nil {
		return fmt.Errorf("container manager not initialized")
	}
	data, err := a.connectionStore.Load()
	if err != nil {
		return err
	}
	var cfg *session.ConnectionConfig
	for _, c := range data.Connections {
		if c.ID == connectionID {
			cfg = &c
			break
		}
	}
	if cfg == nil {
		return fmt.Errorf("connection not found: %s", connectionID)
	}
	if cfg.Type != "container" {
		return fmt.Errorf("connection %s is not a container connection", connectionID)
	}
	rt := container.Runtime(cfg.ContainerRuntime)

	if cfg.ContainerTransport == "local" {
		return a.containerManager.ConnectLocal(connectionID, rt, "")
	}

	var sshCfg *session.ConnectionConfig
	for _, c := range data.Connections {
		if c.ID == cfg.ContainerSSHConnID {
			sshCfg = &c
			break
		}
	}
	if sshCfg == nil {
		return fmt.Errorf("referenced SSH connection missing: %s", cfg.ContainerSSHConnID)
	}

	// Resolve an identity reference into a concrete password/key config
	// before handing the SSH runner its connection config.
	if sshCfg.AuthType == "identity" {
		m, err := a.materializeIdentity(*sshCfg)
		if err != nil {
			return err
		}
		sshCfg = &m
	}

	// 跳板机：复用统一的 setupJumpHostTunnel（与其它连接类型同一段逻辑）。
	// 它会按认证类型解析被引用跳板机连接的凭据并拉起隧道，同时改写
	// sshCfg.Host/Port 指向本地监听口。
	hasTunnel := sshCfg.TunnelSSHConnID != ""
	if hasTunnel {
		if err := a.setupJumpHostTunnel(connectionID, "container", sshCfg); err != nil {
			return err
		}
	}
	if err := a.containerManager.ConnectSSH(connectionID, rt, "", *sshCfg); err != nil {
		if hasTunnel && a.tunnelService != nil {
			a.tunnelService.Stop(connectionID) // 与其它连接一致：连接失败时回收隧道
		}
		return err
	}
	return nil
}

func (a *App) ContainerDisconnect(connectionID string) {
	a.containerManager.Disconnect(connectionID)
	if a.tunnelService != nil {
		a.tunnelService.Stop(connectionID) // 无同名隧道时为 no-op
	}
}

func (a *App) ContainerList(connectionID string) ([]container.Container, error) {
	p, err := a.containerManager.Provider(connectionID)
	if err != nil {
		return nil, err
	}
	return p.List(a.ctx)
}

func (a *App) ContainerInspect(connectionID, containerID string) (container.InspectResult, error) {
	p, err := a.containerManager.Provider(connectionID)
	if err != nil {
		return container.InspectResult{}, err
	}
	return p.Inspect(a.ctx, containerID)
}

func (a *App) ContainerAction(connectionID, containerID, action string) error {
	p, err := a.containerManager.Provider(connectionID)
	if err != nil {
		return err
	}
	return p.Action(a.ctx, containerID, action)
}

func (a *App) ContainerRename(connectionID, containerID, newName string) error {
	p, err := a.containerManager.Provider(connectionID)
	if err != nil {
		return err
	}
	return p.Rename(a.ctx, containerID, newName)
}

func (a *App) ContainerStats(connectionID string) ([]container.Stats, error) {
	p, err := a.containerManager.Provider(connectionID)
	if err != nil {
		return nil, err
	}
	return p.Stats(a.ctx)
}

func (a *App) ContainerImages(connectionID string) ([]container.Image, error) {
	p, err := a.containerManager.Provider(connectionID)
	if err != nil {
		return nil, err
	}
	return p.Images(a.ctx)
}

func (a *App) ContainerRemoveImage(connectionID, imageID string) error {
	p, err := a.containerManager.Provider(connectionID)
	if err != nil {
		return err
	}
	return p.RemoveImage(a.ctx, imageID)
}

func (a *App) ContainerCreate(connectionID string, opts container.CreateOptions) error {
	p, err := a.containerManager.Provider(connectionID)
	if err != nil {
		return err
	}
	return p.Create(a.ctx, opts)
}

func (a *App) ContainerNamespaces(connectionID string) ([]string, error) {
	p, err := a.containerManager.Provider(connectionID)
	if err != nil {
		return nil, err
	}
	return p.Namespaces(a.ctx)
}

func (a *App) ContainerSetNamespace(connectionID, ns string) error {
	return a.containerManager.SetNamespace(connectionID, ns)
}

func (a *App) ContainerStartLogs(connectionID, containerID string, tail int, timestamps bool) (string, error) {
	return a.containerManager.StartLogStream(connectionID, containerID, tail, timestamps)
}

func (a *App) ContainerStartPull(connectionID, image string) (string, error) {
	return a.containerManager.StartPullStream(connectionID, image)
}

func (a *App) ContainerStopStream(streamID string) {
	a.containerManager.StopStream(streamID)
}

func (a *App) ContainerExecSession(connectionID, containerID, shell string) (*session.SessionInfo, error) {
	if a.containerManager == nil {
		return nil, fmt.Errorf("container manager not initialized")
	}
	// initial size fallback; real size arrives via Resize after the frontend mounts xterm
	pty, err := a.containerManager.Exec(connectionID, containerID, shell, 80, 24)
	if err != nil {
		return nil, err
	}
	id := uuid.New().String()
	sess := session.NewContainerExecSession(id, pty)
	sess.SetOnDataCallback(func(data []byte) {
		a.emit("session:data", map[string]interface{}{
			"id":   sess.ID(),
			"data": string(data),
		})
	})
	sess.SetOnStatusChangeCallback(func(status session.SessionStatus) {
		a.emit("session:status", map[string]interface{}{
			"id":     sess.ID(),
			"status": status,
		})
	})
	a.sessionManager.Add(sess)
	return &session.SessionInfo{ID: id, Type: "container-exec", Title: containerID, Status: session.StatusConnected}, nil
}
