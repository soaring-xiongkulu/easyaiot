//go:build !windows && !darwin && !linux

package update

import "fmt"

// applyPlatform fallback for unsupported platforms (never shipped).
func (m *Manager) applyPlatform(pend *PendingUpdate, onProgress func(Progress)) error {
	return fmt.Errorf("unsupported platform")
}
