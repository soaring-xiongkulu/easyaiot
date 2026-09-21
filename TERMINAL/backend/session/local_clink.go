package session

import (
	"os"
	"path/filepath"
	"strings"
)

// ClinkShellPathPrefix marks a local-terminal ShellPath that launches
// cmd.exe with clink (https://chrisant996.github.io/clink/) injected, e.g.
// "clink://C:\Program Files\clink\clink.exe". It mirrors the wsl:// scheme:
// the prefix carries the launch mode, the rest is the clink executable path.
// Combine with admin:// (admin://clink://...) for an elevated variant.
const ClinkShellPathPrefix = "clink://"

// clinkProfileDirOverride is the directory handed to clink via
// `inject --profile`. Set by the app at startup (and on data-dir changes)
// to <dataDir>/clink; empty falls back to the OS config dir.
var clinkProfileDirOverride string

// SetClinkProfileDir points clink sessions at dir. Called from app startup
// with the resolved data directory so the profile lives next to the other
// Terminal state.
func SetClinkProfileDir(dir string) {
	clinkProfileDirOverride = dir
}

// ParseClinkShellPath splits a clink:// ShellPath into the clink executable
// path. ok is false when path does not carry the clink:// prefix.
func ParseClinkShellPath(path string) (clinkPath string, ok bool) {
	const prefix = ClinkShellPathPrefix
	if len(path) < len(prefix) || !strings.EqualFold(path[:len(prefix)], prefix) {
		return "", false
	}
	return path[len(prefix):], true
}

// clinkProfileDir resolves the profile directory passed to clink inject.
func clinkProfileDir() string {
	if clinkProfileDirOverride != "" {
		return clinkProfileDirOverride
	}
	if cfg, err := os.UserConfigDir(); err == nil {
		return filepath.Join(cfg, "Terminal", "clink")
	}
	return filepath.Join(os.TempDir(), "terminal-clink")
}

// ensureClinkProfile creates the clink profile directory and drops the
// enhanced default_settings into it. clink reads a file named
// "default_settings" from the profile directory and applies it UNDER the
// user's clink_settings, so these behave as tuned defaults while every value
// stays user-overridable. Rewritten whenever the built-in content changes;
// a failure must never block the session (clink also runs without it).
func ensureClinkProfile() string {
	dir := clinkProfileDir()
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return ""
	}
	settings := filepath.Join(dir, "default_settings")
	cur, err := os.ReadFile(settings)
	if err != nil || string(cur) != clinkDefaultSettings {
		_ = os.WriteFile(settings, []byte(clinkDefaultSettings), 0o644)
	}
	return dir
}

// buildClinkCommandLine builds the ConPTY command line for a clink-backed
// cmd.exe session, in the shape Tabby uses: `cmd.exe /k <clink> inject`.
// The inject subcommand loads clink's DLL into the running cmd process, and
// --profile points it at Terminal's tuned profile directory. Requires clink
// 1.1+ (older 0.4.x releases have no --profile); on failure cmd simply stays
// open without clink, degrading to a plain Command Prompt session.
//
// Quoting: cmd's /k parser strips the outermost quote pair when the /k
// argument starts with a quote and doesn't meet its single-pair exception
// (more than two quote characters here guarantees that), so the inner
// command is wrapped in one extra pair — the classic `cmd /k ""a" b "c""`
// pattern that survives spaces in both the clink path and the profile dir.
func buildClinkCommandLine(clinkPath, profileDir string) string {
	cmdExe := os.Getenv("ComSpec")
	if cmdExe == "" {
		cmdExe = "cmd.exe"
	}
	inner := "\"" + clinkPath + "\" inject"
	if profileDir != "" {
		inner += " --profile \"" + profileDir + "\""
	}
	return "\"" + cmdExe + "\" /k \"" + inner + "\""
}

// clinkDefaultSettings is written as the profile's default_settings. The
// values mirror Tabby's bundled extras/clink/default_settings, which is
// half of why clink feels so much better inside Tabby than a bare install:
// substring + envvar-expanding completion, 25k history lines with visible
// timestamps, syntax-colored input, and Windows-style default key bindings.
// The other half (WT_SESSION=0, see LocalSession.Connect) tells clink the
// host is a ConPTY terminal so it skips its own ANSI emulation layer.
const clinkDefaultSettings = `# When this file is named "default_settings" and is in the binaries
# directory or profile directory, it provides enhanced default settings.

# Override built-in default settings with ones that provide a more
# enhanced Clink experience.

clink.default_bindings            = windows
clink.autoupdate                  = off
cmd.ctrld_exits                   = False
color.arginfo                     = sgr 38;5;172
color.argmatcher                  = sgr 1;38;5;40
color.cmd                         = bold
color.cmdredir                    = sgr 38;5;172
color.cmdsep                      = sgr 38;5;135
color.comment_row                 = sgr 38;5;87;48;5;18
color.description                 = sgr 38;5;39
color.doskey                      = sgr 1;38;5;75
color.executable                  = sgr 1;38;5;33
color.filtered                    = bold
color.flag                        = sgr 38;5;117
color.hidden                      = sgr 38;5;160
color.histexpand                  = sgr 97;48;5;55
color.horizscroll                 = sgr 38;5;16;48;5;30
color.input                       = sgr 38;5;214
color.readonly                    = sgr 38;5;28
color.selected_completion         = sgr 7
color.selection                   = sgr 38;5;16;48;5;179
color.unrecognized                = sgr 38;5;203
history.max_lines                 = 25000
history.time_stamp                = show
match.expand_envvars              = True
match.substring                   = True
`
