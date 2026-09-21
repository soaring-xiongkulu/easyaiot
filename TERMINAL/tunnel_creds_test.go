package main

// Regression coverage for the tunnel credential prompt path (issue #844): a
// tunnel whose exit SSH connection has no saved password must be startable with
// inline credentials supplied by the frontend's credential dialog.

import (
	"net"
	"testing"

	"easyaiot/terminal/backend/session"
	"easyaiot/terminal/backend/store"
)

// TestWithExitCredOverride locks the override semantics: inline user/password
// fill only the exit connection's EMPTY fields, never overwrite saved values,
// and are not applied to non-exit hops. Empty inline credentials return the
// resolver untouched.
func TestWithExitCredOverride(t *testing.T) {
	conns := map[string]session.ConnectionConfig{
		"exit": {ID: "exit", Host: "h1", User: "exit-user", Password: ""},
		"mid":  {ID: "mid", Host: "h2", User: "", Password: ""},
	}
	base := func(id string) (session.ConnectionConfig, bool) {
		c, ok := conns[id]
		return c, ok
	}

	// Empty inline credentials: resolver returned as-is.
	if got := withExitCredOverride(base, "exit", "", ""); got == nil {
		t.Fatal("empty override: expected the original resolver back")
	}

	resolve := withExitCredOverride(base, "exit", "inline-user", "inline-pw")

	// Exit hop: empty password filled, saved user kept.
	c, ok := resolve("exit")
	if !ok || c.User != "exit-user" || c.Password != "inline-pw" {
		t.Fatalf("exit hop: got user=%q password=%q ok=%v", c.User, c.Password, ok)
	}

	// Non-exit hop: untouched.
	c, ok = resolve("mid")
	if !ok || c.User != "" || c.Password != "" {
		t.Fatalf("non-exit hop: got user=%q password=%q ok=%v", c.User, c.Password, ok)
	}

	// Unknown id still reports not-found.
	if _, ok = resolve("nope"); ok {
		t.Fatal("unknown id: expected not found")
	}
}

// TestApp_StartTunnel_InlineCredentials drives App.StartTunnel end to end: the
// exit connection is saved without a password, so starting the tunnel fails on
// ssh auth; passing the password inline (as the credential dialog would) makes
// it run.
func TestApp_StartTunnel_InlineCredentials(t *testing.T) {
	targetPort := unreachableLocalPort(t)
	sshPort := startFakeJumpSSHD(t)

	cs, err := store.NewConnectionStore(t.TempDir())
	if err != nil {
		t.Fatalf("connection store: %v", err)
	}
	cs.SetPasswordStore(stubPasswordStore{})
	// No saved password — the case the credential prompt exists for.
	if err := cs.Save(session.ConnectionStoreData{
		Connections: []session.ConnectionConfig{{
			ID:       "jump-1",
			Type:     "ssh",
			Host:     "127.0.0.1",
			Port:     sshPort,
			User:     "jump",
			AuthType: "password",
		}},
	}); err != nil {
		t.Fatalf("save jump connection: %v", err)
	}

	ts := store.NewTunnelStore(t.TempDir())
	tunnel := session.Tunnel{
		ID:           "tun-1",
		Name:         "regression",
		Mode:         session.TunnelLocal,
		SSHConnID:    "jump-1",
		ListenPort:   freeLocalPort(t),
		TargetHost:   "127.0.0.1",
		TargetPort:   targetPort,
	}
	if err := ts.Save(session.TunnelStoreData{Version: 1, Tunnels: []session.Tunnel{tunnel}}); err != nil {
		t.Fatalf("save tunnel: %v", err)
	}

	a := NewApp("")
	a.connectionStore = cs
	a.tunnelService = session.NewTunnelService()
	a.tunnelStore = ts

	// Guard: without inline credentials the ssh handshake fails.
	st, err := a.StartTunnel("tun-1", "", "")
	if err != nil {
		t.Fatalf("no inline creds: unexpected error: %v", err)
	}
	if st.Status != session.TunnelError {
		t.Fatalf("no inline creds: expected error state, got %q (%s)", st.Status, st.Error)
	}
	a.StopTunnel("tun-1")

	// With the password supplied inline the tunnel comes up.
	st, err = a.StartTunnel("tun-1", "", "jump-pw")
	if err != nil {
		t.Fatalf("inline creds: unexpected error: %v", err)
	}
	if st.Status != session.TunnelRunning {
		t.Fatalf("inline creds: expected running state, got %q (%s)", st.Status, st.Error)
	}
	a.StopTunnel("tun-1")
}

// freeLocalPort reserves an ephemeral loopback port for the tunnel's local
// listener and releases it immediately.
func freeLocalPort(t *testing.T) int {
	t.Helper()
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("reserve port: %v", err)
	}
	port := ln.Addr().(*net.TCPAddr).Port
	ln.Close()
	return port
}
