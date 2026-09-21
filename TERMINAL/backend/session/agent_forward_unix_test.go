//go:build !windows

package session

import (
	"strings"
	"testing"
)

func TestLocalAgentSocket(t *testing.T) {
	t.Run("missing", func(t *testing.T) {
		t.Setenv("SSH_AUTH_SOCK", "")
		if _, err := localAgentSocket(); err == nil || !strings.Contains(err.Error(), "SSH_AUTH_SOCK") {
			t.Fatalf("localAgentSocket() error = %v, want SSH_AUTH_SOCK error", err)
		}
	})

	t.Run("trimmed", func(t *testing.T) {
		t.Setenv("SSH_AUTH_SOCK", "  /tmp/test-agent.sock  ")
		got, err := localAgentSocket()
		if err != nil {
			t.Fatalf("localAgentSocket() error = %v", err)
		}
		if got != "/tmp/test-agent.sock" {
			t.Fatalf("localAgentSocket() = %q, want trimmed path", got)
		}
	})
}
