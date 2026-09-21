//go:build !windows
// +build !windows

package session

import "fmt"

// WSLSession is a stub for non-Windows platforms (WSL only exists on Windows).
// It satisfies the Session interface but Connect always returns an error.
type WSLSession struct {
	baseSession
}

func NewWSLSession(id string) *WSLSession {
	return &WSLSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "wsl",
			status:      StatusDisconnected,
		},
	}
}

func (s *WSLSession) Connect(_ ConnectionConfig) error {
	return fmt.Errorf("WSL is only supported on Windows")
}

func (s *WSLSession) Disconnect() error     { return nil }
func (s *WSLSession) IsConnected() bool     { return false }
func (s *WSLSession) Resize(_, _ int) error { return nil }
func (s *WSLSession) Write(_ []byte) error  { return nil }
