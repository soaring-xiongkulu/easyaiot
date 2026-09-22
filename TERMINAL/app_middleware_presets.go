package main

import (
	"easyaiot/terminal/backend/log"
	"easyaiot/terminal/backend/store"
)

// ensureMiddlewarePresets seeds the built-in EasyAIoT middleware quick-access
// group into the connection store. Runs once after stores init and again
// after every credential setup/unlock: seeding writes password fields, which
// the connection store can only encrypt with the vault key — while the vault
// is locked the save fails and the seed marker stays unwritten, so the next
// call retries. Idempotent: already-present preset IDs are never touched.
func (a *App) ensureMiddlewarePresets() {
	if a.dataDir == "" || a.connectionStore == nil {
		return
	}
	lang := ""
	if a.settingsStore != nil {
		if s, err := a.settingsStore.Load(); err == nil {
			lang = s.Language
		}
	}
	if err := store.EnsureMiddlewarePresets(a.dataDir, a.connectionStore, lang); err != nil {
		log.Writef("middleware presets: %v", err)
	}
}
