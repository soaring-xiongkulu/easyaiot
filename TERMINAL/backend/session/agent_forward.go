package session

import (
	"fmt"

	"golang.org/x/crypto/ssh"
	"golang.org/x/crypto/ssh/agent"
)

// requestAgentForwarding registers the local agent channel handler before
// requesting forwarding on the session, matching OpenSSH's ssh -A behavior.
func requestAgentForwarding(client *ssh.Client, session *ssh.Session) error {
	if err := forwardLocalAgent(client); err != nil {
		return fmt.Errorf("connect to local SSH agent: %w", err)
	}
	if err := agent.RequestAgentForwarding(session); err != nil {
		return fmt.Errorf("server rejected SSH agent forwarding: %w", err)
	}
	return nil
}
