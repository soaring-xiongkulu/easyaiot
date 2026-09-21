package sync

// syncedFiles is the single source of truth for the config files that
// participate in cloud sync. Encrypt (crypto.go), decrypt (crypto.go),
// content comparison (sync_service.go), the git commit whitelist (git.go),
// the empty-dir probe (isConfigDirEmpty) and the password-rotation file list
// (ChangePassword) all iterate this slice so their scopes can never drift
// apart again.
//
// ai-sessions.json and skills.json are intentionally absent — they are
// local-only data and must never be committed to the sync repo (a stray
// ai-sessions.json left in the repo dir from an old build stays untracked).
//
// settings.json is intentionally absent: it is device-local (theme,
// paths, shells, keybindings, UI state) and changes too often to sync
// well. The syncable AI slice (model catalog + maxTurns) lives in
// ai.json instead; see AIConfigStore.
var syncedFiles = []string{
	"connections.json",
	"favorites.json",
	"ai.json",
	"quickCommands.json",
	"tunnels.json",
	"identities.json",
	"proxies.json",
}
