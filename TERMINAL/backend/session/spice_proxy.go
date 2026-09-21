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

// SPICEProxy bridges WebSocket (frontend spice-html5) to TCP (SPICE server).
// One instance per SPICE session, bound to a random local port.
type SPICEProxy struct {
	listener net.Listener
	target   string
	stopCh   chan struct{}
	stopOnce sync.Once
	wg       sync.WaitGroup
	mu       sync.Mutex
	wsConn   *websocket.Conn
	tcpConn  net.Conn
}

func NewSPICEProxy(target string) *SPICEProxy {
	return &SPICEProxy{
		target: target,
		stopCh: make(chan struct{}),
	}
}

// Start begins listening on a random local port and returns the WebSocket URL.
func (p *SPICEProxy) Start() (string, error) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return "", fmt.Errorf("spice proxy listen: %w", err)
	}
	p.listener = ln

	upgrader := websocket.Upgrader{
		CheckOrigin:  func(r *http.Request) bool { return true },
		Subprotocols: []string{"binary"},
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		ws, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			log.Writef("[SPICEProxy] WebSocket upgrade failed: %v", err)
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
	log.Writef("[SPICEProxy] Listening on ws://127.0.0.1:%d, target: %s", addr.Port, p.target)
	return fmt.Sprintf("ws://127.0.0.1:%d", addr.Port), nil
}

func (p *SPICEProxy) handleWebSocket(ws *websocket.Conn) {
	p.mu.Lock()
	if p.wsConn != nil {
		p.mu.Unlock()
		log.Writef("[SPICEProxy] Rejecting additional WebSocket connection")
		ws.Close()
		return
	}
	p.wsConn = ws
	p.mu.Unlock()
	log.Writef("[SPICEProxy] WebSocket client connected")

	// Allow large SPICE frames (up to 16 MB).
	ws.SetReadLimit(16 << 20)

	defer func() {
		p.mu.Lock()
		if p.wsConn == ws {
			p.wsConn = nil
		}
		p.mu.Unlock()
	}()

	tcp, err := net.DialTimeout("tcp", p.target, 5*time.Second)
	if err != nil {
		log.Writef("[SPICEProxy] TCP dial to %s failed: %v", p.target, err)
		ws.Close()
		return
	}
	log.Writef("[SPICEProxy] TCP connection to %s established", p.target)

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
				log.Writef("[SPICEProxy] WebSocket read error: %v", err)
				return
			}
			if msgType == websocket.BinaryMessage {
				if _, err := tcp.Write(data); err != nil {
					log.Writef("[SPICEProxy] TCP write error: %v", err)
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
				log.Writef("[SPICEProxy] TCP read error: %v", err)
				return
			}
			if err := ws.WriteMessage(websocket.BinaryMessage, buf[:n]); err != nil {
				log.Writef("[SPICEProxy] WebSocket write error: %v", err)
				return
			}
		}
	}()
}

// Stop closes all connections and waits for goroutines to exit.
// Listener is closed before wg.Wait() so handleWebSocket has no
// window to accept and spawn goroutines that never reach Done
// (SESSION-04).
func (p *SPICEProxy) Stop() {
	p.stopOnce.Do(func() { close(p.stopCh) })
	p.mu.Lock()
	if p.wsConn != nil {
		p.wsConn.Close()
	}
	if p.tcpConn != nil {
		p.tcpConn.Close()
	}
	p.mu.Unlock()
	if p.listener != nil {
		p.listener.Close()
	}
	p.wg.Wait()
}
