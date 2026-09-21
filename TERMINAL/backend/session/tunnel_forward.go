package session

import (
	"encoding/base64"
	"encoding/binary"
	"fmt"
	"io"
	"net"
	"strconv"
	"strings"
	"time"

	"golang.org/x/crypto/ssh"
	"golang.org/x/net/proxy"
)

// ConnResolver resolves a saved SSH connection by its ID. app.go supplies one
// backed by the connection store so the tunnel layer can look up the exit
// connection and recurse its jump hosts without importing the store package.
type ConnResolver func(id string) (ConnectionConfig, bool)

// userTunnelEntry is one running user-configured tunnel: the local (or remote)
// listener plus every ssh.Client in its chain, so Stop can tear the whole thing
// down.
type userTunnelEntry struct {
	listener net.Listener
	clients  []*ssh.Client // chain order; last is the exit
	quit     chan struct{}
}

// StartTunnel brings a user-configured tunnel up: it dials the proxy chain
// (recursing the exit connection's own jump hosts, optionally entering through
// an upstream SOCKS5/HTTP proxy) and starts the listener for the tunnel's mode.
// It returns the running state; on failure the returned state carries the error
// and nothing is left running.
func (ts *TunnelService) StartTunnel(t Tunnel, resolve ConnResolver) TunnelState {
	ts.mu.Lock()
	if _, exists := ts.userTunnels[t.ID]; exists {
		ts.mu.Unlock()
		return ts.setState(t.ID, TunnelState{ID: t.ID, Status: TunnelRunning})
	}
	ts.mu.Unlock()

	chain, err := buildHopChain(t.SSHConnID, resolve)
	if err != nil {
		return ts.setState(t.ID, TunnelState{ID: t.ID, Status: TunnelError, Error: err.Error()})
	}

	exit, clients, err := ts.dialChain(chain, t.Upstream)
	if err != nil {
		return ts.setState(t.ID, TunnelState{ID: t.ID, Status: TunnelError, Error: err.Error()})
	}

	quit := make(chan struct{})
	listener, err := ts.startListener(t, exit, quit)
	if err != nil {
		closeClients(clients)
		return ts.setState(t.ID, TunnelState{ID: t.ID, Status: TunnelError, Error: err.Error()})
	}

	ts.mu.Lock()
	ts.userTunnels[t.ID] = &userTunnelEntry{listener: listener, clients: clients, quit: quit}
	ts.mu.Unlock()

	// Watch the exit client: keepalive actively closes a dead chain, and Wait
	// unblocks when the connection drops, so we can flip the tunnel to error.
	go tunnelKeepAlive(exit, quit, "tunnel="+t.ID)
	go func() {
		exit.Wait()
		select {
		case <-quit:
			// Stopped by the user; state already handled by StopTunnel.
		default:
			ts.StopTunnel(t.ID)
			ts.setState(t.ID, TunnelState{ID: t.ID, Status: TunnelError, Error: "ssh chain disconnected"})
		}
	}()

	port := listener.Addr().(*net.TCPAddr).Port
	return ts.setState(t.ID, TunnelState{ID: t.ID, Status: TunnelRunning, LocalPort: port})
}

// startListener opens the listener appropriate to the tunnel's mode and starts
// its accept loop. For local/dynamic the listener is local (net.Listen); for
// remote it lives on the exit host (exit.Listen).
func (ts *TunnelService) startListener(t Tunnel, exit *ssh.Client, quit chan struct{}) (net.Listener, error) {
	bindHost := t.ListenHost
	if bindHost == "" {
		bindHost = "127.0.0.1"
	}
	bindAddr := net.JoinHostPort(bindHost, strconv.Itoa(t.ListenPort))

	switch t.Mode {
	case TunnelLocal:
		ln, err := net.Listen("tcp", bindAddr)
		if err != nil {
			return nil, fmt.Errorf("tunnel listen: %w", err)
		}
		target := net.JoinHostPort(t.TargetHost, strconv.Itoa(t.TargetPort))
		go acceptLoop(ln, quit, func(c net.Conn) {
			remote, err := exit.Dial("tcp", target)
			if err != nil {
				c.Close()
				return
			}
			pipe(c, remote)
		})
		return ln, nil

	case TunnelDynamic:
		ln, err := net.Listen("tcp", bindAddr)
		if err != nil {
			return nil, fmt.Errorf("tunnel listen: %w", err)
		}
		go acceptLoop(ln, quit, func(c net.Conn) {
			target, err := socks5Handshake(c)
			if err != nil {
				c.Close()
				return
			}
			remote, err := exit.Dial("tcp", target)
			if err != nil {
				socks5Reply(c, socks5HostUnreachable)
				c.Close()
				return
			}
			if err := socks5Reply(c, socks5Success); err != nil {
				remote.Close()
				c.Close()
				return
			}
			pipe(c, remote)
		})
		return ln, nil

	case TunnelRemote:
		ln, err := exit.Listen("tcp", bindAddr)
		if err != nil {
			// The common failure is the remote port already being bound — a
			// stale sshd session that never tore its forward down, or another
			// process on the server — so point the user there.
			return nil, fmt.Errorf("tunnel remote listen: %w (check whether the port is already in use on the server by a stale session or another process)", err)
		}
		target := net.JoinHostPort(t.TargetHost, strconv.Itoa(t.TargetPort))
		go acceptLoop(ln, quit, func(c net.Conn) {
			local, err := net.Dial("tcp", target)
			if err != nil {
				c.Close()
				return
			}
			pipe(c, local)
		})
		return ln, nil

	default:
		return nil, fmt.Errorf("unknown tunnel mode %q", t.Mode)
	}
}

// TestTunnel validates a tunnel configuration without persisting or
// registering it: the tunnel is brought up through the same path as StartTunnel
// (SSH chain dial + auth, then listener bind — for remote mode that also proves
// the port is free on the server) under a throwaway ID, and torn down
// immediately once the listener is bound. Running means everything bound;
// Error carries the reason. Throwaway-ID states never reach the UI (see
// setState), so failures are reported only through the return value.
func (ts *TunnelService) TestTunnel(t Tunnel, resolve ConnResolver) TunnelState {
	t.ID = fmt.Sprintf("__test__%d", time.Now().UnixNano())
	st := ts.StartTunnel(t, resolve)
	ts.StopTunnel(t.ID)
	return st
}

// StopTunnel tears down a running user tunnel (listener + whole ssh.Client
// chain). No-op if the tunnel isn't running.
func (ts *TunnelService) StopTunnel(id string) {
	ts.mu.Lock()
	entry, ok := ts.userTunnels[id]
	if ok {
		delete(ts.userTunnels, id)
	}
	ts.mu.Unlock()
	if !ok {
		return
	}
	close(entry.quit)
	entry.listener.Close()
	closeClients(entry.clients)
	ts.setState(id, TunnelState{ID: id, Status: TunnelStopped})
}

// buildHopChain resolves the exit connection and recurses its jump host
// (ConnectionConfig.TunnelSSHConnID) into an ordered chain, outermost first:
// [firstHop, …, exit]. A connection with no jump host yields a single-element
// chain (direct to the exit). Loops are rejected.
func buildHopChain(exitID string, resolve ConnResolver) ([]ConnectionConfig, error) {
	if exitID == "" {
		return nil, fmt.Errorf("no SSH connection selected")
	}
	var chain []ConnectionConfig
	seen := make(map[string]bool)
	for id := exitID; id != ""; {
		if seen[id] {
			return nil, fmt.Errorf("proxy chain has a loop at connection %s", id)
		}
		seen[id] = true
		cfg, ok := resolve(id)
		if !ok {
			return nil, fmt.Errorf("SSH connection %s not found", id)
		}
		chain = append(chain, cfg)
		id = cfg.TunnelSSHConnID
	}
	// chain is exit-first; reverse to outermost-first.
	for i, j := 0, len(chain)-1; i < j; i, j = i+1, j-1 {
		chain[i], chain[j] = chain[j], chain[i]
	}
	return chain, nil
}

// dialChain establishes the SSH clients along the chain and returns the exit
// client (chain tail) plus every client for teardown. The first hop is dialed
// directly (or through the upstream proxy); each subsequent hop is dialed
// through the previous client — the standard ProxyJump chaining.
func (ts *TunnelService) dialChain(chain []ConnectionConfig, upstream *SocksProxy) (*ssh.Client, []*ssh.Client, error) {
	var clients []*ssh.Client
	var prev *ssh.Client

	for i, cfg := range chain {
		addr := net.JoinHostPort(cfg.Host, strconv.Itoa(cfg.Port))
		authMethods, cleanup, err := makeSSHAuthMethodsForAttempt(cfg, nil)
		if err != nil {
			closeClients(clients)
			return nil, nil, fmt.Errorf("ssh auth %s: %w", addr, err)
		}

		var raw net.Conn
		if i == 0 {
			raw, err = dialFirstHop(addr, upstream)
		} else {
			raw, err = prev.Dial("tcp", addr)
		}
		if err != nil {
			cleanup()
			closeClients(clients)
			return nil, nil, fmt.Errorf("dial %s: %w", addr, err)
		}

		clientConfig := &ssh.ClientConfig{
			User:            cfg.User,
			Auth:            authMethods,
			Timeout:         30 * time.Second,
			HostKeyCallback: ssh.InsecureIgnoreHostKey(),
			Config:          sshAlgorithms(),
		}
		sshConn, chans, reqs, err := ssh.NewClientConn(raw, addr, clientConfig)
		cleanup()
		if err != nil {
			raw.Close()
			closeClients(clients)
			return nil, nil, fmt.Errorf("ssh handshake %s: %w", addr, err)
		}
		client := ssh.NewClient(sshConn, chans, reqs)
		clients = append(clients, client)
		prev = client
	}

	return prev, clients, nil
}

// dialFirstHop dials the first hop directly, or through an upstream SOCKS5/HTTP
// proxy when configured (the chain's entry point).
func dialFirstHop(addr string, upstream *SocksProxy) (net.Conn, error) {
	if upstream == nil {
		conn, err := net.DialTimeout("tcp", addr, 30*time.Second)
		if err == nil {
			if tcp, ok := conn.(*net.TCPConn); ok {
				tcp.SetKeepAlive(true)
				tcp.SetKeepAlivePeriod(sshKeepAliveInterval)
			}
		}
		return conn, err
	}

	proxyAddr := net.JoinHostPort(upstream.Host, strconv.Itoa(upstream.Port))
	switch upstream.Kind {
	case "", "socks5":
		var auth *proxy.Auth
		if upstream.User != "" {
			auth = &proxy.Auth{User: upstream.User, Password: upstream.Pass}
		}
		d, err := proxy.SOCKS5("tcp", proxyAddr, auth, &net.Dialer{Timeout: 30 * time.Second})
		if err != nil {
			return nil, err
		}
		return d.Dial("tcp", addr)
	case "http":
		return dialHTTPConnect(proxyAddr, upstream, addr)
	default:
		return nil, fmt.Errorf("unsupported upstream proxy kind %q", upstream.Kind)
	}
}

// dialHTTPConnect opens a CONNECT tunnel through an HTTP proxy to addr.
func dialHTTPConnect(proxyAddr string, up *SocksProxy, addr string) (net.Conn, error) {
	conn, err := net.DialTimeout("tcp", proxyAddr, 30*time.Second)
	if err != nil {
		return nil, err
	}
	req := "CONNECT " + addr + " HTTP/1.1\r\nHost: " + addr + "\r\n"
	if up.User != "" {
		cred := basicAuth(up.User, up.Pass)
		req += "Proxy-Authorization: Basic " + cred + "\r\n"
	}
	req += "\r\n"
	if _, err := conn.Write([]byte(req)); err != nil {
		conn.Close()
		return nil, err
	}
	// Read status line up to the header terminator, bounded by the connect timeout.
	if err := conn.SetReadDeadline(time.Now().Add(30 * time.Second)); err != nil {
		conn.Close()
		return nil, err
	}
	buf := make([]byte, 0, 256)
	one := make([]byte, 1)
	for {
		if _, err := io.ReadFull(conn, one); err != nil {
			conn.Close()
			return nil, err
		}
		buf = append(buf, one[0])
		if len(buf) >= 4 && string(buf[len(buf)-4:]) == "\r\n\r\n" {
			break
		}
		if len(buf) > 4096 {
			conn.Close()
			return nil, fmt.Errorf("http proxy response too large")
		}
	}
	if len(buf) < 12 || string(buf[9:12]) != "200" {
		conn.Close()
		return nil, fmt.Errorf("http proxy CONNECT failed")
	}
	// Clear the read deadline so the connection is usable for the SSH session.
	if err := conn.SetReadDeadline(time.Time{}); err != nil {
		conn.Close()
		return nil, err
	}
	return conn, nil
}

// --- accept / copy helpers ---

func acceptLoop(ln net.Listener, quit chan struct{}, handle func(net.Conn)) {
	for {
		conn, err := ln.Accept()
		if err != nil {
			select {
			case <-quit:
			default:
			}
			return
		}
		go handle(conn)
	}
}

// pipe copies bidirectionally between a and b and closes both when either side
// ends.
func pipe(a, b net.Conn) {
	done := make(chan struct{}, 2)
	go func() { io.Copy(a, b); done <- struct{}{} }()
	go func() { io.Copy(b, a); done <- struct{}{} }()
	<-done
	a.Close()
	b.Close()
}

func closeClients(clients []*ssh.Client) {
	for _, c := range clients {
		c.Close()
	}
}

func basicAuth(user, pass string) string {
	return base64.StdEncoding.EncodeToString([]byte(user + ":" + pass))
}

// --- runtime state ---

// setState records a tunnel's runtime state and notifies the callback (app.go
// wires it to a Wails event). Returns the state for convenience.
func (ts *TunnelService) setState(id string, st TunnelState) TunnelState {
	// Throwaway IDs from TestTunnel never surface in the UI: no recording, no
	// event — a failed test reports through its return value, not a toast.
	if strings.HasPrefix(id, "__test__") {
		return st
	}
	ts.mu.Lock()
	ts.states[id] = st
	cb := ts.onState
	ts.mu.Unlock()
	if cb != nil {
		cb(st)
	}
	return st
}

// SetStateCallback registers a callback invoked whenever a tunnel's state
// changes.
func (ts *TunnelService) SetStateCallback(cb func(TunnelState)) {
	ts.mu.Lock()
	ts.onState = cb
	ts.mu.Unlock()
}

// TunnelStates returns a snapshot of all known tunnel runtime states.
func (ts *TunnelService) TunnelStates() []TunnelState {
	ts.mu.Lock()
	defer ts.mu.Unlock()
	out := make([]TunnelState, 0, len(ts.states))
	for _, st := range ts.states {
		out = append(out, st)
	}
	return out
}

// --- minimal SOCKS5 server (CONNECT only, no auth) for dynamic tunnels ---

const (
	socks5Success         = 0x00
	socks5HostUnreachable = 0x04
)

// socks5Handshake performs the server side of a SOCKS5 CONNECT negotiation on
// conn and returns the requested "host:port". Only the no-auth method and the
// CONNECT command are supported — enough for a local dynamic-forwarding proxy.
func socks5Handshake(conn net.Conn) (string, error) {
	head := make([]byte, 2)
	if _, err := io.ReadFull(conn, head); err != nil {
		return "", err
	}
	if head[0] != 0x05 {
		return "", fmt.Errorf("socks: bad version %d", head[0])
	}
	methods := make([]byte, int(head[1]))
	if _, err := io.ReadFull(conn, methods); err != nil {
		return "", err
	}
	// Reply: version 5, no authentication required.
	if _, err := conn.Write([]byte{0x05, 0x00}); err != nil {
		return "", err
	}

	req := make([]byte, 4)
	if _, err := io.ReadFull(conn, req); err != nil {
		return "", err
	}
	if req[0] != 0x05 {
		return "", fmt.Errorf("socks: bad request version %d", req[0])
	}
	if req[1] != 0x01 { // CONNECT only
		socks5Reply(conn, 0x07)
		return "", fmt.Errorf("socks: unsupported command %d", req[1])
	}

	var host string
	switch req[3] {
	case 0x01: // IPv4
		b := make([]byte, 4)
		if _, err := io.ReadFull(conn, b); err != nil {
			return "", err
		}
		host = net.IP(b).String()
	case 0x03: // domain
		l := make([]byte, 1)
		if _, err := io.ReadFull(conn, l); err != nil {
			return "", err
		}
		b := make([]byte, int(l[0]))
		if _, err := io.ReadFull(conn, b); err != nil {
			return "", err
		}
		host = string(b)
	case 0x04: // IPv6
		b := make([]byte, 16)
		if _, err := io.ReadFull(conn, b); err != nil {
			return "", err
		}
		host = net.IP(b).String()
	default:
		socks5Reply(conn, 0x08)
		return "", fmt.Errorf("socks: unknown address type %d", req[3])
	}

	pb := make([]byte, 2)
	if _, err := io.ReadFull(conn, pb); err != nil {
		return "", err
	}
	port := binary.BigEndian.Uint16(pb)
	return net.JoinHostPort(host, strconv.Itoa(int(port))), nil
}

// socks5Reply writes a SOCKS5 reply with the given status and a zero
// bound-address (which clients ignore for CONNECT).
func socks5Reply(conn net.Conn, status byte) error {
	_, err := conn.Write([]byte{0x05, status, 0x00, 0x01, 0, 0, 0, 0, 0, 0})
	return err
}
