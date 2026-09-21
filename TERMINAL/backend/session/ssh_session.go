package session

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"os"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"golang.org/x/crypto/ssh"
	"golang.org/x/text/encoding"
	"golang.org/x/text/encoding/japanese"
	"golang.org/x/text/encoding/korean"
	"golang.org/x/text/encoding/simplifiedchinese"
	"golang.org/x/text/encoding/traditionalchinese"
	"golang.org/x/text/transform"

	"easyaiot/terminal/backend/log"
)

const (
	// Keepalive cadence. This is pure keep-alive (no reply awaited): every
	// interval we send one global request just to keep traffic flowing so a
	// server/NAT/firewall idle timeout doesn't drop an otherwise-healthy
	// connection. Dead-connection detection is NOT done here — see readLoop
	// (EOF) and the OS-level TCP keepalive set in Connect.
	sshKeepAliveInterval = 90 * time.Second

	// Windows OpenSSH announces itself with a "for_Windows" marker in its
	// SSH identification string (e.g. "SSH-2.0-OpenSSH_for_Windows_9.5"),
	// unlike Linux/BSD OpenSSH ("SSH-2.0-OpenSSH_9.9p1"). We match on the
	// marker to detect the remote OS at handshake time with zero extra
	// round-trips.
	windowsOpenSSHMarker = "for_Windows"

	// RemoteOS value reported to the frontend when the marker matches.
	remoteOSWindowsOpenSSH = "windows-openssh"
)

type SSHSession struct {
	baseSession
	// outputRouteMu makes the binary/text routing decision atomic with
	// EndZmodem. Without it, readLoop could observe binary mode, get paused,
	// then emit post-transfer shell output as binary after EndZmodem returned.
	outputRouteMu       sync.Mutex
	client              *ssh.Client
	session             *ssh.Session
	stdin               io.WriteCloser
	stdout              io.Reader
	stderr              io.Reader
	quit                chan struct{}
	quitOnce            sync.Once
	authAnswerCh        chan []byte
	expectOutput        *postLoginOutputBuffer
	x11Forwarder        *x11Forwarder
	integrationTempPath string

	// osc7 extracts OSC-7 cwd reports emitted by the remote shell or tools.
	// Only used from the readLoop goroutine.
	osc7 osc7Scanner

	enc            encoding.Encoding     // input(write) codec; nil = utf-8 passthrough
	encoder        transform.Transformer // cached encoder; nil = utf-8 passthrough (F-003)
	decoder        *encoding.Decoder     // persistent streaming decoder for output(read)
	decodeLeftover []byte                // trailing partial multibyte bytes between reads
	decodeScratch  []byte                // reusable src buffer for decodeOutput (F-002)
	encScratch     []byte                // reusable dst buffer for encodeInput (F-003)

	// Disconnect diagnostics (see readLoop / disconnect logs).
	lastRecv atomic.Value // []byte: tail of most recent server output (diagnostics)
	lastSent atomic.Value // []byte: most recent input sent to server (diagnostics)

	// remoteOS records the detected remote operating system ("windows-openssh"
	// for Microsoft's OpenSSH for Windows, "" otherwise). Set once during
	// Connect from the server identification string.
	remoteOS string

	// cwdHookInstalled records that the runtime OSC-7 cwd hook has already
	// been written to this session's shell, so re-toggling follow does not
	// re-send the snippet. Session objects are recreated on reconnect, so the
	// flag resets naturally and the reconnect re-injection still fires.
	cwdHookInstalled atomic.Bool
}

func NewSSHSession(id string) *SSHSession {
	return &SSHSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "ssh",
			status:      StatusDisconnected,
		},
		quit: make(chan struct{}),
	}
}

// RemoteOS returns the detected remote operating system. For Microsoft's
// OpenSSH for Windows this is "windows-openssh"; otherwise it is empty
// (undetermined). Read-only and set once during Connect.
func (s *SSHSession) RemoteOS() string {
	return s.remoteOS
}

func shouldPromptForSSHPassword(config ConnectionConfig) bool {
	if config.Password != "" {
		return false
	}
	return config.AuthType == "" || config.AuthType == "password"
}

func (s *SSHSession) Connect(config ConnectionConfig) error {
	s.SetLogOnConnect(config.LogOnConnect)
	s.setStatus(StatusConnecting)
	if config.Name != "" {
		s.title = config.Name
	} else {
		s.title = fmt.Sprintf("%s@%s", config.User, config.Host)
	}

	// Set up keyboard-interactive auth input channel.
	s.mu.Lock()
	s.authAnswerCh = make(chan []byte, 256)
	s.expectOutput = newPostLoginOutputBuffer()
	s.mu.Unlock()
	defer func() {
		s.mu.Lock()
		s.authAnswerCh = nil
		s.mu.Unlock()
	}()

	// For password auth without a stored password, prompt in the terminal
	// before the SSH handshake. This covers servers that do not advertise
	// keyboard-interactive support (the kbCallback fallback below).
	if shouldPromptForSSHPassword(config) {
		s.emitData([]byte("\r\nPassword: "))
		var answer string
	promptLoop:
		for {
			select {
			case data := <-s.authAnswerCh:
				for _, b := range data {
					switch b {
					case '\r', '\n':
						break promptLoop
					case '\x03': // Ctrl+C
						s.emitData([]byte("^C\r\n"))
						return fmt.Errorf("auth cancelled")
					case 127, '\b': // Backspace
						if len(answer) > 0 {
							answer = answer[:len(answer)-1]
						}
					case '\x15': // Ctrl+U
						answer = ""
					default:
						answer += string(b)
					}
				}
			case <-time.After(120 * time.Second):
				s.emitData([]byte("\r\nAuth timeout\r\n"))
				return fmt.Errorf("auth timeout")
			}
		}
		s.emitData([]byte("\r\n"))
		config.Password = answer
	}

	// Auto-answer keyboard-interactive challenges with the saved password on
	// the FIRST challenge. Many servers (e.g. SuSE/NetIQ) advertise only
	// keyboard-interactive (no "password" method), so the ssh.Password method
	// above is rejected and the callback gets invoked with a "Password: "
	// prompt. Without this, the user would be prompted for a password that is
	// already saved. If the saved password is wrong, the server re-challenges
	// and we fall through to interactive prompting so the user can type the
	// correct one.
	var kbAutoAnswered int32
	kbCallback := func(user, instruction string, questions []string, echos []bool) ([]string, error) {
		if isSavedPasswordChallenge(config, questions, echos) && atomic.CompareAndSwapInt32(&kbAutoAnswered, 0, 1) {
			answers := make([]string, len(questions))
			for i := range questions {
				answers[i] = config.Password
			}
			return answers, nil
		}
		answers := make([]string, len(questions))
		for i, q := range questions {
			s.emitData([]byte("\r\n" + q + " "))
			var answer string
		loop:
			for {
				select {
				case data := <-s.authAnswerCh:
					for _, b := range data {
						switch b {
						case '\r', '\n':
							break loop
						case '\x03':
							s.emitData([]byte("^C\r\n"))
							return nil, fmt.Errorf("auth cancelled")
						case 127, '\b':
							if len(answer) > 0 {
								answer = answer[:len(answer)-1]
								if echos[i] {
									s.emitData([]byte("\b \b"))
								}
							}
						case '\x15': // Ctrl+U
							answer = ""
						default:
							answer += string(b)
							if echos[i] {
								s.emitData([]byte{b})
							}
						}
					}
				case <-time.After(120 * time.Second):
					s.emitData([]byte("\r\nAuth timeout\r\n"))
					return nil, fmt.Errorf("auth timeout")
				}
			}
			s.emitData([]byte("\r\n"))
			answers[i] = answer
		}
		return answers, nil
	}

	addr := net.JoinHostPort(config.Host, strconv.Itoa(config.Port))
	newConfig := func(challenge ssh.KeyboardInteractiveChallenge) sshClientConfigFactory {
		return func() (*ssh.ClientConfig, func(), error) {
			authMethods, cleanup, err := makeSSHAuthMethodsForAttempt(config, challenge)
			if err != nil {
				return nil, nil, err
			}
			return &ssh.ClientConfig{
				User:            config.User,
				Auth:            authMethods,
				Timeout:         30 * time.Second,
				HostKeyCallback: ssh.InsecureIgnoreHostKey(),
			}, cleanup, nil
		}
	}
	var keyboardConfig sshClientConfigFactory
	if config.AuthType != "kerberos" {
		keyboardConfig = newConfig(kbCallback)
	}
	client, err := dialSSHWithAuthRetry(addr, newConfig(nil), keyboardConfig, func() (net.Conn, error) {
		return dialFirstHop(addr, config.Proxy)
	})
	if err != nil {
		s.setStatus(StatusError)
		return err
	}

	// Detect Windows OpenSSH from the server identification string exchanged
	// during the handshake. This is available before any auth/shell and needs
	// no extra round-trip; the marker "for_Windows" only appears in Microsoft's
	// OpenSSH fork.
	if strings.Contains(string(client.ServerVersion()), windowsOpenSSHMarker) {
		s.remoteOS = remoteOSWindowsOpenSSH
	}

	session, err := client.NewSession()
	if err != nil {
		client.Close()
		s.setStatus(StatusError)
		return fmt.Errorf("new session: %w", err)
	}

	if config.AgentForwarding {
		if err := requestAgentForwarding(client, session); err != nil {
			// Match OpenSSH -A semantics: forwarding failure is visible but does
			// not discard an otherwise usable SSH connection. This commonly
			// happens when AllowAgentForwarding is disabled on the server.
			s.emitData([]byte("\r\n\x1b[33m[ssh agent forwarding: " + err.Error() + "]\x1b[0m\r\n"))
		}
	}

	modes := ssh.TerminalModes{
		ssh.ECHO:          1,
		ssh.TTY_OP_ISPEED: 38400,
		ssh.TTY_OP_OSPEED: 38400,
	}

	cols, rows := s.getInitialSize(80, 24)

	// X11 forwarding: per RFC 4254 §6.3.1, x11-req is a *channel request*
	// sent on the session channel. Sending it via client.SendRequest
	// routes it through the global-request transport path and OpenSSH
	// servers silently return REQUEST_FAILURE. We send it BEFORE
	// RequestPty so the SSH server has $DISPLAY ready for the initial
	// shell.
	if config.X11Forwarding {
		xauthPath := os.Getenv("XAUTHORITY")
		if xauthPath == "" {
			if home, herr := os.UserHomeDir(); herr == nil {
				xauthPath = home + "/.Xauthority"
			}
		}
		resolvedDisplay := ResolveSSHX11Display()
		fwd, ferr := startX11Forward(client, session, xauthPath, resolvedDisplay)
		switch {
		case ferr == nil, errors.Is(ferr, errX11TrustedFallback):
			s.x11Forwarder = fwd
		default:
			s.emitData([]byte("\r\n\x1b[31m[x11: " + ferr.Error() + "]\x1b[0m\r\n"))
		}
		if s.x11Forwarder != nil {
			s.x11Forwarder.onError = func(msg string) {
				s.emitData([]byte("\r\n\x1b[33m" + msg + "\x1b[0m\r\n"))
			}
		}
	}

	if err := session.RequestPty("xterm-256color", rows, cols, modes); err != nil {
		session.Close()
		client.Close()
		s.setStatus(StatusError)
		return fmt.Errorf("request pty: %w", err)
	}

	stdinPipe, err := session.StdinPipe()
	if err != nil {
		session.Close()
		client.Close()
		s.setStatus(StatusError)
		return fmt.Errorf("stdin pipe: %w", err)
	}

	stdoutPipe, err := session.StdoutPipe()
	if err != nil {
		session.Close()
		client.Close()
		s.setStatus(StatusError)
		return fmt.Errorf("stdout pipe: %w", err)
	}

	stderrPipe, err := session.StderrPipe()
	if err != nil {
		session.Close()
		client.Close()
		s.setStatus(StatusError)
		return fmt.Errorf("stderr pipe: %w", err)
	}

	// Shell integration changes normal shell startup, so it can be disabled.
	startCmd, integrationTempPath := "", ""
	if config.shellIntegrationEnabled() {
		startCmd, integrationTempPath = injectShellIntegration(client)
	}
	if startCmd != "" {
		if err := session.Start(startCmd); err != nil {
			sshRemoveRemoteTemp(client, integrationTempPath)
			integrationTempPath = ""
			log.Writef("ssh: integration start failed, falling back to plain shell: %v", err)
			if err := session.Shell(); err != nil {
				session.Close()
				client.Close()
				s.setStatus(StatusError)
				return fmt.Errorf("shell: %w", err)
			}
		}
	} else if err := session.Shell(); err != nil {
		session.Close()
		client.Close()
		s.setStatus(StatusError)
		return fmt.Errorf("shell: %w", err)
	}

	s.client = client
	s.session = session
	s.integrationTempPath = integrationTempPath
	s.stdin = stdinPipe
	s.stdout = stdoutPipe
	s.stderr = stderrPipe
	s.setStatus(StatusConnected)

	// Apply pending terminal size if one was set before connection.
	if cols, rows := s.GetPendingSize(); cols > 0 && rows > 0 {
		_ = s.session.WindowChange(rows, cols)
	}

	go func() {
		werr := session.Wait()
		last, _ := s.lastRecv.Load().([]byte)
		sent, _ := s.lastSent.Load().([]byte)
		log.Writef("ssh disconnect: session.Wait returned (%v), %s lastRecv=%s lastSent=%s", werr, s.kaDiag(), tailHex(last, 64), tailHex(sent, 32))
		s.Disconnect()
	}()

	go s.readLoop()
	go s.readStderr()
	go s.startKeepAlive()
	go s.runPostLoginAutomation(config)

	return nil
}

// isSavedPasswordChallenge limits automatic answers to an unambiguous
// password-only prompt. Key passphrases and password+OTP challenges remain
// interactive so credentials are never sent to the wrong question.
func isSavedPasswordChallenge(config ConnectionConfig, questions []string, echos []bool) bool {
	return (config.AuthType == "" || config.AuthType == "password") &&
		config.Password != "" && len(questions) == 1 && len(echos) == 1 && !echos[0]
}

func (s *SSHSession) readStderr() {
	buf := make([]byte, 4096)
	for {
		n, err := s.stderr.Read(buf)
		if n > 0 {
			// Prefix stderr output so it can be distinguished in the UI
			// stderr is emitted raw (not decoded): it is a separate byte stream and
			// sharing the stdout decoder's leftover buffer could corrupt stdout. In
			// normal PTY shell sessions stderr is merged into the PTY (stdout) anyway.
			data := append([]byte("\r\n\x1b[31m[stderr] \x1b[0m"), buf[:n]...)
			s.emitData(data)
		}
		if err != nil {
			return
		}
	}
}

func (s *SSHSession) readLoop() {
	// 16K read buffer (F-001) reused across iterations. Each consumer either
	// copies into its own storage (lastRecv, decodeOutput, offerExpectOutput's
	// string conversion) or passes the slice to a callback that owns the data
	// lifecycle (emitData / emitBinary), so reusing the backing array is safe.
	buf := make([]byte, 16*1024)
	for {
		n, err := s.stdout.Read(buf)
		if n > 0 {
			s.RecordReadActivity()
			data := buf[:n]
			// lastRecv outlives this iteration (Disconnect logs it after
			// readLoop returns) so it must hold an independent copy. It
			// keeps the RAW server bytes (diagnostics), not the cleaned
			// stream below.
			s.lastRecv.Store(append([]byte(nil), data...))
			// OSC-7 extraction runs on the RAW byte stream, BEFORE decoding:
			// the sequence is pure ASCII while legacy codecs (GBK/Big5/...)
			// could mangle its bytes or withhold a fragment in their
			// cross-chunk multibyte leftover. The cwd itself is percent-
			// decoded UTF-8 and goes straight to the sink, never back into
			// the terminal stream. The cleaned remainder replaces the data
			// for every downstream consumer so stripped sequences never
			// render. During zmodem transfers the raw bytes are emitted
			// unchanged (binary fidelity); the scanner still runs so its
			// state cannot desync.
			cwd, cleaned, found := s.osc7.Feed(data)
			if found && TerminalCwdSink != nil {
				TerminalCwdSink(s.id, cwd)
			}
			s.offerExpectOutput(cleaned)
			s.outputRouteMu.Lock()
			if s.IsZmodemMode() {
				s.emitBinary(data)
			} else if looksLikeZmodemHeader(data) {
				log.Writef("ssh: zmodem header detected in output, switching to binary mode (may be a false positive on vim/TUI output)")
				s.baseSession.SetZmodemMode(true)
				s.emitBinary(data)
			} else {
				s.emitData(s.decodeOutput(cleaned))
			}
			s.outputRouteMu.Unlock()
		}
		if err != nil {
			if err != io.EOF {
				log.Writef("ssh disconnect: read error: %v, %s", err, s.kaDiag())
				s.emitData([]byte(fmt.Sprintf("\r\n\x1b[31m[read error: %v]\x1b[0m\r\n", err)))
			} else {
				last, _ := s.lastRecv.Load().([]byte)
				sent, _ := s.lastSent.Load().([]byte)
				log.Writef("ssh disconnect: remote closed (EOF), %s lastRecv=%s lastSent=%s", s.kaDiag(), tailHex(last, 64), tailHex(sent, 32))
				s.emitData(disconnectNotice("Connection closed by remote host."))
			}
			s.Disconnect()
			return
		}
	}
}

// tailHex returns up to the last max bytes of b as hex, for disconnect
// diagnostics (what the server sent right before closing).
func tailHex(b []byte, max int) string {
	if len(b) > max {
		b = b[len(b)-max:]
	}
	return fmt.Sprintf("% x", b)
}

// kaDiag formats idle state for disconnect diagnostics: how long since the
// last byte from the server. Keepalive here is send-only (no reply awaited),
// so there is no failure/last-OK state to report — a disconnect is detected
// by readLoop (EOF) or the OS TCP keepalive, not by this loop.
func (s *SSHSession) kaDiag() string {
	return fmt.Sprintf("idle=%v", s.idleSince().Truncate(time.Second))
}

func (s *SSHSession) offerExpectOutput(data []byte) {
	s.mu.RLock()
	output := s.expectOutput
	s.mu.RUnlock()
	if output != nil {
		output.Append(data)
	}
}

func (s *SSHSession) runPostLoginAutomation(config ConnectionConfig) {
	if len(config.PostLoginExpectSteps) > 0 {
		s.runPostLoginExpect(config)
		return
	}
	s.runPostLoginScript(config.PostLoginScript)
}

func (s *SSHSession) runPostLoginExpect(config ConnectionConfig) {
	// Wait for shell to finish initialization so the first prompt can be matched.
	if !s.waitIdle(5*time.Second, 300*time.Millisecond) {
		return
	}
	s.mu.RLock()
	output := s.expectOutput
	s.mu.RUnlock()
	if output == nil {
		return
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	go func() {
		select {
		case <-s.quit:
			cancel()
		case <-ctx.Done():
		}
	}()

	err := runPostLoginExpectAutomation(ctx, postLoginExpectAutomationConfig{
		Steps: config.PostLoginExpectSteps,
		Variables: map[string]string{
			"host":     config.Host,
			"user":     config.User,
			"password": config.Password,
		},
		Output: output,
		Send: func(data []byte) error {
			if s.stdin == nil {
				return fmt.Errorf("not connected")
			}
			_, err := s.stdin.Write(s.encodeInput(data))
			return err
		},
		IsConnected:    func() bool { return s.Status() == StatusConnected },
		DefaultTimeout: 10 * time.Second,
	})
	if err != nil && s.Status() == StatusConnected {
		s.emitData([]byte(fmt.Sprintf("\r\n\x1b[33m[post-login expect: %v]\x1b[0m\r\n", err)))
	}
}

func (s *SSHSession) runPostLoginScript(script string) {
	s.baseSession.RunPostLoginScript(context.Background(), script, func(data []byte) {
		if s.stdin != nil {
			s.stdin.Write(s.encodeInput(data))
		}
	}, s.IsConnected)
}

func (s *SSHSession) startKeepAlive() {
	ticker := time.NewTicker(sshKeepAliveInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			if s.Status() != StatusConnected {
				return
			}
			// Pure keep-alive: send one global request just to keep traffic
			// flowing, and do NOT wait for a reply. wantReply=false means
			// crypto/ssh takes no lock and returns immediately, so a slow or
			// silent server can never stall this loop (an earlier wantReply=true
			// version leaked a goroutine holding mux.globalSentMu, which wedged
			// all later keepalives and let the connection idle out). Detecting a
			// dead connection is readLoop's job (EOF) plus the OS TCP keepalive.
			_, _, _ = s.client.SendRequest("keepalive@openssh.com", false, nil)

		case <-s.quit:
			return
		}
	}
}

func (s *SSHSession) Write(data []byte) error {
	// During keyboard-interactive auth, route input to the auth callback.
	s.mu.RLock()
	ch := s.authAnswerCh
	s.mu.RUnlock()
	if ch != nil {
		ch <- data
		return nil
	}
	if s.stdin == nil {
		return fmt.Errorf("not connected")
	}
	enc := s.encodeInput(data)
	s.lastSent.Store(append([]byte(nil), enc...))
	_, err := s.stdin.Write(enc)
	return err
}

// Disconnect tears down the SSH session. It uses sync.Once so the entire
// teardown sequence executes exactly once, regardless of how many goroutines
// call Disconnect concurrently (session.Wait, readLoop error, keepalive
// failure, or explicit user close).
func (s *SSHSession) Disconnect() error {
	s.quitOnce.Do(func() {
		s.SetZmodemMode(false)
		close(s.quit)
		if s.x11Forwarder != nil {
			s.x11Forwarder.stop()
			s.x11Forwarder = nil
		}
		if s.session != nil {
			s.session.Close()
		}
		if s.client != nil {
			sshCleanupRemoteTemp(s.client, s.integrationTempPath)
			s.integrationTempPath = ""
			s.client.Close()
		}
		s.setStatus(StatusDisconnected)
	})
	return nil
}

// InjectCwdHook installs the OSC-7 cwd reporting hook into the shell that is
// already running on this session's pty (typed in via stdin). The shell is
// detected over a separate exec channel, exactly like startup injection. The
// hook is installed only once per session; a failed attempt stays un-flagged
// so a later retry re-runs detection. It reports whether the hook was
// injected NOW (false means it was already installed from an earlier call).
func (s *SSHSession) InjectCwdHook() (bool, error) {
	if s.cwdHookInstalled.Load() {
		return false, nil
	}
	if s.client == nil {
		return false, fmt.Errorf("ssh session not connected")
	}
	shell, err := sshRunCommand(s.client, "echo $SHELL", "", sshIntegrationTimeout)
	if err != nil {
		return false, fmt.Errorf("detect shell: %w", err)
	}
	snippet, ok := buildRuntimeCwdHook(strings.TrimSpace(shell))
	if !ok {
		return false, fmt.Errorf("unsupported shell for cwd hook: %s", strings.TrimSpace(shell))
	}
	if err := s.Write([]byte(snippet)); err != nil {
		return false, err
	}
	s.cwdHookInstalled.Store(true)
	return true, nil
}

// CwdHookInstalled reports whether the runtime OSC-7 cwd hook has already
// been typed into this session's shell. The frontend checks it before its
// confirmation dialog: an already-injected session never prompts again.
func (s *SSHSession) CwdHookInstalled() bool {
	return s.cwdHookInstalled.Load()
}

func (s *SSHSession) Resize(cols, rows int) error {
	// Always save the desired size so it can be applied after Connect finishes.
	s.SetPendingSize(cols, rows)
	if s.session == nil {
		// The frontend fits the terminal as soon as a session is created, which
		// races Connect(). The pending size above is retained and applied once
		// Connect establishes the shell channel, so a nil channel here is a
		// no-op (the size still lands), not a failure worth surfacing — it only
		// produces spurious "session not connected" errors in the dev log.
		return nil
	}
	return s.session.WindowChange(rows, cols)
}

func (s *SSHSession) IsConnected() bool {
	return s.Status() == StatusConnected
}

// SetEncoding configures the character encoding for this session.
// name: "" / "utf-8" (passthrough) | "gbk" | "gb2312" | "gb18030" |
// "big5" | "shift-jis" | "euc-jp" | "euc-kr".
func (s *SSHSession) SetEncoding(name string) {
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
// call. The session lock serializes normal reads with ZMODEM trailing output.
func (s *SSHSession) decodeOutput(data []byte) []byte {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.decodeOutputLocked(data)
}

func (s *SSHSession) decodeOutputLocked(data []byte) []byte {
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
			continue // dst full but more src consumable; drain
		}
		break // nil or ErrShortSrc: remaining src is an incomplete trailing rune
	}
	// Buffer any incomplete trailing rune into a fresh slice so the next
	// read's append(s.decodeScratch, data...) isn't racing with decodeLeftover
	// backing storage.
	if len(src) > 0 {
		s.decodeLeftover = append(s.decodeLeftover[:0], src...)
	} else {
		s.decodeLeftover = src[:0]
	}
	return out
}

// SetZmodemMode serializes externally requested mode changes with readLoop's
// output routing decision. Internal readLoop detection already holds this lock
// and therefore calls baseSession.SetZmodemMode directly.
func (s *SSHSession) SetZmodemMode(v bool) {
	s.outputRouteMu.Lock()
	s.baseSession.SetZmodemMode(v)
	s.outputRouteMu.Unlock()
}

// EndZmodem leaves binary mode and runs bytes following the final ZMODEM
// handshake through the same streaming decoder as ordinary SSH output.
func (s *SSHSession) EndZmodem(trailing []byte) {
	s.outputRouteMu.Lock()
	defer s.outputRouteMu.Unlock()
	s.mu.Lock()
	s.setZmodemModeLocked(false)
	decoded := append([]byte(nil), s.decodeOutputLocked(trailing)...)
	w := s.outputLogWriter
	cb := s.onDataCallback
	s.mu.Unlock()
	if w != nil && len(decoded) > 0 {
		w(decoded)
	}
	if cb != nil && len(decoded) > 0 {
		cb(decoded)
	}
}

// encodeInput converts user keystrokes (UTF-8) to the configured encoding
// before writing to the remote. Each call handles a complete UTF-8 input.
func (s *SSHSession) encodeInput(data []byte) []byte {
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

// encodingByName maps a connection's encoding setting to an x/text codec.
// Returns nil for UTF-8 / empty (no conversion).
func encodingByName(name string) encoding.Encoding {
	switch name {
	case "gbk", "gb2312": // GB2312 is a subset of GBK; decode with GBK
		return simplifiedchinese.GBK
	case "gb18030":
		return simplifiedchinese.GB18030
	case "big5":
		return traditionalchinese.Big5
	case "shift-jis":
		return japanese.ShiftJIS
	case "euc-jp":
		return japanese.EUCJP
	case "euc-kr":
		return korean.EUCKR
	default: // "", "utf-8"
		return nil
	}
}
