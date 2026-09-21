//go:build windows
// +build windows

package session

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"sync"
	"time"

	"github.com/UserExistsError/conpty"
	"golang.org/x/sys/windows"
)

// RunLocalPtyBroker implements Terminal's administrator-shell broker mode. The
// unelevated app launches a copy of itself with the "runas" verb and the
// --local-pty-broker argument; that elevated copy (this code) never touches
// the webview or app stores — it spawns the requested shell inside a ConPTY
// and relays bytes between the pseudo console and the control pipe until
// either side goes away. It returns true when args selected broker mode; main
// exits without initializing the app in that case.
func RunLocalPtyBroker(args []string) bool {
	if len(args) != 3 || args[1] != "--local-pty-broker" {
		return false
	}
	os.Exit(serveLocalPtyBroker(args[2]))
	return true
}

// serveLocalPtyBroker serves one elevated shell and returns the process exit
// code, so tests can run it in-process.
func serveLocalPtyBroker(pipeName string) int {
	pipe, err := dialPtyBrokerPipe(pipeName)
	if err != nil {
		return 1
	}
	// Announce the connection; the app waits for this frame instead of
	// ConnectNamedPipe (see startElevatedPty).
	if err := ptyFrameWriteTo(pipe, ptyFrameHello, nil); err != nil {
		pipe.Close()
		return 1
	}

	frameType, payload, err := ptyFrameReadFrom(pipe)
	if err != nil {
		pipe.Close()
		return 1
	}
	if frameType != ptyFrameSpawn {
		pipe.Close()
		return 1
	}
	var spec localPtySpawn
	if err := json.Unmarshal(payload, &spec); err != nil {
		pipe.Close()
		return 1
	}

	if !conpty.IsConPtyAvailable() {
		noteAndClose(pipe, "ConPTY is not available on this Windows version")
		return 1
	}

	cols, rows := spec.Cols, spec.Rows
	if cols <= 0 || rows <= 0 {
		cols, rows = 80, 24
	}
	env := os.Environ()
	if len(spec.Env) > 0 {
		env = append(env, spec.Env...)
	}
	cpty, err := conpty.Start(spec.CommandLine,
		conpty.ConPtyDimensions(cols, rows),
		conpty.ConPtyWorkDir(spec.WorkDir),
		conpty.ConPtyEnv(env))
	if err != nil {
		noteAndClose(pipe, fmt.Sprintf("start shell: %v", err))
		return 1
	}

	// The app side vanished (tab closed, app quit, pipe broke): kill the
	// shell so it cannot linger elevated with no one attached.
	pipeBroken := make(chan struct{})
	shellExited := make(chan struct{})
	var brokenOnce, killOnce sync.Once
	signalPipeBroken := func() { brokenOnce.Do(func() { close(pipeBroken) }) }
	terminate := func() {
		killOnce.Do(func() {
			cpty.Close()
			// ClosePseudoConsole ends the console session; make sure the
			// client itself is gone even if it somehow survived.
			if proc, err := windows.OpenProcess(windows.PROCESS_TERMINATE, false, uint32(cpty.Pid())); err == nil {
				windows.TerminateProcess(proc, 1)
				windows.CloseHandle(proc)
			}
		})
	}

	// ConPTY output → app.
	go func() {
		buf := make([]byte, 4096)
		for {
			n, err := cpty.Read(buf)
			if n > 0 {
				if ptyFrameWriteTo(pipe, ptyFrameData, buf[:n]) != nil {
					signalPipeBroken()
					return
				}
			}
			if err != nil {
				close(shellExited)
				return
			}
		}
	}()

	// App input / resize → ConPTY.
	go func() {
		for {
			frameType, payload, err := ptyFrameReadFrom(pipe)
			if err != nil {
				signalPipeBroken()
				return
			}
			switch frameType {
			case ptyFrameInput:
				if len(payload) > 0 {
					cpty.Write(payload)
				}
			case ptyFrameResize:
				if len(payload) >= 4 {
					cols := int(payload[0]) | int(payload[1])<<8
					rows := int(payload[2]) | int(payload[3])<<8
					cpty.Resize(cols, rows)
				}
			}
		}
	}()

	select {
	case <-pipeBroken:
		terminate()
		pipe.Close()
		return 1
	case <-shellExited:
		ptyFrameWriteTo(pipe, ptyFrameExited, nil)
		pipe.Close()
		return 0
	}
}

// noteAndClose tells the app why no shell could be started: the note travels
// as PTY output (the terminal shows it), the exited frame ends the session.
func noteAndClose(pipe *os.File, note string) {
	ptyFrameWriteTo(pipe, ptyFrameData, []byte("\r\n[administrator shell: "+note+"]\r\n"))
	ptyFrameWriteTo(pipe, ptyFrameExited, nil)
	pipe.Close()
}

// dialPtyBrokerPipe connects to the app's control pipe. The pipe exists
// before the broker is launched, but retry briefly anyway to absorb
// scheduling jitter between ShellExecuteEx returning and the broker starting.
func dialPtyBrokerPipe(pipeName string) (*os.File, error) {
	deadline := time.Now().Add(10 * time.Second)
	namePtr, err := windows.UTF16PtrFromString(pipeName)
	if err != nil {
		return nil, err
	}
	for {
		// FILE_FLAG_OVERLAPPED matches the server side: os.File routes the
		// handle through Go's async I/O machinery, which is what lets the
		// relay's blocked Read coexist with blocked Writes on this handle.
		handle, err := windows.CreateFile(
			namePtr,
			windows.GENERIC_READ|windows.GENERIC_WRITE,
			0, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OVERLAPPED, 0)
		if err == nil {
			return os.NewFile(uintptr(handle), pipeName), nil
		}
		if !errors.Is(err, windows.ERROR_PIPE_BUSY) && !errors.Is(err, windows.ERROR_FILE_NOT_FOUND) {
			return nil, err
		}
		if time.Now().After(deadline) {
			return nil, err
		}
		time.Sleep(100 * time.Millisecond)
	}
}
