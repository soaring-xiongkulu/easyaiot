package sync

// syncedFiles is the single source of truth for the config files that
// participate in cloud sync. Encrypt (crypto.go), decrypt (crypto.go),
// content comparison (sync_service.go), the git commit whitelist (git.go),
// the empty-dir probe (isConfigDirEmpty) and the password-rotation file list
// (ChangePassword) all iterate this slice so their scopes can never drift
// apart again.
//
// settings.json is intentionally absent: it is device-local (theme,
// paths, shells, keybindings, UI state) and changes too often to sync
// well.
var syncedFiles = []string{
	"connections.json",
	"favorites.json",
	"quickCommands.json",
	"tunnels.json",
	"identities.json",
	"proxies.json",
}
