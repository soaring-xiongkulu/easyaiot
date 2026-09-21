package session

import (
	"context"
	"fmt"
	"io"
	"net"
	"strconv"
	"sync"
	"time"

	"golang.org/x/text/encoding"
	"golang.org/x/text/transform"
)

const (
	// Telnet protocol constants
	telnetIAC  = 255
	telnetWILL = 251
	telnetWONT = 252
	telnetDO   = 253
	telnetDONT = 254
	telnetSB   = 250
	telnetSE   = 240

	// Telnet options
	telnetOptBinary          = 0
	telnetOptEcho            = 1
	telnetOptSuppressGoAhead = 3
	telnetOptTerminalType    = 24
	telnetOptNAWS            = 31

	// Sub-negotiation
	telnetTTYPEIs   = 0
	telnetTTYPESend = 1
)

type TelnetSession struct {
	*baseSession
	conn     net.Conn
	cancel   context.CancelFunc
	quit     chan struct{}
	quitOnce sync.Once

	enc            encoding.Encoding    // input(write) codec; nil = utf-8 passthrough
	encoder        transform.Transformer // cached encoder; nil = utf-8 passthrough
	decoder        *encoding.Decoder     // persistent streaming decoder for output(read)
	decodeLeftover []byte                // trailing partial multibyte bytes between reads
	decodeScratch  []byte                // reusable src buffer for decodeOutput
	encScratch     []byte                // reusable dst buffer for encodeInput

	// Telnet option state (configured in Connect, consumed by Write)
	localEcho   bool
	telnetSendMode    string // "character" | "line"
	newlineMode string // "cr" | "crlf"
	lineBuf           []byte
}

func NewTelnetSession(id string) *TelnetSession {
	return &TelnetSession{
		baseSession: &baseSession{
			id:          id,
			sessionType: "telnet",
			status:      StatusDisconnected,
		},
		quit: make(chan struct{}),
	}
}

func (s *TelnetSession) Connect(config ConnectionConfig) error {
	s.SetLogOnConnect(config.LogOnConnect)
	s.setStatus(StatusConnecting)
	if config.Name != "" {
		s.title = config.Name
	} else {
		s.title = fmt.Sprintf("%s:%d", config.Host, config.Port)
	}

	addr := net.JoinHostPort(config.Host, strconv.Itoa(config.Port))
	dialer := net.Dialer{Timeout: 15 * time.Second}
	conn, err := dialer.Dial("tcp", addr)
	if err != nil {
		s.setStatus(StatusError)
		return fmt.Errorf("telnet dial: %w", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	s.conn = conn
	s.cancel = cancel
	s.setStatus(StatusConnected)

	// Store telnet option configuration for use by Write()
	s.localEcho = config.LocalEcho
	s.telnetSendMode = config.TelnetSendMode
	s.newlineMode = config.NewlineMode

	// Proactively negotiate binary transmission, character-at-a-time mode,
	// and terminal type — unless the user opted for passive negotiation.
	if config.TelnetNegotiationMode != "passive" {
		s.conn.Write([]byte{telnetIAC, telnetWILL, telnetOptBinary})
		s.conn.Write([]byte{telnetIAC, telnetDO, telnetOptSuppressGoAhead})
		s.conn.Write([]byte{telnetIAC, telnetWILL, telnetOptTerminalType})

		if cols, rows := s.GetPendingSize(); cols > 0 && rows > 0 {
			s.sendNAWS(cols, rows)
		} else {
			s.sendNAWS(80, 24)
		}
	}

	go s.readLoop(ctx)
	go s.runPostLoginScript(ctx, config.PostLoginScript)

	// Auto-login: send username/password if configured
	if config.User != "" {
		go s.sendAutoLogin(ctx, config.User, config.Password)
	}

	return nil
}

func (s *TelnetSession) readLoop(ctx context.Context) {
	buf := make([]byte, 16384)
	for {
		select {
		case <-ctx.Done():
			return
		default:
		}

		n, err := s.conn.Read(buf)
		if n > 0 {
			s.RecordReadActivity()
			s.handleRead(buf[:n])
		}
		if err != nil {
			if err != io.EOF {
				s.emitData([]byte(fmt.Sprintf("\r\n\x1b[31m[read error: %v]\x1b[0m\r\n", err)))
			} else {
				s.emitData(disconnectNotice("Connection closed by remote host."))
			}
			s.Disconnect()
			return
		}
	}
}

func (s *TelnetSession) handleRead(data []byte) {
	filtered := s.filterIAC(data)
	if len(filtered) > 0 {
		s.emitData(s.decodeOutput(filtered))
	}
}

func (s *TelnetSession) filterIAC(data []byte) []byte {
	var out []byte
	i := 0
	for i < len(data) {
		if data[i] == telnetIAC && i+1 < len(data) {
			cmd := data[i+1]
			switch cmd {
			case telnetWILL, telnetWONT, telnetDO, telnetDONT:
				if i+2 < len(data) {
					s.handleNegotiation(cmd, data[i+2])
					i += 3
					continue
				}
			case telnetSB:
				s.handleSubNegotiation(data, i)
				// Skip to end of sub-negotiation.
				found := false
				for j := i + 2; j < len(data)-1; j++ {
					if data[j] == telnetIAC && data[j+1] == telnetSE {
						i = j + 2
						found = true
						break
					}
				}
				if !found {
					i = len(data)
				}
				continue
			case telnetIAC:
				out = append(out, telnetIAC)
				i += 2
				continue
			default:
				i += 2
				continue
			}
		} else {
			out = append(out, data[i])
			i++
		}
	}
	return out
}

func (s *TelnetSession) handleSubNegotiation(data []byte, start int) {
	if start+3 >= len(data) {
		return
	}
	opt := data[start+2]
	if opt == telnetOptTerminalType && data[start+3] == telnetTTYPESend {
		// Server requests terminal type: reply with "xterm-256color"
		term := []byte("xterm-256color")
		msg := make([]byte, 0, 4+len(term))
		msg = append(msg, telnetIAC, telnetSB, telnetOptTerminalType, telnetTTYPEIs)
		msg = append(msg, term...)
		msg = append(msg, telnetIAC, telnetSE)
		s.conn.Write(msg)
	}
}

func (s *TelnetSession) handleNegotiation(cmd byte, opt byte) {
	switch cmd {
	case telnetWILL:
		// Server offers to do something.
		switch opt {
		case telnetOptBinary, telnetOptSuppressGoAhead:
			s.reply(telnetDO, opt) // Accept
		case telnetOptEcho:
			s.reply(telnetDO, opt) // Accept server echoing
		case telnetOptTerminalType:
			s.reply(telnetDO, opt) // Accept server knows terminal type
		default:
			s.reply(telnetDONT, opt)
		}
	case telnetDO:
		// Server asks us to do something.
		switch opt {
		case telnetOptBinary, telnetOptSuppressGoAhead, telnetOptNAWS, telnetOptTerminalType:
			s.reply(telnetWILL, opt) // Accept
		case telnetOptEcho:
			s.reply(telnetWONT, opt) // We don't echo locally
		default:
			s.reply(telnetWONT, opt)
		}
	}
}

func (s *TelnetSession) reply(cmd byte, opt byte) {
	if s.conn == nil {
		return
	}
	s.conn.Write([]byte{telnetIAC, cmd, opt})
}

func (s *TelnetSession) sendNAWS(cols, rows int) {
	if s.conn == nil {
		return
	}
	data := []byte{
		telnetIAC, telnetSB, telnetOptNAWS,
		byte(cols >> 8), byte(cols & 0xff),
		byte(rows >> 8), byte(rows & 0xff),
		telnetIAC, telnetSE,
	}
	s.conn.Write(data)
}

func (s *TelnetSession) sendAutoLogin(ctx context.Context, user, password string) {
	// Conservative fix (SESSION-05): the previous fixed 1500ms / 1200ms
	// sleeps could land the username in the shell prompt on slow
	// servers. Replace with a shorter initial wait and bail early on
	// context cancel. A full prompt-detection rewrite would require
	// touching the readLoop and is out of scope for a conservative fix.
	time.Sleep(500 * time.Millisecond)

	select {
	case <-ctx.Done():
		return
	default:
	}

	if s.conn != nil {
		s.conn.Write([]byte(user + "\r\n"))
	}

	if password != "" {
		time.Sleep(500 * time.Millisecond)
		select {
		case <-ctx.Done():
			return
		default:
		}
		if s.conn != nil {
			s.conn.Write([]byte(password + "\r\n"))
		}
	}
}

func (s *TelnetSession) runPostLoginScript(ctx context.Context, script string) {
	s.baseSession.RunPostLoginScript(ctx, script, func(data []byte) {
		if s.conn != nil {
			s.conn.Write(data)
		}
	}, s.IsConnected)
}

func (s *TelnetSession) Write(data []byte) error {
	if s.conn == nil {
		return fmt.Errorf("not connected")
	}

	encoded := s.encodeInput(data)

	// Line mode: buffer until \r or \n, then flush
	if s.telnetSendMode == "line" {
		for _, b := range encoded {
			s.lineBuf = append(s.lineBuf, b)
			if b == '\r' || b == '\n' {
				flush := s.lineBuf
				// Apply CRLF translation on the flushed line
				if s.newlineMode == "crlf" {
					var translated []byte
					for _, fb := range flush {
						if fb == '\r' {
							translated = append(translated, '\r', '\n')
						} else {
							translated = append(translated, fb)
						}
					}
					flush = translated
				}
				_, err := s.conn.Write(flush)
				s.lineBuf = s.lineBuf[:0]
				return err
			}
		}
		// Echo each character locally while buffering for visibility
		s.emitData(data)
		return nil
	}

	// Character mode: apply CRLF translation, then send immediately
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

	// Local echo: show typed characters in terminal (for servers that don't echo)
	if err == nil && s.localEcho {
		s.emitData(data)
	}

	return err
}

func (s *TelnetSession) Disconnect() error {
	s.quitOnce.Do(func() {
		close(s.quit)
	})
	if s.cancel != nil {
		s.cancel()
	}
	if s.conn != nil {
		s.conn.Close()
	}
	s.setStatus(StatusDisconnected)
	return nil
}

func (s *TelnetSession) Resize(cols, rows int) error {
	s.SetPendingSize(cols, rows)
	if s.conn == nil {
		return fmt.Errorf("session not connected")
	}
	s.sendNAWS(cols, rows)
	return nil
}

func (s *TelnetSession) IsConnected() bool {
	return s.Status() == StatusConnected
}

// SetEncoding configures the character encoding for this session.
// name: "" / "utf-8" (passthrough) | "gbk" | "gb2312" | "gb18030" |
// "big5" | "shift-jis" | "euc-jp" | "euc-kr".
func (s *TelnetSession) SetEncoding(name string) {
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

// decodeOutput converts a chunk of remote bytes to UTF-8 using the configured
// decoder. Partial trailing multibyte sequences are buffered until the next
// call. Must only be called from the single readLoop goroutine.
func (s *TelnetSession) decodeOutput(data []byte) []byte {
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
// before writing to the remote. Each call handles a complete UTF-8 input.
func (s *TelnetSession) encodeInput(data []byte) []byte {
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
