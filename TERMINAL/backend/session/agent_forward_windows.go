//go:build windows

package session

import (
	"fmt"

	sshagent "github.com/xanzy/ssh-agent"
	"golang.org/x/crypto/ssh"
	"golang.org/x/crypto/ssh/agent"
)

// localAgentAuthMethod uses Pageant when available, then falls back to the
// Windows OpenSSH agent named pipe. sshagent.New implements that priority.
func localAgentAuthMethod() (ssh.AuthMethod, func(), error) {
	localAgent, conn, err := sshagent.New()
	if err != nil {
		return nil, func() {}, fmt.Errorf("Pageant or Windows OpenSSH agent unavailable: %w", err)
	}
	cleanup := func() {}
	if conn != nil {
		cleanup = func() { _ = conn.Close() }
	}
	return ssh.PublicKeysCallback(localAgent.Signers), cleanup, nil
}

// forwardLocalAgent uses PuTTY Pageant when it is running, then falls back to
// the Windows OpenSSH agent at \\.\pipe\openssh-ssh-agent. That selection
// order is implemented by github.com/xanzy/ssh-agent.
func forwardLocalAgent(client *ssh.Client) error {
	localAgent, _, err := sshagent.New()
	if err != nil {
		return fmt.Errorf("Pageant or Windows OpenSSH agent unavailable: %w", err)
	}
	if err := agent.ForwardToAgent(client, localAgent); err != nil {
		return fmt.Errorf("forward Pageant or Windows OpenSSH agent: %w", err)
	}
	return nil
}
