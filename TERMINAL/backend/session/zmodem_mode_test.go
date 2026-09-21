package session

import (
	"bytes"
	"testing"
	"time"
)

func TestZmodemModeTimesOut(t *testing.T) {
	oldTimeout := zmodemModeTimeout
	zmodemModeTimeout = 10 * time.Millisecond
	t.Cleanup(func() { zmodemModeTimeout = oldTimeout })

	s := &baseSession{}
	s.SetZmodemMode(true)
	if !s.IsZmodemMode() {
		t.Fatal("zmodem mode was not enabled")
	}
	time.Sleep(30 * time.Millisecond)
	if s.IsZmodemMode() {
		t.Fatal("zmodem mode did not time out")
	}
}

func TestZmodemBinaryActivityExtendsTimeout(t *testing.T) {
	oldTimeout := zmodemModeTimeout
	zmodemModeTimeout = 30 * time.Millisecond
	t.Cleanup(func() { zmodemModeTimeout = oldTimeout })

	s := &baseSession{}
	s.SetZmodemMode(true)
	time.Sleep(20 * time.Millisecond)
	s.emitBinary([]byte{1})
	time.Sleep(20 * time.Millisecond)
	if !s.IsZmodemMode() {
		t.Fatal("binary activity did not extend zmodem timeout")
	}
	time.Sleep(20 * time.Millisecond)
	if s.IsZmodemMode() {
		t.Fatal("zmodem mode remained enabled after activity stopped")
	}
}

func TestEndingZmodemModeStopsTimeout(t *testing.T) {
	oldTimeout := zmodemModeTimeout
	zmodemModeTimeout = 10 * time.Millisecond
	t.Cleanup(func() { zmodemModeTimeout = oldTimeout })

	s := &baseSession{}
	s.SetZmodemMode(true)
	s.SetZmodemMode(false)
	time.Sleep(20 * time.Millisecond)
	if s.IsZmodemMode() {
		t.Fatal("zmodem mode was re-enabled by a stale timer")
	}
	s.mu.RLock()
	defer s.mu.RUnlock()
	if s.zmodemTimer != nil {
		t.Fatal("zmodem timer was not cleared")
	}
}

func TestOldZmodemTimerCannotDisableNewGeneration(t *testing.T) {
	oldTimeout := zmodemModeTimeout
	zmodemModeTimeout = 20 * time.Millisecond
	t.Cleanup(func() { zmodemModeTimeout = oldTimeout })

	s := &baseSession{}
	s.SetZmodemMode(true)
	time.Sleep(15 * time.Millisecond)
	s.SetZmodemMode(false)
	s.SetZmodemMode(true)
	time.Sleep(10 * time.Millisecond)
	if !s.IsZmodemMode() {
		t.Fatal("stale timer disabled a newer zmodem generation")
	}
	s.SetZmodemMode(false)
}

func TestEndZmodemRestoresAndLogsTrailingOutput(t *testing.T) {
	var logged []byte
	var emitted []byte
	s := &baseSession{outputLogWriter: func(data []byte) {
		logged = append(logged, data...)
	}, onDataCallback: func(data []byte) { emitted = append(emitted, data...) }}
	s.SetZmodemMode(true)

	trailing := []byte("root@host:~# ")
	s.EndZmodem(trailing)

	if s.IsZmodemMode() {
		t.Fatal("EndZmodem did not leave binary mode")
	}
	if !bytes.Equal(logged, trailing) {
		t.Fatalf("logged output = %q, want %q", logged, trailing)
	}
	if !bytes.Equal(emitted, trailing) {
		t.Fatalf("emitted output = %q, want %q", emitted, trailing)
	}
}

func TestSSHEndZmodemDecodesTrailingOutput(t *testing.T) {
	s := NewSSHSession("test")
	s.SetEncoding("gbk")
	s.SetZmodemMode(true)

	// GBK for "你好# ". This verifies trailing prompt bytes return through
	// the same configured decoder rather than being written raw to xterm.
	var got []byte
	s.SetOnDataCallback(func(data []byte) { got = append(got, data...) })
	s.EndZmodem([]byte{0xc4, 0xe3, 0xba, 0xc3, '#', ' '})
	if string(got) != "你好# " {
		t.Fatalf("emitted output = %q, want %q", got, "你好# ")
	}
	if s.IsZmodemMode() {
		t.Fatal("EndZmodem did not leave binary mode")
	}
}
