//go:build !windows

package session

import "fmt"

// RDPSession is a stub for non-Windows platforms.
// It satisfies the Session interface but Connect always returns an error.
type RDPSession struct {
	baseSession
}

func NewRDPSession(id string) *RDPSession {
	return &RDPSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "rdp",
			status:      StatusDisconnected,
		},
	}
}

func (s *RDPSession) Connect(_ ConnectionConfig) error {
	return fmt.Errorf("RDP is only supported on Windows")
}

func (s *RDPSession) Disconnect() error { return nil }

func (s *RDPSession) IsConnected() bool { return false }

func (s *RDPSession) Resize(_, _ int) error { return nil }

func (s *RDPSession) Write(_ []byte) error { return nil }

// Stub methods called from app.go

func (s *RDPSession) ClientAreaScreenRect() (x, y, w, h int) { return }

func (s *RDPSession) SetParentHwnd(_ uintptr) {}

func (s *RDPSession) SetPosition(_, _, _, _ int) {}

func (s *RDPSession) Show() {}

func (s *RDPSession) Hide() {}

func (s *RDPSession) SetFullScreen(_ bool) {}

func (s *RDPSession) SetOnFullScreenExit(_ func()) {}

func (s *RDPSession) Invalidate() {}

func (s *RDPSession) Snapshot() (string, error) {
	return "", fmt.Errorf("RDP is only supported on Windows")
}
