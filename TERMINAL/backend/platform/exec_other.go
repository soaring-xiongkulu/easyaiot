//go:build !windows

package platform

import "os/exec"

// HideConsoleWindow is a no-op on non-Windows platforms: there is no console
// window to suppress when spawning child processes.
func HideConsoleWindow(cmd *exec.Cmd) {}
