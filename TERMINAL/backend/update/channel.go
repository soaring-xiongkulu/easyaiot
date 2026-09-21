package update

// Channel describes how the running install should be updated.
type Channel string

const (
	// ChannelPortable means in-place self-update: replace the current binary
	// (and bundle payload files) directly.
	ChannelPortable Channel = "portable"
	// ChannelInstaller means a Windows NSIS install: updates run the new
	// installer silently after the app exits.
	ChannelInstaller Channel = "installer"
)

// DetectChannel reports how the running install should be updated. The
// platform-specific detection lives in channel_<os>.go.
func DetectChannel() Channel {
	return detectChannel()
}
