//go:build !windows

package session

import (
	"fmt"
	"net"
	"os"
	"strings"

	"golang.org/x/crypto/ssh"
	"golang.org/x/crypto/ssh/agent"
)

func localAgentAuthMethod() (ssh.AuthMethod, func(), error) {
	addr, err := localAgentSocket()
	if err != nil {
		return nil, func() {}, err
	}
	conn, err := net.Dial("unix", addr)
	if err != nil {
		return nil, func() {}, fmt.Errorf("connect to SSH_AUTH_SOCK %q: %w", addr, err)
	}
	return ssh.PublicKeysCallback(agent.NewClient(conn).Signers), func() { _ = conn.Close() }, nil
}

// localAgentSocket returns the Unix socket exported by the SSH agent in the
// Terminal process environment. On macOS this is normally inherited from
// launchd; third-party agents must expose SSH_AUTH_SOCK to the app process.
func localAgentSocket() (string, error) {
	addr := strings.TrimSpace(os.Getenv("SSH_AUTH_SOCK"))
	if addr == "" {
		return "", fmt.Errorf("SSH_AUTH_SOCK is not set; start an SSH agent and expose its socket to Terminal")
	}
	return addr, nil
}

func forwardLocalAgent(client *ssh.Client) error {
	addr, err := localAgentSocket()
	if err != nil {
		return err
	}
	if err := agent.ForwardToRemote(client, addr); err != nil {
		return fmt.Errorf("connect to SSH_AUTH_SOCK %q: %w", addr, err)
	}
	return nil
}
