package session

import (
	"bufio"
	"errors"
	"net"
	"os"
	"strconv"
	"strings"
	"testing"
	"time"

	"golang.org/x/crypto/ssh"
)

// Throwaway ed25519 host key generated for this test file only.
const testHostKeyPEM = `-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACDRZOogzYJH2+dHR2DzalwSpBRlruM7iyYOPB3U73OljQAAAJAyohktMqIZ
LQAAAAtzc2gtZWQyNTUxOQAAACDRZOogzYJH2+dHR2DzalwSpBRlruM7iyYOPB3U73OljQ
AAAEAQ+apRyVK0+7YQsk2Eo9jqx9EWht1aU8k2RMdUD4qIr9Fk6iDNgkfb50dHYPNqXBKk
FGWu4zuLJg48HdTvc6WNAAAACmt4bkBreG4tcGMBAgM=
-----END OPENSSH PRIVATE KEY-----`

// startAuthTestServer serves SSH connections with the given callbacks on a
// loopback port. The accept loop runs for the whole test because
// dialSSHWithAuthRetry reconnects for its keyboard-interactive phase.
func startAuthTestServer(t *testing.T, config *ssh.ServerConfig) string {
	t.Helper()
	signer, err := ssh.ParsePrivateKey([]byte(testHostKeyPEM))
	if err != nil {
		t.Fatalf("parse test host key: %v", err)
	}
	config.AddHostKey(signer)
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
				_, chans, reqs, err := ssh.NewServerConn(conn, config)
				if err != nil {
					return
				}
				go ssh.DiscardRequests(reqs)
				for newCh := range chans {
					newCh.Reject(ssh.UnknownChannelType, "handshake-only test server")
				}
			}()
		}
	}()
	return ln.Addr().String()
}

// dialAuthTest dials addr through the patched auth flow with a password-type
// connection config, mirroring the interactive session's call shape.
func dialAuthTest(t *testing.T, addr, password string, kb ssh.KeyboardInteractiveChallenge) (*ssh.Client, error) {
	t.Helper()
	config := ConnectionConfig{AuthType: "password", Password: password}
	newConfig := func(challenge ssh.KeyboardInteractiveChallenge) sshClientConfigFactory {
		return func() (*ssh.ClientConfig, func(), error) {
			methods, cleanup, err := makeSSHAuthMethodsForAttempt(config, challenge)
			if err != nil {
				return nil, nil, err
			}
			return &ssh.ClientConfig{
				User:            "tester",
				Auth:            methods,
				Timeout:         5 * time.Second,
				HostKeyCallback: ssh.InsecureIgnoreHostKey(),
			}, cleanup, nil
		}
	}
	return dialSSHWithAuthRetry(addr, newConfig(nil), newConfig(kb), func() (net.Conn, error) {
		return net.DialTimeout("tcp", addr, 5*time.Second)
	})
}

// Server that advertises keyboard-interactive but rejects its initiation with
// a bare USERAUTH_FAILURE — exactly what x/crypto's server does when
// KeyboardInteractiveCallback errors before prompting, and what real servers
// do when the method is unusable for the account (root restricted to keys,
// dropbear without PAM). This is the shape that used to abort the handshake
// with "unexpected message type 51 (expected 60)".
func newColdKeyboardInteractiveServer(password string) *ssh.ServerConfig {
	return &ssh.ServerConfig{
		PasswordCallback: func(conn ssh.ConnMetadata, got []byte) (*ssh.Permissions, error) {
			if string(got) == password {
				return &ssh.Permissions{}, nil
			}
			return nil, errors.New("wrong password")
		},
		KeyboardInteractiveCallback: func(conn ssh.ConnMetadata, challenge ssh.KeyboardInteractiveChallenge) (*ssh.Permissions, error) {
			return nil, errors.New("keyboard-interactive unavailable")
		},
	}
}

func TestDialSSHWithAuthRetryColdKeyboardInteractive(t *testing.T) {
	addr := startAuthTestServer(t, newColdKeyboardInteractiveServer("right"))

	t.Run("wrong password surfaces the server's auth error, not the 51/60 protocol leak", func(t *testing.T) {
		_, err := dialAuthTest(t, addr, "wrong", func(user, instruction string, questions []string, echos []bool) ([]string, error) {
			return nil, errors.New("unexpected prompt")
		})
		if err == nil {
			t.Fatal("expected auth failure")
		}
		if strings.Contains(err.Error(), kbdIntColdFailMarker) {
			t.Fatalf("error leaks the keyboard-interactive protocol failure: %v", err)
		}
		if !strings.Contains(err.Error(), authExhaustedMarker) {
			t.Fatalf("error is not a plain auth failure: %v", err)
		}
	})

	t.Run("right password connects without ever touching keyboard-interactive", func(t *testing.T) {
		client, err := dialAuthTest(t, addr, "right", func(user, instruction string, questions []string, echos []bool) ([]string, error) {
			return nil, errors.New("keyboard-interactive must not be reached when the password is right")
		})
		if err != nil {
			t.Fatalf("expected success: %v", err)
		}
		client.Close()
	})
}

// Server where password auth is rejected and login only completes through a
// keyboard-interactive prompt (OTP/2FA boxes, SuSE-style password-over-kbdint).
func newKeyboardInteractiveOnlyServer(password string) *ssh.ServerConfig {
	return &ssh.ServerConfig{
		PasswordCallback: func(conn ssh.ConnMetadata, got []byte) (*ssh.Permissions, error) {
			return nil, errors.New("password auth disabled")
		},
		KeyboardInteractiveCallback: func(conn ssh.ConnMetadata, challenge ssh.KeyboardInteractiveChallenge) (*ssh.Permissions, error) {
			_, err := challenge("", "", []string{"Password: "}, []bool{false})
			if err != nil {
				return nil, err
			}
			return &ssh.Permissions{}, nil
		},
	}
}

func TestDialSSHWithAuthRetryKeyboardInteractiveFallback(t *testing.T) {
	addr := startAuthTestServer(t, newKeyboardInteractiveOnlyServer("otp-answer"))

	client, err := dialAuthTest(t, addr, "unused", func(user, instruction string, questions []string, echos []bool) ([]string, error) {
		answers := make([]string, len(questions))
		for i := range questions {
			answers[i] = "otp-answer"
		}
		return answers, nil
	})
	if err != nil {
		t.Fatalf("expected keyboard-interactive fallback to authenticate: %v", err)
	}
	client.Close()
}

func TestSplitSSHAuthMethodsKeepsKeyboardInteractiveOutOfFirstPhase(t *testing.T) {
	kb := func(user, instruction string, questions []string, echos []bool) ([]string, error) {
		return nil, errors.New("unused")
	}
	methods, kbAuth := splitSSHAuthMethods(ConnectionConfig{AuthType: "password", Password: "pw"}, kb)
	if len(methods) != 1 {
		t.Fatalf("primary methods = %d entries, want exactly the password method", len(methods))
	}
	if kbAuth == nil {
		t.Fatal("keyboard-interactive method missing from the retry phase")
	}
	methods, kbAuth = splitSSHAuthMethods(ConnectionConfig{AuthType: "password", Password: "pw"}, nil)
	if len(methods) != 1 || kbAuth != nil {
		t.Fatalf("nil callback must yield no retry method, got %d methods and kbAuth=%v", len(methods), kbAuth)
	}
}

// Live probe for servers that reproduce issue-reported handshakes, e.g.
// TERMINAL_LIVE_SSH=10.10.10.3:22 go test -run TestLiveSSH ./backend/session/
// Sends a dummy password only; at worst it burns one failed login attempt.
func TestLiveSSHColdKeyboardInteractiveServer(t *testing.T) {
	addr := os.Getenv("TERMINAL_LIVE_SSH")
	if addr == "" {
		t.Skip("set TERMINAL_LIVE_SSH=host[:port] to run")
	}
	host, portStr, err := net.SplitHostPort(addr)
	if err != nil {
		host, portStr = addr, "22"
	}
	port, err := strconv.Atoi(portStr)
	if err != nil {
		t.Fatalf("bad TERMINAL_LIVE_SSH port: %v", err)
	}
	_, err = dialAuthTest(t, net.JoinHostPort(host, strconv.Itoa(port)), "__terminal_diag__", func(user, instruction string, questions []string, echos []bool) ([]string, error) {
		return nil, errors.New("live probe does not answer challenges")
	})
	if err == nil {
		t.Fatal("expected the dummy password to be rejected")
	}
	if strings.Contains(err.Error(), kbdIntColdFailMarker) {
		t.Fatalf("handshake still leaks the keyboard-interactive protocol failure: %v", err)
	}
	t.Logf("live probe error (should be a plain auth failure): %v", err)
}

func TestDialSSHWithCipherFallbackRebuildsClientConfig(t *testing.T) {
	configCalls := 0
	dialCalls := 0
	cleanupCalls := 0
	newConfig := func() (*ssh.ClientConfig, func(), error) {
		configCalls++
		return &ssh.ClientConfig{User: "test", HostKeyCallback: ssh.InsecureIgnoreHostKey()}, func() { cleanupCalls++ }, nil
	}
	dial := func() (net.Conn, error) {
		dialCalls++
		client, server := net.Pipe()
		go func() {
			defer server.Close()
			_, _ = bufio.NewReader(server).ReadString('\n')
		}()
		return client, nil
	}

	if _, err := dialSSHWithCipherFallback("example.invalid:22", newConfig, dial); err == nil {
		t.Fatal("dialSSHWithCipherFallback() error = nil, want handshake error")
	}
	if configCalls != 2 {
		t.Fatalf("client config factory called %d times, want 2", configCalls)
	}
	if dialCalls != 2 {
		t.Fatalf("dialer called %d times, want 2", dialCalls)
	}
	if cleanupCalls != 2 {
		t.Fatalf("attempt cleanup called %d times, want 2", cleanupCalls)
	}
}
