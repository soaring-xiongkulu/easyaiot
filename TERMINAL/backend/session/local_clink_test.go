//go:build windows
// +build windows

package session

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestParseClinkShellPath(t *testing.T) {
	const clinkPath = `C:\Program Files\clink\clink.exe`
	for _, tc := range []struct {
		name, in, want string
		ok             bool
	}{
		{"prefixed", ClinkShellPathPrefix + clinkPath, clinkPath, true},
		{"prefixed uppercase scheme", "CLINK://" + clinkPath, clinkPath, true},
		{"admin composition", AdminShellPathPrefix + ClinkShellPathPrefix + clinkPath, "", false},
		{"plain path", clinkPath, "", false},
		{"wsl scheme", "wsl://Ubuntu", "", false},
		{"empty", "", "", false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			got, ok := ParseClinkShellPath(tc.in)
			if ok != tc.ok || got != tc.want {
				t.Fatalf("ParseClinkShellPath(%q) = (%q, %v), want (%q, %v)", tc.in, got, ok, tc.want, tc.ok)
			}
		})
	}
}

func TestBuildClinkCommandLine(t *testing.T) {
	t.Setenv("ComSpec", `C:\Windows\System32\cmd.exe`)
	got := buildClinkCommandLine(`C:\Program Files\clink\clink.exe`, `C:\Users\a b\AppData\Local\clink`)

	// The whole /k argument is wrapped in an extra outer quote pair so cmd's
	// /k parser strips it (leaving the inner quoting balanced) even though
	// both the clink path and the profile dir contain spaces.
	want := `"C:\Windows\System32\cmd.exe" /k ""C:\Program Files\clink\clink.exe" inject --profile "C:\Users\a b\AppData\Local\clink""`
	if got != want {
		t.Fatalf("buildClinkCommandLine =\n %q\nwant\n %q", got, want)
	}
	if n := strings.Count(got, `"`); n != 8 {
		t.Fatalf("quote count = %d, want 8 (cmd pair + outer pair + two inner pairs)", n)
	}
}

func TestBuildClinkCommandLineNoProfile(t *testing.T) {
	t.Setenv("ComSpec", "")
	// Empty ComSpec falls back to PATH-resolved cmd.exe; an empty profile dir
	// must omit the --profile flag entirely, not emit `--profile ""`.
	got := buildClinkCommandLine(`C:\clink\clink.exe`, "")
	want := `"cmd.exe" /k ""C:\clink\clink.exe" inject"`
	if got != want {
		t.Fatalf("buildClinkCommandLine = %q, want %q", got, want)
	}
}

func TestEnsureClinkProfile(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "clink")
	SetClinkProfileDir(dir)
	t.Cleanup(func() { SetClinkProfileDir("") })

	if got := ensureClinkProfile(); got != dir {
		t.Fatalf("ensureClinkProfile() = %q, want %q", got, dir)
	}
	settings := filepath.Join(dir, "default_settings")
	cur, err := os.ReadFile(settings)
	if err != nil {
		t.Fatalf("default_settings not written: %v", err)
	}
	if string(cur) != clinkDefaultSettings {
		t.Fatalf("default_settings content mismatch")
	}

	// Rewrites when the built-in content changes, never on unchanged reruns.
	if err := os.WriteFile(settings, []byte("stale"), 0o644); err != nil {
		t.Fatalf("seed stale file: %v", err)
	}
	ensureClinkProfile()
	cur, err = os.ReadFile(settings)
	if err != nil {
		t.Fatalf("reread: %v", err)
	}
	if string(cur) != clinkDefaultSettings {
		t.Fatalf("stale default_settings was not refreshed")
	}
}

func TestShellNameClink(t *testing.T) {
	if got := shellName(ClinkShellPathPrefix + `C:\clink\clink.exe`); got != "CMD (Clink)" {
		t.Fatalf("shellName(clink) = %q, want %q", got, "CMD (Clink)")
	}
	if got := shellName(AdminShellPathPrefix + ClinkShellPathPrefix + `C:\clink\clink.exe`); got != "CMD (Clink) (Admin)" {
		t.Fatalf("shellName(admin clink) = %q, want %q", got, "CMD (Clink) (Admin)")
	}
}
