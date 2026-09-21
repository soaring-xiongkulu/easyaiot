//go:build windows

package main

import (
	"bytes"
	"fmt"
	"image"
	"image/png"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"unicode/utf16"
	"unsafe"

	"easyaiot/terminal/backend/platform"
	"easyaiot/terminal/backend/session"
	"golang.org/x/sys/windows"
	"golang.org/x/sys/windows/registry"
)

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

	hasShell := func(name string) bool {
		for _, sh := range shells {
			if strings.EqualFold(filepath.Base(sh), name) {
				return true
			}
		}
		return false
	}

	add("pwsh.exe")
	add("powershell.exe")
	add("cmd.exe")
	// CMD (Clink) rides the user's installed clink (1.1+); the Tabby-style
	// profile tuning happens at session start (backend/session/local_clink.go).
	if clink := findClink(); clink != "" {
		shells = append(shells, session.ClinkShellPathPrefix+clink)
	}
	for _, p := range []string{
		`C:\Program Files\Git\bin\bash.exe`,
		`C:\Program Files (x86)\Git\bin\bash.exe`,
		`C:\ProgramData\chocolatey\bin\bash.exe`,
	} {
		add(p)
	}
	// Third-party shells (Cygwin, MSYS2, Nushell): probe well-known install
	// locations and the registry so they are offered automatically, without
	// any user configuration. Added after the built-ins and before the
	// generic PATH bash.exe fallback, whose System32 hit they preempt when a
	// real bash exists.
	for _, sh := range detectThirdPartyShells(probeCygwinRootdir(),
		func(p string) bool {
			_, err := os.Stat(p)
			return err == nil
		},
		exec.LookPath) {
		add(sh)
	}
	if !hasShell("bash.exe") {
		add("bash.exe")
	}
	if distros, _ := listWSLDistros(); len(distros) > 0 {
		for _, d := range distros {
			shells = append(shells, "wsl://"+d)
		}
	}
	// Administrator variants ride on the detected cmd/powershell paths (UAC
	// elevation via the broker in backend/session/local_admin_windows.go).
	// Only offered when Terminal itself is unelevated — as admin they would be
	// indistinguishable duplicates of the plain entries.
	if !session.IsProcessElevated() {
		for _, sh := range shells {
			base := strings.ToLower(filepath.Base(sh))
			if base == "cmd.exe" || base == "powershell.exe" {
				shells = append(shells, session.AdminShellPathPrefix+sh)
			}
		}
		for _, sh := range shells {
			if _, ok := session.ParseClinkShellPath(sh); ok {
				shells = append(shells, session.AdminShellPathPrefix+sh)
			}
		}
	}
	return shells
}

// detectThirdPartyShells probes well-known third-party shell installs that
// should be offered alongside the built-in shells: Cygwin bash, MSYS2 bash
// and Nushell. cygwinRegRoot is the Cygwin setup registry probe result (""
// when absent). Only paths that actually exist are returned; duplicates are
// removed case-insensitively.
func detectThirdPartyShells(cygwinRegRoot string, exists func(string) bool, lookPath func(string) (string, error)) []string {
	var out []string
	seen := make(map[string]bool)
	add := func(path string) {
		if path == "" {
			return
		}
		key := strings.ToLower(path)
		if seen[key] {
			return
		}
		seen[key] = true
		out = append(out, path)
	}

	// Cygwin: setup.exe records the install root in the registry; also probe
	// the conventional install dirs.
	cygwinRoots := []string{`C:\cygwin64`, `C:\cygwin`, `C:\tools\cygwin64`, `C:\tools\cygwin`}
	if cygwinRegRoot != "" {
		cygwinRoots = append([]string{cygwinRegRoot}, cygwinRoots...)
	}
	for _, root := range cygwinRoots {
		bash := filepath.Join(root, "bin", "bash.exe")
		if exists(bash) {
			add(bash)
		}
	}

	// MSYS2: bash lives under usr\bin and there is no registry entry.
	msysRoots := []string{`C:\msys64`, `C:\msys32`, `C:\tools\msys64`, `C:\tools\msys32`}
	if home, err := os.UserHomeDir(); err == nil && home != "" {
		msysRoots = append(msysRoots, filepath.Join(home, "msys64"), filepath.Join(home, "msys32"))
	}
	for _, root := range msysRoots {
		bash := filepath.Join(root, "usr", "bin", "bash.exe")
		if exists(bash) {
			add(bash)
		}
	}

	// Nushell: usually on PATH (scoop/choco/winget shims).
	if nu, err := lookPath("nu.exe"); err == nil && nu != "" {
		add(nu)
	}

	return out
}

// probeCygwinRootdir reads the Cygwin setup install root from the registry.
// Returns "" when Cygwin is absent or the key cannot be read.
func probeCygwinRootdir() string {
	keys := []string{
		`SOFTWARE\Cygwin\setup`,
		`SOFTWARE\WOW6432Node\Cygwin\setup`,
	}
	for _, k := range keys {
		for _, root := range []registry.Key{registry.LOCAL_MACHINE, registry.CURRENT_USER} {
			key, err := registry.OpenKey(root, k, registry.QUERY_VALUE)
			if err != nil {
				continue
			}
			rootdir, _, err := key.GetStringValue("rootdir")
			key.Close()
			if err == nil && rootdir != "" {
				return rootdir
			}
		}
	}
	return ""
}

// findClink locates the user's clink (1.1+): PATH first (covers installs
// that put themselves on PATH, scoop shims and chocolatey shims), then the
// well known install directories clink's setup and package managers use.
// The release layout ships arch-named executables (clink_x64.exe,
// clink_arm64.exe, ... from the official zip), older/manual installs have a
// plain clink.exe — both are accepted. Returns "" when clink is not found.
func findClink() string {
	archExe := map[string]string{
		"amd64": "clink_x64.exe",
		"arm64": "clink_arm64.exe",
		"386":   "clink_x86.exe",
	}[runtime.GOARCH]
	for _, name := range []string{archExe, "clink.exe"} {
		if name == "" {
			continue
		}
		if p, err := exec.LookPath(name); err == nil {
			return p
		}
	}
	for _, dir := range []string{
		filepath.Join(os.Getenv("ProgramFiles"), "clink"),
		filepath.Join(os.Getenv("ProgramFiles(x86)"), "clink"),
		filepath.Join(os.Getenv("LOCALAPPDATA"), "clink"),
		filepath.Join(os.Getenv("USERPROFILE"), "scoop", "apps", "clink", "current"),
		filepath.Join(os.Getenv("SCOOP"), "apps", "clink", "current"),
	} {
		if dir == "" {
			continue
		}
		for _, name := range []string{archExe, "clink.exe"} {
			if name == "" {
				continue
			}
			p := filepath.Join(dir, name)
			if _, err := os.Stat(p); err == nil {
				return p
			}
		}
	}
	return ""
}

func listWSLDistros() ([]string, error) {
	cmd := exec.Command("wsl.exe", "-l", "-q")
	platform.HideConsoleWindow(cmd)
	out, err := cmd.Output()
	if err != nil {
		return nil, nil
	}
	return parseWSLDistros(out), nil
}

func parseWSLDistros(raw []byte) []string {
	if len(raw) == 0 {
		return nil
	}

	content := string(raw)
	if len(raw) >= 2 && raw[0] == 0xFF && raw[1] == 0xFE {
		u16 := make([]uint16, 0, len(raw)/2)
		for i := 2; i+1 < len(raw); i += 2 {
			u16 = append(u16, uint16(raw[i])|uint16(raw[i+1])<<8)
		}
		content = string(utf16.Decode(u16))
	}

	var distros []string
	seen := make(map[string]bool)
	for _, line := range strings.Split(content, "\n") {
		line = strings.TrimSpace(line)
		line = strings.ReplaceAll(line, "\x00", "")
		line = strings.TrimSpace(strings.TrimPrefix(line, "*"))
		if line == "" {
			continue
		}
		lower := strings.ToLower(line)
		if strings.Contains(lower, "docker-desktop") {
			continue
		}
		if !seen[line] {
			seen[line] = true
			distros = append(distros, line)
		}
	}
	return distros
}

const (
	GWLP_WNDPROC     = ^uintptr(3)
	WM_ENTERSIZEMOVE = 0x0231
	WM_EXITSIZEMOVE  = 0x0232
	WM_SYSCOMMAND    = 0x0112
	WM_SIZE          = 0x0005
	SC_MAXIMIZE      = 0xF030
	SC_MINIMIZE      = 0xF020
	SC_RESTORE       = 0xF120
)

func (a *App) findMainWindow() uintptr {
	pid := windows.GetCurrentProcessId()
	var result uintptr

	user32 := windows.NewLazySystemDLL("user32.dll")
	procEnumWindows := user32.NewProc("EnumWindows")
	procGetWindowThreadProcessId := user32.NewProc("GetWindowThreadProcessId")
	procGetWindowTextW := user32.NewProc("GetWindowTextW")

	cb := windows.NewCallback(func(hwnd windows.HWND, lParam uintptr) uintptr {
		var wndPid uint32
		procGetWindowThreadProcessId.Call(uintptr(hwnd), uintptr(unsafe.Pointer(&wndPid)))
		if wndPid != pid {
			return 1 // continue
		}
		// Verify it has our window title so we don't pick up invisible helper windows.
		buf := make([]uint16, 256)
		procGetWindowTextW.Call(uintptr(hwnd), uintptr(unsafe.Pointer(&buf[0])), 255)
		if windows.UTF16ToString(buf) == "终端" {
			result = uintptr(hwnd)
			return 0 // stop
		}
		return 1 // continue
	})
	procEnumWindows.Call(cb, 0)
	return result
}

// bringMainWindowToFront raises the main window to the foreground once. After a
// relaunch the fresh instance can otherwise open behind other windows on Windows:
// SetForegroundWindow is normally restricted, but a process spawned by the
// currently-foreground process is one of the documented exceptions, so a single
// raise works while the old instance (the foreground process) is still alive.
// No-op when no main window has been created yet.
func (a *App) bringMainWindowToFront() {
	hwnd := a.mainHwnd
	if hwnd == 0 {
		hwnd = a.findMainWindow()
	}
	if hwnd == 0 {
		return
	}
	user32 := windows.NewLazySystemDLL("user32.dll")
	procSetForegroundWindow := user32.NewProc("SetForegroundWindow")
	procBringWindowToTop := user32.NewProc("BringWindowToTop")
	procSetForegroundWindow.Call(hwnd)
	procBringWindowToTop.Call(hwnd)
}

// emitMoveResize sends a move/resize event to the frontend without blocking.
// It must never be called from within the WndProc modal resize/move loop.
func (a *App) emitMoveResize(event string) {
	if a.moveResizeCh == nil {
		return
	}
	select {
	case a.moveResizeCh <- event:
	default:
	}
}

func (a *App) subclassMainWindow() {
	if a.mainHwnd == 0 {
		return
	}
	user32 := windows.NewLazySystemDLL("user32.dll")
	procSetWindowLongPtrW := user32.NewProc("SetWindowLongPtrW")
	procCallWindowProcW := user32.NewProc("CallWindowProcW")

	cb := windows.NewCallback(func(hwnd windows.HWND, msg uint32, wparam, lparam uintptr) uintptr {
		switch msg {
		case WM_ENTERSIZEMOVE:
			a.inSizeMove = true
			a.emitMoveResize("rdp:move-resize-start")
		case WM_EXITSIZEMOVE:
			a.inSizeMove = false
			a.emitMoveResize("rdp:move-resize-end")
		case WM_SYSCOMMAND:
			switch wparam {
			case SC_MAXIMIZE, SC_MINIMIZE, SC_RESTORE:
				a.emitMoveResize("rdp:move-resize-start")
			}
		case WM_SIZE:
			if !a.inSizeMove {
				a.emitMoveResize("rdp:move-resize-end")
			}
		}
		ret, _, _ := procCallWindowProcW.Call(a.originalWndProc, uintptr(hwnd), uintptr(msg), wparam, lparam)
		return ret
	})
	a.wndProcCb = cb

	orig, _, _ := procSetWindowLongPtrW.Call(a.mainHwnd, GWLP_WNDPROC, cb)
	a.originalWndProc = orig
}

func (a *App) unsubclassMainWindow() {
	if a.originalWndProc == 0 || a.mainHwnd == 0 {
		return
	}
	user32 := windows.NewLazySystemDLL("user32.dll")
	procSetWindowLongPtrW := user32.NewProc("SetWindowLongPtrW")
	procSetWindowLongPtrW.Call(a.mainHwnd, GWLP_WNDPROC, a.originalWndProc)
	a.originalWndProc = 0
}

// configureMacKeyRepeat is a no-op on Windows; the press-and-hold accent
// picker only exists on macOS. See app_darwin.go for details.
func (a *App) configureMacKeyRepeat() {}

// hideProcWindow prevents batch-file shims (e.g. VS Code's code.cmd) from
// flashing a console window: shims can only run through cmd.exe, which
// allocates a console of its own when launched from a GUI process that has
// none. HideWindow (STARTF_USESHOWWINDOW, SW_HIDE) suppresses that console.
// It must only be applied to shims: GUI exes honor STARTF_USESHOWWINDOW for
// their first window too, so hiding them would leave the editor invisible.
// Editors needing a CLI shim for wait semantics (VS Code's -w lives in the
// node cli.js, not in Code.exe) are launched via their shim + HideWindow.
func hideProcWindow(cmd *exec.Cmd) {
	ext := strings.ToLower(filepath.Ext(cmd.Path))
	if ext == ".cmd" || ext == ".bat" {
		cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	}
}

// openAsInfo mirrors the shell32 OPENASINFO structure for SHOpenWithDialog.
type openAsInfo struct {
	file  uintptr // PCSZW: file to open
	class uintptr // PCSZW: optional ProgID hint (unused)
	flags uint32
}

const (
	oaifAllowRegistration   = 0x00000001 // offer the "always use this app" checkbox
	oaifExec                = 0x00000004 // execute the picked application
	coinitApartmentThreaded = 0x2        // COINIT_APARTMENTTHREADED
)

// openWithSystem pops the system "open with" dialog for the file and executes
// the application the user picks (owned by the main window, so it stays on
// top). It calls the documented SHOpenWithDialog API directly: the legacy
// rundll32 shell32.dll,OpenAs_RunDLLW entry was tried first, but its
// dialog-to-app hand-off corrupts the path on Win10 — the picked app received
// mojibake instead of the file (reproduced with Notepad). The call blocks
// until the dialog closes; cancelling it counts as success.
func (a *App) openWithSystem(p string) error {
	p16, err := windows.UTF16PtrFromString(p)
	if err != nil {
		return err
	}
	// SHOpenWithDialog requires COM (STA) on the calling thread. S_OK (0)
	// means this call initialized it and must pair an uninitialize; S_FALSE
	// (1, already initialized) must not.
	ole32 := windows.NewLazySystemDLL("ole32.dll")
	if r, _, _ := ole32.NewProc("CoInitializeEx").Call(0, coinitApartmentThreaded); r == 0 {
		defer ole32.NewProc("CoUninitialize").Call()
	}
	info := openAsInfo{file: uintptr(unsafe.Pointer(p16)), flags: oaifAllowRegistration | oaifExec}
	shell32 := windows.NewLazySystemDLL("shell32.dll")
	r1, _, callErr := shell32.NewProc("SHOpenWithDialog").Call(a.findMainWindow(), uintptr(unsafe.Pointer(&info)))
	if r1 != 0 {
		return nil
	}
	// User closed the dialog without choosing an app — not an error.
	if errno, ok := callErr.(windows.Errno); ok && errno == windows.ERROR_CANCELLED {
		return nil
	}
	return fmt.Errorf("open-with dialog failed: %w", callErr)
}

// detectExternalEditors scans for text editors installed on this Windows host
// and returns only those actually found. Console-based editors (Vim, Neovim,
// nano, Micro) are excluded: spawned from a GUI app without a console they
// exit immediately, so they aren't offered. Every GUI editor is probed on PATH
// first, then falls back to common install dirs (globbing versioned folders),
// because default Windows installs often leave these off PATH.
func detectExternalEditors() []ExternalEditorOption {
	type fixed struct{ glob, suffix string }
	type editor struct {
		name, prog, pathCmd string
		fixed               []fixed
	}
	// VS Code family: the -w (wait) flag is implemented by the node cli.js
	// invoked from the bin\*.cmd shim, NOT by the GUI exe — launching Code.exe
	// directly exits immediately and breaks auto-upload. So even when the exe
	// is found at a fixed path, the command must point at the bin shim.
	editors := []editor{
		{"VS Code", "code", "code -w", []fixed{
			{filepath.Join(os.Getenv("LOCALAPPDATA"), "Programs", "Microsoft VS Code", "bin", "code.cmd"), " -w"},
			{filepath.Join(os.Getenv("ProgramFiles"), "Microsoft VS Code", "bin", "code.cmd"), " -w"},
		}},
		{"VS Code Insiders", "code-insiders", "code-insiders -w", []fixed{
			{filepath.Join(os.Getenv("LOCALAPPDATA"), "Programs", "Microsoft VS Code Insiders", "bin", "code-insiders.cmd"), " -w"},
			{filepath.Join(os.Getenv("ProgramFiles"), "Microsoft VS Code Insiders", "bin", "code-insiders.cmd"), " -w"},
		}},
		{"VSCodium", "codium", "codium -w", []fixed{
			{filepath.Join(os.Getenv("LOCALAPPDATA"), "Programs", "VSCodium", "bin", "codium.cmd"), " -w"},
			{filepath.Join(os.Getenv("ProgramFiles"), "VSCodium", "bin", "codium.cmd"), " -w"},
		}},
		{"Sublime Text", "subl", "subl -w", []fixed{
			{filepath.Join(os.Getenv("ProgramFiles"), "Sublime Text", "subl.exe"), " -w"},
			{filepath.Join(os.Getenv("ProgramFiles(x86)"), "Sublime Text", "subl.exe"), " -w"},
			{filepath.Join(os.Getenv("LOCALAPPDATA"), "Programs", "Sublime Text", "subl.exe"), " -w"},
		}},
		{"Atom", "atom", "atom", []fixed{
			{filepath.Join(os.Getenv("LOCALAPPDATA"), "atom", "bin", "atom.exe"), ""},
			{filepath.Join(os.Getenv("ProgramFiles"), "Atom", "bin", "atom.exe"), ""},
		}},
		{"gVim", "gvim", "gvim", []fixed{
			{filepath.Join(os.Getenv("ProgramFiles"), "Vim", "vim*", "gvim.exe"), ""},
			{filepath.Join(os.Getenv("ProgramFiles(x86)"), "Vim", "vim*", "gvim.exe"), ""},
		}},
		{"Emacs", "emacs", "emacs", []fixed{
			{filepath.Join(os.Getenv("ProgramFiles"), "Emacs", "emacs-*", "bin", "emacs.exe"), ""},
			{filepath.Join(os.Getenv("LOCALAPPDATA"), "Programs", "Emacs", "emacs-*", "bin", "emacs.exe"), ""},
		}},
		{"Notepad++", "notepad++", "notepad++", []fixed{
			{filepath.Join(os.Getenv("ProgramFiles"), "Notepad++", "notepad++.exe"), ""},
			{filepath.Join(os.Getenv("ProgramFiles(x86)"), "Notepad++", "notepad++.exe"), ""},
			{filepath.Join(os.Getenv("LOCALAPPDATA"), "Programs", "Notepad++", "notepad++.exe"), ""},
		}},
		{"EmEditor", "emeditor", "emeditor", []fixed{
			{filepath.Join(os.Getenv("ProgramFiles"), "EmEditor", "emeditor.exe"), ""},
			{filepath.Join(os.Getenv("ProgramFiles(x86)"), "EmEditor", "emeditor.exe"), ""},
			{filepath.Join(os.Getenv("LOCALAPPDATA"), "Programs", "EmEditor", "emeditor.exe"), ""},
		}},
		{"Notepad--", "notepad--", "notepad--", []fixed{
			{filepath.Join(os.Getenv("ProgramFiles"), "Notepad--", "Notepad--.exe"), ""},
			{filepath.Join(os.Getenv("LOCALAPPDATA"), "Programs", "Notepad--", "Notepad--.exe"), ""},
		}},
		// Notepad lives in System32, which is always on PATH.
		{"Notepad", "notepad", "notepad", nil},
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

	for _, e := range editors {
		// Prefer the real GUI exe in known install dirs: launching it directly
		// avoids the batch shim (code.cmd) and the console window it flashes.
		for _, f := range e.fixed {
			matches, _ := filepath.Glob(f.glob)
			if len(matches) > 0 {
				add(e.name, "\""+matches[0]+"\""+f.suffix)
				break
			}
		}
		if seen[e.name] {
			continue
		}
		// Fall back to PATH (may resolve to a shim — covered by hideProcWindow).
		if _, err := exec.LookPath(e.prog); err == nil {
			add(e.name, e.pathCmd)
		}
	}

	return out
}

// Win11 rounds the corners of top-level windows whose DWM frame is intact.
// Wails' frameless windows keep WS_THICKFRAME, but Wails only extends the DWM
// frame (DwmExtendFrameIntoClientArea) from its WM_ACTIVATE handler, and the
// window's first activation happens inside CreateWindowEx (WS_VISIBLE) before
// Wails' WndProc is hooked — so that first extension is missed. A freshly
// launched binary then shows square corners until the next activation
// (minimise/restore, alt-tab) reapplies it. Asking DWM directly for rounded
// corners makes the first paint correct regardless of activation timing; on
// pre-Win11 systems the unsupported attribute call fails silently, which is
// fine.
const (
	dwmwaWindowCornerPreference = 33
	dwmwcpRound                 = 2
)

var procDwmSetWindowAttribute = syscall.NewLazyDLL("dwmapi.dll").NewProc("DwmSetWindowAttribute")

// applyRoundedCorners sets DWMWCP_ROUND on the given HWND.
func applyRoundedCorners(hwnd unsafe.Pointer) {
	if hwnd == nil {
		return
	}
	preference := uint32(dwmwcpRound)
	_, _, _ = procDwmSetWindowAttribute.Call(
		uintptr(hwnd),
		dwmwaWindowCornerPreference,
		uintptr(unsafe.Pointer(&preference)),
		unsafe.Sizeof(preference),
	)
}

// systemPrefersDark reports whether Windows is in app dark mode, reading the
// same Personalization registry value the WebView2 engine maps to the CSS
// prefers-color-scheme media query. Needed because v3's IsDarkMode() is
// unavailable before Run() and the startup background colour must be resolved
// at window creation. Any failure defaults to dark.
func systemPrefersDark() bool {
	k, err := registry.OpenKey(registry.CURRENT_USER,
		`Software\Microsoft\Windows\CurrentVersion\Themes\Personalize`, registry.QUERY_VALUE)
	if err != nil {
		return true
	}
	defer k.Close()
	val, _, err := k.GetIntegerValue("AppsUseLightTheme")
	if err != nil {
		return true
	}
	return val == 0
}

// waitForRelaunchParent and the TERMINAL_RELAUNCH_PID handshake were removed:
// the relaunch is now quit-then-spawn (relaunchPending + spawnSuccessorProcess
// in main.go), so the successor never sees the lock held.

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

// trayIconPNG returns the tray icon bytes, pre-scaled to the exact OS
// small-icon size (SM_CXSMICON — 16px at 100% DPI, 20/24px at higher scaling)
// with a box filter. wails otherwise hands the raw PNG to
// CreateIconFromResourceEx and GDI's rescale is what made the icon look
// mushy. Called once during tray setup; per-monitor DPI changes are not
// re-rendered (rare for a tray icon).
func trayIconPNG() []byte {
	user32 := windows.NewLazySystemDLL("user32.dll")
	const smCxSmIcon = 49
	size, _, _ := user32.NewProc("GetSystemMetrics").Call(smCxSmIcon)
	if size == 0 {
		size = 16
	}
	return scalePNG(appIconTrayPNG, int(size), int(size))
}

// scalePNG decodes a PNG and box-filter downsamples it to w×h, returning the
// result re-encoded as PNG. On any decode error the input is returned
// unchanged (wails then falls back to GDI scaling). Box filtering averages
// each destination pixel over its source rectangle — the right filter for
// large ratios and cheap enough for a one-shot 64→16px icon.
func scalePNG(data []byte, w, h int) []byte {
	src, err := png.Decode(bytes.NewReader(data))
	if err != nil {
		return data
	}
	b := src.Bounds()
	sw, sh := b.Dx(), b.Dy()
	if sw == 0 || sh == 0 {
		return data
	}
	dst := image.NewRGBA(image.Rect(0, 0, w, h))
	for y := 0; y < h; y++ {
		sy0, sy1 := y*sh/h, (y+1)*sh/h
		if sy1 <= sy0 {
			sy1 = sy0 + 1
		}
		for x := 0; x < w; x++ {
			sx0, sx1 := x*sw/w, (x+1)*sw/w
			if sx1 <= sx0 {
				sx1 = sx0 + 1
			}
			// Average in premultiplied space so transparent edges don't
			// bleed dark fringes into the glyph.
			var rs, gs, bs, as float64
			for sy := sy0; sy < sy1; sy++ {
				for sx := sx0; sx < sx1; sx++ {
					r, g, bl, a := src.At(b.Min.X+sx, b.Min.Y+sy).RGBA()
					rs += float64(r)
					gs += float64(g)
					bs += float64(bl)
					as += float64(a)
				}
			}
			n := float64((sx1 - sx0) * (sy1 - sy0))
			rs, gs, bs, as = rs/n, gs/n, bs/n, as/n
			a8 := uint8(as/257 + 0.5)
			off := (y*w + x) * 4
			if a8 == 0 {
				continue // leave transparent
			}
			dst.Pix[off+0] = uint8(rs/as*257 + 0.5)
			dst.Pix[off+1] = uint8(gs/as*257 + 0.5)
			dst.Pix[off+2] = uint8(bs/as*257 + 0.5)
			dst.Pix[off+3] = a8
		}
	}
	var buf bytes.Buffer
	if err := png.Encode(&buf, dst); err != nil {
		return data
	}
	return buf.Bytes()
}
