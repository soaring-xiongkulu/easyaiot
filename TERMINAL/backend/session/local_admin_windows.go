//go:build windows
// +build windows

package session

import (
	"crypto/rand"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"sync"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
)

// AdminShellPathPrefix marks a local-terminal ShellPath that must be launched
// with administrator privileges (UAC elevation), e.g.
// "admin://C:\Windows\System32\cmd.exe". It mirrors the wsl:// scheme: the
// prefix carries the launch mode, the rest is the ordinary shell path.
const AdminShellPathPrefix = "admin://"

// errElevationCancelled reports that the user dismissed the UAC prompt.
var errElevationCancelled = errors.New("the UAC elevation prompt was cancelled")

// ParseAdminShellPath splits an admin:// ShellPath into the plain shell path.
// ok is false when path does not carry the admin:// prefix.
func ParseAdminShellPath(path string) (inner string, ok bool) {
	const prefix = AdminShellPathPrefix
	if len(path) < len(prefix) || lowerASCII(path[:len(prefix)]) != prefix {
		return "", false
	}
	return path[len(prefix):], true
}

// lowerASCII is strings.ToLower restricted to the prefix check — the prefix is
// pure ASCII so a full Unicode lowercase pass is unnecessary.
func lowerASCII(s string) string {
	b := []byte(s)
	for i := range b {
		if b[i] >= 'A' && b[i] <= 'Z' {
			b[i] += 'a' - 'A'
		}
	}
	return string(b)
}

// IsProcessElevated reports whether the current process runs with an elevated
// (administrator) token. Used to skip the elevation dance when Terminal itself
// already runs as administrator, and to hide the admin shell options from the
// connection form in that case (they would be indistinguishable duplicates).
func IsProcessElevated() bool {
	var token windows.Token
	if err := windows.OpenProcessToken(windows.CurrentProcess(), windows.TOKEN_QUERY, &token); err != nil {
		return false
	}
	defer token.Close()
	var elevation uint32
	var returned uint32
	if err := windows.GetTokenInformation(token, windows.TokenElevation, (*byte)(unsafe.Pointer(&elevation)), uint32(unsafe.Sizeof(elevation)), &returned); err != nil {
		return false
	}
	return elevation != 0
}

// localPtySpawn is the spawn request the unelevated app sends to the elevated
// broker once their control pipe is connected. Traveling as the first pipe
// message (instead of ShellExecuteEx parameters) avoids re-quoting a command
// line through argv.
type localPtySpawn struct {
	CommandLine string   `json:"commandLine"`
	WorkDir     string   `json:"workDir,omitempty"`
	// Extra environment entries for the spawned shell (on top of the
	// broker's environ); nil keeps the broker's plain environment. Used e.g.
	// by clink:// shells to pass WT_SESSION=0 into the elevated ConPTY.
	Env  []string `json:"env,omitempty"`
	Cols int      `json:"cols"`
	Rows int      `json:"rows"`
}

// Frame types of the broker pipe protocol. Every message is
// [type:1][length:2 little-endian][payload]; payload length is u16 so the
// largest frame is 64 KiB and writers must chunk larger writes.
const (
	ptyFrameData   = 1 // broker → app: PTY output bytes
	ptyFrameInput  = 2 // app → broker: user keystrokes
	ptyFrameResize = 3 // app → broker: payload cols u16 LE, rows u16 LE
	ptyFrameExited = 4 // broker → app: the shell exited (payload: optional note)
	ptyFrameSpawn  = 5 // app → broker: localPtySpawn JSON, sent once on connect
	ptyFrameHello  = 6 // broker → app: empty payload announcing the connection
)

const ptyFrameHeaderSize = 3
const ptyFrameMaxPayload = 0xFFFF

func ptyFrameWriteTo(w io.Writer, frameType byte, payload []byte) error {
	head := [ptyFrameHeaderSize]byte{frameType, byte(len(payload)), byte(len(payload) >> 8)}
	if _, err := w.Write(head[:]); err != nil {
		return err
	}
	if len(payload) == 0 {
		return nil
	}
	_, err := w.Write(payload)
	return err
}

// ptyFrameReadFrom reads one complete frame. io.EOF from the underlying pipe
// (broken by either side) propagates unchanged; short reads become
// io.ErrUnexpectedEOF via io.ReadFull.
func ptyFrameReadFrom(r io.Reader) (frameType byte, payload []byte, err error) {
	head := make([]byte, ptyFrameHeaderSize)
	if _, err = io.ReadFull(r, head); err != nil {
		return 0, nil, err
	}
	n := int(head[1]) | int(head[2])<<8
	payload = make([]byte, n)
	if _, err = io.ReadFull(r, payload); err != nil {
		return 0, nil, err
	}
	return head[0], payload, nil
}

// waitBrokerHello blocks until the broker announces its connection with the
// hello frame. Until the broker's first CreateFile lands, the pipe sits in
// listening state and reads fail fast with ERROR_PIPE_LISTENING — retried
// with a short backoff until the deadline (Go's overlapped deadline support
// bounds the whole wait). brokerGone lets a crashed broker fail fast.
func (p *adminPty) waitBrokerHello(brokerGone <-chan struct{}, timeout time.Duration) error {
	if err := p.f.SetDeadline(time.Now().Add(timeout)); err != nil {
		return fmt.Errorf("deadline: %w", err)
	}
	defer p.f.SetDeadline(time.Time{})
	for {
		frameType, _, err := ptyFrameReadFrom(p.f)
		switch {
		case err == nil && frameType == ptyFrameHello:
			return nil
		case err == nil:
			return fmt.Errorf("unexpected frame type %d", frameType)
		case errors.Is(err, windows.ERROR_PIPE_LISTENING):
			select {
			case <-brokerGone:
				return errors.New("elevated broker exited before connecting")
			case <-time.After(50 * time.Millisecond):
			}
		default:
			return err
		}
	}
}

// adminPty is the app-side half of an elevated local shell: a ConPTY running
// inside the elevated broker process, relayed over a named pipe restricted to
// the current user. It implements the pieces LocalSession needs from a ConPTY
// (Read/Write/Resize/Close) so the session code can treat both alike.
type adminPty struct {
	f *os.File

	writeMu sync.Mutex
	pending []byte // undelivered data-frame bytes (Read's buffer may be smaller)
	exited  bool
}

// startElevatedPty launches Terminal's PTY broker with the "runas" verb (which
// pops the UAC prompt), waits for the broker to connect back over a named pipe
// that only the current user may open, and hands it the spawn request.
func startElevatedPty(spec localPtySpawn) (*adminPty, error) {
	suffix := make([]byte, 8)
	if _, err := rand.Read(suffix); err != nil {
		return nil, fmt.Errorf("pipe name: %w", err)
	}
	pipeName := `\\.\pipe\terminal-pty-` + hex.EncodeToString(suffix)

	handle, err := createPtyPipeServer(pipeName)
	if err != nil {
		return nil, fmt.Errorf("create pipe: %w", err)
	}

	exe, err := os.Executable()
	if err != nil {
		windows.CloseHandle(handle)
		return nil, fmt.Errorf("locate executable: %w", err)
	}
	brokerProc, err := shellExecuteRunAs(exe, "--local-pty-broker "+pipeName)
	if err != nil {
		windows.CloseHandle(handle)
		return nil, err
	}
	if brokerProc != 0 {
		defer windows.CloseHandle(brokerProc)
	}

	// Deliberately NO ConnectNamedPipe here: an overlapped handle whose
	// connect went through ConnectNamedPipe silently black-holes every later
	// read completion under Go's I/O machinery (verified against a minimal
	// reproduction). A freshly created pipe instance already accepts client
	// connections on its own — the broker announces itself with a hello
	// frame, which doubles as the connect synchronization point.
	p := &adminPty{f: os.NewFile(uintptr(handle), pipeName)}

	// Bail early when the broker process dies (UAC approved yet the process
	// crashed, killed) instead of riding out the full hello timeout.
	brokerGone := make(chan struct{})
	if brokerProc != 0 {
		go func() {
			windows.WaitForSingleObject(brokerProc, windows.INFINITE)
			close(brokerGone)
		}()
	}

	if err := p.waitBrokerHello(brokerGone, 30*time.Second); err != nil {
		p.Close()
		return nil, fmt.Errorf("broker handshake: %w", err)
	}

	specBytes, err := json.Marshal(spec)
	if err == nil {
		err = ptyFrameWriteTo(p.f, ptyFrameSpawn, specBytes)
	}
	if err != nil {
		p.Close()
		return nil, fmt.Errorf("send spawn request: %w", err)
	}
	return p, nil
}

// createPtyPipeServer creates the broker-side-connectable pipe. The explicit
// security descriptor grants full access to the creating user only — without
// it the default pipe DACL would still keep other low-integrity processes out,
// but spelling it out documents that the pipe carries an administrator shell's
// I/O and must not be reachable by anyone else on the machine.
func createPtyPipeServer(pipeName string) (windows.Handle, error) {
	token, err := windows.OpenCurrentProcessToken()
	if err != nil {
		return 0, err
	}
	defer token.Close()
	user, err := token.GetTokenUser()
	if err != nil {
		return 0, err
	}
	sd, err := windows.SecurityDescriptorFromString("D:P(A;;GA;;;" + user.User.Sid.String() + ")")
	if err != nil {
		return 0, err
	}
	sa := &windows.SecurityAttributes{SecurityDescriptor: sd}
	namePtr, err := windows.UTF16PtrFromString(pipeName)
	if err != nil {
		return 0, err
	}
	// FILE_FLAG_OVERLAPPED is required: os.File drives overlapped handles
	// through Go's async I/O machinery, which is what makes a concurrent
	// blocked Read and blocked Write on the SAME pipe handle work (the relay
	// reads output while the session writes keystrokes). Sync-mode handles
	// deadlock exactly there.
	return windows.CreateNamedPipe(
		namePtr,
		windows.PIPE_ACCESS_DUPLEX|windows.FILE_FLAG_FIRST_PIPE_INSTANCE|windows.FILE_FLAG_OVERLAPPED,
		windows.PIPE_TYPE_BYTE|windows.PIPE_READMODE_BYTE|windows.PIPE_WAIT|windows.PIPE_REJECT_REMOTE_CLIENTS,
		1, 65536, 65536, 0, sa)
}

// shellExecuteRunAs launches target with the "runas" verb, which routes the
// launch through UAC. Returns the spawned process handle (the caller closes
// it), or errElevationCancelled when the user dismissed the prompt.
func shellExecuteRunAs(target, parameters string) (windows.Handle, error) {
	// SHELLEXECUTEINFOW, laid out for natural x64 alignment: field order and
	// types match the Win32 struct so unsafe casting stays valid.
	type shellExecuteInfo struct {
		cbSize         uint32
		fMask          uint32
		hwnd           windows.HWND
		lpVerb         uintptr
		lpFile         uintptr
		lpParameters   uintptr
		lpDirectory    uintptr
		nShow          int32
		hInstApp       uintptr
		lpIDList       uintptr
		lpClass        uintptr
		hkeyClass      windows.Handle
		dwHotKey       uint32
		hIconOrMonitor uintptr
		hProcess       windows.Handle
	}

	const (
		seeMaskNOCLOSEPROCESS = 0x00000040
		seeMaskNOASYNC        = 0x00001000
		swHide                = 0
	)

	verb, _ := windows.UTF16PtrFromString("runas")
	file, _ := windows.UTF16PtrFromString(target)
	params, _ := windows.UTF16PtrFromString(parameters)
	info := shellExecuteInfo{
		cbSize:       uint32(unsafe.Sizeof(shellExecuteInfo{})),
		fMask:        seeMaskNOCLOSEPROCESS | seeMaskNOASYNC,
		lpVerb:       uintptr(unsafe.Pointer(verb)),
		lpFile:       uintptr(unsafe.Pointer(file)),
		lpParameters: uintptr(unsafe.Pointer(params)),
		nShow:        swHide,
	}

	shell32 := windows.NewLazySystemDLL("shell32.dll")
	procShellExecuteExW := shell32.NewProc("ShellExecuteExW")
	ret, _, _ := procShellExecuteExW.Call(uintptr(unsafe.Pointer(&info)))
	if ret == 0 {
		// Cancelled UAC is the common failure and deserves its own message;
		// anything else surfaces the raw code for diagnosis.
		if errors.Is(windows.GetLastError(), windows.ERROR_CANCELLED) {
			return 0, errElevationCancelled
		}
		return 0, fmt.Errorf("ShellExecuteEx(runas) failed: %w", windows.GetLastError())
	}
	return info.hProcess, nil
}

// Read delivers PTY output bytes, transparently unwrapping data frames and
// turning the broker's exited frame into io.EOF once all preceding output has
// been handed out. Only the session's readLoop goroutine may call it.
func (p *adminPty) Read(buf []byte) (int, error) {
	for {
		if len(p.pending) > 0 {
			n := copy(buf, p.pending)
			p.pending = p.pending[n:]
			return n, nil
		}
		if p.exited {
			return 0, io.EOF
		}
		frameType, payload, err := ptyFrameReadFrom(p.f)
		if err != nil {
			// A broken pipe means the broker (or the whole elevated shell)
			// is gone — the same clean-EOF treatment the ConPTY path gives
			// post-exit read errors.
			return 0, io.EOF
		}
		switch frameType {
		case ptyFrameData:
			p.pending = append(p.pending[:0], payload...)
		case ptyFrameExited:
			p.exited = true
		}
	}
}

// Write sends user keystrokes to the broker, chunking to the u16 frame limit
// (pasted text can exceed 64 KiB in one call).
func (p *adminPty) Write(data []byte) (int, error) {
	p.writeMu.Lock()
	defer p.writeMu.Unlock()
	written := 0
	for written < len(data) {
		end := written + ptyFrameMaxPayload
		if end > len(data) {
			end = len(data)
		}
		if err := ptyFrameWriteTo(p.f, ptyFrameInput, data[written:end]); err != nil {
			return written, err
		}
		written = end
	}
	return len(data), nil
}

// Resize forwards a frontend terminal resize to the broker's ConPTY.
func (p *adminPty) Resize(cols, rows int) error {
	p.writeMu.Lock()
	defer p.writeMu.Unlock()
	payload := make([]byte, 4)
	binary.LittleEndian.PutUint16(payload[0:], uint16(cols))
	binary.LittleEndian.PutUint16(payload[2:], uint16(rows))
	return ptyFrameWriteTo(p.f, ptyFrameResize, payload)
}

// Close tears down the pipe. The broker sees the broken pipe, kills the
// elevated shell and exits. Safe to call from the session teardown path even
// while a Read is blocked — closing the handle unblocks it with an error.
func (p *adminPty) Close() error {
	return p.f.Close()
}
