package session

import (
	"fmt"
	"net"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"easyaiot/terminal/backend/log"
)

// VNCProxy bridges WebSocket (frontend noVNC) to TCP (VNC server).
// One instance per VNC session, bound to a random local port.
type VNCProxy struct {
	listener net.Listener
	target   string
	stopCh   chan struct{}
	stopOnce sync.Once
	wg       sync.WaitGroup
	mu       sync.Mutex
	wsConn   *websocket.Conn
	tcpConn  net.Conn
}

func NewVNCProxy(target string) *VNCProxy {
	return &VNCProxy{
		target: target,
		stopCh: make(chan struct{}),
	}
}

// Start begins listening on a random local port and returns the WebSocket URL.
func (p *VNCProxy) Start() (string, error) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return "", fmt.Errorf("vnc proxy listen: %w", err)
	}
	p.listener = ln

	upgrader := websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool { return true },
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		ws, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			log.Writef("[VNCProxy] WebSocket upgrade failed: %v", err)
			return
		}
		p.handleWebSocket(ws)
	})

	p.wg.Add(1)
	go func() {
		defer p.wg.Done()
		_ = http.Serve(ln, mux)
	}()

	addr := ln.Addr().(*net.TCPAddr)
	log.Writef("[VNCProxy] Listening on ws://127.0.0.1:%d, target: %s", addr.Port, p.target)
	return fmt.Sprintf("ws://127.0.0.1:%d", addr.Port), nil
}

func (p *VNCProxy) handleWebSocket(ws *websocket.Conn) {
	p.mu.Lock()
	if p.wsConn != nil {
		p.mu.Unlock()
		log.Writef("[VNCProxy] Rejecting additional WebSocket connection")
		ws.Close()
		return
	}
	p.wsConn = ws
	p.mu.Unlock()
	log.Writef("[VNCProxy] WebSocket client connected")

	// Clean up wsConn when this client disconnects so new clients can connect.
	defer func() {
		p.mu.Lock()
		if p.wsConn == ws {
			p.wsConn = nil
		}
		p.mu.Unlock()
	}()

	tcp, err := net.DialTimeout("tcp", p.target, 5*time.Second)
	if err != nil {
		log.Writef("[VNCProxy] TCP dial to %s failed: %v", p.target, err)
		ws.Close()
		return
	}
	log.Writef("[VNCProxy] TCP connection to %s established", p.target)

	p.mu.Lock()
	p.tcpConn = tcp
	p.mu.Unlock()

	p.wg.Add(2)

	go func() {
		defer p.wg.Done()
		defer tcp.Close()
		for {
			select {
			case <-p.stopCh:
				return
			default:
			}
			msgType, data, err := ws.ReadMessage()
			if err != nil {
				log.Writef("[VNCProxy] WebSocket read error: %v", err)
				return
			}
			if msgType == websocket.BinaryMessage {
				if _, err := tcp.Write(data); err != nil {
					log.Writef("[VNCProxy] TCP write error: %v", err)
					return
				}
			}
		}
	}()

	go func() {
		defer p.wg.Done()
		defer ws.Close()
		buf := make([]byte, 32768)
		for {
			select {
			case <-p.stopCh:
				return
			default:
			}
			n, err := tcp.Read(buf)
			if err != nil {
				log.Writef("[VNCProxy] TCP read error: %v", err)
				return
			}
			if err := ws.WriteMessage(websocket.BinaryMessage, buf[:n]); err != nil {
				log.Writef("[VNCProxy] WebSocket write error: %v", err)
				return
			}
		}
	}()
}

// Stop closes all connections and waits for goroutines to exit.
func (p *VNCProxy) Stop() {
	p.stopOnce.Do(func() { close(p.stopCh) })
	p.mu.Lock()
	if p.wsConn != nil {
		p.wsConn.Close()
	}
	if p.tcpConn != nil {
		p.tcpConn.Close()
	}
	p.mu.Unlock()
	// Close the listener BEFORE wg.Wait() so handleWebSocket can exit
	// and add to the wait group cleanly — otherwise a new connection
	// accepted in the window between listener.Close() and wg.Wait()
	// adds goroutines that never reach Done (SESSION-04).
	if p.listener != nil {
		p.listener.Close()
	}
	p.wg.Wait()
}
