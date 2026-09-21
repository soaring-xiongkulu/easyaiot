//go:build windows

package session

import "syscall"

// isPathHidden reports whether a file at the given absolute path has the
// Windows FILE_ATTRIBUTE_HIDDEN flag set.
func isPathHidden(absPath string) bool {
	p, err := syscall.UTF16PtrFromString(absPath)
	if err != nil {
		return false
	}
	attrs, err := syscall.GetFileAttributes(p)
	if err != nil {
		return false
	}
	return attrs&syscall.FILE_ATTRIBUTE_HIDDEN != 0
}
