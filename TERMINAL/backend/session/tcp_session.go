package session

import (
	"fmt"
	"io"
	"net"
	"sync"
	"time"

	"golang.org/x/text/encoding"
	"golang.org/x/text/transform"
)

// TCPSession is a general-purpose "raw TCP" console: it opens a plain TCP
// socket to host:port and shuttles raw bytes between it and the terminal with
// no protocol negotiation. It is the modern stand-in for networking to a
// device that speaks a plaintext/terminal protocol (serial-debug ports,
// telnet-style control planes) without committing to a specific negotiation.
// Reuses the same byte-stream structure as the serial session, including the
// optional byte-helper options (encoding / newline / local echo).
type TCPSession struct {
	baseSession
	conn     net.Conn
	quit     chan struct{}
	quitOnce sync.Once

	encMu          sync.RWMutex
	enc            encoding.Encoding
	decoder        *encoding.Decoder
	encoder        *encoding.Encoder
	decodeLeftover []byte
	decodeScratch  []byte
	encScratch     []byte

	newlineMode string // "cr" (default, no translation) | "crlf"
	localEcho   bool
}

func NewTCPSession(id string) *TCPSession {
	return &TCPSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "tcp",
			status:      StatusDisconnected,
		},
		quit: make(chan struct{}),
	}
}

func (s *TCPSession) Connect(config ConnectionConfig) error {
	s.SetLogOnConnect(config.LogOnConnect)
	if config.Host == "" {
		s.setStatus(StatusError)
		return fmt.Errorf("tcp host is required")
	}
	port := config.Port
	if port <= 0 {
		port = 23
	}
	s.newlineMode = config.NewlineMode
	s.localEcho = config.LocalEcho
	s.setupEncoding(config.Encoding)
	s.setStatus(StatusConnecting)
	s.title = fmt.Sprintf("%s:%d", config.Host, port)

	addr := net.JoinHostPort(config.Host, fmt.Sprintf("%d", port))
	conn, err := net.DialTimeout("tcp", addr, 10*time.Second)
	if err != nil {
		s.setStatus(StatusError)
		return fmt.Errorf("tcp dial %s: %w", addr, err)
	}
	// conn is assigned once before readLoop starts; Write() on a closed conn
	// returns an error, matching the SSH/Telnet convention of not nil-ing
	// closed handles.
	s.conn = conn
	s.setStatus(StatusConnected)

	go s.readLoop()
	return nil
}

// setupEncoding configures the character encoding for this session.
// name: "" / "utf-8" (passthrough) | "gbk" | "gb2312" | "gb18030" |
// "big5" | "shift-jis" | "euc-jp" | "euc-kr".
func (s *TCPSession) setupEncoding(name string) {
	enc := encodingByName(name)
	s.encMu.Lock()
	defer s.encMu.Unlock()
	s.enc = enc
	if enc == nil {
		s.decoder = nil
		s.encoder = nil
	} else {
		s.decoder = enc.NewDecoder()
		s.encoder = enc.NewEncoder()
	}
	s.decodeLeftover = nil
}

// decodeOutput converts a chunk of remote bytes to UTF-8 using the configured
// decoder. Partial trailing multibyte sequences are buffered until the next
// call. Must only be called from the single readLoop goroutine.
func (s *TCPSession) decodeOutput(data []byte) []byte {
	s.encMu.Lock()
	defer s.encMu.Unlock()
	if s.decoder == nil {
		return data
	}
	s.decodeScratch = s.decodeScratch[:0]
	s.decodeScratch = append(s.decodeScratch, s.decodeLeftover...)
	s.decodeScratch = append(s.decodeScratch, data...)
	src := s.decodeScratch

	var out []byte
	dst := make([]byte, 8192)
	for {
		nDst, nSrc, err := s.decoder.Transform(dst, src, false)
		out = append(out, dst[:nDst]...)
		src = src[nSrc:]
		if err == transform.ErrShortDst {
			continue
		}
		break
	}
	if len(src) > 0 {
		s.decodeLeftover = append(s.decodeLeftover[:0], src...)
	} else {
		s.decodeLeftover = src[:0]
	}
	return out
}

// encodeInput converts user keystrokes (UTF-8) to the configured encoding
// before writing to the remote. Each call handles a complete UTF-8 input.
func (s *TCPSession) encodeInput(data []byte) []byte {
	s.encMu.RLock()
	encoder := s.encoder
	s.encMu.RUnlock()
	if encoder == nil {
		return data
	}
	encoder.Reset()
	s.encScratch = s.encScratch[:0]
	nDst, _, err := encoder.Transform(s.encScratch, data, true)
	if err != nil && err != transform.ErrShortSrc {
		return data
	}
	return s.encScratch[:nDst]
}

func (s *TCPSession) readLoop() {
	// 16 KiB reused read buffer; emitData copies the bytes so buf[:n] can be
	// handed off without an extra allocation.
	buf := make([]byte, 16384)
	for {
		select {
		case <-s.quit:
			return
		default:
		}
		n, err := s.conn.Read(buf)
		if n > 0 {
			s.emitData(s.decodeOutput(buf[:n]))
		}
		if err != nil {
			if err != io.EOF {
				s.emitData([]byte(fmt.Sprintf("\r\n\x1b[31m[TCP read error: %v]\x1b[0m\r\n", err)))
			} else {
				s.emitData(disconnectNotice("Connection closed by remote host."))
			}
			s.Disconnect()
			return
		}
	}
}

func (s *TCPSession) Write(data []byte) error {
	if s.conn == nil {
		return fmt.Errorf("tcp connection not connected")
	}

	encoded := s.encodeInput(data)

	// Translate \r to \r\n when newline mode is CRLF.
	if s.newlineMode == "crlf" {
		var translated []byte
		for _, b := range encoded {
			if b == '\r' {
				translated = append(translated, '\r', '\n')
			} else {
				translated = append(translated, b)
			}
		}
		encoded = translated
	}

	_, err := s.conn.Write(encoded)

	// Local echo: show typed characters in terminal when remote doesn't echo.
	if err == nil && s.localEcho {
		s.emitData(data)
	}

	return err
}

func (s *TCPSession) Disconnect() error {
	s.quitOnce.Do(func() {
		close(s.quit)
		if s.conn != nil {
			_ = s.conn.Close()
		}
		s.setStatus(StatusDisconnected)
	})
	return nil
}

func (s *TCPSession) Resize(cols, rows int) error {
	// Raw TCP has no terminal-size negotiation; store for consistency (no-op).
	s.SetPendingSize(cols, rows)
	return nil
}

func (s *TCPSession) IsConnected() bool {
	return s.Status() == StatusConnected
}
