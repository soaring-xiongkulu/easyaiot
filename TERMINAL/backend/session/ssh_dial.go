package session

import (
	"errors"
	"fmt"
	"io"
	"net"
	"strconv"
	"strings"
	"time"

	"golang.org/x/crypto/ssh"
)

type sshConnDialer func() (net.Conn, error)
type sshClientConfigFactory func() (*ssh.ClientConfig, func(), error)

// dialSSHWithCipherFallback keeps modern AEAD preference, but retries a
// handshake EOF once with CTR first for servers that falsely advertise GCM.
func dialSSHWithCipherFallback(addr string, newConfig sshClientConfigFactory, dial sshConnDialer) (*ssh.Client, error) {
	algorithms := []ssh.Config{sshAlgorithms(), sshAlgorithmsCTRFirst()}
	var lastErr error
	for i, algorithms := range algorithms {
		conn, err := dial()
		if err != nil {
			return nil, fmt.Errorf("tcp dial: %w", err)
		}
		config, cleanup, err := newConfig()
		if err != nil {
			conn.Close()
			return nil, fmt.Errorf("ssh auth: %w", err)
		}
		if tcpConn, ok := conn.(*net.TCPConn); ok {
			tcpConn.SetKeepAlive(true)
			tcpConn.SetKeepAlivePeriod(sshKeepAliveInterval)
		}
		attempt := *config
		attempt.Config = algorithms
		sshConn, chans, reqs, err := ssh.NewClientConn(conn, addr, &attempt)
		cleanup()
		if err == nil {
			return ssh.NewClient(sshConn, chans, reqs), nil
		}
		conn.Close()
		lastErr = err
		if i == 0 && errors.Is(err, io.EOF) {
			continue
		}
		break
	}
	return nil, fmt.Errorf("ssh handshake: %w", lastErr)
}

// splitSSHAuthMethods separates the password/key methods from the
// keyboard-interactive fallback. The dialer tries them in two phases — see
// dialSSHWithAuthRetry for why keyboard-interactive must not be offered on
// the first handshake.
func splitSSHAuthMethods(config ConnectionConfig, kbCallback ssh.KeyboardInteractiveChallenge) ([]ssh.AuthMethod, ssh.AuthMethod) {
	methods, _ := makeSSHAuthMethods(config, nil)
	if kbCallback == nil {
		return methods, nil
	}
	return methods, ssh.KeyboardInteractive(kbCallback)
}

// Markers within x/crypto's error strings. The library returns both as plain
// fmt.Errorf values with no typed sentinel, so the message is the only
// stable handle.
const (
	authExhaustedMarker  = "unable to authenticate"
	kbdIntColdFailMarker = "unexpected message type 51 (expected 60)"
)

// dialSSHWithAuthRetry dials with the primary auth methods (password/key)
// first, and retries once with keyboard-interactive added.
//
// x/crypto aborts the handshake with "ssh: unexpected message type 51
// (expected 60)" when a server answers the keyboard-interactive initiation
// with USERAUTH_FAILURE before any info request. RFC 4252 allows that reply
// and OpenSSH's own client treats it as a plain rejection, but servers that
// advertise keyboard-interactive yet fail it cold are common (root login
// restricted to keys, dropbear without PAM), so offering keyboard-interactive
// unconditionally turned every ordinary password rejection on those hosts
// into that cryptic protocol error. Trying it only after the primary methods
// are exhausted keeps prompt-based logins (OTP/2FA, keyboard-interactive-only
// servers) working while a plain rejection surfaces as the server's own auth
// error.
func dialSSHWithAuthRetry(addr string, newConfig, newConfigWithKeyboard sshClientConfigFactory, dial sshConnDialer) (*ssh.Client, error) {
	client, err := dialSSHWithCipherFallback(addr, newConfig, dial)
	if newConfigWithKeyboard == nil || err == nil || !strings.Contains(err.Error(), authExhaustedMarker) {
		return client, err
	}
	client, retryErr := dialSSHWithCipherFallback(addr, newConfigWithKeyboard, dial)
	if retryErr == nil || !strings.Contains(retryErr.Error(), kbdIntColdFailMarker) {
		return client, retryErr
	}
	// The server rejects keyboard-interactive outright; report the honest
	// auth failure from the first handshake instead of x/crypto's protocol
	// internals.
	return nil, err
}

// dialSSHTCP dials addr (through the upstream proxy when non-nil), performs the
// SSH handshake, and returns a *ssh.Client. Used by the SFTP and monitor
// sessions, which previously dialed directly via ssh.Dial.
func dialSSHTCP(addr string, clientConfig *ssh.ClientConfig, upstream *SocksProxy) (*ssh.Client, error) {
	raw, err := dialFirstHop(addr, upstream)
	if err != nil {
		return nil, fmt.Errorf("tcp dial: %w", err)
	}
	conn, chans, reqs, err := ssh.NewClientConn(raw, addr, clientConfig)
	if err != nil {
		raw.Close()
		return nil, fmt.Errorf("ssh handshake: %w", err)
	}
	return ssh.NewClient(conn, chans, reqs), nil
}

// DialSSHClient 建立非交互 SSH 连接（容器 runner 用，无 PTY、无键盘交互回显）。
// 与 ssh_session 的交互式拨号共享认证与密钥交换配置。
func DialSSHClient(config ConnectionConfig) (*ssh.Client, error) {
	kb := func(user, instruction string, questions []string, echos []bool) ([]string, error) {
		return nil, fmt.Errorf("keyboard-interactive not supported in this context")
	}
	addr := net.JoinHostPort(config.Host, strconv.Itoa(config.Port))
	newConfig := func(challenge ssh.KeyboardInteractiveChallenge) sshClientConfigFactory {
		return func() (*ssh.ClientConfig, func(), error) {
			authMethods, cleanup, err := makeSSHAuthMethodsForAttempt(config, challenge)
			if err != nil {
				return nil, nil, err
			}
			return &ssh.ClientConfig{
				User:            config.User,
				Auth:            authMethods,
				Timeout:         30 * time.Second,
				HostKeyCallback: ssh.InsecureIgnoreHostKey(),
			}, cleanup, nil
		}
	}
	var keyboardConfig sshClientConfigFactory
	if config.AuthType != "kerberos" {
		keyboardConfig = newConfig(kb)
	}
	return dialSSHWithAuthRetry(addr, newConfig(nil), keyboardConfig, func() (net.Conn, error) {
		return net.DialTimeout("tcp", addr, 30*time.Second)
	})
}
