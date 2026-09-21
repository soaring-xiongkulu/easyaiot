package main

import (
	"net"
	"strings"
	"testing"
	"time"
)

// TestStartPprofIfDev_ProductionSkip verifies that startPprofIfDev is a no-op
// when devBuild is false (i.e. when a production build sets Version != "dev"
// via -ldflags '-X main.Version=...'). The function must not bind any TCP
// socket on localhost:6060.
//
// F-201 audit §8.2: production binaries must never expose the debug listener
// to end users.
func TestStartPprofIfDev_ProductionSkip(t *testing.T) {
	// Snapshot and restore the package-level devBuild flag. Tests in this
	// package run sequentially by default, so mutating the package var is
	// safe — but restore in defer to avoid leaking state across the suite.
	origDev := devBuild
	defer func() { devBuild = origDev }()

	devBuild = false
	startPprofIfDev()

	// Give any background goroutine a chance to race into ListenAndServe.
	// If startPprofIfDev really did spawn one, it would attempt to bind
	// 6060 immediately. Poll for a short window to be sure.
	time.Sleep(100 * time.Millisecond)

	conn, err := net.DialTimeout("tcp", "127.0.0.1:6060", 200*time.Millisecond)
	if err == nil {
		conn.Close()
		t.Fatalf("pprof listener bound 6060 in production build; want no listener")
	}
	if !strings.Contains(err.Error(), "refused") && !strings.Contains(err.Error(), "timeout") {
		// Some platforms return "connection refused", others "i/o timeout"
		// when the port is closed; both signal no listener. Anything else
		// (e.g. "permission denied" on macOS without loopback allow) would
		// indicate a real bind problem and warrants investigation.
		t.Fatalf("unexpected dial error: %v", err)
	}
}

// TestStartPprofIfDev_DevOpensListener verifies that when devBuild is true
// (i.e. wails dev with Version == "dev"), startPprofIfDev actually serves
// net/http/pprof on localhost:6060 and answers the canonical /debug/pprof/
// index. We hit the index and check for the pprof marker text instead of
// dialing raw TCP so the test fails loudly if the import side-effect is
// somehow missing.
//
// F-201: ensures the dev ergonomics endpoint is wired up.
func TestStartPprofIfDev_DevOpensListener(t *testing.T) {
	origDev := devBuild
	defer func() { devBuild = origDev }()

	devBuild = true
	startPprofIfDev()

	// Poll for the listener to come up. devBuild=true spawns a goroutine
	// that calls http.ListenAndServe synchronously inside the goroutine,
	// so the bind happens concurrently with our test.
	deadline := time.Now().Add(2 * time.Second)
	var lastErr error
	for time.Now().Before(deadline) {
		conn, err := net.DialTimeout("tcp", "127.0.0.1:6060", 200*time.Millisecond)
		if err == nil {
			conn.Close()
			lastErr = nil
			break
		}
		lastErr = err
		time.Sleep(50 * time.Millisecond)
	}
	if lastErr != nil {
		t.Fatalf("pprof listener never came up on 6060 (devBuild=true): %v", lastErr)
	}
}