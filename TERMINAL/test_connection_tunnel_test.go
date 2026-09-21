package main

// End-to-end regression coverage for the tunnel path of App.TestConnection.
// The fake target below is unreachable directly (nothing listens on the port);
// it is only reachable through the fake SSH jump host via direct-tcpip
// forwarding, so a passing probe proves the connection actually rode the
// tunnel instead of dialing the target address directly.

import (
	"crypto/ed25519"
	"crypto/rand"
	"fmt"
	"io"
	"net"
	"testing"

	"golang.org/x/crypto/ssh"

	"easyaiot/terminal/backend/session"
	"easyaiot/terminal/backend/store"
)

// stubPasswordStore satisfies store.PasswordStore without any crypto.
type stubPasswordStore struct{}

func (stubPasswordStore) Encrypt(s string) (string, error) { return s, nil }
func (stubPasswordStore) Decrypt(s string) (string, error) { return s, nil }

// unreachableLocalPort returns a loopback port with no listener, so a direct
// dial to it always fails with connection refused.
func unreachableLocalPort(t *testing.T) int {
	t.Helper()
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("reserve port: %v", err)
	}
	port := ln.Addr().(*net.TCPAddr).Port
	ln.Close()
	return port
}

// startFakeJumpSSHD starts a minimal SSH server that accepts password auth
// (user "jump", password "jump-pw") and direct-tcpip channels — acting as the
// jump host whose forwarding makes the unreachable target reachable.
func startFakeJumpSSHD(t *testing.T) int {
	t.Helper()
	_, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("generate host key: %v", err)
	}
	signer, err := ssh.NewSignerFromKey(priv)
	if err != nil {
		t.Fatalf("host signer: %v", err)
	}
	serverConfig := &ssh.ServerConfig{
		PasswordCallback: func(m ssh.ConnMetadata, pw []byte) (*ssh.Permissions, error) {
			if m.User() == "jump" && string(pw) == "jump-pw" {
				return &ssh.Permissions{}, nil
			}
			return nil, fmt.Errorf("auth rejected for %q", m.User())
		},
	}
	serverConfig.AddHostKey(signer)

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	t.Cleanup(func() { ln.Close() })

	go func() {
		for {
			conn, err := ln.Accept()
			if err != nil {
				return
			}
			go func() {
				sconn, chans, reqs, err := ssh.NewServerConn(conn, serverConfig)
				if err != nil {
					conn.Close()
					return
				}
				defer sconn.Close()
				go func() {
					for req := range reqs {
						if req.WantReply {
							_ = req.Reply(false, nil)
						}
					}
				}()
				for newChan := range chans {
					if newChan.ChannelType() != "direct-tcpip" {
						_ = newChan.Reject(ssh.UnknownChannelType, "unsupported")
						continue
					}
					ch, chReqs, err := newChan.Accept()
					if err != nil {
						continue
					}
					go func() {
						for req := range chReqs {
							if req.WantReply {
								_ = req.Reply(false, nil)
							}
						}
					}()
					// Hold the channel open and drain it until the client closes.
					go func() {
						_, _ = io.Copy(io.Discard, ch)
						_ = ch.Close()
					}()
				}
			}()
		}
	}()

	return ln.Addr().(*net.TCPAddr).Port
}

// TestApp_TestConnection_RidesJumpHostTunnel locks in that TestConnection
// honors config.TunnelSSHConnID for non-k8s/container types: the probe must
// ride a jump-host tunnel like a real CreateSession connect does, instead of
// dialing config.Host:Port directly.
func TestApp_TestConnection_RidesJumpHostTunnel(t *testing.T) {
	targetPort := unreachableLocalPort(t)
	sshPort := startFakeJumpSSHD(t)

	cs, err := store.NewConnectionStore(t.TempDir())
	if err != nil {
		t.Fatalf("connection store: %v", err)
	}
	cs.SetPasswordStore(stubPasswordStore{})
	if err := cs.Save(session.ConnectionStoreData{
		Connections: []session.ConnectionConfig{{
			ID:       "jump-1",
			Type:     "ssh",
			Host:     "127.0.0.1",
			Port:     sshPort,
			User:     "jump",
			AuthType: "password",
			Password: "jump-pw",
		}},
	}); err != nil {
		t.Fatalf("save jump connection: %v", err)
	}

	a := NewApp("")
	a.connectionStore = cs
	a.tunnelService = session.NewTunnelService()

	// Through the tunnel the jump host serves the direct-tcpip channel itself,
	// so the probe succeeds even though nothing listens on targetPort.
	desc, err := a.TestConnection(session.ConnectionConfig{
		Type:            "tcp",
		Host:            "127.0.0.1",
		Port:            targetPort,
		TunnelSSHConnID: "jump-1",
	})
	if err != nil {
		t.Fatalf("TestConnection with tunnel: %v", err)
	}
	if desc == "" {
		t.Fatal("TestConnection returned empty description")
	}

	// Guard: without the tunnel the same target is unreachable — proving the
	// tunnel was what made the first probe succeed.
	if _, err := a.TestConnection(session.ConnectionConfig{
		Type: "tcp",
		Host: "127.0.0.1",
		Port: targetPort,
	}); err == nil {
		t.Fatal("direct probe to unreachable target unexpectedly succeeded")
	}
}
