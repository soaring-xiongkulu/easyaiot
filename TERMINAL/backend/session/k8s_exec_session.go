package session

import (
	"sync"

	"github.com/gorilla/websocket"
	"easyaiot/terminal/backend/log"
)

var _ Session = (*K8sExecSession)(nil)

type K8sExecSession struct {
	baseSession
	conn     *websocket.Conn
	writeMu  sync.Mutex
	quitOnce sync.Once
}

func NewK8sExecSession(id string, conn *websocket.Conn) *K8sExecSession {
	s := &K8sExecSession{
		baseSession: baseSession{id: id, sessionType: "k8s-exec", status: StatusConnected},
		conn:        conn,
	}
	go s.readLoop()
	return s
}

// Connect is a no-op: the websocket is already dialed by the App layer via DialExec.
func (s *K8sExecSession) Connect(_ ConnectionConfig) error { return nil }

func (s *K8sExecSession) readLoop() {
	for {
		_, msg, err := s.conn.ReadMessage()
		if err != nil {
			s.setStatus(StatusDisconnected)
			s.emitData(disconnectNotice("K8s exec session closed"))
			return
		}
		ch, payload, ok := decodeFrame(msg)
		if !ok {
			continue
		}
		switch ch {
		case execChStdout, execChStderr:
			s.RecordReadActivity()
			s.emitData(payload)
		case execChError:
			if len(payload) > 0 {
				log.Writef("[k8s-exec] error channel: %s", string(payload))
			}
		}
	}
}

func (s *K8sExecSession) Write(data []byte) error {
	s.writeMu.Lock()
	defer s.writeMu.Unlock()
	return s.conn.WriteMessage(websocket.BinaryMessage, encodeStdin(data))
}

func (s *K8sExecSession) Resize(cols, rows int) error {
	frame, err := encodeResize(cols, rows)
	if err != nil {
		return err
	}
	s.writeMu.Lock()
	defer s.writeMu.Unlock()
	return s.conn.WriteMessage(websocket.BinaryMessage, frame)
}

func (s *K8sExecSession) Disconnect() error {
	var err error
	s.quitOnce.Do(func() {
		err = s.conn.Close()
		s.setStatus(StatusDisconnected)
	})
	return err
}

func (s *K8sExecSession) IsConnected() bool { return s.Status() == StatusConnected }
