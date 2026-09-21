//go:build !windows
// +build !windows

package session

// RunLocalPtyBroker is the Windows administrator-shell broker hook; on other
// platforms administrator local terminals don't exist and this is a no-op.
func RunLocalPtyBroker(args []string) bool {
	return false
}
