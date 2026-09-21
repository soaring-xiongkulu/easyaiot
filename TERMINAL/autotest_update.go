package main

import (
	"os"
	"time"

	"easyaiot/terminal/backend/log"
	"easyaiot/terminal/backend/update"
)

// autotestUpdate drives the full update pipeline (check → download → verify →
// apply → restart) unattended. It is inert unless TERMINAL_UPDATE_AUTOTEST=1;
// combine with TERMINAL_UPDATE_API_BASE pointing at a local release server to
// end-to-end test a locally built old/new version pair:
//
//	run 1 (old binary): check → download → apply → relaunch itself with the
//	                    same env, then quit
//	run 2 (new binary): check finds no newer version → log PASS → exit 0
//
// The verdict is observable in ~/.terminal/terminal.log:
//
//	[autotest] APPLIED vX → vY
//	[autotest] PASS: running latest vY
func (a *App) autotestUpdate() {
	time.Sleep(4 * time.Second) // let the app + event plumbing settle
	if a.window != nil {
		a.window.Hide() // defensive: headless e2e runs must not flash a window
	}

	log.Writef("[autotest] start, current=%s", Version)

	info, err := update.Check(Version, "github")
	if err != nil {
		log.Writef("[autotest] CHECK FAILED: %v", err)
		os.Exit(2)
	}
	if !info.HasUpdate {
		log.Writef("[autotest] PASS: running latest %s", info.Latest)
		os.Exit(0)
	}

	log.Writef("[autotest] update available: %s -> %s (%d assets)", Version, info.Latest, len(info.Assets))

	if _, err := updateManager.Download(info.Assets, func(p update.Progress) {
		log.Writef("[autotest] progress: %s received=%d total=%d", p.Phase, p.Received, p.Total)
	}); err != nil {
		log.Writef("[autotest] DOWNLOAD FAILED: %v", err)
		os.Exit(3)
	}
	log.Writef("[autotest] download verified, applying")

	if err := updateManager.Apply(func(p update.Progress) {
		log.Writef("[autotest] progress: %s", p.Phase)
	}); err != nil {
		log.Writef("[autotest] APPLY FAILED: %v", err)
		os.Exit(4)
	}

	log.Writef("[autotest] APPLIED %s -> %s; relaunching same env", Version, info.Latest)

	// Relaunch through the shared quit-then-spawn path: run 2 inherits the
	// full environment (including TERMINAL_UPDATE_AUTOTEST) and starts only
	// after run 1 has released the single-instance lock. Spawning first
	// would make run 2 exit as a "second instance".
	relaunchPending.Store(true)
	a.app.Quit()
}
