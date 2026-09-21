package session

import (
	"sync"
)

// ExecPTY mirrors container.PTYStream; container already imports session,
// so a minimal interface here avoids an import cycle.
type ExecPTY interface {
	Data() <-chan []byte
	Write(p []byte) error
	Resize(cols, rows int) error
	Close() error
}

var _ Session = (*ContainerExecSession)(nil)

type ContainerExecSession struct {
	baseSession
	pty      ExecPTY
	writeMu  sync.Mutex
	quitOnce sync.Once
}

func NewContainerExecSession(id string, pty ExecPTY) *ContainerExecSession {
	s := &ContainerExecSession{
		baseSession: baseSession{id: id, sessionType: "container-exec", status: StatusConnected},
		pty:         pty,
	}
	go s.readLoop()
	return s
}

// Connect is a no-op: the exec stream is already established by the App layer.
func (s *ContainerExecSession) Connect(_ ConnectionConfig) error { return nil }

func (s *ContainerExecSession) readLoop() {
	for data := range s.pty.Data() {
		s.RecordReadActivity()
		s.emitData(data)
	}
	s.setStatus(StatusDisconnected)
	s.emitData(disconnectNotice("Container exec session closed"))
}

func (s *ContainerExecSession) Write(data []byte) error {
	s.writeMu.Lock()
	defer s.writeMu.Unlock()
	return s.pty.Write(data)
}

func (s *ContainerExecSession) Resize(cols, rows int) error { return s.pty.Resize(cols, rows) }

func (s *ContainerExecSession) Disconnect() error {
	var err error
	s.quitOnce.Do(func() {
		err = s.pty.Close()
		s.setStatus(StatusDisconnected)
	})
	return err
}

func (s *ContainerExecSession) IsConnected() bool { return s.Status() == StatusConnected }
