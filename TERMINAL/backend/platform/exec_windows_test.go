//go:build windows

package platform

import (
	"os/exec"
	"testing"
)

// HideConsoleWindow must set SysProcAttr.HideWindow (CREATE_NO_WINDOW) so
// console-subsystem children spawned from Terminal's GUI process do not get a
// visible conhost window. Every wsl.exe / cmd.exe spawn site is expected to
// go through this helper; this test pins the behavior it promises.
func TestHideConsoleWindow(t *testing.T) {
	cmd := exec.Command("wsl.exe", "-l", "-q")
	HideConsoleWindow(cmd)
	if cmd.SysProcAttr == nil || !cmd.SysProcAttr.HideWindow {
		t.Fatal("HideConsoleWindow must set SysProcAttr.HideWindow")
	}
}
