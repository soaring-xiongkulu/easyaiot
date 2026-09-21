//go:build !windows
// +build !windows

package session

import "fmt"

// WSLFileSession is a stub for non-Windows platforms (WSL only exists on
// Windows). It satisfies the Session interface but Connect always errors. WSL
// file transfers are therefore never reachable on mac/linux builds.
type WSLFileSession struct {
	baseSession
}

func NewWSLFileSession(id string) *WSLFileSession {
	return &WSLFileSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "wsl-file",
			status:      StatusDisconnected,
		},
	}
}

func (s *WSLFileSession) Connect(_ ConnectionConfig) error {
	return fmt.Errorf("WSL is only supported on Windows")
}

func (s *WSLFileSession) Disconnect() error     { return nil }
func (s *WSLFileSession) IsConnected() bool     { return false }
func (s *WSLFileSession) Resize(_, _ int) error { return nil }
func (s *WSLFileSession) Write(_ []byte) error  { return nil }
