//go:build windows
// +build windows

package session

import (
	"bytes"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/UserExistsError/conpty"
)

func TestParseAdminShellPath(t *testing.T) {
	const cmdPath = `C:\Windows\System32\cmd.exe`
	for _, tc := range []struct {
		name, in, want string
		ok             bool
	}{
		{"prefixed", AdminShellPathPrefix + cmdPath, cmdPath, true},
		{"prefixed uppercase", "ADMIN://" + cmdPath, cmdPath, true},
		{"plain path", cmdPath, "", false},
		{"wsl scheme", "wsl://Ubuntu", "", false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			got, ok := ParseAdminShellPath(tc.in)
			if ok != tc.ok || got != tc.want {
				t.Fatalf("ParseAdminShellPath(%q) = (%q, %v), want (%q, %v)", tc.in, got, ok, tc.want, tc.ok)
			}
		})
	}
}

func TestShellNameAdminSuffix(t *testing.T) {
	if got := shellName(AdminShellPathPrefix + `C:\Windows\System32\cmd.exe`); got != "cmd (Admin)" {
		t.Fatalf("shellName(admin cmd) = %q, want %q", got, "cmd (Admin)")
	}
	if got := shellName(`C:\Windows\System32\cmd.exe`); got == "cmd (Admin)" {
		t.Fatalf("shellName(plain cmd) = %q, must not carry the Admin suffix", got)
	}
}

// TestAdminPtyBrokerRelay drives the full broker protocol in-process, without
// elevation: the test plays the app side (pipe server, spawn frame, adminPty)
// while serveLocalPtyBroker runs in a goroutine playing the broker.
func TestAdminPtyBrokerRelay(t *testing.T) {
	if !conpty.IsConPtyAvailable() {
		t.Skip("ConPTY not available on this Windows version")
	}

	suffix := make([]byte, 8)
	if _, err := rand.Read(suffix); err != nil {
		t.Fatal(err)
	}
	pipeName := `\\.\pipe\terminal-pty-test-` + hex.EncodeToString(suffix)

	handle, err := createPtyPipeServer(pipeName)
	if err != nil {
		t.Fatalf("pipe server: %v", err)
	}
	brokerDone := make(chan int, 1)

	p := &adminPty{f: os.NewFile(uintptr(handle), pipeName)}
	defer p.Close()

	go func() { brokerDone <- serveLocalPtyBroker(pipeName) }()

	// Same handshake as production: broker hello, then the spawn request.
	brokerGone := make(chan struct{})
	if err := p.waitBrokerHello(brokerGone, 10*time.Second); err != nil {
		t.Fatalf("handshake: %v", err)
	}

	comspec := os.Getenv("ComSpec")
	if comspec == "" {
		comspec = `C:\Windows\System32\cmd.exe`
	}
	specBytes, err := json.Marshal(localPtySpawn{
		CommandLine: fmt.Sprintf(`"%s" /k`, comspec),
		Cols:        80,
		Rows:        25,
	})
	if err != nil {
		t.Fatal(err)
	}
	if err := ptyFrameWriteTo(p.f, ptyFrameSpawn, specBytes); err != nil {
		t.Fatalf("send spawn: %v", err)
	}

	// ConPTY suppresses cmd's classic banner, so drive the round trip
	// directly: the echoed command text plus its output must come back
	// through the relay.
	const marker = "TERMINAL_ADMIN_RELAY_OK"
	if _, err := p.Write([]byte("echo " + marker + "\r\n")); err != nil {
		t.Fatalf("write input: %v", err)
	}
	waitForMarker(t, p, marker, 20*time.Second)

	if err := p.Resize(100, 30); err != nil {
		t.Fatalf("resize: %v", err)
	}

	// Closing the pipe must make the broker kill the shell and exit — an
	// elevated process must never linger without its owner.
	p.Close()
	select {
	case code := <-brokerDone:
		t.Logf("broker exited with code %d", code)
	case <-time.After(10 * time.Second):
		t.Fatal("broker did not exit after the control pipe closed")
	}
}

// waitForMarker accumulates relayed PTY output until substr appears. The
// watchdog closes the pipe on timeout so a blocked read unwinds and the
// failure path actually fires instead of hanging to the test timeout.
func waitForMarker(t *testing.T, p *adminPty, substr string, timeout time.Duration) {
	t.Helper()
	type outcome struct {
		acc []byte
		err error
	}
	done := make(chan outcome, 1)
	go func() {
		acc := make([]byte, 0, 8192)
		buf := make([]byte, 4096)
		for {
			n, err := p.Read(buf)
			acc = append(acc, buf[:n]...)
			if bytes.Contains(acc, []byte(substr)) {
				done <- outcome{acc, nil}
				return
			}
			if err != nil {
				done <- outcome{acc, err}
				return
			}
		}
	}()
	select {
	case o := <-done:
		if o.err != nil {
			t.Fatalf("relay closed before %q appeared (saw %q): %v", substr, truncateOutput(o.acc), o.err)
		}
	case <-time.After(timeout):
		p.Close()
		t.Fatalf("timed out waiting for %q", substr)
	}
}

func truncateOutput(b []byte) string {
	const max = 512
	if len(b) > max {
		return string(b[:max]) + "..."
	}
	return string(b)
}

// TestFrameRoundTrip pins the wire format: type/length framing with u16
// little-endian payload lengths.
func TestFrameRoundTrip(t *testing.T) {
	payloads := [][]byte{nil, []byte("x"), bytes.Repeat([]byte{0xAB}, ptyFrameMaxPayload)}
	for _, want := range payloads {
		var buf bytes.Buffer
		if err := ptyFrameWriteTo(&buf, ptyFrameData, want); err != nil {
			t.Fatalf("write frame (len %d): %v", len(want), err)
		}
		gotType, gotPayload, err := ptyFrameReadFrom(&buf)
		if err != nil {
			t.Fatalf("read frame (len %d): %v", len(want), err)
		}
		if gotType != ptyFrameData || !bytes.Equal(gotPayload, want) {
			t.Fatalf("round trip mismatch: type=%d len=%d want len=%d", gotType, len(gotPayload), len(want))
		}
	}
}
