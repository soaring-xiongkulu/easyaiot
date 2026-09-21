//go:build windows

package update

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"

	"easyaiot/terminal/backend/log"
)

func (m *Manager) applyPlatform(pend *PendingUpdate, onProgress func(Progress)) error {
	switch pend.Kind {
	case "installer":
		return launchInstallerUpdate(pend, onProgress)
	case "portable":
		if err := applyBinary(pend.NewBinary, onProgress); err != nil {
			return err
		}
		return copyPlugins(pend.StageDir)
	}
	return fmt.Errorf("unsupported payload kind %q", pend.Kind)
}

// copyPlugins merges the extracted plugins/ directory (VcXsrv) next to the
// running executable. New files are added; existing ones are overwritten.
func copyPlugins(stage string) error {
	exe, err := os.Executable()
	if err != nil {
		return err
	}
	src := filepath.Join(stage, "plugins")
	if _, err := os.Stat(src); err != nil {
		// No plugins payload (older release) — not fatal.
		return nil
	}
	dst := filepath.Join(filepath.Dir(exe), "plugins")
	return filepath.Walk(src, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(src, path)
		if err != nil {
			return err
		}
		target := filepath.Join(dst, rel)
		if info.IsDir() {
			return os.MkdirAll(target, 0755)
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		if err := os.MkdirAll(filepath.Dir(target), 0755); err != nil {
			return err
		}
		return os.WriteFile(target, data, 0755)
	})
}

// launchInstallerUpdate writes a detached updater script that waits for the
// running app to exit, runs the new NSIS installer silently, relaunches the
// app, and finally removes the staging dir and itself. The app must quit right
// after Apply() returns.
//
// Two NSIS quirks are handled here:
//   - /D=<dir> (last parameter, unquoted) forces the installer to target the
//     directory the app actually runs from, since project.nsi has a fixed
//     default InstallDir and no InstallDirRegKey.
//   - Silent installs skip the MUI finish page, so MUI_FINISHPAGE_RUN never
//     fires — the script relaunches the app explicitly.
func launchInstallerUpdate(pend *PendingUpdate, onProgress func(Progress)) error {
	if onProgress != nil {
		onProgress(Progress{Phase: "applying", Total: -1, Message: "installer-launched"})
	}

	appExe, err := os.Executable()
	if err != nil {
		return err
	}
	appDir := filepath.Dir(appExe)

	script := filepath.Join(pend.StageDir, "updater.cmd")
	content := fmt.Sprintf(`@echo off
:waitloop
tasklist /FI "IMAGENAME eq Terminal.exe" 2>nul | find /I "Terminal.exe" >nul
if not errorlevel 1 (
  timeout /t 1 /nobreak >nul
  goto waitloop
)
start "" /wait "%s" /S /D=%s
start "" "%s"
rmdir /s /q "%s"
del "%%~f0"
`, pend.FilePath, appDir, appExe, pend.StageDir)
	if err := os.WriteFile(script, []byte(content), 0644); err != nil {
		return err
	}

	cmd := exec.Command("cmd.exe", "/C", "start", "", "cmd.exe", "/C", script)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: 0x00000008 | 0x00000200} // DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
	if err := cmd.Start(); err != nil {
		return err
	}
	log.Writef("[update] installer updater launched: %s", script)
	return nil
}
