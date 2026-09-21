//go:build linux

package main

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
	"unsafe"
)

func (a *App) findMainWindow() uintptr { return 0 }

// hideProcWindow is a no-op on non-Windows platforms: the console-flash issue
// is Windows-specific (batch-file shims spawning cmd.exe). See app_windows.go.
func hideProcWindow(cmd *exec.Cmd) {}

func (a *App) subclassMainWindow() {}

func (a *App) unsubclassMainWindow() {}

// bringMainWindowToFront is a no-op on non-Windows platforms: the relaunched-
// window-behind-others issue is Windows-specific and does not occur here.
func (a *App) bringMainWindowToFront() {}

func (a *App) GetAvailableShells() []string {
	var shells []string
	var seen = make(map[string]bool)

	add := func(path string) {
		if path == "" {
			return
		}
		abs, err := exec.LookPath(path)
		if err != nil {
			return
		}
		key := strings.ToLower(strings.ReplaceAll(abs, `\`, `/`))
		if seen[key] {
			return
		}
		seen[key] = true
		shells = append(shells, abs)
	}

	add(os.Getenv("SHELL"))
	add("bash")
	add("zsh")
	add("fish")
	add("sh")
	return shells
}

// configureMacKeyRepeat is a no-op on non-macOS platforms; the press-and-hold
// accent picker only exists on macOS. See app_darwin.go for details.
func (a *App) configureMacKeyRepeat() {}

// detectExternalEditors scans for text editors installed on this Linux host
// and returns only those actually found. All editors work here (they inherit a
// usable terminal, and GUI editors open their own windows), so terminal editors
// are offered too. There are no fixed-path/.app bundles to add beyond PATH.
func detectExternalEditors() []ExternalEditorOption {
	type cand struct{ name, prog, command string }
	pathCands := []cand{
		{"VS Code", "code", "code -w"},
		{"VS Code Insiders", "code-insiders", "code-insiders -w"},
		{"VSCodium", "codium", "codium -w"},
		{"Sublime Text", "subl", "subl -w"},
		{"Atom", "atom", "atom"},
		{"Vim", "vim", "vim"},
		{"gVim", "gvim", "gvim"},
		{"Neovim", "nvim", "nvim"},
		{"Emacs", "emacs", "emacs"},
		{"nano", "nano", "nano"},
		{"Micro", "micro", "micro"},
		{"gedit", "gedit", "gedit"},
		{"Kate", "kate", "kate"},
		{"mousepad", "mousepad", "mousepad"},
		{"pluma", "pluma", "pluma"},
	}

	var out []ExternalEditorOption
	seen := map[string]bool{} // by canonical display name
	add := func(name, command string) {
		if seen[name] {
			return
		}
		seen[name] = true
		out = append(out, ExternalEditorOption{Label: name + " (" + command + ")", Value: command})
	}

	for _, c := range pathCands {
		if _, err := exec.LookPath(c.prog); err == nil {
			add(c.name, c.command)
		}
	}

	return out
}

// applyRoundedCorners is a no-op on Linux: window corners are handled by the
// platform (the Windows build asks DWM for Win11 rounded corners instead).
func applyRoundedCorners(unsafe.Pointer) {}

// openWithSystem opens the file with its default associated application via
// xdg-open. Linux has no scriptable cross-desktop "open with" picker, so the
// degrading behaviour from the issue discussion applies: no chooser, the file
// simply opens in whatever the desktop currently associates with the extension.
func (a *App) openWithSystem(p string) error {
	cmd := exec.Command("xdg-open", p)
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to open %s: %w", p, err)
	}
	go cmd.Wait()
	return nil
}

// systemPrefersDark reports whether the Linux desktop prefers a dark colour
// scheme, queried from the freedesktop colour-scheme setting — the same value
// WebKitGTK maps to the CSS prefers-color-scheme media query. Read failures
// (no gsettings, minimal WMs) default to dark. Needed because v3's
// IsDarkMode() is unavailable before Run() (see main.go windowBackgroundColour).
func systemPrefersDark() bool {
	ctx, cancel := context.WithTimeout(context.Background(), 250*time.Millisecond)
	defer cancel()
	out, err := exec.CommandContext(ctx, "gsettings", "get",
		"org.gnome.desktop.interface", "color-scheme").Output()
	if err != nil {
		return true
	}
	return !strings.Contains(strings.ToLower(string(out)), "light")
}

// spawnSuccessorProcess starts a fresh, detached copy of the current
// executable. Called from main() AFTER w3app.Run() has returned and the
// process is about to exit, so the successor starts with the single-instance
// lock free and the stores quiesced (see RelaunchApp for why spawn happens
// after quit).
func spawnSuccessorProcess() error {
	exe, err := os.Executable()
	if err != nil {
		return err
	}
	cmd := exec.Command(exe)
	cmd.Dir = filepath.Dir(exe)
	return cmd.Start()
}

// trayIconPNG returns the tray icon bytes as-is off Windows: macOS and Linux
// tray implementations take the PNG directly and size it themselves (see
// app_windows.go for the Windows exact-size scaling).
func trayIconPNG() []byte {
	return appIconTrayPNG
}
