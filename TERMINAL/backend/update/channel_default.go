//go:build !windows

package update

// detectChannel is the default for every platform except Windows: self-update
// always replaces the binary in place. deb/rpm installs resolve to the same
// channel; replacing /usr/bin/terminal fails with a permission error for
// unprivileged users, which the UI surfaces alongside the hint to prefer the
// package manager.
func detectChannel() Channel {
	return ChannelPortable
}
