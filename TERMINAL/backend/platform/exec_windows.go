//go:build windows

package platform

import (
	"os/exec"
	"syscall"
)

// HideConsoleWindow sets CREATE_NO_WINDOW on cmd so spawning a
// console-subsystem executable (wsl.exe, cmd.exe, docker.exe, ...) from
// Terminal's GUI-subsystem process — which has no console of its own — does
// not make Windows allocate a visible conhost window that flashes on screen.
//
// This is the single shared entry point for every fire-and-forget child
// process in the codebase (wsl.exe one-shots, file-panel helpers, distro
// listing, ...). New exec.Command call sites for console executables must go
// through it; without it each spawn flashes a console window. Sessions that
// run inside a ConPTY are exempt: the pseudoconsole is headless and conpty
// manages its own (windowless) conhost.
func HideConsoleWindow(cmd *exec.Cmd) {
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
}
