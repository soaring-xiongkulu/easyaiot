//go:build linux

package update

// applyPlatform replaces the binary in place. deb/rpm installs resolve to the
// portable channel too; the replacement fails with a permission error for
// unprivileged users, which the UI surfaces as update feedback.
func (m *Manager) applyPlatform(pend *PendingUpdate, onProgress func(Progress)) error {
	return applyBinary(pend.NewBinary, onProgress)
}
