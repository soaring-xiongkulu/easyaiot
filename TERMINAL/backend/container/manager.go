package container

import (
	"context"
	"fmt"
	"sync"

	"github.com/google/uuid"
	"easyaiot/terminal/backend/session"
	"golang.org/x/crypto/ssh"
)

type EventEmitter func(name string, payload any)

type Manager struct {
	mu      sync.RWMutex
	conns   map[string]*conn
	streams map[string]*streamHandle
	emit    EventEmitter
}

type conn struct {
	id       string
	provider *Provider
	ssh      *ssh.Client // local 为 nil
	onClose  func()
}

type streamHandle struct {
	connID string
	stream LineStream
}

func NewManager() *Manager {
	return &Manager{
		conns:   map[string]*conn{},
		streams: map[string]*streamHandle{},
		emit:    func(string, any) {},
	}
}

func (m *Manager) SetEventEmitter(e EventEmitter) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.emit = e
}

func (m *Manager) emitEvent(name string, payload any) {
	m.mu.RLock()
	e := m.emit
	m.mu.RUnlock()
	e(name, payload)
}

func (m *Manager) ConnectLocal(id string, rt Runtime, ns string) error {
	if !rt.Valid() {
		return fmt.Errorf("invalid runtime %q", rt)
	}
	p := NewProvider(rt, ns, NewLocalRunner())
	if err := ValidateRuntime(context.Background(), rt, p.runner); err != nil {
		return err
	}
	m.Disconnect(id) // 同 id 重连：先回收旧连接
	m.mu.Lock()
	m.conns[id] = &conn{id: id, provider: p}
	m.mu.Unlock()
	return nil
}

func (m *Manager) ConnectSSH(id string, rt Runtime, ns string, cfg session.ConnectionConfig) error {
	if !rt.Valid() {
		return fmt.Errorf("invalid runtime %q", rt)
	}
	client, err := session.DialSSHClient(cfg)
	if err != nil {
		return err
	}
	p := NewProvider(rt, ns, NewSSHRunner(client))
	if err := ValidateRuntime(context.Background(), rt, p.runner); err != nil {
		client.Close()
		return err
	}
	m.Disconnect(id) // 同 id 重连：先回收旧连接
	m.mu.Lock()
	m.conns[id] = &conn{id: id, provider: p, ssh: client}
	m.mu.Unlock()
	return nil
}

func (m *Manager) Disconnect(id string) {
	m.mu.Lock()
	c, ok := m.conns[id]
	delete(m.conns, id)
	var streams []*streamHandle
	for sid, s := range m.streams {
		if s.connID == id {
			streams = append(streams, s)
			delete(m.streams, sid)
		}
	}
	m.mu.Unlock()
	for _, s := range streams {
		_ = s.stream.Close()
	}
	if ok {
		if c.ssh != nil {
			_ = c.ssh.Close()
		}
		if c.onClose != nil {
			c.onClose()
		}
	}
}

func (m *Manager) Provider(id string) (*Provider, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	c, ok := m.conns[id]
	if !ok {
		return nil, fmt.Errorf("container connection not found: %s", id)
	}
	return c.provider, nil
}

// SetNamespace 切换连接的 namespace：用同一 runner 重建 provider，SSH 连接与进行中的流不受影响。
func (m *Manager) SetNamespace(connID, ns string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	c, ok := m.conns[connID]
	if !ok {
		return fmt.Errorf("container connection not found: %s", connID)
	}
	c.provider = NewProvider(c.provider.Runtime(), ns, c.provider.runner)
	return nil
}

// startStream 启动流并注册，逐行推事件，结束推 stream-end。
func (m *Manager) startStream(connID string, stream LineStream) string {
	sid := uuid.New().String()
	m.mu.Lock()
	m.streams[sid] = &streamHandle{connID: connID, stream: stream}
	m.mu.Unlock()
	go func() {
		var err error
		for line := range stream.Lines() {
			m.emitEvent("container:stream:"+sid, map[string]any{"line": line})
		}
		err = stream.Wait()
		errMsg := ""
		if err != nil {
			errMsg = err.Error()
		}
		m.emitEvent("container:stream-end:"+sid, map[string]any{"error": errMsg})
		m.mu.Lock()
		delete(m.streams, sid)
		m.mu.Unlock()
	}()
	return sid
}

func (m *Manager) StartLogStream(connID, id string, tail int, timestamps bool) (string, error) {
	p, err := m.Provider(connID)
	if err != nil {
		return "", err
	}
	s, err := p.Logs(context.Background(), id, tail, true, timestamps)
	if err != nil {
		return "", err
	}
	return m.startStream(connID, s), nil
}

func (m *Manager) StartPullStream(connID, image string) (string, error) {
	p, err := m.Provider(connID)
	if err != nil {
		return "", err
	}
	s, err := p.Pull(context.Background(), image)
	if err != nil {
		return "", err
	}
	return m.startStream(connID, s), nil
}

func (m *Manager) StopStream(streamID string) {
	m.mu.Lock()
	s, ok := m.streams[streamID]
	delete(m.streams, streamID)
	m.mu.Unlock()
	if ok {
		_ = s.stream.Close()
	}
}

func (m *Manager) Exec(connID, id, shell string, cols, rows int) (PTYStream, error) {
	p, err := m.Provider(connID)
	if err != nil {
		return nil, err
	}
	return p.Exec(context.Background(), id, shell, cols, rows)
}
