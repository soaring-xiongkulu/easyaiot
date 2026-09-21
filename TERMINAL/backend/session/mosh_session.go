package session

import (
	"bufio"
	"context"
	"fmt"
	"net"
	"strconv"
	"strings"
	"sync"
	"time"

	mosh "github.com/unixshells/mosh-go"
	"golang.org/x/crypto/ssh"
	"golang.org/x/text/encoding"
	"golang.org/x/text/transform"
)

type MoshSession struct {
	baseSession
	moshClient *mosh.Client
	sshClient  *ssh.Client
	cancel     context.CancelFunc
	quit       chan struct{}
	quitOnce   sync.Once

	mu             sync.RWMutex
	enc            encoding.Encoding
	decoder        *encoding.Decoder
	encoder        *encoding.Encoder
	decodeLeftover []byte
	decodeScratch  []byte
	encScratch     []byte
}

func NewMoshSession(id string) *MoshSession {
	return &MoshSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "mosh",
			status:      StatusDisconnected,
		},
		quit: make(chan struct{}),
	}
}

func (s *MoshSession) Connect(config ConnectionConfig) error {
	s.SetLogOnConnect(config.LogOnConnect)
	s.setStatus(StatusConnecting)
	if config.Name != "" {
		s.title = config.Name
	} else {
		s.title = fmt.Sprintf("%s@%s (mosh)", config.User, config.Host)
	}

	// Step 1: SSH to remote and start mosh-server to get key + UDP port.
	authMethods, cleanup, err := makeSSHAuthMethodsForAttempt(config, nil)
	if err != nil {
		s.setStatus(StatusError)
		return fmt.Errorf("mosh ssh auth: %w", err)
	}
	defer cleanup()
	addr := net.JoinHostPort(config.Host, strconv.Itoa(config.Port))
	clientConfig := &ssh.ClientConfig{
		User:            config.User,
		Auth:            authMethods,
		Timeout:         30 * time.Second,
		HostKeyCallback: ssh.InsecureIgnoreHostKey(),
		Config:          sshAlgorithms(),
	}

	conn, err := net.DialTimeout("tcp", addr, clientConfig.Timeout)
	if err != nil {
		s.setStatus(StatusError)
		return fmt.Errorf("mosh ssh dial: %w", err)
	}

	sshConn, chans, reqs, err := ssh.NewClientConn(conn, addr, clientConfig)
	if err != nil {
		conn.Close()
		s.setStatus(StatusError)
		return fmt.Errorf("mosh ssh handshake: %w", err)
	}
	client := ssh.NewClient(sshConn, chans, reqs)

	key, udpPort, err := startMoshServer(client)
	if err != nil {
		client.Close()
		s.setStatus(StatusError)
		return fmt.Errorf("mosh-server: %w", err)
	}

	s.sshClient = client

	// Step 2: Dial mosh server over UDP.
	moshClient, err := mosh.Dial(config.Host, udpPort, key)
	if err != nil {
		client.Close()
		s.setStatus(StatusError)
		return fmt.Errorf("mosh dial: %w", err)
	}

	s.moshClient = moshClient
	s.setStatus(StatusConnected)

	// Send the initial terminal size.  Transport().SetPending injects the
	// resize as the next state in the mosh protocol, bypassing the Client
	// action queue which would otherwise wait for a server ACK.
	cols, rows := s.getInitialSize(80, 24)
	resizeBytes := mosh.MarshalUserMessage([]mosh.UserInstruction{
		{Width: int32(cols), Height: int32(rows)},
	})
	moshClient.Transport().SetPending(resizeBytes)

	ctx, cancel := context.WithCancel(context.Background())
	s.cancel = cancel

	go s.readLoop(ctx)
	go s.runPostLoginScript(ctx, config.PostLoginScript)

	return nil
}

func (s *MoshSession) runPostLoginScript(ctx context.Context, script string) {
	s.baseSession.RunPostLoginScript(ctx, script, func(data []byte) {
		if s.moshClient != nil {
			s.moshClient.Send(data)
		}
	}, s.IsConnected)
}

func startMoshServer(client *ssh.Client) (key string, udpPort int, err error) {
	session, err := client.NewSession()
	if err != nil {
		return "", 0, fmt.Errorf("new session: %w", err)
	}
	defer session.Close()

	stdout, err := session.StdoutPipe()
	if err != nil {
		return "", 0, fmt.Errorf("stdout pipe: %w", err)
	}
	stderr, err := session.StderrPipe()
	if err != nil {
		return "", 0, fmt.Errorf("stderr pipe: %w", err)
	}

	if err := session.Start("mosh-server new -s"); err != nil {
		return "", 0, fmt.Errorf("start mosh-server: %w", err)
	}

	var output strings.Builder
	stdoutScanner := bufio.NewScanner(stdout)
	// Raise the default 64 KiB line cap so a chatty mosh-server banner
	// (key + port) doesn't get truncated (SESSION-13).
	stdoutScanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	for stdoutScanner.Scan() {
		output.WriteString(stdoutScanner.Text())
		output.WriteByte('\n')
	}
	if err := stdoutScanner.Err(); err != nil {
		return "", 0, fmt.Errorf("read mosh stdout: %w", err)
	}
	stderrScanner := bufio.NewScanner(stderr)
	stderrScanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	for stderrScanner.Scan() {
		output.WriteString(stderrScanner.Text())
		output.WriteByte('\n')
	}
	if err := stderrScanner.Err(); err != nil {
		return "", 0, fmt.Errorf("read mosh stderr: %w", err)
	}
	session.Wait()

	out := output.String()
	for _, line := range strings.Split(out, "\n") {
		line = strings.TrimSpace(line)

		if strings.HasPrefix(line, "MOSH_KEY=") {
			key = strings.TrimPrefix(line, "MOSH_KEY=")
		}
		if strings.HasPrefix(line, "MOSH_PORT=") {
			fmt.Sscanf(strings.TrimPrefix(line, "MOSH_PORT="), "%d", &udpPort)
		}

		if strings.HasPrefix(line, "MOSH CONNECT ") {
			parts := strings.Fields(line)
			if len(parts) >= 4 {
				fmt.Sscanf(parts[2], "%d", &udpPort)
				key = parts[3]
			}
		}
	}

	if key == "" || udpPort == 0 {
		return "", 0, fmt.Errorf("missing key or port in mosh-server output: %s", out)
	}

	return key, udpPort, nil
}

// SetEncoding configures the character encoding for this session.
// name: "" / "utf-8" (passthrough) | "gbk" | "gb2312" | "gb18030" |
// "big5" | "shift-jis" | "euc-jp" | "euc-kr".
func (s *MoshSession) SetEncoding(name string) {
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
func (s *MoshSession) decodeOutput(data []byte) []byte {
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
func (s *MoshSession) encodeInput(data []byte) []byte {
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

// moshReadInterval is the timeout passed to moshClient.Recv. The previous
// 100 ms value woke the readLoop 10 times/sec per idle session and was the
// dominant contributor to the user's reported 900+ idle wakeups (F-009).
// 1 s keeps the keepalive-feel responsive while only waking the goroutine
// once per second on idle; shutdown still happens via ctx.Done() / s.quit.
const moshReadInterval = 1 * time.Second

func (s *MoshSession) readLoop(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			return
		case <-s.quit:
			return
		default:
		}

		data := s.moshClient.Recv(moshReadInterval)
		if len(data) > 0 {
			s.RecordReadActivity()
			s.emitData(s.decodeOutput(data))
		}

		if s.moshClient == nil {
			return
		}
	}
}

func (s *MoshSession) Write(data []byte) error {
	if s.moshClient == nil {
		return fmt.Errorf("not connected")
	}
	s.moshClient.Send(s.encodeInput(data))
	return nil
}

func (s *MoshSession) Disconnect() error {
	s.quitOnce.Do(func() {
		close(s.quit)
	})
	if s.cancel != nil {
		s.cancel()
	}
	if s.moshClient != nil {
		s.moshClient.Close()
	}
	if s.sshClient != nil {
		s.sshClient.Close()
	}
	s.setStatus(StatusDisconnected)
	return nil
}

func (s *MoshSession) Resize(cols, rows int) error {
	s.SetPendingSize(cols, rows)
	if s.moshClient == nil {
		return fmt.Errorf("session not connected")
	}
	s.moshClient.Resize(uint16(cols), uint16(rows))
	return nil
}

func (s *MoshSession) IsConnected() bool {
	return s.Status() == StatusConnected
}
