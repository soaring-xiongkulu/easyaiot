//go:build windows
// +build windows

package session

import (
	"fmt"
	"strings"
)

// WSLSession is a terminal session that launches a WSL distribution via
// wsl.exe. It reuses LocalSession's entire ConPTY / pending-size / decode
// machinery by composition, overriding only the two things that differ: the
// reported session type and a Connect that always forces the `wsl://<distro>`
// shell. This keeps the PTY plumbing in a single implementation instead of a
// copy-paste variant.
type WSLSession struct {
	*LocalSession
}

func NewWSLSession(id string) *WSLSession {
	return &WSLSession{LocalSession: NewLocalSession(id)}
}

// Type reports "wsl" so type-routing (panel/companion) keys off the WSL type
// even though the underlying engine is the local ConPTY session.
func (s *WSLSession) Type() string { return "wsl" }

// Connect requires a `wsl://<distro>` shell path and delegates the rest to
// LocalSession, which launches wsl.exe -d <distro> for that shell.
func (s *WSLSession) Connect(config ConnectionConfig) error {
	if !strings.HasPrefix(strings.ToLower(config.ShellPath), "wsl://") {
		return fmt.Errorf("WSL session requires a wsl://<distro> shell path")
	}
	return s.LocalSession.Connect(config)
}
