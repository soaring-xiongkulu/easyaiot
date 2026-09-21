//go:build android

package log

import (
	"os"
	"path/filepath"
)

// logPath on Android: the app sandbox has no home directory, so write into
// the process temp dir (Android points TMPDIR at the app's private cache
// dir). Failure to open the log file is already tolerated by callers.
func logPath() string {
	return filepath.Join(os.TempDir(), "terminal.log")
}
