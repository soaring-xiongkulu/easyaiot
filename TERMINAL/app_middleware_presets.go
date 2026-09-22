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
// call retries. Idempotent: already-present preset IDs are never touched
// except by a version-bump roster refresh.
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
	changed, err := store.EnsureMiddlewarePresets(a.dataDir, a.connectionStore, lang)
	if err != nil {
		log.Writef("middleware presets: %v", err)
		return
	}
	// Seeding writes behind the frontend's back (startup / credential unlock).
	// Push the refreshed roster so the UI's in-memory copy — which may predate
	// the seeded passwords — cannot stale-write empty credentials back over
	// the just-healed presets on its next full-list save.
	if changed {
		if data, err := a.connectionStore.Load(); err == nil {
			a.emit("store:connections:changed", data)
		}
	}
}
