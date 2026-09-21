package main

// TestConnection implements the frontend's "test connection" button (issue #377).
// It probes whether a connection config can connect / authenticate WITHOUT
// opening a persistent session. Session-owned protocols (ssh, telnet, ftp, s3,
// webdav, smb, redis, mongodb, database) are delegated to session.ProbeConnection
// after identity/proxy references are materialized. k8s and container need the
// app's managers (and the store for referenced SSH connections / k8s tunnels),
// so they are handled here directly.

import (
	"context"
	"fmt"
	"net"
	"time"

	"github.com/google/uuid"

	"easyaiot/terminal/backend/container"
	"easyaiot/terminal/backend/k8s"
	"easyaiot/terminal/backend/session"
)

// TestConnection returns a short human-readable description on success, or a
// readable error (never echoing the password) on failure.
func (a *App) TestConnection(config session.ConnectionConfig) (string, error) {
	// Defensive: a new-connection form snapshot may carry an empty password even
	// when the OS keychain already has one (mirrors CreateSession/SessionStart).
	if config.Password == "" && config.ID != "" && a.connectionStore != nil {
		if pw, err := a.connectionStore.EnsurePassword(config.ID); err == nil && pw != "" {
			config.Password = pw
		}
	}
	// Resolve identity / proxy references for the protocols that consume them
	// (ssh-family). No-ops when not configured.
	mc, err := a.materializeIdentity(config)
	if err != nil {
		return "", err
	}
	mc, err = a.materializeProxy(mc)
	if err != nil {
		return "", err
	}

	switch mc.Type {
	case "k8s":
		return a.testK8sConnection(mc)
	case "container":
		return a.testContainerConnection(mc)
	default:
		// Honor the jump-host tunnel exactly like a real session connect
		// (CreateSession): establish the local forward first, point the
		// probe at the listener, then tear the tunnel down when done.
		if mc.TunnelSSHConnID != "" {
			key := uuid.New().String()
			if err := a.setupJumpHostTunnel(key, mc.Type, &mc); err != nil {
				return "", err
			}
			defer a.tunnelService.Stop(key)
		}
		return session.ProbeConnection(mc)
	}
}

// testContainerConnection probes the container engine reachability. Reuses the
// same building blocks as ContainerConnect (NewProvider + ValidateRuntime), but
// without registering a persistent connection. For SSH transport it loads the
// referenced SSH connection from the store, materializes its identity, dials,
// and runs the runtime probe on the remote host.
func (a *App) testContainerConnection(config session.ConnectionConfig) (string, error) {
	if a.connectionStore == nil {
		return "", fmt.Errorf("connection store not initialized")
	}
	rt := container.Runtime(config.ContainerRuntime)

	if config.ContainerTransport == "local" {
		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
		defer cancel()
		runner := container.NewLocalRunner()
		if err := container.ValidateRuntime(ctx, rt, runner); err != nil {
			return "", err
		}
		return fmt.Sprintf("container: %s engine reachable locally", rt), nil
	}

	// SSH transport: resolve the referenced SSH connection.
	if config.ContainerSSHConnID == "" {
		return "", fmt.Errorf("referenced SSH connection missing")
	}
	data, err := a.connectionStore.Load()
	if err != nil {
		return "", err
	}
	var sshCfg *session.ConnectionConfig
	for _, c := range data.Connections {
		if c.ID == config.ContainerSSHConnID {
			sshCfg = &c
			break
		}
	}
	if sshCfg == nil {
		return "", fmt.Errorf("referenced SSH connection not found: %s", config.ContainerSSHConnID)
	}
	if sshCfg.AuthType == "identity" {
		m, err := a.materializeIdentity(*sshCfg)
		if err != nil {
			return "", err
		}
		sshCfg = &m
	}

	// Mirror ContainerConnect: honor the referenced connection's own jump-host
	// tunnel before dialing through it.
	if sshCfg.TunnelSSHConnID != "" && a.tunnelService != nil {
		var tunnelCfg *session.ConnectionConfig
		for _, c := range data.Connections {
			if c.ID == sshCfg.TunnelSSHConnID {
				tunnelCfg = &c
				break
			}
		}
		if tunnelCfg == nil {
			return "", fmt.Errorf("tunnel SSH connection not found: %s", sshCfg.TunnelSSHConnID)
		}
		if tunnelCfg.AuthType == "identity" {
			m, err := a.materializeIdentity(*tunnelCfg)
			if err != nil {
				return "", err
			}
			tunnelCfg = &m
		}
		key := uuid.New().String()
		localPort, err := a.tunnelService.Start(key, *tunnelCfg, sshCfg.Host, sshCfg.Port, nil)
		if err != nil {
			return "", fmt.Errorf("tunnel start: %w", err)
		}
		defer a.tunnelService.Stop(key)
		sshCfg.Host = "127.0.0.1"
		sshCfg.Port = localPort
	}

	client, err := session.DialSSHClient(*sshCfg)
	if err != nil {
		return "", fmt.Errorf("container over ssh: %w", err)
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	runner := container.NewSSHRunner(client)
	if err := container.ValidateRuntime(ctx, rt, runner); err != nil {
		return "", err
	}
	return fmt.Sprintf("container: %s engine reachable via ssh %s@%s", rt, sshCfg.User, sshCfg.Host), nil
}

// testK8sConnection probes the kubernetes apiserver by building a client from
// the kubeconfig (lazy, no I/O) and issuing a GET /version. Reuses ConnectWith /
// Request / Disconnect so auth, tunnel dial override and TLS all behave exactly
// like a real K8sConnect. An incorrect cluster name or credentials surface as
// a non-2xx status or a dial error.
func (a *App) testK8sConnection(config session.ConnectionConfig) (string, error) {
	if a.k8sManager == nil {
		return "", fmt.Errorf("k8s manager not initialized")
	}

	sourceIsPath := config.K8sConfigInline == ""
	source := config.K8sConfigInline
	if sourceIsPath {
		source = config.K8sConfigPath
	}
	raw, err := readKubeconfigSource(source, sourceIsPath)
	if err != nil {
		return "", err
	}
	contextName := config.K8sContext
	tunnelID := config.TunnelSSHConnID

	if tunnelID == "" {
		connID, err := a.k8sManager.ConnectWith(raw, contextName, k8s.ConnectOptions{})
		if err != nil {
			return "", err
		}
		defer a.k8sManager.Disconnect(connID)
		return a.probeK8sAPIServer(connID, contextName)
	}

	// SSH tunnel for k8s (mirrors K8sConnect).
	if a.tunnelService == nil || a.connectionStore == nil {
		return "", fmt.Errorf("tunnel service or connection store not initialized")
	}
	data, err := a.connectionStore.Load()
	if err != nil {
		return "", fmt.Errorf("load connections for tunnel: %w", err)
	}
	var tunnelSSHConfig *session.ConnectionConfig
	for _, c := range data.Connections {
		if c.ID == tunnelID {
			tunnelSSHConfig = &c
			break
		}
	}
	if tunnelSSHConfig == nil {
		return "", fmt.Errorf("tunnel SSH connection not found: %s", tunnelID)
	}
	if tunnelSSHConfig.AuthType == "identity" {
		m, err := a.materializeIdentity(*tunnelSSHConfig)
		if err != nil {
			return "", err
		}
		tunnelSSHConfig = &m
	}

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

	tunnelKey := uuid.New().String()
	localPort, err := a.tunnelService.Start(tunnelKey, *tunnelSSHConfig, targetHost, targetPort, nil)
	if err != nil {
		return "", fmt.Errorf("tunnel start: %w", err)
	}

	var dialer net.Dialer
	dialOverride := func(ctx context.Context, _, _ string) (net.Conn, error) {
		return dialer.DialContext(ctx, "tcp", k8s.LocalAddr(localPort))
	}
	onClose := func() { a.tunnelService.Stop(tunnelKey) }
	connID, err := a.k8sManager.ConnectWith(raw, contextName, k8s.ConnectOptions{
		PresetID:     tunnelKey,
		DialOverride: dialOverride,
		OnClose:      onClose,
	})
	if err != nil {
		a.tunnelService.Stop(tunnelKey)
		return "", err
	}
	defer a.k8sManager.Disconnect(connID)
	return a.probeK8sAPIServer(connID, contextName)
}

// probeK8sAPIServer issues a GET /version on an existing k8s connection and maps
// the result to a readable success/failure.
func (a *App) probeK8sAPIServer(connID, contextName string) (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	status, _, err := a.k8sManager.Request(ctx, connID, "GET", "/version", nil, "")
	if err != nil {
		return "", fmt.Errorf("k8s apiserver: %w", err)
	}
	if status >= 400 {
		label := contextName
		if label == "" {
			label = "current context"
		}
		return "", fmt.Errorf("k8s apiserver (%s) returned HTTP %d", label, status)
	}
	label := contextName
	if label == "" {
		label = "current context"
	}
	return fmt.Sprintf("k8s: connected to apiserver (context %q)", label), nil
}