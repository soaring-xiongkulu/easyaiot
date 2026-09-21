package update

import (
	"errors"
	"os"

	"github.com/minio/selfupdate"
	"easyaiot/terminal/backend/log"
)

// Apply installs the staged update in place and reports progress. The caller
// is responsible for relaunching/restarting the app afterwards. The
// platform-specific logic lives in apply_<os>.go (applyPlatform).
func (m *Manager) Apply(onProgress func(Progress)) error {
	pend := m.Pending()
	if pend == nil {
		return errors.New("no staged update")
	}
	return m.applyPlatform(pend, onProgress)
}

// applyBinary replaces the running executable with newBinary using
// minio/selfupdate (which handles the Windows locked-file rename dance and
// Unix permission semantics). A backup copy of the current binary is kept at
// <exe>.terminal-old and removed on success or used for a best-effort rollback.
func applyBinary(newBinary string, onProgress func(Progress)) error {
	if onProgress != nil {
		onProgress(Progress{Phase: "applying", Total: -1})
	}

	exe, err := os.Executable()
	if err != nil {
		return err
	}

	backupPath := exe + ".terminal-old"
	backedUp := false
	if data, err := os.ReadFile(exe); err == nil {
		if werr := os.WriteFile(backupPath, data, 0755); werr == nil {
			backedUp = true
		}
	}

	f, err := os.Open(newBinary)
	if err != nil {
		return err
	}
	defer f.Close()

	if err := selfupdate.Apply(f, selfupdate.Options{}); err != nil {
		log.Writef("[update] apply failed: %v", err)
		// Best-effort rollback: selfupdate may have already renamed the
		// running exe away, so restoring the backup makes the app runnable.
		if backedUp {
			if rerr := os.Rename(backupPath, exe); rerr == nil {
				log.Writef("[update] rolled back from backup")
			}
		}
		return err
	}

	if backedUp {
		_ = os.Remove(backupPath)
	}
	log.Writef("[update] binary replaced: %s", exe)
	return nil
}
