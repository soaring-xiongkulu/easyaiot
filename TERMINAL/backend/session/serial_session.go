package session

import (
	"fmt"
	"io"
	"sync"

	"go.bug.st/serial"
	"golang.org/x/text/encoding"
	"golang.org/x/text/transform"
)

// SerialConfig holds serial port connection parameters.
type SerialConfig struct {
	PortName string
	BaudRate int
	DataBits int
	StopBits serial.StopBits
	Parity   serial.Parity
}

type SerialSession struct {
	baseSession
	port     serial.Port
	config   SerialConfig
	quit     chan struct{}
	quitOnce sync.Once

	mu             sync.RWMutex
	enc            encoding.Encoding
	decoder        *encoding.Decoder
	encoder        *encoding.Encoder
	decodeLeftover []byte
	decodeScratch  []byte
	encScratch     []byte

	localEcho   bool
	newlineMode string // "cr" | "crlf"
}

func NewSerialSession(id string) *SerialSession {
	return &SerialSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "serial",
			status:      StatusDisconnected,
		},
		quit: make(chan struct{}),
	}
}

func (s *SerialSession) Connect(config ConnectionConfig) error {
	s.SetLogOnConnect(config.LogOnConnect)
	s.localEcho = config.LocalEcho
	s.newlineMode = config.NewlineMode
	// Serial sessions ignore other ConnectionConfig fields; they receive
	// their real config via SetSerialConfig before Connect is called.
	if s.config.PortName == "" || s.config.BaudRate == 0 {
		s.setStatus(StatusError)
		return fmt.Errorf("serial config not set: call SetSerialConfig before Connect")
	}
	s.setStatus(StatusConnecting)
	s.title = fmt.Sprintf("%s@%d", s.config.PortName, s.config.BaudRate)

	mode := &serial.Mode{
		BaudRate: s.config.BaudRate,
		DataBits: s.config.DataBits,
		StopBits: s.config.StopBits,
		Parity:   s.config.Parity,
	}

	port, err := serial.Open(s.config.PortName, mode)
	if err != nil {
		s.setStatus(StatusError)
		return fmt.Errorf("serial open %s: %w", s.config.PortName, err)
	}
	// s.port is assigned once before readLoop starts. Write() is safe to call
	// on a closed port (returns an error), matching SSH/Telnet convention of
	// not nil-ing closed handles.
	s.port = port
	s.setStatus(StatusConnected)

	go s.readLoop()
	return nil
}

// normalizeNewlines converts lone \r to \r\n so that carriage returns
// from serial devices produce proper line breaks in the terminal.
// \r\n sequences are kept as-is.
// Special cases: when \r is followed by another \r (double Enter)
// or when \r is at end of data (trailing Enter), don't add extra \n
// to avoid extra blank lines on empty command echo.
func normalizeNewlines(data []byte) []byte {
	out := make([]byte, 0, len(data)+16)
	for i := 0; i < len(data); i++ {
		b := data[i]
		if b == '\r' {
			// Check if followed by \n (keep as-is)
			if i+1 < len(data) && data[i+1] == '\n' {
				out = append(out, b)
			} else if i+1 < len(data) && data[i+1] == '\r' {
				// Double \r (double Enter): just pass through, don't add extra newline
				// This avoids the extra blank line when user presses Enter on empty prompt
				out = append(out, b)
			} else if i+1 >= len(data) {
				// Trailing \r at end of data: this is likely an empty Enter
				// Don't convert to avoid extra blank line from echo
				out = append(out, b)
			} else {
				// Lone \r not at end, convert to \r\n
				out = append(out, '\r', '\n')
			}
		} else {
			out = append(out, b)
		}
	}
	return out
}

func (s *SerialSession) SetSerialConfig(cfg SerialConfig) {
	s.config = cfg
}

// SetEncoding configures the character encoding for this session.
// name: "" / "utf-8" (passthrough) | "gbk" | "gb2312" | "gb18030" |
// "big5" | "shift-jis" | "euc-jp" | "euc-kr".
func (s *SerialSession) SetEncoding(name string) {
	enc := encodingByName(name)
	s.mu.Lock()
	s.enc = enc
	if enc == nil {
		s.decoder = nil
		s.encoder = nil
	} else {
		s.decoder = enc.NewDecoder()
		s.encoder = enc.NewEncoder()
	}
	s.decodeLeftover = nil
	s.mu.Unlock()
}

// decodeOutput converts a chunk of device bytes to UTF-8 using the configured
// decoder. Partial trailing multibyte sequences are buffered until the next
// call. Must only be called from the single readLoop goroutine.
func (s *SerialSession) decodeOutput(data []byte) []byte {
	s.mu.Lock()
	defer s.mu.Unlock()
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
// before writing to the device. Each call handles a complete UTF-8 input.
func (s *SerialSession) encodeInput(data []byte) []byte {
	s.mu.RLock()
	encoder := s.encoder
	s.mu.RUnlock()
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

func (s *SerialSession) readLoop() {
	// 16 KiB reused read buffer; emitData/emitBinary's callbacks copy the
	// bytes, so buf[:n] can be handed off without an extra allocation.
	buf := make([]byte, 16384)
	for {
		n, err := s.port.Read(buf)
		if n > 0 {
			data := buf[:n]
			if s.IsZmodemMode() {
				s.emitBinary(data)
			} else if looksLikeZmodemHeader(data) {
				s.SetZmodemMode(true)
				s.emitBinary(data)
			} else {
				normalized := normalizeNewlines(data)
				decoded := s.decodeOutput(normalized)
				s.emitData(decoded)
			}
		}
		if err != nil {
			if err != io.EOF {
				s.emitData([]byte(fmt.Sprintf("\r\n\x1b[31m[Serial read error: %v]\x1b[0m\r\n", err)))
			} else {
				s.emitData(disconnectNotice("Serial device disconnected."))
			}
			s.Disconnect()
			return
		}
	}
}

func (s *SerialSession) Write(data []byte) error {
	if s.port == nil {
		return fmt.Errorf("serial port not connected")
	}

	encoded := s.encodeInput(data)

	// Translate \r to \r\n when newline mode is CRLF
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

	_, err := s.port.Write(encoded)

	// Local echo: show typed characters in terminal when device doesn't echo
	if err == nil && s.localEcho {
		s.emitData(data)
	}

	return err
}

func (s *SerialSession) Disconnect() error {
	s.quitOnce.Do(func() {
		s.SetZmodemMode(false)
		close(s.quit)
		if s.port != nil {
			s.port.Close()
		}
		s.setStatus(StatusDisconnected)
	})
	return nil
}

func (s *SerialSession) Resize(cols, rows int) error {
	// Serial sessions don't support terminal resize in the SSH sense.
	// Store pending size for consistency but it's a no-op.
	s.SetPendingSize(cols, rows)
	return nil
}

func (s *SerialSession) IsConnected() bool {
	return s.Status() == StatusConnected
}

// ListSerialPorts returns the names of available serial ports.
func ListSerialPorts() ([]string, error) {
	ports, err := serial.GetPortsList()
	if err != nil {
		return nil, err
	}
	names := make([]string, len(ports))
	for i, p := range ports {
		names[i] = p
	}
	return names, nil
}
