package session

import (
	"fmt"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"time"
)

// ParseDisplay parses an X11 $DISPLAY string into its host, display number,
// and screen number. host is "" for local (":0", "unix:0", or a full XQuartz
// abstract socket path starting with "/"). Returns an error for empty or
// malformed values.
func ParseDisplay(s string) (host string, display, screen int, err error) {
	if s == "" {
		return "", 0, 0, fmt.Errorf("empty DISPLAY")
	}

	// XQuartz full abstract socket path: use the path as-is, no host/port
	// parsing. The whole string is the local endpoint.
	if strings.HasPrefix(s, "/") {
		return "", 0, 0, nil
	}

	// Split "host:display.screen" or "host:display" or "unix:display.screen".
	var rest string
	if i := strings.LastIndex(s, ":"); i < 0 {
		return "", 0, 0, fmt.Errorf("missing ':' in %q", s)
	} else {
		host, rest = s[:i], s[i+1:]
	}
	if host == "unix" {
		host = ""
	}

	dispStr := rest
	if i := strings.Index(rest, "."); i >= 0 {
		dispStr = rest[:i]
		if rest[i+1:] != "" {
			screen, err = strconv.Atoi(rest[i+1:])
			if err != nil {
				return "", 0, 0, fmt.Errorf("bad screen: %w", err)
			}
		}
	}
	display, err = strconv.Atoi(dispStr)
	if err != nil {
		return "", 0, 0, fmt.Errorf("bad display: %w", err)
	}
	if display < 0 {
		return "", 0, 0, fmt.Errorf("negative display: %d", display)
	}
	return host, display, screen, nil
}

// resolveLocalDisplay returns a usable X11 display string. A non-empty raw
// value (normally $DISPLAY) is used verbatim. When it's empty on macOS/Linux
// — a GUI-launched app often doesn't inherit $DISPLAY, and a macOS .app opened
// from Finder/Dock has its environment stripped entirely — it probes the
// standard socket dir /tmp/.X11-unix/Xn and returns ":n" for the lowest live
// socket (XQuartz/Xorg both listen there). Returns "" if nothing is found.
func resolveLocalDisplay(raw string) string {
	if raw != "" || runtime.GOOS == "windows" {
		return raw
	}
	entries, err := os.ReadDir("/tmp/.X11-unix")
	if err != nil {
		return ""
	}
	best := -1
	for _, e := range entries {
		name := e.Name()
		if !strings.HasPrefix(name, "X") {
			continue
		}
		n, aerr := strconv.Atoi(name[1:])
		if aerr != nil || n < 0 {
			continue
		}
		if best == -1 || n < best {
			best = n
		}
	}
	if best == -1 {
		return ""
	}
	return ":" + strconv.Itoa(best)
}

// DialLocalX connects to the X server pointed to by `display`.
//   - ":N" / "unix:N"                         → unix socket /tmp/.X11-unix/XN
//     on Linux/macOS, with a parallel TCP fallback to 127.0.0.1:6000+N.
//   - "host:N"                                → TCP host:6000+N.
//   - A path beginning with "/" (XQuartz etc.) → that exact unix socket.
//
// Local dials try unix and TCP in parallel (5s total) and return whichever
// wins, so an X server with no unix socket (e.g. -nolisten unix, Wayland
// shim) still works.
func DialLocalX(display string) (net.Conn, error) {
	host, disp, _, err := ParseDisplay(display)
	if err != nil {
		return nil, err
	}

	if host == "" || host == "localhost" || host == "127.0.0.1" {
		conn, err := dialLocal(runtime.GOOS, display, disp, 5*time.Second)
		if err != nil && runtime.GOOS == "windows" {
			// VcXsrv not running — try to start it.
			if started := tryStartLocalXServer(disp); started {
				conn, err = dialLocal(runtime.GOOS, display, disp, 5*time.Second)
			}
		}
		return conn, err
	}
	return net.DialTimeout("tcp", net.JoinHostPort(host, "600"+strconv.Itoa(disp)), 5*time.Second)
}

// findFreeDisplay scans display numbers starting from startFrom, returning
// the first one where no X server is listening. Returns -1 if no free
// display is found in the range [startFrom, 99].
func findFreeDisplay(startFrom int) int {
	for d := startFrom; d < 100; d++ {
		port := fmt.Sprintf("127.0.0.1:%d", 6000+d)
		c, err := net.DialTimeout("tcp", port, 200*time.Millisecond)
		if err != nil {
			return d // port not reachable → display is free
		}
		c.Close()
	}
	return -1
}

// launchVcXsrv starts a new VcXsrv instance on the given display number
// and waits up to 5 s for it to become ready. Returns the exec.Cmd so the
// caller can manage the process lifetime (e.g. kill it when done). Returns
// nil if VcXsrv is already running on this display, the binary cannot be
// found, or the process fails to become ready within the timeout.
// Extra args (e.g. "-multiwindow") are appended after "-clipboard".
// No-op on non-Windows platforms.
func launchVcXsrv(disp int, extraArgs ...string) *exec.Cmd {
	if runtime.GOOS != "windows" {
		return nil
	}
	port := fmt.Sprintf("127.0.0.1:%d", 6000+disp)
	if c, err := net.DialTimeout("tcp", port, 200*time.Millisecond); err == nil {
		c.Close()
		return nil // already running
	}
	dispStr := strconv.Itoa(disp)
	for _, path := range vcxsrvCandidates() {
		if _, err := os.Stat(path); err != nil {
			continue
		}
		args := append([]string{":" + dispStr, "-clipboard"}, extraArgs...)
		cmd := exec.Command(path, args...)
		home, _ := os.UserHomeDir()
		cmd.Dir = home
		if err := cmd.Start(); err != nil {
			return nil
		}
		// Wait for VcXsrv to open its TCP socket (up to 5 s).
		for i := 0; i < 50; i++ {
			time.Sleep(100 * time.Millisecond)
			if c, err := net.DialTimeout("tcp", port, 200*time.Millisecond); err == nil {
				c.Close()
				return cmd
			}
		}
		// Timed out — kill the partial process so we don't leak zombies.
		cmd.Process.Kill()
		return nil
	}
	return nil
}

// tryStartLocalXServer is the fire-and-forget version of launchVcXsrv.
// It starts VcXsrv on the given display in multiwindow mode and releases
// the process handle so VcXsrv outlives the current session. Used by SSH
// X11 forwarding where the X server should stay running across multiple
// connections and each X client gets its own window.
// Returns true if it spawned a new process (caller should retry the dial).
func tryStartLocalXServer(disp int) bool {
	cmd := launchVcXsrv(disp, "-multiwindow")
	if cmd != nil {
		// Release the process handle — VcXsrv keeps running independently.
		cmd.Process.Release()
		return true
	}
	return false
}

func dialLocal(goos, display string, disp int, timeout time.Duration) (net.Conn, error) {
	tcpAddr := net.JoinHostPort("127.0.0.1", "600"+strconv.Itoa(disp))
	if goos == "windows" {
		return net.DialTimeout("tcp", tcpAddr, timeout)
	}

	var unixAddr string
	if strings.HasPrefix(display, "/") {
		unixAddr = display
	} else {
		unixAddr = "/tmp/.X11-unix/X" + strconv.Itoa(disp)
	}

	type result struct {
		conn net.Conn
		err  error
	}
	ch := make(chan result, 2)
	go func() { c, e := net.DialTimeout("unix", unixAddr, timeout); ch <- result{c, e} }()
	go func() { c, e := net.DialTimeout("tcp", tcpAddr, timeout); ch <- result{c, e} }()
	var firstErr error
	for i := 0; i < 2; i++ {
		r := <-ch
		if r.err == nil {
			return r.conn, nil
		}
		if firstErr == nil {
			firstErr = r.err
		}
	}
	return nil, firstErr
}

// vcxsrvCandidates returns ordered paths where vcxsrv.exe may be found:
// bundled copy (production + dev), then system-wide installs.
func vcxsrvCandidates() []string {
	var paths []string
	if exe, err := os.Executable(); err == nil {
		dir := filepath.Dir(exe)
		paths = append(paths, filepath.Join(dir, "plugins", "vcxsrv", "vcxsrv.exe"))
	}
	// Development convenience: wails dev runs from the project root
	if wd, err := os.Getwd(); err == nil {
		paths = append(paths, filepath.Join(wd, "plugins", "vcxsrv", "vcxsrv.exe"))
	}
	paths = append(paths,
		`C:\Program Files\VcXsrv\vcxsrv.exe`,
		`C:\Program Files (x86)\VcXsrv\vcxsrv.exe`,
	)
	return paths
}

// --- SSH X11 forwarding shared VcXsrv ---
//
// SSH X11 forwarding sessions share a single dedicated VcXsrv instance.
// This isolates Terminal's X11 forwarding from external X servers (e.g.
// MobaXterm on :0) and keeps the X server running across multiple SSH
// sessions. The process is killed on application shutdown.

var (
	sshX11Mu      sync.Mutex
	sshX11Display string   // e.g. "localhost:0"
	sshX11Vcxsrv  *exec.Cmd // nil on non-Windows or if launch failed
)

// ResolveSSHX11Display returns the X11 display for SSH X11 forwarding sessions.
// On Windows it starts a dedicated VcXsrv instance on a free display; on other
// platforms it returns $DISPLAY (or probes /tmp/.X11-unix). Idempotent —
// subsequent calls return the same display without side effects.
func ResolveSSHX11Display() string {
	sshX11Mu.Lock()
	defer sshX11Mu.Unlock()

	if sshX11Display != "" {
		return sshX11Display
	}

	if runtime.GOOS == "windows" {
		d := findFreeDisplay(0)
		if d < 0 {
			return ""
		}
		sshX11Display = "localhost:" + strconv.Itoa(d)
		// -multiwindow: each X client gets its own Windows window
		// (the opposite of X11 Desktop which uses single-window mode).
		sshX11Vcxsrv = launchVcXsrv(d, "-multiwindow")
	} else {
		display := os.Getenv("DISPLAY")
		if display == "" {
			display = resolveLocalDisplay("")
		}
		sshX11Display = display
	}
	return sshX11Display
}

// CleanupSSHX11Server kills the shared VcXsrv process started for SSH X11
// forwarding. Call on application shutdown. Safe to call multiple times;
// no-op on non-Windows platforms.
func CleanupSSHX11Server() {
	sshX11Mu.Lock()
	defer sshX11Mu.Unlock()

	if sshX11Vcxsrv != nil {
		sshX11Vcxsrv.Process.Kill()
		sshX11Vcxsrv = nil
	}
	sshX11Display = ""
}

// sshX11DisplayNumber returns the display number of the cached SSH X11
// display, or -1 if it has not been resolved yet.
func sshX11DisplayNumber() int {
	sshX11Mu.Lock()
	defer sshX11Mu.Unlock()

	if sshX11Display == "" {
		return -1
	}
	_, disp, _, err := ParseDisplay(sshX11Display)
	if err != nil {
		return -1
	}
	return disp
}
