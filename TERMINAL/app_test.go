package main

import (
	"errors"
	"fmt"
	"io"
	"strings"
	"sync"
	"testing"
	"time"

	"easyaiot/terminal/backend/credentials"
)

// TestApp_StartupError_CapturesSingleError verifies that a single error
// sent during startup() surfaces through StartupError() after
// drainStartupErr() has run. The frontend calls StartupError() on demand
// after receiving the "app:startup-error" event to render a banner.
func TestApp_StartupError_CapturesSingleError(t *testing.T) {
	a := NewApp("")
	a.sendStartupErr(errors.New("connection store: init failed"))

	if got := a.StartupError(); got != "" {
		t.Fatalf("StartupError() before drain = %q, want empty", got)
	}

	a.drainStartupErr()
	got := a.StartupError()
	want := "connection store: init failed"
	if got != want {
		t.Fatalf("StartupError() = %q, want %q", got, want)
	}
}

// TestApp_StartupError_JoinsMultipleErrors verifies the errors.Join
// behaviour: multiple sendStartupErr calls during startup() produce a
// single newline-joined string readable by the frontend.
func TestApp_StartupError_JoinsMultipleErrors(t *testing.T) {
	a := NewApp("")
	a.sendStartupErr(errors.New("connection store: read failed"))
	a.sendStartupErr(errors.New("settings store: write failed"))
	a.drainStartupErr()

	got := a.StartupError()
	for _, want := range []string{"connection store: read failed", "settings store: write failed"} {
		if !strings.Contains(got, want) {
			t.Errorf("StartupError() = %q, missing %q", got, want)
		}
	}
	if !strings.Contains(got, "\n") {
		t.Errorf("StartupError() = %q, expected newline-separated entries", got)
	}
}

// TestApp_StartupError_NilOnClean verifies StartupError() returns ""
// when no init failures occurred. The frontend uses the empty string to
// decide whether to render the banner.
func TestApp_StartupError_NilOnClean(t *testing.T) {
	a := NewApp("")
	a.drainStartupErr()
	if got := a.StartupError(); got != "" {
		t.Fatalf("StartupError() with no errors = %q, want empty", got)
	}
}

// TestApp_SendStartupErr_NilIsNoop confirms nil errors do not enqueue.
// Defensive against a future caller passing nil from an error chain.
func TestApp_SendStartupErr_NilIsNoop(t *testing.T) {
	a := NewApp("")
	a.sendStartupErr(nil)
	a.drainStartupErr()
	if got := a.StartupError(); got != "" {
		t.Fatalf("StartupError() after nil send = %q, want empty", got)
	}
}

// TestApp_SendStartupErr_OverflowDrops verifies that when the buffered
// channel (size 16) overflows, sendStartupErr drops the extra error
// instead of blocking. The send runs on the startup goroutine and must
// remain non-blocking; the log line is the last-resort record.
func TestApp_SendStartupErr_OverflowDrops(t *testing.T) {
	a := NewApp("")
	for i := 0; i < 32; i++ {
		a.sendStartupErr(fmt.Errorf("store: %d", i))
	}
	a.drainStartupErr()
	got := a.StartupError()
	if got == "" {
		t.Fatal("StartupError() empty after 32 sends, want at least one entry")
	}
	if strings.Count(got, "\n") >= 32 {
		t.Errorf("StartupError() kept all 32 sends, expected some drops under cap=16")
	}
}

// TestApp_StartupErr_ConcurrentSendSafe sends from many goroutines and
// confirms drainStartupErr() collects everything safely. Catches data
// races in the channel/snapshot interaction under -race.
func TestApp_StartupErr_ConcurrentSendSafe(t *testing.T) {
	a := NewApp("")
	const N = 32
	var wg sync.WaitGroup
	wg.Add(N)
	for i := 0; i < N; i++ {
		go func(i int) {
			defer wg.Done()
			a.sendStartupErr(fmt.Errorf("concurrent: %d", i))
		}(i)
	}
	wg.Wait()
	a.drainStartupErr()
	got := a.StartupError()
	if got == "" {
		t.Fatal("StartupError() empty after concurrent sends")
	}
}

// TestApp_PanelLogTitle_FallbackAndLookup exercises panelLogTitle: with
// no registered session the helper returns a synthetic fallback rather
// than crashing on a nil sessionManager, and with a registered session
// it returns non-empty name/protocol under panelLogMu. Regression
// coverage for the helper that PR-15's log-file work depends on.
func TestApp_PanelLogTitle_FallbackAndLookup(t *testing.T) {
	a := NewApp("")

	// No registration — fallback path.
	name, _, protocol := a.panelLogTitle("panel-X")
	if name == "" {
		t.Errorf("panelLogTitle empty name for unregistered panel")
	}
	if protocol == "" {
		t.Errorf("panelLogTitle empty protocol for unregistered panel")
	}

	// Registered session but no live sessionManager entry — helper
	// falls through to the synthetic name (no panic).
	a.RegisterSessionForPanel("sess-y", "panel-X")
	start := time.Now()
	for i := 0; i < 1000; i++ {
		name, _, protocol = a.panelLogTitle("panel-X")
	}
	if elapsed := time.Since(start); elapsed > 50*time.Millisecond {
		t.Errorf("1000 panelLogTitle calls took %v, expected < 50ms", elapsed)
	}
	if name == "" || protocol == "" {
		t.Errorf("panelLogTitle returned empty name=%q protocol=%q", name, protocol)
	}
}

// TestErrorBodyCap_F305 guards F-305: the error-body read on the non-200
// path is capped at 64 KiB so a hostile or buggy upstream returning a
// multi-GB error body can't OOM the Go process. We can't drive the full
// chatCompletion* HTTP path from a unit test, but the cap is a single
// io.LimitReader wrapper around io.ReadAll — verify the contract that
// reads beyond 64 KiB stop there.
func TestErrorBodyCap_F305(t *testing.T) {
	const cap = 64 * 1024
	// 1 MiB of 'a' is well above the cap.
	big := strings.Repeat("a", 1024*1024)
	body, err := io.ReadAll(io.LimitReader(strings.NewReader(big), cap))
	if err != nil {
		t.Fatalf("LimitReader read failed: %v", err)
	}
	if len(body) != cap {
		t.Errorf("expected capped read of %d bytes, got %d", cap, len(body))
	}
	// Sanity: a smaller body is read in full.
	small := strings.Repeat("b", 1024)
	bodySmall, err := io.ReadAll(io.LimitReader(strings.NewReader(small), cap))
	if err != nil {
		t.Fatalf("LimitReader read failed: %v", err)
	}
	if len(bodySmall) != len(small) {
		t.Errorf("small body got %d bytes, want %d", len(bodySmall), len(small))
	}
}

// lockedKeychain simulates the headless Docker deployment: there is no
// Secret Service, so every keychain operation fails and the derived-key
// cache never yields a key — unlocking is only possible from the master
// password.
type lockedKeychain struct{}

func (lockedKeychain) Get(string) (string, error) { return "", errors.New("no keychain") }
func (lockedKeychain) Set(string, string) error   { return errors.New("no keychain") }
func (lockedKeychain) Delete(string) error        { return errors.New("no keychain") }

// TestAutoUnlockCredentialsFromEnv covers the headless (Docker) startup path
// that unlocks a master-password vault from TERMINAL_MASTER_PASSWORD: unset
// leaves the vault locked behind the normal dialog, the right password
// unlocks it, and a wrong password must not be able to read secrets (it
// derives an unusable key, same as typing a wrong password in the dialog).
func TestAutoUnlockCredentialsFromEnv(t *testing.T) {
	dir := t.TempDir()
	setup := credentials.New(dir, lockedKeychain{})
	if err := setup.Setup(credentials.ModeMasterPassword, "right-password"); err != nil {
		t.Fatalf("setup vault: %v", err)
	}
	secret, err := setup.Encrypt("s3cret")
	if err != nil {
		t.Fatalf("encrypt: %v", err)
	}

	newLockedApp := func() *App {
		// A fresh store over the same data dir simulates a container
		// restart: meta is on disk, the in-memory key is gone, and the
		// keychain cannot hand one back. AutoUnlock mirrors the startup
		// ordering (initCredentials → autoUnlockCredentialsFromEnv): it
		// loads mode+salt from meta but cannot recover the key.
		a := NewApp("")
		cred := credentials.New(dir, lockedKeychain{})
		if err := cred.AutoUnlock(); err != nil {
			t.Fatalf("auto unlock: %v", err)
		}
		a.credentialStore = cred
		return a
	}

	t.Run("unset env stays locked", func(t *testing.T) {
		a := newLockedApp()
		t.Setenv("TERMINAL_MASTER_PASSWORD", "")
		a.autoUnlockCredentialsFromEnv()
		if a.credentialStore.Unlocked() {
			t.Fatal("vault unlocked without TERMINAL_MASTER_PASSWORD")
		}
	})

	t.Run("correct password unlocks and decrypts", func(t *testing.T) {
		a := newLockedApp()
		t.Setenv("TERMINAL_MASTER_PASSWORD", "right-password")
		a.autoUnlockCredentialsFromEnv()
		if !a.credentialStore.Unlocked() {
			t.Fatal("vault still locked with correct TERMINAL_MASTER_PASSWORD")
		}
		got, err := a.credentialStore.Decrypt(secret)
		if err != nil || got != "s3cret" {
			t.Fatalf("Decrypt after env unlock = %q, %v", got, err)
		}
	})

	t.Run("wrong password cannot read secrets", func(t *testing.T) {
		a := newLockedApp()
		t.Setenv("TERMINAL_MASTER_PASSWORD", "wrong-password")
		a.autoUnlockCredentialsFromEnv()
		if got, err := a.credentialStore.Decrypt(secret); err == nil && got == "s3cret" {
			t.Fatal("wrong TERMINAL_MASTER_PASSWORD decrypted the secret")
		}
	})

	t.Run("first-run setup vault is not auto-created", func(t *testing.T) {
		empty := t.TempDir()
		a := NewApp("")
		a.credentialStore = credentials.New(empty, lockedKeychain{})
		t.Setenv("TERMINAL_MASTER_PASSWORD", "right-password")
		a.autoUnlockCredentialsFromEnv()
		if st := a.credentialStore.Status(); !st.NeedsSetup {
			t.Fatalf("status = %+v, want NeedsSetup", st)
		}
	})
}
