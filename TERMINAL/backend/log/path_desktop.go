//go:build !android

package log

import (
	"os"
	"path/filepath"
)

// logPath returns the desktop log location (~/.terminal/terminal.log).
func logPath() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return "terminal.log"
	}
	return filepath.Join(home, ".terminal", "terminal.log")
}
