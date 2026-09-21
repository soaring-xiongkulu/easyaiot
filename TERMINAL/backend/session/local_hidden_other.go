//go:build !windows

package session

// isPathHidden always returns false on non-Windows platforms because hidden
// files are identified by the dot-prefix convention which is handled by the
// caller.
func isPathHidden(absPath string) bool { return false }
