//go:build windows

package update

import (
	"golang.org/x/sys/windows/registry"
)

// detectChannel distinguishes NSIS installs (registry uninstall key written by
// build/windows/installer/project.nsi) from portable-zip runs. The NSIS
// installer is 32-bit and writes without SetRegView, so on 64-bit Windows the
// key lands in the WOW6432Node (32-bit) view — check both views.
func detectChannel() Channel {
	const key = `Software\Microsoft\Windows\CurrentVersion\Uninstall\Terminal`
	for _, root := range []registry.Key{registry.LOCAL_MACHINE, registry.CURRENT_USER} {
		for _, flags := range []uint32{registry.QUERY_VALUE, registry.QUERY_VALUE | registry.WOW64_32KEY} {
			k, err := registry.OpenKey(root, key, flags)
			if err == nil {
				k.Close()
				return ChannelInstaller
			}
		}
	}
	return ChannelPortable
}
