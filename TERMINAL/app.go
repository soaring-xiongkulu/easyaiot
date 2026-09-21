package main

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/wailsapp/wails/v3/pkg/application"
	"easyaiot/terminal/backend/container"
	"easyaiot/terminal/backend/credentials"
	"easyaiot/terminal/backend/importer"
	"easyaiot/terminal/backend/k8s"
	"easyaiot/terminal/backend/log"
	"easyaiot/terminal/backend/platform"
	"easyaiot/terminal/backend/session"
	"easyaiot/terminal/backend/store"
	"easyaiot/terminal/backend/sync"
	"easyaiot/terminal/backend/update"
	"easyaiot/terminal/backend/utils"
	"golang.org/x/crypto/ssh"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	goruntime "runtime"
	"strconv"
	"strings"
	stdsync "sync"
	"sync/atomic"
	"time"
)

type App struct {
	ctx                  context.Context
	app                  *application.App
	window               *application.WebviewWindow
	sessionManager       *session.SessionManager
	k8sManager           *k8s.Manager
	containerManager     *container.Manager
	connectionStore      *store.ConnectionStore
	aiSessionStore       *store.AISessionStore
	settingsStore        *store.SettingsStore
	aiConfigStore        *store.AIConfigStore
	identityStore        *store.IdentityStore
	proxyStore           *store.ProxyStore
	localStateStore      *store.LocalStateStore
	quickCommandsStore   *store.QuickCommandsStore
	skillsStore          *store.SkillsStore
	commandsStore        *store.CommandsStore
	tunnelStore          *store.TunnelStore
	terminalHistoryStore *store.TerminalHistoryStore
	recentStore          *store.RecentStore
	favoriteStore        *store.FavoriteStore
	syncService          *sync.SyncService
	tunnelService        *session.TunnelService
	mainHwnd             uintptr
	originalWndProc      uintptr
	wndProcCb            uintptr // keep alive to prevent GC
	inSizeMove           bool
	webviewDataPath      string
	// dataDir is the resolved config data directory, passed to store
	// constructors. Resolved at startup; finalized by bootstrap in a later task.
	dataDir         string
	credentialStore *credentials.Store
	storesReady     bool
	chatCancel      atomic.Pointer[context.CancelFunc] // F-308: active stream cancellation, per-call swap so overlap is safe
	moveResizeCh    chan string                        // defer EventsEmit from WndProc
	// F-043: foreground flag — true while the window is visible and the
	// user is interacting; background goroutines (keepalive, output_log
	// flush, k8s watches, auto-sync) should consult IsForeground before
	// burning CPU. Updated via SetAppVisibility (frontend bridge) and a
	// low-frequency minimised poll as a fallback for paths that don't
	// fire visibilitychange (e.g. app hidden via Cmd+H on macOS).
	foreground   atomic.Bool
	foregroundMu stdsync.RWMutex
	// F-212: last seen connections snapshot so emitConnDelta (F-204) can
	// compute upsert/remove deltas without re-shipping the full store on
	// every save.
	lastConnSnapshot   session.ConnectionStoreData
	lastConnSnapshotMu stdsync.RWMutex

	// F-208: single shared http.Client for chatCompletion* /
	// FetchModels calls. Built lazily once on first use so tests that
	// don't hit the LLM path don't pay for the transport; subsequent
	// calls reuse the keep-alive pool and skip the TCP+TLS handshake.
	httpClient     *http.Client
	httpClientOnce stdsync.Once

	// session objects and the log file spans all of them. sessionToPanel
	// tracks the current session→panel binding so emitData can look up
	// the right logger. panelAutoTriggered records which panels have
	// already been considered for the LogOnConnect auto-enable so
	// reconnects don't re-enable a log the user manually stopped.
	panelLogs          map[string]*session.OutputLogger
	sessionToPanel     map[string]string
	panelAutoTriggered map[string]bool
	panelLogMu         stdsync.Mutex
	// customLogDir, when non-empty, overrides defaultSessionLogDir()
	// as the target for new session logs. Set from settings via
	// SetDefaultSessionLogDir; ongoing logs are not migrated.
	customLogDir         string
	sessionLogFilename   string
	sessionLogSettingsMu stdsync.RWMutex

	// errCh accumulates non-fatal init failures during startup() so the
	// frontend can surface them (see StartupError / "app:startup-error"
	// event). Stores may stay nil if their init fails — the existing
	// nil-guard pattern is preserved so today's working configs keep
	// loading; the additive channel just makes the failure visible.
	errCh      chan error
	startupErr error
}

func NewApp(webviewDataPath string) *App {
	a := &App{
		webviewDataPath:    webviewDataPath,
		panelLogs:          make(map[string]*session.OutputLogger),
		sessionToPanel:     make(map[string]string),
		panelAutoTriggered: make(map[string]bool),
		k8sManager:         k8s.NewManager(),
		containerManager:   container.NewManager(),
		errCh:              make(chan error, 16),
	}

	// Transfer progress is published as Wails events, not OSC sequences in the
	// terminal data stream.
	session.TransferEventSink = func(sid string, payload map[string]any) {
		a.emit("sftp:transfer", payload)
	}

	// OSC-7 cwd reports from SSH/WSL terminals (see backend/session/shell_
	// integration.go) are forwarded so the frontend can follow the active
	// directory in the sidebar.
	session.TerminalCwdSink = func(sid string, cwd string) {
		a.emit("terminal:cwd", map[string]any{"sessionId": sid, "cwd": cwd})
	}

	return a
}

// emit is a v3 helper that forwards an event to the frontend. It no-ops when
// the application reference is not yet attached (e.g. in unit tests that build
// an App without a running Wails runtime), matching the previous
// `if a.ctx != nil` defensiveness.
func (a *App) emit(name string, data ...any) {
	if a.app == nil {
		return
	}
	a.app.Event.Emit(name, data...)
}

// win returns the single application window, used to drive window operations
// from the v3 application object.
func (a *App) win() *application.WebviewWindow {
	return a.window
}

func (a *App) ServiceStartup(ctx context.Context, options application.ServiceOptions) error {
	a.ctx = ctx

	a.k8sManager.SetEventEmitter(func(name string, payload any) {
		a.emit(name, payload)
	})
	a.containerManager.SetEventEmitter(func(name string, payload any) {
		a.emit(name, payload)
	})

	// Init logger first so subsequent log.Writef calls actually write
	if err := log.Init(); err != nil {
		fmt.Printf("WARN: log.Init failed: %v\n", err)
	}

	// On macOS, disable the system press-and-hold accent picker for this app so
	// that holding a key repeats input in the terminal (see app_darwin.go).
	a.configureMacKeyRepeat()

	a.sessionManager = session.NewSessionManager()
	a.tunnelService = session.NewTunnelService()

	// Defer EventsEmit from WndProc to avoid blocking the modal resize/move loop.
	a.moveResizeCh = make(chan string, 10)
	go func() {
		for evt := range a.moveResizeCh {
			a.emit(evt)
			if evt == "rdp:move-resize-end" {
				// Notify the frontend that the native window stopped resizing
				// (drag-to-restore / maximize / programmatic resize). The terminal
				// re-fits on this signal because the browser does not always fire a
				// final window.resize at the settled size after a native drag, which
				// otherwise leaves the canvas at a stale small row count (issue #656).
				// Platform-neutral name; on non-Windows it simply never fires.
				a.emit("window:resize-end")
				a.saveWindowStateFromRuntime()
			}
		}
	}()

	// Discover main window HWND for RDP child window embedding
	a.mainHwnd = a.findMainWindow()
	a.subclassMainWindow()

	// Resolve data directory. First run (no bootstrap, no existing config)
	// defers all store init until the frontend calls SetDataDir.
	dd, err := store.ResolveDataDir()
	if err != nil {
		log.Writef("Failed to resolve data dir: %v", err)
		a.sendStartupErr(fmt.Errorf("data dir: %w", err))
		a.drainStartupErr()
		return nil
	}
	if dd.FirstRun {
		a.dataDir = ""
		a.emit("app:firstRun", nil)
		a.drainStartupErr()
		return nil
	}
	a.dataDir = dd.Path

	a.initStores(dd.Path, dd.Upgrade)
	return nil
}

// initStores initializes every config store under dataDir and brings up the
// credential store + sync service. Extracted from startup so first-run defers
// it until SetDataDir picks a directory; on the normal path it runs once at
// startup. Runs exactly once either way.
func (a *App) initStores(dataDir string, upgrade bool) {
	// Point clink:// local shells at the app data dir (they drop a tuned
	// clink profile next to the stores; see backend/session/local_clink.go).
	session.SetClinkProfileDir(filepath.Join(dataDir, "clink"))

	cs, err := store.NewConnectionStore(dataDir)
	if err != nil {
		log.Writef("Failed to init connection store: %v", err)
		a.sendStartupErr(fmt.Errorf("connection store: %w", err))
	} else {
		a.connectionStore = cs
	}

	ass, err := store.NewAISessionStore(dataDir)
	if err != nil {
		log.Writef("Failed to init AI session store: %v", err)
		a.sendStartupErr(fmt.Errorf("ai session store: %w", err))
	} else {
		a.aiSessionStore = ass
	}

	ss, err := store.NewSettingsStore(dataDir)
	if err != nil {
		log.Writef("Failed to init settings store: %v", err)
		a.sendStartupErr(fmt.Errorf("settings store: %w", err))
	} else {
		a.settingsStore = ss
		// Prime the session-log directory override from persisted settings
		// so a log Enable that lands before the settings UI opens still
		// respects the user's choice from a prior run.
		if settings, err := ss.Load(); err == nil {
			a.SetDefaultSessionLogDir(settings.Terminal.SessionLogDir)
			a.setSessionLogFilename(settings.Terminal.SessionLogFilename)
		}
	}

	acs, err := store.NewAIConfigStore(dataDir)
	if err != nil {
		log.Writef("Failed to init AI config store: %v", err)
		a.sendStartupErr(fmt.Errorf("ai config store: %w", err))
	} else {
		a.aiConfigStore = acs
	}

	is, err := store.NewIdentityStore(dataDir)
	if err != nil {
		log.Writef("Failed to init identity store: %v", err)
		a.sendStartupErr(fmt.Errorf("identity store: %w", err))
	} else {
		a.identityStore = is
	}

	ps, err := store.NewProxyStore(dataDir)
	if err != nil {
		log.Writef("Failed to init proxy store: %v", err)
		a.sendStartupErr(fmt.Errorf("proxy store: %w", err))
	} else {
		a.proxyStore = ps
	}

	a.terminalHistoryStore = store.NewTerminalHistoryStore(dataDir)
	a.quickCommandsStore = store.NewQuickCommandsStore(dataDir)
	a.skillsStore = store.NewSkillsStore(dataDir)
	a.commandsStore = store.NewCommandsStore(dataDir)
	a.tunnelStore = store.NewTunnelStore(dataDir)
	a.localStateStore = store.NewLocalStateStore(dataDir)
	a.recentStore = store.NewRecentStore(dataDir)
	if _, err := a.recentStore.Load(); err != nil {
		log.Writef("recentStore.Load: %v", err)
	}
	a.favoriteStore = store.NewFavoriteStore(dataDir)
	if _, err := a.favoriteStore.Load(); err != nil {
		log.Writef("favoriteStore.Load: %v", err)
	}

	// Push tunnel runtime state to the frontend, and bring up auto-start tunnels.
	a.tunnelService.SetStateCallback(func(st session.TunnelState) {
		a.emit("tunnel:state", st)
	})
	go a.autoStartTunnels()
	go a.watchForeground(a.ctx)

	// Credential store + auto-unlock / upgrade (wires PasswordStore into
	// connection + settings stores).
	a.initCredentials(dataDir, upgrade)

	// Sync service: sync metadata (sync-config.json + local repo clone) lives
	// in the system user-config dir; the config files it encrypts/decrypts are
	// read from dataDir.
	syncSvc, err := sync.NewSyncService(dataDir)
	if err != nil {
		log.Writef("Failed to create sync service: %v", err)
		a.sendStartupErr(fmt.Errorf("sync service: %w", err))
	} else {
		a.syncService = syncSvc
		// Normalize enc:v1: fields at the sync boundary using the credential
		// store (set by initCredentials above).
		syncSvc.SetPasswordStore(a.credentialStore)
		// Auto-sync on startup if enabled
		if syncSvc.IsAutoSyncEnabled() {
			go func() {
				result, err := syncSvc.Sync()
				if err != nil {
					log.Writef("Auto-sync on startup failed: %v", err)
				} else if result.Direction == sync.SyncConflict {
					a.emit("sync:conflict", map[string]interface{}{
						"localTime":  result.Conflict.LocalTime.Format(time.RFC3339),
						"remoteTime": result.Conflict.RemoteTime.Format(time.RFC3339),
					})
				}
				// Reload in-memory stores after a startup pull so the UI shows
				// the freshly synced config without requiring a restart.
				if err == nil && result.Direction == sync.SyncPull {
					a.reloadStoresAfterSync()
				}
				a.emit("sync:completed")
			}()
		}
	}

	a.storesReady = true

	// Raise the window to the foreground once, shortly after launch. On Windows a
	// relaunched instance can otherwise land behind other windows; the short delay
	// keeps this one-shot raise inside the window where the old (foreground)
	// process is still alive, which is what grants the set-foreground permission
	// (see RelaunchApp). No-op on other platforms.
	go func() {
		time.Sleep(250 * time.Millisecond)
		a.bringMainWindowToFront()
	}()

	// Drain any non-fatal init failures and surface them to the frontend so
	// the user sees a banner instead of getting an NPE on the first store
	// call. Additive only — stores that failed to init are still nil and
	// guarded as before; the app still launches.
	a.drainStartupErr()
	if a.startupErr != nil {
		a.emit("app:startup-error", a.startupErr.Error())
	}
}

// initCredentials wires the credential store as the PasswordStore for the
// connection + settings stores, silently auto-upgrading existing users
// (bootstrap + keychain mode + legacy migration) or auto-unlocking on the
// normal path.
func (a *App) initCredentials(dataDir string, upgrade bool) {
	cred := credentials.New(dataDir, sync.NewKeychain())

	if upgrade {
		// Only this once (the upgrade migration) is worth logging; ordinary
		// starts share the same AutoUnlock path and would be noise.
		m, _ := credentials.ReadMeta(dataDir)
		if m != nil {
			log.Writef("[upgrade] existing credentials.meta mode=%q", m.Mode)
		} else {
			log.Writef("[upgrade] no credentials.meta → auto-setup keychain")
		}
		// Existing user: silently auto-upgrade to default + keychain mode.
		if err := store.WriteBootstrap("default", ""); err != nil {
			log.Writef("bootstrap write failed (default pointer): %v", err)
		}
		// Idempotency (review Critical #1): Setup generates a NEW random key and
		// overwrites the keychain entry. If a prior upgrade already ran but
		// bootstrap.json was lost (deleted / <exe>/data unwritable / portable zip
		// extracted to a new folder), credentials.meta still exists and the fields
		// are already encrypted under the persisted key — running Setup again would
		// orphan them. Recover the existing key instead.
		if meta, _ := credentials.ReadMeta(dataDir); meta == nil {
			if err := cred.Setup(credentials.ModeKeychain, ""); err != nil {
				log.Writef("credential auto-upgrade setup failed: %v", err)
			} else if _, err := store.MigrateLegacyKeychainToInPlace(dataDir, sync.NewKeychain(), cred); err != nil {
				log.Writef("legacy migration failed: %v", err)
			}
		} else if err := cred.AutoUnlock(); err != nil {
			log.Writef("credential auto-unlock failed: %v", err)
		}
		// Re-run the legacy migration on every upgrade. It is idempotent (only
		// backfills connections whose JSON password field is still empty) and
		// closes the window where a user's first-launch migration failed and
		// was then skipped forever because credentials.meta already existed.
		// Only meaningful when the credential store holds a usable key.
		if cred.Unlocked() {
			if _, err := store.MigrateLegacyKeychainToInPlace(dataDir, sync.NewKeychain(), cred); err != nil {
				log.Writef("legacy migration failed: %v", err)
			}
		}
	} else if err := cred.AutoUnlock(); err != nil {
		log.Writef("credential auto-unlock failed: %v", err)
	}

	a.credentialStore = cred
	// Only log when startup lands in a state that prompts a credential dialog
	// (setup/keychain-lost), so a normal unlocked start stays silent.
	if st := cred.Status(); st.NeedsSetup || st.KeychainLost {
		log.Writef("[cred-dialog] mode=%q unlocked=%v keychainLost=%v needsSetup=%v",
			st.Mode, st.Unlocked, st.KeychainLost, st.NeedsSetup)
	}
	if a.connectionStore != nil {
		a.connectionStore.SetPasswordStore(cred)
		// Fall back to the pre-enc:v1 keychain (conn/<id>) so passwords from
		// the old scheme remain usable if the one-shot migration didn't run.
		a.connectionStore.SetLegacyKeychain(sync.NewKeychain())
	}
	if a.settingsStore != nil {
		a.settingsStore.SetPasswordStore(cred)
	}
	if a.aiConfigStore != nil {
		a.aiConfigStore.SetPasswordStore(cred)
		// One-shot settings->ai.json migration. Runs after the password store
		// is wired so model apiKeys land encrypted; the settings.json copy is
		// left intact so a rollback to a pre-split build still finds them.
		if a.settingsStore != nil {
			if settings, err := a.settingsStore.Load(); err == nil {
				if err := a.aiConfigStore.MigrateFromSettingsIfNeeded(settings); err != nil {
					log.Writef("ai.json migration failed: %v", err)
				}
			}
		}
	}
	if a.identityStore != nil {
		a.identityStore.SetPasswordStore(cred)
	}
	if a.proxyStore != nil {
		a.proxyStore.SetPasswordStore(cred)
	}
}

// sendStartupErr records a non-fatal init failure so the frontend can see
// it after startup completes. Channel is buffered (16) and only written
// from the startup goroutine, so the send is non-blocking.
func (a *App) sendStartupErr(err error) {
	if err == nil {
		return
	}
	select {
	case a.errCh <- err:
	default:
		// Channel full — best-effort drop. The log line is the
		// last-resort record in this case.
		log.Writef("startup error channel full, dropping: %v", err)
	}
}

// drainStartupErr joins every error sent during startup into a single
// startupErr the frontend can query via StartupError().
func (a *App) drainStartupErr() {
	var errs []error
	for {
		select {
		case err := <-a.errCh:
			if err != nil {
				errs = append(errs, err)
			}
		default:
			a.startupErr = errors.Join(errs...)
			return
		}
	}
}

// StartupError returns a human-readable, newline-joined list of any
// non-fatal errors that occurred during startup, or "" if startup
// completed cleanly. The frontend can call this on demand (e.g. after
// the "app:startup-error" event) to display a banner.
func (a *App) StartupError() string {
	if a.startupErr == nil {
		return ""
	}
	return a.startupErr.Error()
}

// saveWindowStateFromRuntime saves the current window geometry using runtime
// API calls. Called from the WndProc event loop on Windows (WM_EXITSIZEMOVE).
func (a *App) saveWindowStateFromRuntime() {
	if a.localStateStore == nil {
		return
	}
	// Do not save geometry when minimised — the position is off-screen
	// (-32000, -32000 on Windows) and the size is the tiny taskbar thumbnail,
	// which would restore incorrectly.
	if a.win().IsMinimised() {
		return
	}
	ls, err := a.localStateStore.Load()
	if err != nil {
		return
	}
	ls.WindowX, ls.WindowY = a.window.Position()
	ls.WindowWidth, ls.WindowHeight = a.window.Size()
	ls.WindowMaximised = a.window.IsMaximised()
	_ = a.localStateStore.Save(ls)
}

func (a *App) SaveWindowState(x, y, width, height int, maximised bool) {
	if a.localStateStore == nil {
		return
	}
	ls, err := a.localStateStore.Load()
	if err != nil {
		return
	}
	ls.WindowX = x
	ls.WindowY = y
	ls.WindowWidth = width
	ls.WindowHeight = height
	ls.WindowMaximised = maximised
	a.localStateStore.Save(ls)
}

// resetWindowGeometry recovers a lost window (tray menu item): shows it,
// restores it from maximised, centres it on the PRIMARY screen at the app's
// standard 1200x800, and persists the new geometry so the next start doesn't
// restore the lost position. The size is clamped to the primary screen's
// work area so the taskbar isn't covered.
func (a *App) resetWindowGeometry() {
	win := a.win()
	if win == nil || a.app == nil {
		return
	}
	win.UnMaximise()

	const stdW, stdH = 1200, 800
	screen := a.app.Screen.GetPrimary()
	if screen == nil {
		// Screen API unavailable — at least centre it on the default screen.
		win.SetSize(stdW, stdH)
		win.Center()
	} else {
		wa := screen.WorkArea
		w, h := stdW, stdH
		if w > wa.Width {
			w = wa.Width
		}
		if h > wa.Height {
			h = wa.Height
		}
		win.SetSize(w, h)
		win.SetPosition(wa.X+(wa.Width-w)/2, wa.Y+(wa.Height-h)/2)
	}

	// Persist so a restart doesn't resurrect the lost position. Deferred so
	// the window manager settles the move/resize first.
	time.AfterFunc(300*time.Millisecond, a.saveWindowStateFromRuntime)

	// The whole point is recovering a lost window — raise it to the
	// foreground last so the repositioned result is what the user sees.
	showMainWindow(win)
}

// IsForeground reports whether the app window is currently in the
// foreground. Background goroutines consult this before running work
// that should pause when the user can't see the terminal (F-043).
func (a *App) IsForeground() bool {
	return a.foreground.Load()
}

// SetAppVisibility is the lifecycle hook the frontend fires from
// document.visibilitychange. It updates the foreground flag, emits a
// `app:visibility` event so other Go-side listeners (e.g. auto-sync,
// AI SSE keepalive) can pause/resume, and is safe to call from any
// goroutine.
//
// Pass visible=false when the page goes hidden (tab switch, OS minimise,
// Cmd+H, etc.). The polling goroutine started in startup() is a
// fallback for cases where the JS event doesn't fire (e.g. macOS Cmd+H
// before any document has loaded).
func (a *App) SetAppVisibility(visible bool) {
	prev := a.foreground.Load()
	if prev == visible {
		return
	}
	a.foreground.Store(visible)
	a.foregroundMu.Lock()
	a.foregroundMu.Unlock()
	if a.ctx != nil {
		a.emit("app:visibility", visible)
	}
}

// connDelta is the wire shape for store:connections:delta — only the
// changed connection (or all connections on first emit) crosses the
// bridge instead of the full store blob. See F-204.
type connDelta struct {
	Kind string                       `json:"kind"`         // "upsert" | "remove" | "replace"
	ID   string                       `json:"id,omitempty"` // for upsert/remove
	Conn *session.ConnectionConfig    `json:"connection,omitempty"`
	All  *session.ConnectionStoreData `json:"all,omitempty"` // for replace (first emit)
}

// F-205: typed event shapes + pooled buffer so session:data emits
// stop allocating a fresh map[string]interface{} per chunk.
type sessionDataEvent struct {
	ID   string `json:"id"`
	Data string `json:"data"`
}

type sessionBinaryEvent struct {
	ID   string `json:"id"`
	Data string `json:"data"`
}

var sessionDataPool = stdsync.Pool{
	New: func() any {
		b := &bytes.Buffer{}
		b.Grow(8 * 1024) // typical SSH chunk size, avoids re-grow on small inputs
		return b
	},
}

// computeConnDelta returns the set of upsert/remove deltas between
// the last snapshot and newData. If no snapshot exists yet (first save
// after startup), returns a single "replace" delta carrying the full
// new data so the frontend can hydrate without waiting for a sync.
func (a *App) computeConnDelta(newData session.ConnectionStoreData) []connDelta {
	a.lastConnSnapshotMu.RLock()
	prev := a.lastConnSnapshot
	a.lastConnSnapshotMu.RUnlock()

	if prev.Connections == nil && prev.Groups == nil {
		// F-204: no prior snapshot — ship a single replace so the
		// frontend can hydrate without waiting for sync.
		all := newData
		return []connDelta{{Kind: "replace", All: &all}}
	}

	prevIDs := make(map[string]struct{}, len(prev.Connections))
	for _, c := range prev.Connections {
		prevIDs[c.ID] = struct{}{}
	}
	newIDs := make(map[string]struct{}, len(newData.Connections))
	for _, c := range newData.Connections {
		newIDs[c.ID] = struct{}{}
	}

	var deltas []connDelta
	for _, c := range newData.Connections {
		if _, ok := prevIDs[c.ID]; !ok {
			cc := c
			deltas = append(deltas, connDelta{Kind: "upsert", ID: c.ID, Conn: &cc})
		}
	}
	for id := range prevIDs {
		if _, ok := newIDs[id]; !ok {
			deltas = append(deltas, connDelta{Kind: "remove", ID: id})
		}
	}
	return deltas
}

// saveConnSnapshot updates the snapshot used for future delta
// computation. Called after every successful Save.
func (a *App) saveConnSnapshot(data session.ConnectionStoreData) {
	a.lastConnSnapshotMu.Lock()
	a.lastConnSnapshot = data
	a.lastConnSnapshotMu.Unlock()
}

// which don't fire the JS visibilitychange event (Cmd+H on macOS before
// the WebView is loaded, OS-level Alt+Tab) still update the foreground
// flag. Runs every 2s — coarse on purpose, this is a lifecycle hint not
// a hot path. Exits when ctx is done.
func (a *App) watchForeground(ctx context.Context) {
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			if a.ctx == nil {
				continue
			}
			visible := !a.win().IsMinimised()
			if visible != a.foreground.Load() {
				a.SetAppVisibility(visible)
			}
		}
	}
}

func (a *App) shutdown() {
	a.unsubclassMainWindow()
	if a.tunnelService != nil {
		a.tunnelService.Shutdown()
	}
	if a.sessionManager != nil {
		a.sessionManager.CloseAll()
	}
	cleanupExtEditsOnExit()
	session.CleanupSSHX11Server()
	if a.terminalHistoryStore != nil {
		_ = a.terminalHistoryStore.Close()
	}
	os.RemoveAll(a.webviewDataPath)
}

// FavoriteStore methods

func (a *App) GetFavoriteConnections() []string {
	if a.favoriteStore == nil {
		return []string{}
	}
	return a.favoriteStore.GetAll()
}

func (a *App) SaveFavoriteConnections(ids []string) error {
	if a.favoriteStore == nil {
		return fmt.Errorf("favorite store not initialized")
	}
	if _, err := a.favoriteStore.Load(); err != nil {
		log.Writef("favoriteStore.Load: %v", err)
	}
	err := a.favoriteStore.Save(ids)
	if err == nil {
		a.emit("store:favorites:changed", a.favoriteStore.GetAll())
		a.triggerAutoSync()
	}
	return err
}

// ConnectionStore methods

func (a *App) SaveConnections(data session.ConnectionStoreData) error {
	if a.connectionStore == nil {
		return fmt.Errorf("connection store not initialized")
	}
	err := a.connectionStore.Save(data)
	if err == nil {
		a.emit("store:connections:changed", data)
		a.triggerAutoSync()
	}
	return err
}

func (a *App) LoadConnections() (session.ConnectionStoreData, error) {
	if a.connectionStore == nil {
		return session.ConnectionStoreData{}, fmt.Errorf("connection store not initialized")
	}
	return a.connectionStore.Load()
}

func (a *App) LoadIdentities() (session.IdentityStoreData, error) {
	if a.identityStore == nil {
		return session.IdentityStoreData{Identities: []session.Identity{}}, nil
	}
	return a.identityStore.Load()
}

func (a *App) SaveIdentities(data session.IdentityStoreData) error {
	if a.identityStore == nil {
		return fmt.Errorf("identity store not initialized")
	}
	return a.identityStore.Save(data)
}

func (a *App) LoadProxies() (session.ProxyStoreData, error) {
	if a.proxyStore == nil {
		return session.ProxyStoreData{Proxies: []session.Proxy{}}, nil
	}
	return a.proxyStore.Load()
}

func (a *App) SaveProxies(data session.ProxyStoreData) error {
	if a.proxyStore == nil {
		return fmt.Errorf("proxy store not initialized")
	}
	return a.proxyStore.Save(data)
}

// ExportConnections writes the full store to destPath as a .utm file. When
// password is non-empty, password fields are encrypted; otherwise cleared.
func (a *App) ExportConnections(destPath, password string) error {
	if a.connectionStore == nil {
		return fmt.Errorf("connection store not initialized")
	}
	data, err := a.connectionStore.Load()
	if err != nil {
		return err
	}
	out, err := importer.ExportUniterm(data, password)
	if err != nil {
		return err
	}
	return os.WriteFile(destPath, out, 0600)
}

// ParseImportFile parses a third-party or own-format file into an ImportResult
// with regenerated ids. It does not write to the store.
func (a *App) ParseImportFile(format, srcPath, password string) (*importer.ImportResult, error) {
	return importer.Parse(format, srcPath, importer.ParseOptions{Password: password})
}

// ApplyImport merges parsed connections into the existing store and saves,
// reusing existing groups by path. The saved result is broadcast via the
// existing store:connections:changed event.
func (a *App) ApplyImport(data session.ConnectionStoreData) error {
	if a.connectionStore == nil {
		return fmt.Errorf("connection store not initialized")
	}
	existing, err := a.connectionStore.Load()
	if err != nil {
		return err
	}
	merged := importer.MergeImported(existing, data)
	return a.SaveConnections(merged)
}

// TunnelStore methods

func (a *App) SaveTunnels(data session.TunnelStoreData) error {
	if a.tunnelStore == nil {
		return fmt.Errorf("tunnel store not initialized")
	}
	err := a.tunnelStore.Save(data)
	if err == nil {
		a.emit("store:tunnels:changed", data)
	}
	return err
}

func (a *App) LoadTunnels() (session.TunnelStoreData, error) {
	if a.tunnelStore == nil {
		return session.TunnelStoreData{}, fmt.Errorf("tunnel store not initialized")
	}
	return a.tunnelStore.Load()
}

// connResolver returns a resolver over the current saved connections so the
// tunnel layer can look up the exit connection and recurse its jump hosts.
func (a *App) connResolver() (session.ConnResolver, error) {
	conns, err := a.connectionStore.Load()
	if err != nil {
		return nil, err
	}
	index := make(map[string]session.ConnectionConfig, len(conns.Connections))
	for _, c := range conns.Connections {
		index[c.ID] = c
	}
	idResolve, err := a.identityResolver()
	if err != nil {
		return nil, err
	}
	return func(id string) (session.ConnectionConfig, bool) {
		c, ok := index[id]
		if !ok {
			return session.ConnectionConfig{}, false
		}
		if c.AuthType == "identity" {
			m, err := session.MaterializeIdentity(c, idResolve)
			if err != nil {
				return session.ConnectionConfig{}, false
			}
			return m, true
		}
		return c, true
	}, nil
}

// identityResolver 返回基于当前身份库的解密 resolver（镜像 connResolver）。
func (a *App) identityResolver() (session.IdentityResolver, error) {
	if a.identityStore == nil {
		return func(string) (session.Identity, bool) { return session.Identity{}, false }, nil
	}
	data, err := a.identityStore.Load()
	if err != nil {
		return nil, err
	}
	index := make(map[string]session.Identity, len(data.Identities))
	for _, id := range data.Identities {
		index[id.ID] = id
	}
	return func(id string) (session.Identity, bool) {
		ident, ok := index[id]
		return ident, ok
	}, nil
}

// materializeIdentity resolves an identity-reference config into a concrete
// password/key config. No-op for non-identity configs.
func (a *App) materializeIdentity(config session.ConnectionConfig) (session.ConnectionConfig, error) {
	if config.AuthType != "identity" {
		return config, nil
	}
	resolve, err := a.identityResolver()
	if err != nil {
		return config, err
	}
	return session.MaterializeIdentity(config, resolve)
}

// proxyResolver returns a resolver over the saved proxies (mirrors identityResolver).
func (a *App) proxyResolver() (session.ProxyResolver, error) {
	if a.proxyStore == nil {
		return func(string) (session.SocksProxy, bool) { return session.SocksProxy{}, false }, nil
	}
	data, err := a.proxyStore.Load()
	if err != nil {
		return nil, err
	}
	index := make(map[string]session.Proxy, len(data.Proxies))
	for _, p := range data.Proxies {
		index[p.ID] = p
	}
	return func(id string) (session.SocksProxy, bool) {
		p, ok := index[id]
		if !ok || !p.IsActive() {
			return session.SocksProxy{}, false
		}
		return session.SocksProxy{Kind: p.Kind, Host: p.Host, Port: p.Port, User: p.User, Pass: p.Pass}, true
	}, nil
}

// systemProxyFor resolves the OS system proxy for reaching host:port: the
// registry/system config, PAC scripts, and the HTTP(S)_PROXY env fallback,
// via the shared cached resolver (llmProxy). direct=true means the system
// resolved this target to a direct connection (no proxy or PAC says DIRECT).
func systemProxyFor(host string, port int) (*session.SocksProxy, bool, error) {
	req := &http.Request{URL: &url.URL{Scheme: "https", Host: net.JoinHostPort(host, strconv.Itoa(port))}}
	u, err := llmProxy(req)
	if err != nil {
		return nil, false, err
	}
	if u == nil || u.Host == "" {
		return nil, true, nil
	}
	switch u.Scheme {
	case "socks", "socks5":
		return &session.SocksProxy{Kind: "socks5", Host: u.Hostname(), Port: proxyPort(u, 1080)}, false, nil
	default: // "http", "https"
		return &session.SocksProxy{Kind: "http", Host: u.Hostname(), Port: proxyPort(u, 80)}, false, nil
	}
}

// proxyPort extracts the port from a resolved proxy URL, falling back to the
// scheme's conventional default when the system config omitted it.
func proxyPort(u *url.URL, fallback int) int {
	if n, err := strconv.Atoi(u.Port()); err == nil && n > 0 {
		return n
	}
	return fallback
}

// materializeProxy resolves config.ProxyId into config.Proxy. No-op when no
// proxy is set. Mirrors materializeIdentity. The "system" sentinel resolves
// the OS system proxy against the connection target (see systemProxyFor). A
// proxy disabled via its enable toggle (issue #749) is skipped silently: the
// connection dials directly.
func (a *App) materializeProxy(config session.ConnectionConfig) (session.ConnectionConfig, error) {
	if config.ProxyId == "" {
		return config, nil
	}
	if config.ProxyId == session.ProxyIDSystem {
		p, direct, err := systemProxyFor(config.Host, config.Port)
		if err != nil {
			return config, fmt.Errorf("resolve system proxy: %w", err)
		}
		if direct {
			return config, nil
		}
		config.Proxy = p
		return config, nil
	}
	resolve, err := a.proxyResolver()
	if err != nil {
		return config, err
	}
	p, ok := resolve(config.ProxyId)
	if !ok {
		if name, disabled := a.proxyDisabledName(config.ProxyId); disabled {
			log.Writef("[materializeProxy] proxy %q disabled, connecting direct", name)
			return config, nil
		}
		return config, fmt.Errorf("referenced proxy not found: %s", config.ProxyId)
	}
	config.Proxy = &p
	return config, nil
}

// proxyDisabledName reports whether the referenced proxy exists but is toggled
// off, returning its name for logging.
func (a *App) proxyDisabledName(id string) (string, bool) {
	if a.proxyStore == nil {
		return "", false
	}
	data, err := a.proxyStore.Load()
	if err != nil {
		return "", false
	}
	for _, p := range data.Proxies {
		if p.ID == id {
			return p.Name, !p.IsActive()
		}
	}
	return "", false
}

// withExitCredOverride wraps a ConnResolver so the tunnel's exit connection
// gets its empty user/password filled from inline credentials — the same
// semantics as the TunnelSSHUser/TunnelSSHPassword handling in app_terminal.go:
// inline values only fill EMPTY fields (never overwrite saved ones) and only on
// the exit hop. Empty inline credentials return the resolver unchanged.
func withExitCredOverride(resolve session.ConnResolver, exitID, user, password string) session.ConnResolver {
	if user == "" && password == "" {
		return resolve
	}
	return func(id string) (session.ConnectionConfig, bool) {
		cfg, ok := resolve(id)
		if !ok || id != exitID {
			return cfg, ok
		}
		if cfg.User == "" && user != "" {
			cfg.User = user
		}
		if cfg.Password == "" && password != "" {
			cfg.Password = password
		}
		return cfg, true
	}
}

// StartTunnel brings the tunnel with the given ID up and returns its state.
// user/password carry inline credentials resolved by the frontend's credential
// dialog for exit connections with nothing saved; they only fill empty fields.
func (a *App) StartTunnel(id, user, password string) (session.TunnelState, error) {
	if a.tunnelService == nil || a.tunnelStore == nil || a.connectionStore == nil {
		return session.TunnelState{}, fmt.Errorf("tunnel service not initialized")
	}
	data, err := a.tunnelStore.Load()
	if err != nil {
		return session.TunnelState{}, err
	}
	var t *session.Tunnel
	for i := range data.Tunnels {
		if data.Tunnels[i].ID == id {
			t = &data.Tunnels[i]
			break
		}
	}
	if t == nil {
		return session.TunnelState{}, fmt.Errorf("tunnel %s not found", id)
	}
	resolve, err := a.connResolver()
	if err != nil {
		return session.TunnelState{}, err
	}
	resolve = withExitCredOverride(resolve, t.SSHConnID, user, password)
	st := a.tunnelService.StartTunnel(*t, resolve)
	// A failed start is reported through the state (Status=Error + Error text);
	// returning a Go error here too would turn the Wails call into a rejected
	// promise and the frontend would lose the state it needs for the toast.
	return st, nil
}

// StopTunnel tears down the tunnel with the given ID.
func (a *App) StopTunnel(id string) error {
	if a.tunnelService != nil {
		a.tunnelService.StopTunnel(id)
	}
	return nil
}

// TestTunnel validates an unsaved tunnel configuration: it brings the tunnel
// up under a throwaway ID through the same path as StartTunnel (SSH chain
// dial/auth, then listener bind — for remote mode that also proves the port is
// free on the server) and tears it down immediately. Status=Running means
// everything bound; Error carries the reason. user/password carry inline
// credentials resolved by the frontend's credential dialog (same override
// semantics as StartTunnel).

func (a *App) TestTunnel(t session.Tunnel, user, password string) (session.TunnelState, error) {
	if a.tunnelService == nil || a.connectionStore == nil {
		return session.TunnelState{}, fmt.Errorf("tunnel service not initialized")
	}
	resolve, err := a.connResolver()
	if err != nil {
		return session.TunnelState{}, err
	}
	resolve = withExitCredOverride(resolve, t.SSHConnID, user, password)
	st := a.tunnelService.TestTunnel(t, resolve)
	return st, nil
}

// ListTunnelStates returns the runtime state of every known tunnel.
func (a *App) ListTunnelStates() []session.TunnelState {
	if a.tunnelService == nil {
		return nil
	}
	return a.tunnelService.TunnelStates()
}

// autoStartTunnels starts every tunnel flagged AutoStart. Errors surface via the
// per-tunnel state event, not as a startup failure.
func (a *App) autoStartTunnels() {
	if a.tunnelService == nil || a.tunnelStore == nil || a.connectionStore == nil {
		return
	}
	data, err := a.tunnelStore.Load()
	if err != nil {
		return
	}
	resolve, err := a.connResolver()
	if err != nil {
		return
	}
	for _, t := range data.Tunnels {
		if t.AutoStart {
			if st := a.tunnelService.StartTunnel(t, resolve); st.Status == session.TunnelError {
				// The failure also reaches the frontend via the tunnel:state
				// event; the log keeps a trace for diagnostics.
				log.Writef("auto-start tunnel %s (%s): %s", t.Name, t.ID, st.Error)
			}
		}
	}
}

// LocalStateStore methods — sidecar visibility that stays local, never synced.

func (a *App) SaveLocalState(state store.LocalState) error {
	if a.localStateStore == nil {
		return fmt.Errorf("local state store not initialized")
	}
	return a.localStateStore.Save(state)
}

func (a *App) LoadLocalState() (store.LocalState, error) {
	if a.localStateStore == nil {
		return store.LocalState{SidebarVisible: true, AISidebarVisible: true}, nil
	}
	return a.localStateStore.Load()
}

// bgDir returns the directory holding the (local-only, never-synced)
// background image. It is rooted under the active data directory so the
// image moves with the config when the data dir is migrated. It is
// created on demand.
func (a *App) bgDir() (string, error) {
	base := a.dataDir
	if base == "" {
		var err error
		base, err = store.DefaultDataDir()
		if err != nil {
			return "", err
		}
	}
	dir := filepath.Join(base, "backgrounds")
	if err := os.MkdirAll(dir, 0700); err != nil {
		return "", err
	}
	return dir, nil
}

var allowedBgExt = map[string]string{
	".png":  "image/png",
	".jpg":  "image/jpeg",
	".jpeg": "image/jpeg",
	".webp": "image/webp",
}

// SetBackgroundImage copies the chosen image into the app's backgrounds
// directory as a single fixed file (overwriting any previous one) and
// returns the stored file name. It does NOT touch local_state.json.
func (a *App) SetBackgroundImage(srcPath string) (string, error) {
	ext := strings.ToLower(filepath.Ext(srcPath))
	if _, ok := allowedBgExt[ext]; !ok {
		return "", fmt.Errorf("unsupported image type: %s", ext)
	}
	dir, err := a.bgDir()
	if err != nil {
		return "", err
	}
	for e := range allowedBgExt {
		_ = os.Remove(filepath.Join(dir, "bg"+e))
	}
	src, err := os.Open(srcPath)
	if err != nil {
		return "", err
	}
	defer src.Close()
	name := "bg" + ext
	dst, err := os.Create(filepath.Join(dir, name))
	if err != nil {
		return "", err
	}
	defer dst.Close()
	if _, err := io.Copy(dst, src); err != nil {
		return "", err
	}
	return name, nil
}

// GetBackgroundImage reads the stored background file and returns it as a
// data URL. Returns an empty string (no error) when name is empty or the
// file is missing, so the frontend degrades gracefully.
func (a *App) GetBackgroundImage(name string) (string, error) {
	if name == "" {
		return "", nil
	}
	ext := strings.ToLower(filepath.Ext(name))
	mime, ok := allowedBgExt[ext]
	if !ok {
		return "", nil
	}
	dir, err := a.bgDir()
	if err != nil {
		return "", err
	}
	data, err := os.ReadFile(filepath.Join(dir, name))
	if err != nil {
		if os.IsNotExist(err) {
			return "", nil
		}
		return "", err
	}
	return "data:" + mime + ";base64," + base64.StdEncoding.EncodeToString(data), nil
}

// ClearBackgroundImage removes any stored background image file.
func (a *App) ClearBackgroundImage() error {
	dir, err := a.bgDir()
	if err != nil {
		return err
	}
	for e := range allowedBgExt {
		_ = os.Remove(filepath.Join(dir, "bg"+e))
	}
	return nil
}

// reloadStoresAfterSync reloads connections and settings from disk and emits
// events so the frontend refreshes after a sync pull.
func (a *App) reloadStoresAfterSync() {
	if a.connectionStore != nil {
		if data, err := a.connectionStore.Load(); err == nil {
			a.emit("store:connections:changed", data)
		}
	}
	if a.settingsStore != nil {
		if settings, err := a.settingsStore.Load(); err == nil {
			a.emit("store:settings:changed", settings)
		}
	}
	if a.aiConfigStore != nil {
		if cfg, err := a.aiConfigStore.Load(); err == nil {
			a.emit("store:ai:changed", cfg)
		}
	}
	if a.quickCommandsStore != nil {
		if data, err := a.quickCommandsStore.Load(); err == nil {
			a.emit("store:quickCommands:changed", data)
		}
	}
	if a.identityStore != nil {
		if data, err := a.identityStore.Load(); err == nil {
			a.emit("store:identities:changed", data)
		}
	}
	if a.proxyStore != nil {
		if data, err := a.proxyStore.Load(); err == nil {
			a.emit("store:proxies:changed", data)
		}
	}
}

func (a *App) triggerAutoSync() {
	if a.syncService == nil || !a.syncService.IsAutoSyncEnabled() {
		return
	}
	go func() {
		result, err := a.syncService.Sync()
		if err != nil {
			log.Writef("Auto-sync failed: %v", err)
		} else if result.Direction == sync.SyncConflict {
			a.emit("sync:conflict", map[string]interface{}{
				"localTime":  result.Conflict.LocalTime.Format(time.RFC3339),
				"remoteTime": result.Conflict.RemoteTime.Format(time.RFC3339),
			})
		}
		if err == nil && result.Direction == sync.SyncPull {
			a.reloadStoresAfterSync()
		}
		a.emit("sync:completed")
	}()
}

// waitSyncReady briefly blocks on the async NewSyncService's Ready()
// channel so callers that arrive during the ~ms-scale startup window
// don't fail with "sync service not initialized" (F-407). Returns
// true once ready, false on timeout.
func (a *App) waitSyncReady(timeout time.Duration) bool {
	if a.syncService == nil {
		return false
	}
	select {
	case <-a.syncService.Ready():
		return true
	case <-time.After(timeout):
		return false
	}
}

func (a *App) SyncGetConfig() (sync.SyncConfig, error) {
	if a.syncService == nil {
		return sync.SyncConfig{}, fmt.Errorf("sync service not initialized")
	}
	if !a.waitSyncReady(time.Second) {
		return sync.SyncConfig{}, fmt.Errorf("sync service still initializing")
	}
	return a.syncService.GetConfig()
}

// SyncSaveConfig saves the sync configuration.
func (a *App) SyncSaveConfig(config sync.SyncConfig, token string) error {
	if a.syncService == nil {
		return fmt.Errorf("sync service not initialized")
	}
	if !a.waitSyncReady(time.Second) {
		return fmt.Errorf("sync service still initializing")
	}
	return a.syncService.SaveConfig(config, token)
}

// SyncNow runs an immediate sync.
func (a *App) SyncNow() (*sync.SyncResult, error) {
	if a.syncService == nil {
		return nil, fmt.Errorf("sync service not initialized")
	}
	if !a.waitSyncReady(time.Second) {
		return nil, fmt.Errorf("sync service still initializing")
	}
	result, err := a.syncService.Sync()
	if err != nil {
		return nil, err
	}
	if result.Direction == sync.SyncConflict {
		a.emit("sync:conflict", map[string]interface{}{
			"localTime":  result.Conflict.LocalTime.Format(time.RFC3339),
			"remoteTime": result.Conflict.RemoteTime.Format(time.RFC3339),
		})
	}
	if result.Direction == sync.SyncPull {
		a.reloadStoresAfterSync()
	}
	a.emit("sync:completed")
	return result, nil
}

// SyncResolveConflict resolves a sync conflict.
func (a *App) SyncResolveConflict(useLocal bool) (*sync.SyncResult, error) {
	if a.syncService == nil {
		return nil, fmt.Errorf("sync service not initialized")
	}
	if !a.waitSyncReady(time.Second) {
		return nil, fmt.Errorf("sync service still initializing")
	}
	result, err := a.syncService.ResolveConflict(useLocal)
	if err != nil {
		return nil, err
	}
	if result.Direction == sync.SyncPull {
		a.reloadStoresAfterSync()
	}
	return result, nil
}

// SyncTestConnection tests the repository connection.
func (a *App) SyncTestConnection() error {
	if a.syncService == nil {
		return fmt.Errorf("sync service not initialized")
	}
	if !a.waitSyncReady(time.Second) {
		return fmt.Errorf("sync service still initializing")
	}
	return a.syncService.TestConnection()
}

// SyncConfigureRepo sets up a new or existing sync repository.
func (a *App) SyncConfigureRepo(repoURL, username, token, masterPassword string) (*sync.SyncResult, error) {
	if a.syncService == nil {
		return nil, fmt.Errorf("sync service not initialized")
	}
	if !a.waitSyncReady(time.Second) {
		return nil, fmt.Errorf("sync service still initializing")
	}
	result, err := a.syncService.ConfigureRepo(repoURL, username, token, masterPassword)
	if err == nil {
		a.reloadStoresAfterSync()
		a.emit("sync:completed")
	}
	return result, err
}

// SyncChangePassword re-encrypts synced files with a new master password.
func (a *App) SyncChangePassword(oldPassword, newPassword string) error {
	if a.syncService == nil {
		return fmt.Errorf("sync service not initialized")
	}
	if !a.waitSyncReady(time.Second) {
		return fmt.Errorf("sync service still initializing")
	}
	return a.syncService.ChangePassword(oldPassword, newPassword)
}

// SyncVerifyPassword verifies the given password can decrypt the repo config.
func (a *App) SyncVerifyPassword(password, username, token string) error {
	if a.syncService == nil {
		return fmt.Errorf("sync service not initialized")
	}
	if !a.waitSyncReady(time.Second) {
		return fmt.Errorf("sync service still initializing")
	}
	return a.syncService.VerifySyncPassword(password, username, token)
}

// SyncDeleteRepo removes the sync repository configuration.
func (a *App) SyncDeleteRepo() error {
	if a.syncService == nil {
		return fmt.Errorf("sync service not initialized")
	}
	if !a.waitSyncReady(time.Second) {
		return fmt.Errorf("sync service still initializing")
	}
	return a.syncService.DeleteRepo()
}

// AI Session Store methods

func (a *App) SaveAISessions(data store.AISessionData) error {
	if a.aiSessionStore == nil {
		return fmt.Errorf("AI session store not initialized")
	}
	return a.aiSessionStore.Save(data)
}

func (a *App) LoadAISessions() (store.AISessionData, error) {
	if a.aiSessionStore == nil {
		return store.AISessionData{}, fmt.Errorf("AI session store not initialized")
	}
	return a.aiSessionStore.Load()
}

// SettingsStore methods

func (a *App) SaveSettings(settings store.AppSettings) error {
	if a.settingsStore == nil {
		return fmt.Errorf("settings store not initialized")
	}
	err := a.settingsStore.Save(settings)
	if err == nil {
		a.SetDefaultSessionLogDir(settings.Terminal.SessionLogDir)
		a.setSessionLogFilename(settings.Terminal.SessionLogFilename)
		a.triggerAutoSync()
		// Re-apply the global show/hide hotkey so binding changes (and the
		// enable switch) take effect immediately. No-op when unchanged.
		applyGlobalShowHideHotkey(a.app, a.window, trayHotkeyBinding(&settings))
	}
	return err
}

func (a *App) LoadSettings() (store.AppSettings, error) {
	if a.settingsStore == nil {
		return store.AppSettings{}, fmt.Errorf("settings store not initialized")
	}
	return a.settingsStore.Load()
}

// AIConfigStore methods

func (a *App) LoadAIModels() (store.AIStoreData, error) {
	if a.aiConfigStore == nil {
		return store.AIStoreData{}, fmt.Errorf("ai config store not initialized")
	}
	return a.aiConfigStore.Load()
}

func (a *App) SaveAIModels(cfg store.AIStoreData) error {
	if a.aiConfigStore == nil {
		return fmt.Errorf("ai config store not initialized")
	}
	err := a.aiConfigStore.Save(cfg)
	if err == nil {
		a.triggerAutoSync()
	}
	return err
}

// QuickCommandsStore methods

func (a *App) SaveQuickCommands(data store.QuickCommandData) error {
	if a.quickCommandsStore == nil {
		return fmt.Errorf("quick commands store not initialized")
	}
	err := a.quickCommandsStore.Save(data)
	if err == nil {
		a.triggerAutoSync()
	}
	return err
}

func (a *App) LoadQuickCommands() (store.QuickCommandData, error) {
	if a.quickCommandsStore == nil {
		return store.QuickCommandData{}, fmt.Errorf("quick commands store not initialized")
	}
	return a.quickCommandsStore.Load()
}

// CommandsStore methods

func (a *App) ListCommands() ([]store.CommandMeta, error) {
	if a.commandsStore == nil {
		return nil, fmt.Errorf("commands store not initialized")
	}
	return a.commandsStore.List()
}

func (a *App) GetCommandBody(name string) (string, error) {
	if a.commandsStore == nil {
		return "", fmt.Errorf("commands store not initialized")
	}
	return a.commandsStore.GetBody(name)
}

func (a *App) SetCommandEnabled(name string, enabled bool) error {
	if a.commandsStore == nil {
		return fmt.Errorf("commands store not initialized")
	}
	return a.commandsStore.SetEnabled(name, enabled)
}

func (a *App) SetCommandLocked(name string, locked bool) error {
	if a.commandsStore == nil {
		return fmt.Errorf("commands store not initialized")
	}
	return a.commandsStore.SetLocked(name, locked)
}

func (a *App) SetCommandSortOrder(name string, order int) error {
	if a.commandsStore == nil {
		return fmt.Errorf("commands store not initialized")
	}
	return a.commandsStore.SetSortOrder(name, order)
}

func (a *App) DeleteCommand(name string) error {
	if a.commandsStore == nil {
		return fmt.Errorf("commands store not initialized")
	}
	return a.commandsStore.Delete(name)
}

func (a *App) CreateCommand(name, description, argumentHint, body string) error {
	if a.commandsStore == nil {
		return fmt.Errorf("commands store not initialized")
	}
	return a.commandsStore.CreateCommand(name, description, argumentHint, body)
}

func (a *App) SaveCommand(name, description, argumentHint, body string) error {
	if a.commandsStore == nil {
		return fmt.Errorf("commands store not initialized")
	}
	return a.commandsStore.SaveCommand(name, description, argumentHint, body)
}

// expandDialogDir expands a leading "~" and returns dir only if it is an
// existing absolute directory; otherwise it returns "".
func expandDialogDir(dir string) string {
	if dir == "~" || strings.HasPrefix(dir, "~/") {
		home, err := os.UserHomeDir()
		if err != nil || home == "" {
			return ""
		}
		dir = filepath.Join(home, strings.TrimPrefix(strings.TrimPrefix(dir, "~"), "/"))
	}
	if dir == "" || !filepath.IsAbs(dir) {
		return ""
	}
	if fi, err := os.Stat(dir); err != nil || !fi.IsDir() {
		return ""
	}
	return dir
}

// resolveDialogDir picks the first candidate that is an existing directory,
// falling back to the home directory. The platform pickers silently ignore a
// non-existent directory URL and reopen at the OS-remembered "last location",
// which on macOS is frequently somewhere with no visible route to ~/... (#947),
// so the fallback has to be resolved here rather than left to the panel.
func resolveDialogDir(candidates ...string) string {
	for _, c := range candidates {
		if dir := expandDialogDir(c); dir != "" {
			return dir
		}
	}
	home, _ := os.UserHomeDir()
	return home
}

// openFileDialog builds an open-file picker that starts in a known-good
// directory. Hidden files are revealed whenever the start directory is itself
// inside a dot directory (~/.ssh, ~/.kube): the platform panels hide those
// entries by default, so navigating up to home and back would otherwise leave
// the target unreachable rather than merely hard to find.
func (a *App) openFileDialog(title, startDir string) *application.OpenFileDialogStruct {
	dir := resolveDialogDir(startDir)
	return a.app.Dialog.OpenFile().
		SetTitle(title).
		SetDirectory(dir).
		ShowHiddenFiles(hasHiddenSegment(dir))
}

// hasHiddenSegment reports whether any path segment starts with a dot, i.e.
// whether reaching dir again by hand requires hidden files to be visible.
func hasHiddenSegment(dir string) bool {
	for _, seg := range strings.Split(filepath.ToSlash(dir), "/") {
		if len(seg) > 1 && seg[0] == '.' {
			return true
		}
	}
	return false
}

// OpenFileDialog opens a single-file picker. startDir is optional and accepts
// "~"-prefixed paths; it defaults to the home directory.
func (a *App) OpenFileDialog(startDir ...string) (string, error) {
	return a.openFileDialog("Select File", firstArg(startDir)).PromptForSingleSelection()
}

// firstArg unwraps the optional trailing argument the dialog bindings take, so
// existing zero-argument callers keep working.
func firstArg(args []string) string {
	if len(args) > 0 {
		return args[0]
	}
	return ""
}

// OpenPrivateKeyFile opens the private-key picker, reads the selected file's
// text and returns it for direct use with the "keyText" auth type (#720). The
// content is validated before returning; a passphrase-protected key is accepted
// (the user supplies its passphrase separately) but content that doesn't look
// like a PEM private key is rejected with an immediate error.
//
// The picker starts in ~/.ssh with hidden files shown, since that is where keys
// live and a dot directory is otherwise unreachable in the panel.
func (a *App) OpenPrivateKeyFile() (string, error) {
	path, err := a.openFileDialog("Select Private Key", "~/.ssh").
		PromptForSingleSelection()
	if err != nil {
		return "", err
	}
	if path == "" {
		// Picker cancelled — nothing to import.
		return "", nil
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return "", fmt.Errorf("read private key: %w", err)
	}
	content := string(data)
	if err := validatePrivateKeyText(content); err != nil {
		return "", err
	}
	return content, nil
}

// validatePrivateKeyText parses content as a private key when possible. An
// OpenSSH/RSA/EC/DSA PEM parsed without a passphrase is valid. Content that
// clearly isn't a private key is rejected up front; content that looks like a
// PEM private key but requires a passphrase to crack is accepted, since the key
// passphrase is entered separately on the form.
func validatePrivateKeyText(content string) error {
	data := []byte(content)
	if _, err := ssh.ParsePrivateKey(data); err == nil {
		return nil
	}
	// Parse can only succeed for an unencrypted key; a passphrase-protected key
	// aborts at the decryption step while still being a valid PEM private key,
	// so accept anything that carries the private-key envelope and reject
	// content that never looked like a key to begin with.
	if !looksLikePrivateKeyPEM(data) {
		return utils.UserErr("invalid_private_key")
	}
	return nil
}

// looksLikePrivateKeyPEM reports whether data begins with a PEM private-key
// envelope (-----BEGIN ... PRIVATE KEY-----), whitespace-insensitive.
func looksLikePrivateKeyPEM(data []byte) bool {
	head := strings.ToUpper(string(bytes.TrimSpace(data)))
	const prefix = "-----BEGIN "
	if !strings.HasPrefix(head, prefix) || !strings.Contains(head, "PRIVATE KEY-----") {
		return false
	}
	return true
}

// OpenKubeconfigFile opens the kubeconfig picker, reads the selected file and
// returns its text for pasting into the inline kubeconfig field. The content is
// parsed as a kubeconfig before returning so obviously wrong files are rejected
// up front; full connection validity is still checked when a context is loaded.
// Starts in ~/.kube with hidden files shown, for the same reason as the key
// picker.
func (a *App) OpenKubeconfigFile() (string, error) {
	path, err := a.openFileDialog("Select Kubeconfig", "~/.kube").
		PromptForSingleSelection()
	if err != nil {
		return "", err
	}
	if path == "" {
		// Picker cancelled — nothing to import.
		return "", nil
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return "", fmt.Errorf("read kubeconfig: %w", err)
	}
	if _, err := k8s.ParseBytes(data); err != nil {
		return "", utils.UserErr("invalid_kubeconfig")
	}
	return string(data), nil
}

// OpenFileDialogFiltered is like OpenFileDialog but restricts the picker to
// a single extension filter (e.g. for importing a specific file format).
func (a *App) OpenFileDialogFiltered(title, filterDisplayName, filterPattern string, startDir ...string) (string, error) {
	return a.app.Dialog.OpenFileWithOptions(&application.OpenFileDialogOptions{
		Title:     title,
		Directory: resolveDialogDir(firstArg(startDir)),
		Filters: []application.FileFilter{
			{DisplayName: filterDisplayName, Pattern: filterPattern},
		},
	}).PromptForSingleSelection()
}

func (a *App) OpenMultipleFilesDialog(startDir ...string) ([]string, error) {
	return a.openFileDialog("Select Files", firstArg(startDir)).
		PromptForMultipleSelection()
}

func (a *App) OpenDirectoryDialog(startDir ...string) (string, error) {
	return a.openFileDialog("Select Directory", firstArg(startDir)).
		CanChooseDirectories(true).
		CanChooseFiles(false).
		PromptForSingleSelection()
}

func (a *App) SaveFileDialog(defaultName string, startDir ...string) (string, error) {
	return a.app.Dialog.SaveFileWithOptions(&application.SaveFileDialogOptions{
		Title:     "Save File",
		Filename:  defaultName,
		Directory: resolveDialogDir(firstArg(startDir)),
	}).PromptForSingleSelection()
}

// SaveFileDialogFiltered is like SaveFileDialog but restricts the picker to
// a single extension filter (e.g. for exporting a specific file format).
func (a *App) SaveFileDialogFiltered(title, defaultName, filterDisplayName, filterPattern string, startDir ...string) (string, error) {
	return a.app.Dialog.SaveFileWithOptions(&application.SaveFileDialogOptions{
		Title:     title,
		Filename:  defaultName,
		Directory: resolveDialogDir(firstArg(startDir)),
		Filters: []application.FileFilter{
			{DisplayName: filterDisplayName, Pattern: filterPattern},
		},
	}).PromptForSingleSelection()
}

func (a *App) GetDesktopPath() (string, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(homeDir, "Desktop"), nil
}

// GetDefaultSSHKeyPaths returns the local default SSH private-key paths for
// the connection form's "use default" button. The standard OpenSSH names under
// ~/.ssh are listed in preference order (id_ed25519, id_rsa, id_ecdsa,
// id_dsa), and only the ones that exist are returned — the frontend cycles
// through them on repeated clicks. When none exist it returns the
// conventional ~/.ssh/id_rsa so the field still gets filled. Paths are always
// absolute — "~" is never expanded at connect time, so a bare "~/.ssh/id_rsa"
// would fail to read.
func (a *App) GetDefaultSSHKeyPaths() []string {
	home, err := os.UserHomeDir()
	if err != nil || home == "" {
		return nil
	}
	sshDir := filepath.Join(home, ".ssh")
	var paths []string
	for _, name := range []string{"id_ed25519", "id_rsa", "id_ecdsa", "id_dsa"} {
		p := filepath.Join(sshDir, name)
		if _, err := os.Stat(p); err == nil {
			paths = append(paths, p)
		}
	}
	if len(paths) == 0 {
		paths = append(paths, filepath.Join(sshDir, "id_rsa"))
	}
	return paths
}

func (a *App) GetPlatform() string {
	return goruntime.GOOS
}

func (a *App) GetAllFonts() ([]platform.FontInfo, error) {
	return platform.GetAllFonts()
}

func (a *App) OnConnectionsChanged(callback func(session.ConnectionStoreData)) {
	a.app.Event.On("store:connections:changed", func(e *application.CustomEvent) {
		if data, ok := e.Data.(session.ConnectionStoreData); ok {
			callback(data)
		}
	})
}

type AppInfo struct {
	Name    string `json:"name"`
	Version string `json:"version"`
}

func (a *App) GetAppInfo() AppInfo {
	return AppInfo{
		Name:    "Carrear's Terminal",
		Version: Version,
	}
}

// relaunchPending marks that the successor process should be spawned once
// the current one has fully exited (checked in main() after w3app.Run()
// returns). Quitting BEFORE spawning is what makes RelaunchApp compatible
// with single-instance locking: if the successor were spawned first, it
// would see the lock still held and exit immediately, killing the app.
// (The old spawn-first order existed to inherit Windows set-foreground
// permission; the successor now focuses itself at startup instead.)
var relaunchPending atomic.Bool

// RelaunchApp quits the current instance and spawns a fresh one afterwards
// so settings that are fixed at startup (e.g. the window title bar) can take
// effect.
func (a *App) RelaunchApp() {
	relaunchPending.Store(true)
	a.app.Quit()
}

func (a *App) CheckForUpdate(source string) (*update.UpdateInfo, error) {
	return update.Check(Version, source)
}

// updateManager holds the in-progress update state (download → apply).
var updateManager = update.NewManager()

// emitUpdateProgress forwards update progress payloads to the frontend.
func (a *App) emitUpdateProgress(p update.Progress) {
	a.app.Event.Emit("update:progress", p)
}

// DownloadUpdate downloads and verifies the best available update asset from
// the ordered candidate list (primary source first, mirror as fallback).
// Progress is streamed to the frontend via the update:progress event.
func (a *App) DownloadUpdate(assets []update.UpdateAsset) error {
	if devBuild {
		return fmt.Errorf("updates are disabled in development builds")
	}
	if len(assets) == 0 {
		return fmt.Errorf("no update assets available")
	}
	_, err := updateManager.Download(assets, a.emitUpdateProgress)
	return err
}

// ApplyUpdate installs the staged update and restarts the app. For Windows
// installer-channel installs it spawns a detached updater that runs the new
// NSIS installer after this process exits (the installer relaunches the app),
// so it just quits instead of relaunching.
func (a *App) ApplyUpdate() error {
	if err := updateManager.Apply(a.emitUpdateProgress); err != nil {
		return err
	}
	if update.DetectChannel() == update.ChannelInstaller {
		a.app.Quit()
		return nil
	}
	a.RelaunchApp()
	return nil
}

// FrontendLog writes a frontend log message to the application log file.
// This is the canonical interface for the frontend to persist debug/audit
// messages alongside backend logs.
func (a *App) FrontendLog(tag string, message string) {
	_ = log.Init()
	log.Writef("[%s] %s", tag, message)
}

// OpenPathInExplorer reveals the given file in the platform file
// manager. On Windows uses `explorer /select,<path>`; macOS uses
// `open -R`; Linux uses `xdg-open <dir>` (no selection semantic in
// xdg-open, so the parent directory is opened).
func (a *App) OpenPathInExplorer(path string) error {
	if path == "" {
		return fmt.Errorf("empty path")
	}
	abs, err := filepath.Abs(path)
	if err != nil {
		abs = path
	}
	isDir := false
	if info, err := os.Stat(abs); err == nil {
		isDir = info.IsDir()
	}
	switch goruntime.GOOS {
	case "windows":
		// explorer.exe returns exit code 1 on success; ignore Run's error.
		if isDir {
			_ = exec.Command("explorer", abs).Run()
		} else {
			_ = exec.Command("explorer", "/select,", abs).Run()
		}
		return nil
	case "darwin":
		if isDir {
			return exec.Command("open", abs).Run()
		}
		return exec.Command("open", "-R", abs).Run()
	default:
		if isDir {
			return exec.Command("xdg-open", abs).Run()
		}
		return exec.Command("xdg-open", filepath.Dir(abs)).Run()
	}
}

type DataDirInfo struct {
	DataDir  string `json:"dataDir"`
	Type     string `json:"type"`
	FirstRun bool   `json:"firstRun"`
}

type CredentialStatus struct {
	Mode            string `json:"mode"`
	Unlocked        bool   `json:"unlocked"`
	NeedsSetup      bool   `json:"needsSetup"`
	KeychainLost    bool   `json:"keychainLost"`
	ExistingSecrets int    `json:"existingSecrets"`
}

// GetDataDirInfo returns the current data directory info for the settings tab.
func (a *App) GetDataDirInfo() (DataDirInfo, error) {
	if a.dataDir == "" {
		return DataDirInfo{DataDir: "", Type: "default", FirstRun: true}, nil
	}
	return DataDirInfo{DataDir: a.dataDir, Type: a.dataDirType(), FirstRun: false}, nil
}

// SetDataDir selects the data directory (first-run) or changes it (migrate
// flag). Returns an error if the target is not writable or, for a non-migrate
// change into an existing dir, the new dir's credentials cannot be unlocked.
func (a *App) SetDataDir(kind, customDir string, migrate bool) error {
	target, err := dataDirFor(kind, customDir)
	if err != nil {
		return err
	}
	if !isWritable(target) {
		return fmt.Errorf("directory not writable: %s", target)
	}
	if err := os.MkdirAll(target, 0755); err != nil {
		return err
	}

	// On first run: init stores at the target and return.
	if a.dataDir == "" {
		a.dataDir = target
		if err := store.WriteBootstrap(kind, customDir); err != nil {
			log.Writef("bootstrap write failed (data dir pointer): %v", err)
		}
		a.initStores(target, false)
		a.emit("app:dataDirReady", target)
		return nil
	}

	// Change directory (runtime).
	if migrate {
		if err := copyDir(a.dataDir, target); err != nil {
			return err
		}
		// Ruling 15: keychain entries are scoped by data-dir hash. The copied
		// files are still encrypted under the current key, but the target dir
		// has no keychain-key/<targetHash> entry, so AutoUnlock would report
		// KeychainLost after restart. Re-scope the current key to the target
		// hash (no re-encryption needed — files stay under the same key).
		// Master-password mode needs nothing: its salt is copied and the user
		// re-enters the password.
		if cs := a.credentialStore; cs != nil {
			st := cs.Status()
			if st.Mode == credentials.ModeKeychain && st.Unlocked {
				if err := credentials.New(target, sync.NewKeychain()).Rekey(credentials.ModeKeychain, nil, cs.Key()); err != nil {
					return err
				}
			}
		}
	} else if !dirUnlockable(target) {
		return errors.New("cannot unlock credentials in the target directory")
	}
	if err := store.WriteBootstrap(kind, customDir); err != nil {
		log.Writef("bootstrap write failed (migrate pointer): %v", err)
	}
	// Remove the source only after bootstrap points at the target; any earlier
	// failure leaves the old dir intact so the user can retry without loss.
	if migrate {
		if err := removeDataDir(a.dataDir); err != nil {
			return err
		}
	}
	return errors.New("restart required") // frontend prompts restart
}

func (a *App) GetCredentialStatus() (CredentialStatus, error) {
	if a.credentialStore == nil {
		return CredentialStatus{NeedsSetup: true}, nil
	}
	st := a.credentialStore.Status()
	return CredentialStatus{
		Mode:         st.Mode,
		Unlocked:     st.Unlocked,
		NeedsSetup:   st.NeedsSetup,
		KeychainLost: st.KeychainLost,
	}, nil
}

func (a *App) SetupCredentials(mode, masterPassword string) error {
	if a.credentialStore == nil {
		return errors.New("credential store not initialized")
	}
	return a.credentialStore.Setup(mode, masterPassword)
}

func (a *App) UnlockCredentials(masterPassword string) error {
	if a.credentialStore == nil {
		return errors.New("credential store not initialized")
	}
	return a.credentialStore.Unlock(masterPassword)
}

func (a *App) SwitchCredentialMode(targetMode, masterPassword string) error {
	cs := a.credentialStore
	if cs == nil || !cs.Status().Unlocked {
		return errors.New("credentials locked")
	}
	oldKey := cs.Key()

	var newKey, newSalt []byte
	switch targetMode {
	case credentials.ModeKeychain:
		// Switching away from master-password removes a protection layer, so
		// require the current master password once — the same verification
		// ChangeMasterPassword does before re-keying.
		if meta, _ := credentials.ReadMeta(a.dataDir); meta != nil && meta.Mode == credentials.ModeMasterPassword {
			if string(sync.DeriveKey(masterPassword, meta.Salt)) != string(oldKey) {
				return errors.New("master password incorrect")
			}
		}
		var err error
		newKey, err = randomKey32()
		if err != nil {
			return err
		}
	case credentials.ModeMasterPassword:
		if masterPassword == "" {
			return errors.New("master password required")
		}
		var err error
		newSalt, err = sync.GenerateSalt()
		if err != nil {
			return err
		}
		newKey = sync.DeriveKey(masterPassword, newSalt)
	default:
		return fmt.Errorf("unknown mode %q", targetMode)
	}

	if err := a.reencryptAll(cs, oldKey, newKey); err != nil {
		return err
	}
	if err := cs.Rekey(targetMode, newSalt, newKey); err != nil {
		// Roll files back under oldKey; otherwise a failed Rekey leaves them
		// encrypted under a key that is never persisted.
		_ = a.reencryptAll(cs, newKey, oldKey)
		return err
	}
	if targetMode == credentials.ModeKeychain {
		_ = cs.ClearKeychainCache()
	}
	return nil
}

func (a *App) ChangeMasterPassword(oldPassword, newPassword string) error {
	cs := a.credentialStore
	if cs == nil {
		return errors.New("credential store not initialized")
	}
	meta, _ := credentials.ReadMeta(a.dataDir)
	if meta == nil || meta.Mode != credentials.ModeMasterPassword {
		return errors.New("not in master-password mode")
	}
	// Verify the old password derives the current key.
	if string(sync.DeriveKey(oldPassword, meta.Salt)) != string(cs.Key()) {
		return errors.New("old password incorrect")
	}
	oldKey := cs.Key()
	newSalt, err := sync.GenerateSalt()
	if err != nil {
		return err
	}
	newKey := sync.DeriveKey(newPassword, newSalt)
	if err := a.reencryptAll(cs, oldKey, newKey); err != nil {
		return err
	}
	if err := cs.Rekey(credentials.ModeMasterPassword, newSalt, newKey); err != nil {
		_ = a.reencryptAll(cs, newKey, oldKey)
		return err
	}
	return nil
}

func (a *App) ResetCredentials() error {
	cs := a.credentialStore
	if cs == nil {
		return errors.New("credential store not initialized")
	}
	// Clear all encrypted fields, delete meta + keychain cache.
	a.clearEncryptedFields()
	_ = cs.ClearKeychainCache()
	_ = os.Remove(credentials.MetaPath(a.dataDir))
	// Force re-setup on next launch.
	cs.SetKey(nil)
	return nil
}

// reencryptAll decrypts all secret fields under oldKey and re-encrypts them
// under newKey by loading (decrypt) then saving (encrypt) both stores.
func (a *App) reencryptAll(cs *credentials.Store, oldKey, newKey []byte) error {
	if a.connectionStore == nil || a.settingsStore == nil || a.identityStore == nil || a.proxyStore == nil {
		return errors.New("stores not initialized")
	}
	conns, err := a.connectionStore.Load()
	if err != nil {
		return err
	}
	settings, err := a.settingsStore.Load()
	if err != nil {
		return err
	}
	idents, err := a.identityStore.Load()
	if err != nil {
		return err
	}
	proxies, err := a.proxyStore.Load()
	if err != nil {
		return err
	}
	// Swap key, re-encrypt on save.
	cs.SetKey(newKey)
	if err := a.connectionStore.Save(conns); err != nil {
		cs.SetKey(oldKey)
		return err
	}
	if err := a.settingsStore.Save(settings); err != nil {
		// Roll the connection store back under oldKey so both files stay
		// encrypted under a single consistent key.
		cs.SetKey(oldKey)
		_ = a.connectionStore.Save(conns)
		return err
	}
	if err := a.identityStore.Save(idents); err != nil {
		// Roll back under oldKey: revert the key and re-save conns and settings
		// so all files stay encrypted under a single consistent key.
		cs.SetKey(oldKey)
		_ = a.connectionStore.Save(conns)
		_ = a.settingsStore.Save(settings)
		return err
	}
	if err := a.proxyStore.Save(proxies); err != nil {
		cs.SetKey(oldKey)
		_ = a.connectionStore.Save(conns)
		_ = a.settingsStore.Save(settings)
		_ = a.identityStore.Save(idents)
		return err
	}
	return nil
}

// clearEncryptedFields rewrites connections.json and settings.json with empty
// secret fields WITHOUT decrypting. It must work while the credential store is
// locked (keychain-lost / reset), when Load()/Save() would fail because they
// require the master key to decrypt the very fields we are clearing.
func (a *App) clearEncryptedFields() {
	clearSecretsInFile(filepath.Join(a.dataDir, "connections.json"), "connections")
	clearSecretsInFile(filepath.Join(a.dataDir, "settings.json"), "settings")
	clearSecretsInFile(filepath.Join(a.dataDir, "identities.json"), "identities")
	clearSecretsInFile(filepath.Join(a.dataDir, "proxies.json"), "proxies")
}

// clearSecretsInFile blanks the secret fields (connections[].password or
// ai.models[].apiKey) in a raw JSON config file, preserving every other field.
// Missing/corrupt files are left untouched.
func clearSecretsInFile(path, kind string) {
	data, err := os.ReadFile(path)
	if err != nil {
		return
	}
	var obj map[string]interface{}
	if err := json.Unmarshal(data, &obj); err != nil {
		return
	}
	switch kind {
	case "connections":
		if conns, ok := obj["connections"].([]interface{}); ok {
			for _, c := range conns {
				if cm, ok := c.(map[string]interface{}); ok {
					cm["password"] = ""
				}
			}
		}
	case "settings":
		if ai, ok := obj["ai"].(map[string]interface{}); ok {
			if models, ok := ai["models"].([]interface{}); ok {
				for _, m := range models {
					if mm, ok := m.(map[string]interface{}); ok {
						mm["apiKey"] = ""
					}
				}
			}
		}
	case "identities":
		if ids, ok := obj["identities"].([]interface{}); ok {
			for _, id := range ids {
				if im, ok := id.(map[string]interface{}); ok {
					im["password"] = ""
				}
			}
		}
	case "proxies":
		if ps, ok := obj["proxies"].([]interface{}); ok {
			for _, p := range ps {
				if pm, ok := p.(map[string]interface{}); ok {
					pm["pass"] = ""
				}
			}
		}
	}
	out, err := json.MarshalIndent(obj, "", "  ")
	if err != nil {
		return
	}
	_ = os.WriteFile(path, out, 0600)
}

func (a *App) dataDirType() string {
	if dd, err := store.ResolveDataDir(); err == nil {
		return dd.Type
	}
	return "custom"
}

func dataDirFor(kind, customDir string) (string, error) {
	switch kind {
	case "default":
		return store.DefaultDataDir()
	case "portable":
		exe, err := os.Executable()
		if err != nil {
			return "", err
		}
		return filepath.Join(filepath.Dir(exe), "data"), nil
	case "custom":
		if customDir == "" {
			return "", errors.New("custom dir required")
		}
		return customDir, nil
	default:
		return "", fmt.Errorf("unknown data dir kind %q", kind)
	}
}

func isWritable(dir string) bool {
	probe := filepath.Join(dir, ".probe")
	if err := os.MkdirAll(dir, 0755); err != nil {
		return false
	}
	if err := os.WriteFile(probe, []byte("x"), 0600); err != nil {
		return false
	}
	_ = os.Remove(probe)
	return true
}

func randomKey32() ([]byte, error) {
	k := make([]byte, 32)
	if _, err := rand.Read(k); err != nil {
		return nil, err
	}
	return k, nil
}

// removeDataDir deletes the files copied out of src during a migration so the
// move leaves no duplicate user data behind. It skips the same skipMigrate
// artifacts (sync repo, sync-config.json, bootstrap.json, .git) that copyDir
// left in place — those are not user config and must stay put.
func removeDataDir(src string) error {
	return filepath.Walk(src, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if path == src {
			return nil // keep the source directory itself
		}
		rel, _ := filepath.Rel(src, path)
		if skipMigrate(rel) {
			if info.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}
		if err := os.RemoveAll(path); err != nil {
			return err
		}
		if info.IsDir() {
			return filepath.SkipDir
		}
		return nil
	})
}

func copyDir(src, dst string) error {
	return filepath.Walk(src, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		rel, _ := filepath.Rel(src, path)
		if skipMigrate(rel) {
			if info.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}
		target := filepath.Join(dst, rel)
		if info.IsDir() {
			return os.MkdirAll(target, 0755)
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		return os.WriteFile(target, data, info.Mode())
	})
}

// skipMigrate reports whether a path (relative to the data-dir root) should be
// excluded from a migration copy. Sync artifacts — the sync working repo, a
// legacy bare repo, and sync-config.json — live in the system default dir and
// are not user data; bootstrap.json is a startup pointer that always sits at
// <exe>/data. Any .git directory is skipped defensively: git object files are
// read-only, so copying them is slow and error-prone.
func skipMigrate(rel string) bool {
	parts := strings.Split(filepath.ToSlash(rel), "/")
	for _, p := range parts {
		if p == ".git" {
			return true
		}
	}
	switch parts[0] {
	case "sync-repo", "sync-repo.git", "sync-config.json", "bootstrap.json":
		return true
	}
	return false
}

func dirUnlockable(target string) bool {
	meta, err := credentials.ReadMeta(target)
	if err != nil || meta == nil {
		return true // no meta → new/empty dir is fine
	}
	probe := credentials.New(target, sync.NewKeychain())
	if err := probe.AutoUnlock(); err != nil {
		return false
	}
	return probe.Status().Unlocked
}
