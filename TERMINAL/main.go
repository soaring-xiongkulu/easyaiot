package main

import (
	"embed"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"runtime/debug"
	"strings"
	"sync"
	"time"

	// F-201: register pprof handlers on the default mux.
	_ "net/http/pprof"

	"github.com/wailsapp/wails/v3/pkg/application"
	"github.com/wailsapp/wails/v3/pkg/events"
	"easyaiot/terminal/backend/log"
	"easyaiot/terminal/backend/session"
	"easyaiot/terminal/backend/store"
)

var Version = "dev"

// devBuild is true for `wails dev` (Version == "dev"); false for production
// builds where `-ldflags '-X main.Version=...'` sets a real version string.
// Used to gate the pprof HTTP listener so production binaries don't open it.
var devBuild = Version == "dev"

//go:embed all:frontend/dist
var assets embed.FS

// appIconTrayPNG is a dedicated tray icon: just the cyan "U" glyph cropped
// from the app icon, pre-scaled to 64px. At the tray's 16-24px sizes the full
// app icon (dark rounded tile + small glyph) turns into an unreadable dark
// blob, and GDI's own downscale of the 1024px icon is mushy — a high-contrast
// glyph filling the canvas stays legible. Scaled at runtime to the exact
// OS small-icon size on Windows (see trayIconPNG in app_windows.go).
//
//go:embed build/appicon_tray.png
var appIconTrayPNG []byte

func main() {
	// Administrator-shell broker mode: an elevated copy of Terminal launched
	// via the "runas" verb relays ConPTY I/O for admin local terminals (see
	// backend/session/local_admin_windows.go). Must run before anything else
	// so the broker never creates a window, webview or app store. It also
	// runs before the single-instance lock, which keeps the broker process
	// exempt — only GUI instances compete for the lock.
	if session.RunLocalPtyBroker(os.Args) {
		return
	}

	// Single-instance relaunch: RelaunchApp/autotest set relaunchPending and
	// quit; the successor is spawned after Run() returns, once the lock is
	// released.

	// Capture top-level panics
	defer func() {
		if r := recover(); r != nil {
			_ = log.Init()
			log.Writef("FATAL PANIC: %v\n%s", r, string(debug.Stack()))
			log.Close()
			os.Exit(1)
		}
	}()

	if err := log.Init(); err != nil {
		println("Failed to init log:", err.Error())
	}
	defer log.Close()

	// F-201: expose net/http/pprof on localhost:6060 for dev builds only.
	// Production builds (wails build) leave Version unchanged from "dev"
	// unless ldflags set it; gate behind a build flag so production does
	// not open a listener.
	startPprofIfDev()

	webviewDataPath := filepath.Join(os.TempDir(), fmt.Sprintf("Terminal-webview2-%d", os.Getpid()))
	os.MkdirAll(webviewDataPath, 0700)

	app := NewApp(webviewDataPath)

	// Read persisted window geometry and theme before creating the window —
	// both are fixed at creation in v3 (services start before the window
	// exists, so ServiceStartup can't position it). Race the loads against a
	// short deadline so a slow disk doesn't delay first paint; on timeout the
	// defaults (1200x800 centered, dark background) are used instead.
	//
	// Geometry comes from localState.json. The theme comes from settings.json,
	// whose store normally starts later in ServiceStartup, so it is loaded
	// directly here via the data-dir bootstrap (loadSavedSettings). Both loads
	// run in parallel against the same deadline.
	systemTitleBar := false
	winW, winH := 1200, 800 // fallback before any saved geometry is applied
	savedX, savedY := 0, 0
	savedMaxed := false
	savedTheme := ""
	var savedSettings store.AppSettings

	deadline := time.After(100 * time.Millisecond)

	settingsCh := make(chan store.AppSettings, 1)
	go func() {
		settingsCh <- loadSavedSettings()
	}()

	if configDir, err := os.UserConfigDir(); err == nil {
		ls := store.NewLocalStateStore(filepath.Join(configDir, "Terminal"))
		done := make(chan store.LocalState, 1)
		go func() {
			if state, err := ls.Load(); err == nil {
				done <- state
				return
			}
			done <- store.LocalState{}
		}()
		select {
		case state := <-done:
			systemTitleBar = state.SystemTitleBar
			if state.WindowWidth > 0 && state.WindowHeight > 0 {
				winW, winH = state.WindowWidth, state.WindowHeight
			}
			savedX, savedY = state.WindowX, state.WindowY
			savedMaxed = state.WindowMaximised
		case <-deadline:
			// Slow disk — paint the defaults. The goroutine continues to load
			// in the background; its result is discarded because the window
			// geometry options are fixed at startup.
		}
	}

	select {
	case savedSettings = <-settingsCh:
		savedTheme = savedSettings.Theme
	case <-deadline:
		// Too slow — windowBackgroundColour falls back to the dark default.
	}

	// Restore a saved position only when one actually exists; otherwise keep v3's
	// default (centered) so a fresh install doesn't land at (0,0).
	startPos := application.WindowCentered
	if savedX != 0 || savedY != 0 {
		startPos = application.WindowXY
	}
	startState := application.WindowStateNormal
	if savedMaxed {
		startState = application.WindowStateMaximised
	}

	// Clean external-edit scratch dirs left behind by previous runs that
	// exited without cleanup (crash / force-kill). Old dirs only: a
	// concurrently running instance keeps its own. Async: it only ever
	// touches dirs older than the stale age, which no new session can
	// collide with (fresh PID + fresh session ID), so startup never waits
	// on it.
	go sweepStaleExtEditDirs()

	// Declared before application.New so the single-instance callback (which
	// runs after startup) can capture it.
	var window *application.WebviewWindow

	w3app := application.New(application.Options{
		Name:       "Terminal",
		Assets:     application.AssetOptions{Handler: application.AssetFileServerFS(assets)},
		OnShutdown: app.shutdown,
		// Single-instance: a second GUI launch acquires the OS lock, notifies
		// this instance (which shows/focuses the existing window) and exits.
		// This prevents two GUI processes from racing on the shared stores in
		// the user's data directory (settings.json, connections, credentials).
		// The admin-shell broker process never reaches application.New, so it
		// is exempt. RelaunchApp sets relaunchPending and quits first; the
		// successor is spawned after Run() returns, with the lock released.
		SingleInstance: &application.SingleInstanceOptions{
			UniqueID: "terminal-gui",
			OnSecondInstanceLaunch: func(data application.SecondInstanceData) {
				showMainWindow(window)
			},
		},
		// WebviewUserDataPath is a Windows-only path for WebView2 user data; it is
		// harmless (ignored) on other platforms.
		Windows: application.WindowsOptions{
			WebviewUserDataPath: webviewDataPath,
			// Disable HTTP integrated-auth SSO. When WebView2 hits an
			// NTLM/Negotiate challenge (most commonly a system proxy
			// answering 407) it otherwise silently attempts to log on with
			// the current Windows identity; with stale credentials this
			// produces repeated 4625 failed-logon events that accumulate
			// into an account lockout. Terminal's frontend is served
			// locally and never needs Windows integrated auth, so switch
			// the schemes off entirely (plus empty allowlists for WebView2
			// runtimes that predate --auth-schemes; unknown switches are
			// ignored harmlessly).
			AdditionalBrowserArgs: []string{
				"--auth-schemes=basic,digest",
				"--auth-server-allowlist=",
				"--auth-negotiate-delegate-allowlist=",
			},
		},
		// Fixed program name so the window's WM_CLASS stays "terminal" — the
		// installed package's .desktop file sets StartupWMClass to the same
		// value, which is what lets the dock/taskbar associate the running
		// window with the app icon.
		Linux: application.LinuxOptions{
			ProgramName: "terminal",
		},
	})

	// On macOS, install the standard App + Edit menus. This must run AFTER
	// application.New(): menu roles dereference the global app instance and
	// panic with a nil pointer otherwise (macOS-only — NewAppMenu returns nil
	// on other platforms, which masked the crash). The Edit menu is what
	// routes the native Cmd+C/V/X/A/Z shortcuts to the first responder — every
	// WKWebView text field (input/textarea/contenteditable) relies on it. An
	// empty menu here used to suppress Wails' defaults but also killed those
	// shortcuts app-wide, forcing per-component JS reimplementations. The menu
	// lives in the top system menu bar, so it doesn't affect the frameless
	// window. On Linux (GTK) a non-nil Menu creates an empty GtkMenuBar that
	// shows as a thin white line in the frameless window, so leave it nil
	// there. See issue #291.
	var appMenu *application.Menu
	if runtime.GOOS == "darwin" {
		appMenu = application.NewMenu()
		appMenu.AddRole(application.AppMenu)
		appMenu.AddRole(application.EditMenu)
	}

	if appMenu != nil {
		w3app.Menu.SetApplicationMenu(appMenu)
	}

	window = w3app.Window.NewWithOptions(application.WebviewWindowOptions{
		Title:           "终端",
		Width:           winW,
		Height:          winH,
		X:               savedX,
		Y:               savedY,
		InitialPosition: startPos,
		StartState:      startState,
		MinWidth:        700,
		MinHeight:       450,
		// Headless local update e2e runs must not flash a window.
		Hidden:           os.Getenv("TERMINAL_UPDATE_AUTOTEST") == "1",
		Frameless:        !systemTitleBar,
		BackgroundColour: windowBackgroundColour(savedTheme),
		EnableFileDrop:   true,
		// Open the WebView2 inspector when the window is first shown. Wails
		// disables browser accelerator keys on Windows (F12 / Ctrl+Shift+I
		// never reach us), and the app's custom context menus hide the
		// default "Inspect" entry — without this there is NO way to open
		// DevTools, even in dev builds. Inert in production: the wails
		// runtime only honors it when built without the `production` tag.
		// (Deliberately NOT a window KeyBinding for F12: that would be
		// window-global and could swallow F12 from TUI apps.)
		OpenInspectorOnStartup: true,
	})

	// Win11 rounded corners: Wails only extends the DWM frame from its
	// WM_ACTIVATE handler, whose first firing (inside CreateWindowEx, before
	// its WndProc is hooked) is missed — so a production binary starts with
	// square corners until the next activation (minimise/restore). Ask DWM
	// for rounded corners on first show instead; see win11_corners_windows.go.
	// WindowShow reliably fires after WebView2 navigation completes, when the
	// native window exists. Idempotent; a no-op on pre-Win11 and other OSes.
	if runtime.GOOS == "windows" {
		window.OnWindowEvent(events.Windows.WindowShow, func(*application.WindowEvent) {
			applyRoundedCorners(window.NativeWindow())
		})
	}

	// Wails v3 delivers OS file drops to Go-side window-event listeners rather
	// than (as v2 did) auto-forwarding them to the frontend. Re-emit the dropped
	// absolute paths under the original v2 event name so `Events.On(...)` pickers
	// (FileSidebar, SFTP tab) keep receiving them for path-based upload.
	window.OnWindowEvent(events.Common.WindowFilesDropped, func(event *application.WindowEvent) {
		filenames := event.Context().DroppedFiles()
		if len(filenames) == 0 {
			return
		}
		x, y, elementID := 0, 0, ""
		if details := event.Context().DropTargetDetails(); details != nil {
			x, y = details.X, details.Y
			elementID = details.ElementID
		}
		w3app.Event.Emit("common:WindowFilesDropped", map[string]any{
			"x":         x,
			"y":         y,
			"elementId": elementID,
			"filenames": filenames,
		})
	})

	// Wire the bound App back to the runtime before registering it as a service:
	// emit() / window operations route through these references.
	app.app = w3app
	app.window = window
	w3app.RegisterService(application.NewService(app))

	// System tray (issue #982): persistent icon with left-click show/hide
	// toggle and a menu (show / hide / reset position / settings / about /
	// quit). Menu labels follow the persisted UI language; English is the
	// fallback for unknown codes. Tray creation must happen after the window
	// exists so the click handlers can drive it.
	setupTray(w3app, app, window, savedSettings.Language)

	// Global show/hide hotkey (issue #982, Windows + platform backends via
	// the wails GlobalShortcutManager). Default Ctrl+M when unset; can be
	// changed or disabled in Settings → Shortcuts.
	applyGlobalShowHideHotkey(w3app, window, trayHotkeyBinding(&savedSettings))

	// Local end-to-end update test hook — inert unless the env var is set
	// (see autotest_update.go).
	if os.Getenv("TERMINAL_UPDATE_AUTOTEST") == "1" {
		go app.autotestUpdate()
	}

	// Show the window as soon as the page's DOM is committed (content starts
	// rendering) instead of waiting for Wails' default, which defers Show until
	// WebViewDidFinishNavigation — i.e. after the multi-MB bundle is parsed and
	// executed. On macOS the window is created hidden and only shown via that
	// late callback, so users see the dock icon for seconds before anything
	// appears. Commit fires well before that; the body background (dark in
	// style.css) is already the right colour, so the early show paints a clean
	// dark window instead of white. Finish-navigation still runs its own
	// Show(), which is idempotent.
	window.OnWindowEvent(events.Mac.WebViewDidCommitNavigation, func(*application.WindowEvent) {
		if os.Getenv("TERMINAL_UPDATE_AUTOTEST") != "1" {
			window.Show()
		}
	})

	err := w3app.Run()
	if err != nil {
		log.Writef("Wails run error: %v", err)
	}

	// Quit-then-spawn relaunch (RelaunchApp / update autotest): the process
	// is exiting and the single-instance lock is released, so the successor
	// starts clean — it would otherwise be rejected as a "second instance".
	if relaunchPending.Load() {
		if err := spawnSuccessorProcess(); err != nil {
			log.Writef("relaunch: spawn successor failed: %v", err)
		}
	}
}

// loadSavedSettings reads the persisted app settings so the window can be
// created with a background colour matching the theme (see
// windowBackgroundColour), the tray menu can follow the UI language, and the
// global hotkey can be registered before Run(). The settings store normally
// initializes later in ServiceStartup, so this goes through the data-dir
// bootstrap directly. Returns the zero value when unavailable (first run /
// read error) — the caller maps that to the dark theme default and Ctrl+M.
func loadSavedSettings() store.AppSettings {
	dd, err := store.ResolveDataDir()
	if err != nil || dd.FirstRun || dd.Path == "" {
		return store.AppSettings{}
	}
	// ResolveDataDir only returns paths that exist (bootstrap paths are
	// validated, the upgrade path is checked for config files), so
	// NewSettingsStore's MkdirAll is a no-op here.
	ss, err := store.NewSettingsStore(dd.Path)
	if err != nil {
		return store.AppSettings{}
	}
	settings, err := ss.Load()
	if err != nil {
		return store.AppSettings{}
	}
	return settings
}

// windowBackgroundColour maps the persisted app theme to the native window
// background colour. That colour is only visible before the webview's first
// paint, so it is matched to the TOP colour of each theme's body gradient in
// frontend/src/style.css — the seam that would otherwise flash in the wrong
// colour on startup. 'system' is resolved from the OS the same way the
// webview engine does (systemtheme_*.go); v3's IsDarkMode() can't be used
// because it reports false before Run().
func windowBackgroundColour(theme string) application.RGBA {
	resolved := theme
	if theme == "" || theme == "system" {
		if systemPrefersDark() {
			resolved = "dark"
		} else {
			resolved = "light"
		}
	}
	switch resolved {
	case "deep-blue":
		return application.RGBA{Red: 16, Green: 23, Blue: 40, Alpha: 255} // #101728
	case "light":
		return application.RGBA{Red: 255, Green: 255, Blue: 255, Alpha: 255} // #ffffff
	default:
		return application.RGBA{Red: 27, Green: 31, Blue: 39, Alpha: 255} // #1b1f27
	}
}

// startPprofIfDev spawns a goroutine that serves net/http/pprof on
// localhost:6060 — only when running a dev build. Production builds
// (Version != "dev") deliberately skip this so end-users never have
// the debug listener open.
//
// The listener stays up for the lifetime of the process; its only job
// is to let `go tool pprof http://localhost:6060/debug/pprof/profile`
// connect and capture CPU/heap/block/goroutine profiles during
// reproduction of perf issues (see F-201 / audit §8.2).
func startPprofIfDev() {
	if !devBuild {
		return
	}
	go func() {
		if err := http.ListenAndServe("localhost:6060", nil); err != nil && err != http.ErrServerClosed {
			log.Writef("pprof listener failed: %v", err)
		}
	}()
}

// System tray support (issue #982): a persistent tray icon with a left-click
// show/hide toggle and a small right-click menu. The tray is what makes the
// window "hide to the notification area" recoverable — without it a hidden
// window could only be brought back via the global hotkey.

// trayLabels carries the tray menu strings for every UI language the
// frontend offers. The Go side can't use the frontend's i18n bundles, so the
// labels live here, keyed by the settings language code; unknown codes fall
// back to English.
var trayLabels = map[string][6]string{
	// show, hide, reset, settings, about, quit
	"en":    {"Show Main Window", "Hide to Tray", "Reset Window Position", "Settings", "About", "Quit"},
	"zh-CN": {"显示主窗口", "隐藏到托盘", "重置窗口位置", "设置", "关于", "退出"},
	"zh-TW": {"顯示主視窗", "隱藏到系統匣", "重置視窗位置", "設定", "關於", "結束"},
	"ja":    {"メインウィンドウを表示", "トレイに隠す", "ウィンドウ位置をリセット", "設定", "バージョン情報", "終了"},
	"ko":    {"메인 창 표시", "트레이로 숨기기", "창 위치 재설정", "설정", "정보", "종료"},
	"de":    {"Hauptfenster anzeigen", "In den Tray minimieren", "Fensterposition zurücksetzen", "Einstellungen", "Über", "Beenden"},
	"es":    {"Mostrar ventana principal", "Ocultar en la bandeja", "Restablecer posición", "Ajustes", "Acerca de", "Salir"},
	"fr":    {"Afficher la fenêtre", "Réduire dans la zone de notification", "Réinitialiser la position", "Paramètres", "À propos", "Quitter"},
	"ru":    {"Показать главное окно", "Свернуть в трей", "Сбросить положение окна", "Настройки", "О программе", "Выход"},
}

func trayLabel(lang string, idx int) string {
	if labels, ok := trayLabels[lang]; ok {
		return labels[idx]
	}
	return trayLabels["en"][idx]
}

const (
	trayShow   = 0
	trayHide   = 1
	trayReset  = 2
	traySet    = 3
	trayAbout  = 4
	trayQuit   = 5
)

// setupTray creates the system tray icon and menu. lang is the persisted UI
// language (from settings.json) used to localize the menu labels.
func setupTray(w3app *application.App, app *App, window *application.WebviewWindow, lang string) {
	tray := w3app.SystemTray.New()
	tray.SetIcon(trayIconPNG())
	tray.SetTooltip("终端")

	menu := application.NewMenu()
	menu.Add(trayLabel(lang, trayShow)).OnClick(func(*application.Context) {
		showMainWindow(window)
	})
	menu.Add(trayLabel(lang, trayHide)).OnClick(func(*application.Context) {
		window.Hide()
	})
	menu.AddSeparator()
	menu.Add(trayLabel(lang, trayReset)).OnClick(func(*application.Context) {
		app.resetWindowGeometry()
	})
	menu.AddSeparator()
	menu.Add(trayLabel(lang, traySet)).OnClick(func(*application.Context) {
		showMainWindow(window)
		app.emit("app:open-settings")
	})
	menu.Add(trayLabel(lang, trayAbout)).OnClick(func(*application.Context) {
		showMainWindow(window)
		app.emit("app:open-about")
	})
	menu.AddSeparator()
	menu.Add(trayLabel(lang, trayQuit)).OnClick(func(*application.Context) {
		w3app.Quit()
	})

	tray.SetMenu(menu)

	// Left click toggles visibility, mirroring MobaXterm's tray behaviour.
	tray.OnClick(func() {
		if window.IsVisible() {
			window.Hide()
		} else {
			showMainWindow(window)
		}
	})

	tray.Show()
}

// showMainWindow brings the window back from hidden/minimised state and
// gives it focus. Safe to call from any goroutine — the wails v3 window
// methods dispatch to the main thread internally.
func showMainWindow(window *application.WebviewWindow) {
	if window == nil {
		return
	}
	if !window.IsVisible() {
		window.Show()
	}
	window.UnMinimise()
	window.Focus()
}

// toggleMainWindow shows the window when hidden (or minimised), hides it
// otherwise.
func toggleMainWindow(window *application.WebviewWindow) {
	if window == nil {
		return
	}
	if window.IsVisible() {
		window.Hide()
	} else {
		showMainWindow(window)
	}
}

// Global show/hide hotkey state. applyGlobalShowHideHotkey swaps the
// registered accelerator; the currently registered string is tracked here so
// unrelated settings saves don't re-register (which would briefly release
// the OS-wide binding). Access is mutex-guarded: SaveSettings runs on a
// binding goroutine while startup applies the initial binding from main.
var (
	trayHotkeyMu      sync.Mutex
	trayHotkeyCurrent string
)

// applyGlobalShowHideHotkey registers (or re-registers) the OS-global
// show/hide shortcut via the wails GlobalShortcutManager, which handles the
// platform backends (RegisterHotKey on Windows, Carbon on macOS, X11 on
// Linux). A nil binding means the default Ctrl+M; a binding with an empty
// key (the UI's "cleared" state) unregisters. Failures (the combo already
// owned by another app) are logged and leave no binding registered.
func applyGlobalShowHideHotkey(w3app *application.App, window *application.WebviewWindow, binding *store.KeyBinding) {
	if w3app == nil {
		return
	}
	trayHotkeyMu.Lock()
	defer trayHotkeyMu.Unlock()

	if trayHotkeyCurrent != "" {
		if err := w3app.GlobalShortcut.Unregister(trayHotkeyCurrent); err != nil {
			log.Writef("global hotkey: unregister %q failed: %v", trayHotkeyCurrent, err)
		}
		trayHotkeyCurrent = ""
	}
	if binding == nil {
		binding = &store.KeyBinding{Ctrl: true, Key: "m"}
	}
	accel := keyBindingAccelerator(binding)
	if accel == "" {
		// Empty key = the UI's "cleared" state — stays unregistered.
		return
	}
	if err := w3app.GlobalShortcut.Register(accel, func() {
		toggleMainWindow(window)
	}); err != nil {
		log.Writef("global hotkey: register %q failed: %v", accel, err)
		return
	}
	trayHotkeyCurrent = accel
}

// keyBindingAccelerator renders a frontend KeyBinding as a wails accelerator
// string ("Ctrl+Alt+M"). Empty string when the binding has no key.
func keyBindingAccelerator(b *store.KeyBinding) string {
	key := strings.ToLower(strings.TrimSpace(b.Key))
	if key == "" {
		return ""
	}
	var parts []string
	if b.Ctrl {
		parts = append(parts, "Ctrl")
	}
	if b.Alt {
		parts = append(parts, "Alt")
	}
	if b.Shift {
		parts = append(parts, "Shift")
	}
	if b.Meta {
		parts = append(parts, "Super")
	}
	return strings.Join(append(parts, key), "+")
}

// trayHotkeyBinding extracts the global show/hide hotkey from the keyboard
// settings map ("trayShowHide" key, same shape as the in-app bindings).
// Absent = default Ctrl+M; present-with-empty-key = disabled.
func trayHotkeyBinding(s *store.AppSettings) *store.KeyBinding {
	if b, ok := s.Keyboard["trayShowHide"]; ok {
		return &b
	}
	return nil
}
