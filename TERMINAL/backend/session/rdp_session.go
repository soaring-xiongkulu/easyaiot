//go:build windows

package session

import (
	"bytes"
	"encoding/base64"
	"fmt"
	"image"
	"image/png"
	"runtime"
	"strings"
	"sync"
	"time"
	"unsafe"

	"github.com/go-ole/go-ole"
	"easyaiot/terminal/backend/log"
	"golang.org/x/sys/windows"
	"golang.org/x/sys/windows/registry"
)

var (
	atlDll              = windows.NewLazySystemDLL("atl.dll")
	procAtlAxWinInit    = atlDll.NewProc("AtlAxWinInit")
	procAtlAxGetControl = atlDll.NewProc("AtlAxGetControl")

	user32Dll              = windows.NewLazySystemDLL("user32.dll")
	procSetWindowPos       = user32Dll.NewProc("SetWindowPos")
	procShowWindow         = user32Dll.NewProc("ShowWindow")
	procDestroyWindow      = user32Dll.NewProc("DestroyWindow")
	procFindWindowW        = user32Dll.NewProc("FindWindowW")
	procPeekMessage        = user32Dll.NewProc("PeekMessageW")
	procTranslateMessage   = user32Dll.NewProc("TranslateMessage")
	procDispatchMessage    = user32Dll.NewProc("DispatchMessageW")
	procGetWindowRect      = user32Dll.NewProc("GetWindowRect")
	procGetClientRect      = user32Dll.NewProc("GetClientRect")
	procClientToScreen     = user32Dll.NewProc("ClientToScreen")
	procPostMessageW       = user32Dll.NewProc("PostMessageW")
	procFindWindowExW      = user32Dll.NewProc("FindWindowExW")
	procSendMessageW       = user32Dll.NewProc("SendMessageW")
	procGetSystemMetrics   = user32Dll.NewProc("GetSystemMetrics")
	procGetWindowThreadPID = user32Dll.NewProc("GetWindowThreadProcessId")
	procInvalidateRect     = user32Dll.NewProc("InvalidateRect")
	procRedrawWindow       = user32Dll.NewProc("RedrawWindow")

	// kernel32Dll is declared in local_session_windows.go (same package).
	procGetCurrentProcID = kernel32Dll.NewProc("GetCurrentProcessId")
)

const (
	WM_CLOSE           = 0x0010
	WM_SIZE            = 0x0005
	SWP_SHOWWINDOW     = 0x0040
	SWP_HIDEWINDOW     = 0x0080
	SWP_NOMOVE         = 0x0002
	SWP_NOSIZE         = 0x0001
	SWP_NOACTIVATE     = 0x0010
	SWP_NOZORDER       = 0x0004
	SWP_ASYNCWINDOWPOS = 0x4000 // non-blocking: avoids freezing RDP COM thread
	WS_EX_NOACTIVATE   = 0x08000000
	WS_CHILD           = 0x40000000
	WS_CLIPSIBLINGS    = 0x04000000
	PM_REMOVE          = 0x0001
	SW_HIDE            = 0
	SW_SHOWNOACTIVATE  = 4
	RDW_INVALIDATE     = 0x0001
	RDW_ALLCHILDREN    = 0x0080
	RDW_UPDATENOW      = 0x0100
	WM_COMMAND         = 0x0111
	BM_CLICK           = 0x00F5
	IDYES              = 6
	IDOK               = 1
	SM_CXSCREEN        = 0
	SM_CYSCREEN        = 1
)

type RDPSession struct {
	baseSession
	parentHwnd uintptr
	hwnd       uintptr
	rdp        *ole.IDispatch
	config     ConnectionConfig
	mu         sync.Mutex
	shown      bool

	// Last known position, used by Show() after Hide()
	trackX, trackY int
	trackW, trackH int

	// Full-screen toggle request, applied on the COM STA thread by the message
	// pump. COM (STA) calls must run on the thread that created the object;
	// calling PutProperty from the Wails binding thread deadlocks.
	fsRequested bool   // a toggle has been requested
	fsValue     bool   // desired FullScreen value
	fsActive    bool   // last observed FullScreen state (for exit detection)
	onFsExit    func() // called (on COM thread) when user leaves full screen via the connection bar
}

// SetOnFullScreenExit registers a callback fired when the user exits the
// ActiveX full screen via its built-in connection bar.
func (s *RDPSession) SetOnFullScreenExit(cb func()) {
	s.mu.Lock()
	s.onFsExit = cb
	s.mu.Unlock()
}

func NewRDPSession(id string) *RDPSession {
	return &RDPSession{
		baseSession: baseSession{
			id:          id,
			sessionType: "rdp",
			status:      StatusDisconnected,
		},
	}
}

// ClientAreaScreenRect returns the main window's client area in screen
// coordinates (physical pixels). Surfaced in the session:status payload; the
// frontend positions the RDP child window from the .rdp-area DOM rect, so these
// values are diagnostic only.
func (s *RDPSession) ClientAreaScreenRect() (x, y, w, h int) {
	if s.parentHwnd == 0 {
		return
	}
	var cr rect
	ret, _, _ := procGetClientRect.Call(s.parentHwnd, uintptr(unsafe.Pointer(&cr)))
	if ret == 0 {
		return
	}
	var origin point
	ret, _, _ = procClientToScreen.Call(s.parentHwnd, uintptr(unsafe.Pointer(&origin)))
	if ret == 0 {
		return
	}
	return int(origin.X), int(origin.Y), int(cr.Right), int(cr.Bottom)
}

func (s *RDPSession) SetParentHwnd(hwnd uintptr) {
	s.parentHwnd = hwnd
}

// autoDismissSecurityDialogs polls for RDP security warning dialogs (e.g.
// cert prompts or "do you want to connect" dialogs) and dismisses them.
func (s *RDPSession) autoDismissSecurityDialogs(stop <-chan struct{}) {
	dialogTitles := []string{
		"远程桌面连接",
		"远程桌面连接安全警告",
		"Remote Desktop Connection",
		"Remote Desktop Connection Security Warning",
		"Windows 安全",
		"Windows Security",
		"安全警告",
		"Security Warning",
	}
	clsName, _ := windows.UTF16PtrFromString("#32770")

	// Our own process ID, used to skip dialogs belonging to the system's mstsc.
	pid, _, _ := procGetCurrentProcID.Call()
	selfPID := uint32(pid)

	ticker := time.NewTicker(50 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-stop:
			return
		case <-ticker.C:
			for _, title := range dialogTitles {
				tPtr, _ := windows.UTF16PtrFromString(title)
				hwnd, _, _ := procFindWindowW.Call(
					uintptr(unsafe.Pointer(clsName)),
					uintptr(unsafe.Pointer(tPtr)),
				)
				if hwnd == 0 {
					continue
				}

				// Only dismiss dialogs owned by our OWN process. The dialog class
				// (#32770) and titles ("远程桌面连接" / "Windows 安全") are shared
				// with the system's mstsc; without this filter we would repeatedly
				// close mstsc's own password/security prompts, causing them to
				// flicker and re-open. (issue #348)
				var dlgPID uint32
				procGetWindowThreadPID.Call(hwnd, uintptr(unsafe.Pointer(&dlgPID)))
				if dlgPID != selfPID {
					continue
				}

				// Dismiss via standard dialog button IDs
				procPostMessageW.Call(hwnd, WM_COMMAND, IDYES, 0)
				procPostMessageW.Call(hwnd, WM_COMMAND, IDOK, 0)
				procPostMessageW.Call(hwnd, WM_COMMAND, IDYES+1, 0) // IDNO sometimes maps to 7

				// Also try clicking buttons directly (Windows 11 may use different labels)
				for _, btnText := range []string{
					"是(&Y)", "是", "Yes", "&Yes",
					"连接(&C)", "连接(&N)", "连接", "Connect", "&Connect",
					"确认", "确认(&Y)", "确认(&O)",
					"确定", "确定(&O)", "OK", "&OK",
					"继续", "继续(&C)", "Continue", "&Continue",
				} {
					btnPtr, _ := windows.UTF16PtrFromString(btnText)
					btnHwnd, _, _ := procFindWindowExW.Call(hwnd, 0, 0, uintptr(unsafe.Pointer(btnPtr)))
					if btnHwnd != 0 {
						procSendMessageW.Call(btnHwnd, BM_CLICK, 0, 0)
						break
					}
				}
			}
		}
	}
}

func (s *RDPSession) Connect(config ConnectionConfig) error {
	defer func() {
		if r := recover(); r != nil {
			log.Writef("[RDP] PANIC in Connect: %v", r)
			s.setStatus(StatusError)
		}
	}()

	// Phase 1: quick state init (brief lock)
	s.mu.Lock()
	s.config = config
	s.title = fmt.Sprintf("%s@%s (RDP)", config.User, config.Host)
	s.setStatus(StatusConnecting)
	s.mu.Unlock()

	runtime.LockOSThread() // pin COM STA to a dedicated OS thread
	ole.CoInitializeEx(0, ole.COINIT_APARTMENTTHREADED)
	defer func() {
		// Properly disconnect the RDP ActiveX control first.
		// This closes network sockets and stops internal threads —
		// skipping it leaks resources that cause progressive lag.
		s.mu.Lock()
		rdp := s.rdp
		s.rdp = nil
		s.mu.Unlock()
		if rdp != nil {
			rdp.CallMethod("Disconnect")
			rdp.Release()
		}

		s.mu.Lock()
		hwnd := s.hwnd
		s.hwnd = 0
		s.mu.Unlock()
		if hwnd != 0 {
			// Hide first to avoid visual flash during destruction
			procSetWindowPos.Call(hwnd, 0, 32000, 32000, 0, 0,
				SWP_NOSIZE|SWP_NOACTIVATE|SWP_NOZORDER|SWP_ASYNCWINDOWPOS)
			procDestroyWindow.Call(hwnd)
		}

		ole.CoUninitialize()
		runtime.UnlockOSThread()
	}()

	if s.parentHwnd == 0 {
		title, _ := windows.UTF16PtrFromString("Terminal")
		hwnd, _, _ := procFindWindowW.Call(0, uintptr(unsafe.Pointer(title)))
		if hwnd == 0 {
			log.Writef("[RDP] ERROR: cannot find main window")
			s.setStatus(StatusError)
			return fmt.Errorf("cannot find main window")
		}
		s.parentHwnd = hwnd
	}

	ret, _, _ := procAtlAxWinInit.Call()
	if ret == 0 {
		log.Writef("[RDP] ERROR: AtlAxWinInit failed")
		s.setStatus(StatusError)
		return fmt.Errorf("AtlAxWinInit failed")
	}

	progID := s.findRdpProgID()
	if progID == "" {
		log.Writef("[RDP] ERROR: no RDP ActiveX control found")
		s.setStatus(StatusError)
		return fmt.Errorf("no RDP ActiveX control found")
	}

	width := config.RdpFixedWidth
	height := config.RdpFixedHeight
	// Sentinel -1 means "follow the display": use the primary monitor's
	// physical resolution as the remote desktop size. (issue: fullscreen option)
	if width == -1 || height == -1 {
		sw, _, _ := procGetSystemMetrics.Call(uintptr(SM_CXSCREEN))
		sh, _, _ := procGetSystemMetrics.Call(uintptr(SM_CYSCREEN))
		width = int(sw)
		height = int(sh)
	}
	if width <= 0 {
		width = 800
	}
	if height <= 0 {
		height = 600
	}

	// Create the RDP container as a WS_CHILD at 32000,32000 (parent-client-
	// relative, i.e. outside the client area = hidden). The actual show/position
	// is done by positionFromMainWindow once Connect succeeds.
	name, _ := windows.UTF16PtrFromString(progID)
	className, _ := windows.UTF16PtrFromString("AtlAxWin")

	createWindowEx := windows.NewLazySystemDLL("user32.dll").NewProc("CreateWindowExW")
	// Create as a WS_CHILD of the main window. A child window:
	//  - follows the parent automatically when it moves (owned top-level windows do not),
	//  - is clipped to the parent's client area (so it can never cover the header/tabs),
	//  - cannot become the foreground window (so cannot push Terminal behind other
	//    windows during/after connect).
	// The RDP overlay is driven purely by sibling z-order: HWND_TOP to show it above
	// the webview, HWND_BOTTOM to tuck it under the webview while an HTML menu/dialog
	// is open — leaving the ActiveX rendering surface untouched, so no black screen
	// on restore. WS_EX_NOACTIVATE keeps the ActiveX + its child dialogs from
	// stealing foreground/focus during Connect.
	hwnd, _, _ := createWindowEx.Call(
		uintptr(WS_EX_NOACTIVATE),
		uintptr(unsafe.Pointer(className)),
		uintptr(unsafe.Pointer(name)),
		uintptr(WS_CHILD|WS_CLIPSIBLINGS),
		32000, 32000, // child-relative; outside the client area = hidden
		uintptr(width), uintptr(height),
		uintptr(s.parentHwnd), // parent window handle
		0,                     // menu
		0,                     // hInstance
		0,                     // lParam
	)
	if hwnd == 0 {
		log.Writef("[RDP] ERROR: CreateWindowExW failed")
		s.setStatus(StatusError)
		return fmt.Errorf("CreateWindowEx failed")
	}

	// No GWLP_HWNDPARENT owner call needed — the window is a genuine child now.

	var unk *ole.IUnknown
	procAtlAxGetControl.Call(hwnd, uintptr(unsafe.Pointer(&unk)))
	if unk == nil {
		procDestroyWindow.Call(hwnd)
		s.setStatus(StatusError)
		return fmt.Errorf("AtlAxGetControl failed")
	}

	dispatch, err := unk.QueryInterface(ole.IID_IDispatch)
	unk.Release()
	if err != nil {
		procDestroyWindow.Call(hwnd)
		s.setStatus(StatusError)
		return fmt.Errorf("QI IDispatch: %w", err)
	}

	s.mu.Lock()
	s.hwnd = hwnd
	s.rdp = dispatch
	s.mu.Unlock()

	port := config.Port
	if port <= 0 {
		port = 3389
	}

	// NonScriptable.ClearTextPassword BEFORE AdvancedSettings.
	s.configureNonScriptable(config.Password)

	dispatch.PutProperty("Server", config.Host)
	// The explicit RdpDomain field wins. As a fallback, the username may
	// carry a Windows login name of the form "DOMAIN\user" (or
	// "MACHINE\user" for a local account) — the same syntax mstsc accepts in
	// its username box — in which case the part before the backslash reaches
	// the ActiveX control's Domain property; a plain name or a UPN
	// ("user@domain") is passed through untouched.
	domain, user := config.RdpDomain, config.User
	if domain == "" {
		domain, user = splitDomainUser(config.User)
	}
	dispatch.PutProperty("UserName", user)
	dispatch.PutProperty("Domain", domain)
	dispatch.PutProperty("DesktopWidth", width)
	dispatch.PutProperty("DesktopHeight", height)
	dispatch.PutProperty("FullScreen", false)

	// AdvancedSettings2
	advObj, _ := dispatch.GetProperty("AdvancedSettings2")
	if advObj != nil {
		adv := advObj.ToIDispatch()
		if adv != nil {
			adv.PutProperty("RDPPort", port)
			adv.PutProperty("RedirectClipboard", true)
			adv.PutProperty("RedirectDrives", true)
			// Let the ActiveX control handle full screen
			// itself and show its built-in connection bar (which carries the
			// restore/exit button). Requires ContainerHandledFullScreen=false.
			adv.PutProperty("DisplayConnectionBar", true)
			adv.PutProperty("EnableAutoReconnect", true)
			if config.RdpEnableNLA {
				adv.PutProperty("EnableCredSspSupport", true)
				adv.PutProperty("AuthenticationLevel", 2)
			} else {
				adv.PutProperty("EnableCredSspSupport", false)
				adv.PutProperty("AuthenticationLevel", 0)
			}
			adv.PutProperty("WarnOnDirectConnect", false)
			// false = ActiveX manages full screen itself
			// (renders its own connection bar with an exit button), instead of
			// delegating to the host container.
			adv.PutProperty("ContainerHandledFullScreen", false)
			if config.RdpSmartSizing {
				adv.PutProperty("SmartSizing", true)
			}
			if config.Password != "" {
				adv.PutProperty("ClearTextPassword", config.Password)
			}
			adv.Release()
		}
	}

	// Route Windows key and special key combos (Win+E, Win+D, Alt+Tab, etc.)
	// to the remote machine instead of the local one. KeyboardHookMode=1 means
	// "apply key combinations at the remote server". (issue #351)
	// Note: Ctrl+Alt+Del is a Secure Attention Sequence and can never be
	// forwarded by any RDP client; use Ctrl+Alt+End instead.
	secObj, _ := dispatch.GetProperty("SecuredSettings2")
	if secObj != nil {
		sec := secObj.ToIDispatch()
		if sec != nil {
			sec.PutProperty("KeyboardHookMode", 1)
			sec.Release()
		}
	}

	// Suppress security prompts on all available AdvancedSettings versions
	for _, ver := range []int{9, 8, 7, 6, 5, 4, 3} {
		propName := fmt.Sprintf("AdvancedSettings%d", ver)
		advHigh, _ := dispatch.GetProperty(propName)
		if advHigh != nil {
			a := advHigh.ToIDispatch()
			if a != nil {
				a.PutProperty("ContainerHandledFullScreen", false)
				a.PutProperty("WarnOnDirectConnect", false)
				// Hide the minimize button on the full-screen connection bar.
				// A minimized RDP window has no taskbar entry to restore from, so it
				// would become unrecoverable. Supported in AdvancedSettings6+.
				a.PutProperty("ConnectionBarShowMinimizeButton", false)
				// ConnectToAdministerServer (AdvancedSettings8+) is the ActiveX
				// equivalent of "mstsc /admin": attach to the remote console
				// (admin) session instead of a fresh virtual session.
				if config.RdpAdminSession {
					a.PutProperty("ConnectToAdministerServer", true)
				}
				a.Release()
			}
		}
	}

	// Suppress server certificate warning at OS level
	setAuthLevelOverride()

	// Auto-dismiss any security dialogs that appear during Connect (e.g.
	// "网站正在尝试启动远程连接"). The goroutine polls for dialog windows
	// and clicks "Yes" to dismiss them.
	// On Windows 11, the dialog may appear after Connect succeeds, so keep
	// polling for a few seconds after connection.
	stopDismiss := make(chan struct{})
	go s.autoDismissSecurityDialogs(stopDismiss)
	defer func() {
		// Keep polling for dialogs after Connect completes. On Windows 11
		// the security warning may appear slightly after connection.
		go func() {
			time.Sleep(5 * time.Second)
			close(stopDismiss)
		}()
	}()

	_, err = dispatch.CallMethod("Connect")
	if err != nil {
		log.Writef("[RDP] Connect failed: %v", err)
		s.mu.Lock()
		s.hwnd = 0
		s.rdp = nil
		s.mu.Unlock()
		dispatch.Release()
		procDestroyWindow.Call(hwnd)
		s.setStatus(StatusError)
		return fmt.Errorf("RDP Connect: %w", err)
	}

	// Immediate show-and-position to avoid white/black screen.
	// Frontend will refine via RDPSetPosition shortly after.
	s.positionFromMainWindow(width, height)

	// Keep WS_EX_NOACTIVATE permanently: the ActiveX control and its child
	// windows can steal foreground during/after Connect, pushing Terminal
	// behind other windows. The flag prevents this. (issue #385, #470)

	s.setStatus(StatusConnected)

	s.runMessagePump()

	return nil
}

type rect struct {
	Left, Top, Right, Bottom int32
}

type msg struct {
	HWND    uintptr
	Message uint32
	WParam  uintptr
	LParam  uintptr
	Time    uint32
	Pt      struct{ X, Y int32 }
}

func (s *RDPSession) runMessagePump() {
	var m msg
	noMsgCount := 0
	disconnectLogged := false
	for {
		s.mu.Lock()
		done := s.hwnd == 0
		s.mu.Unlock()
		if done {
			break
		}

		// Apply any pending full-screen toggle on THIS (COM STA) thread.
		s.mu.Lock()
		if s.fsRequested {
			s.fsRequested = false
			full := s.fsValue
			rdp := s.rdp
			s.fsActive = full
			s.mu.Unlock()
			if rdp != nil {
				rdp.PutProperty("FullScreen", full)
			}
		} else {
			s.mu.Unlock()
		}

		ret, _, _ := procPeekMessage.Call(
			uintptr(unsafe.Pointer(&m)),
			0, 0, 0,
			PM_REMOVE,
		)
		if ret != 0 {
			if m.Message == 0x0012 { // WM_QUIT
				return
			}
			procTranslateMessage.Call(uintptr(unsafe.Pointer(&m)))
			procDispatchMessage.Call(uintptr(unsafe.Pointer(&m)))
			noMsgCount = 0
		} else {
			// No message available; sleep briefly to avoid busy-wait.
			// Check hwnd every ~1 second via heartbeat counter.
			time.Sleep(50 * time.Millisecond)
			noMsgCount++

			// Detect full-screen exit via the built-in connection bar: the
			// control flips FullScreen back to false. Poll on THIS COM thread
			// every ~250ms while full screen is active.
			if noMsgCount%5 == 0 {
				s.mu.Lock()
				active := s.fsActive
				rdp := s.rdp
				s.mu.Unlock()
				if active && rdp != nil {
					fs, err := rdp.GetProperty("FullScreen")
					if err == nil && fs != nil {
						stillFull := false
						if b, ok := fs.Value().(bool); ok {
							stillFull = b
						}
						if !stillFull {
							s.mu.Lock()
							s.fsActive = false
							cb := s.onFsExit
							s.mu.Unlock()
							if cb != nil {
								cb()
							}
						}
					}
				}
			}

			if noMsgCount%20 == 0 {
				// Check if RDP connection is still alive via ActiveX Connected property.
				// When the remote side drops or the connection is lost, this transitions
				// to 0 while the ActiveX window is still alive.
				if !disconnectLogged {
					s.mu.Lock()
					rdp := s.rdp
					s.mu.Unlock()
					if rdp != nil {
						connected, err := rdp.GetProperty("Connected")
						if err == nil && connected != nil {
							v := connected.Value()
							isDisconnected := false
							if b, ok := v.(bool); ok {
								isDisconnected = !b
							} else if v == nil || v == int16(0) || v == int32(0) || v == 0 {
								isDisconnected = true
							}
							if isDisconnected {
								discMsg := "RDP connection was lost"
								// Try to get the disconnect reason
								reason, reasonErr := rdp.GetProperty("DisconnectedReason")
								if reasonErr == nil && reason != nil {
									discMsg = fmt.Sprintf("RDP disconnected: %v", reason.Value())
								}
								log.Writef("[RDP-pump] connection lost: %s, signaling disconnected", discMsg)
								disconnectLogged = true
								s.setStatus(StatusDisconnected)
								// Post WM_QUIT to exit the pump and trigger cleanup
								s.mu.Lock()
								if s.hwnd != 0 {
									procPostMessageW.Call(s.hwnd, 0x0012, 0, 0)
								}
								s.mu.Unlock()
							}
						}
					}
				}
			}
		}
	}
}

func (s *RDPSession) findRdpProgID() string {
	candidates := []string{
		"MsRdpClient12NotSafeForScripting",
		"MsRdpClient11NotSafeForScripting",
		"MsRdpClient10NotSafeForScripting",
		"MsRdpClient9NotSafeForScripting",
		"MsRdpClient8NotSafeForScripting",
		"MsTscAxNotSafeForScripting",
		"MsTscAx",
	}
	ole32 := windows.NewLazySystemDLL("ole32.dll")
	procCLSIDFromProgID := ole32.NewProc("CLSIDFromProgID")
	for _, id := range candidates {
		progID, _ := windows.UTF16PtrFromString(id)
		var clsid ole.GUID
		ret, _, _ := procCLSIDFromProgID.Call(
			uintptr(unsafe.Pointer(progID)),
			uintptr(unsafe.Pointer(&clsid)),
		)
		if ret == 0 {
			return id
		}
	}

	clsidCandidates := []string{
		"{9059F30F-4EB1-4BD2-9FDC-36F43A218F4A}",
		"{54D38BF7-B1EF-4479-9674-1BD6EA465258}",
		"{C0EFA91A-EEB7-41C7-97FA-F0ED645EFB24}",
		"{301B94BA-5F25-4A12-9FFE-3B274E75C7DE}",
		"{5F681803-2900-4C43-A1CC-CF405404A676}",
		"{1FB464C8-09BB-4017-A2F5-EB742F04392F}",
	}
	ole32Dll := windows.NewLazySystemDLL("ole32.dll")
	procCLSIDFromString := ole32Dll.NewProc("CLSIDFromString")
	for _, clsidStr := range clsidCandidates {
		wideStr, _ := windows.UTF16PtrFromString(clsidStr)
		var clsid ole.GUID
		ret, _, _ := procCLSIDFromString.Call(
			uintptr(unsafe.Pointer(wideStr)),
			uintptr(unsafe.Pointer(&clsid)),
		)
		if ret == 0 {
			return clsidStr
		}
	}

	return ""
}

// setAuthLevelOverride sets the system-wide RDP authentication level to 0,
// which suppresses the server certificate warning dialog.
func setAuthLevelOverride() {
	// AuthenticationLevelOverride = 0 disables server cert verification.
	k, err := registry.OpenKey(registry.CURRENT_USER,
		`Software\Microsoft\Terminal Server Client`,
		registry.SET_VALUE)
	if err != nil {
		k, _, err = registry.CreateKey(registry.CURRENT_USER,
			`Software\Microsoft\Terminal Server Client`,
			registry.SET_VALUE)
		if err != nil {
			return
		}
	}
	defer k.Close()
	k.SetDWordValue("AuthenticationLevelOverride", 0)
	// Also disable the redirection warning dialog via the non-policy key
	k.SetDWordValue("ShowRedirectionWarningDialog", 0)

	// RedirectionWarningDialogVersion = 1 suppresses the "unknown remote
	// connection" security warning dialog. Check if already set first.
	if isRDWAlreadySet() {
		return
	}

	// Write to HKCU policy path (no elevation needed, works on Windows 11)
	rdwPath := `Software\Policies\Microsoft\Windows NT\Terminal Services\Client`
	if writeRegDWORD(registry.CURRENT_USER, rdwPath, "RedirectionWarningDialogVersion", 1) {
		return
	}

	// Fallback: try HKLM policy path (requires admin)
	rdwPathLM := `SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services\Client`
	if writeRegDWORD(registry.LOCAL_MACHINE, rdwPathLM, "RedirectionWarningDialogVersion", 1) {
		return
	}
	elevateRegWrite()
}

// isRDWAlreadySet returns true if RedirectionWarningDialogVersion is already 1.
func isRDWAlreadySet() bool {
	paths := []struct {
		root registry.Key
		path string
	}{
		{registry.LOCAL_MACHINE, `SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services\Client`},
		{registry.CURRENT_USER, `Software\Policies\Microsoft\Windows NT\Terminal Services\Client`},
	}
	for _, p := range paths {
		if readRegDWORD(p.root, p.path, "RedirectionWarningDialogVersion") == 1 {
			return true
		}
	}
	return false
}

// writeRegDWORD writes a DWORD value to the registry. Returns true on success.
func writeRegDWORD(root registry.Key, path, name string, value uint32) bool {
	k, err := registry.OpenKey(root, path, registry.SET_VALUE)
	if err != nil {
		k, _, err = registry.CreateKey(root, path, registry.SET_VALUE)
		if err != nil {
			return false
		}
	}
	defer k.Close()
	return k.SetDWordValue(name, value) == nil
}

// readRegDWORD reads a DWORD value from the registry. Returns 0 if not found.
func readRegDWORD(root registry.Key, path, name string) uint32 {
	k, err := registry.OpenKey(root, path, registry.QUERY_VALUE)
	if err != nil {
		return 0
	}
	defer k.Close()
	val, _, err := k.GetIntegerValue(name)
	if err != nil {
		return 0
	}
	return uint32(val)
}

// elevateRegWrite launches reg.exe with the "runas" verb to write the
// RedirectionWarningDialogVersion machine-policy key with admin rights.
func elevateRegWrite() {
	shell32 := windows.NewLazySystemDLL("shell32.dll")
	procShellExecute := shell32.NewProc("ShellExecuteW")

	op, _ := windows.UTF16PtrFromString("runas")
	file, _ := windows.UTF16PtrFromString("reg.exe")
	params, _ := windows.UTF16PtrFromString(
		`add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services\Client" /v RedirectionWarningDialogVersion /t REG_DWORD /d 1 /f`,
	)

	ret, _, _ := procShellExecute.Call(
		0,
		uintptr(unsafe.Pointer(op)),
		uintptr(unsafe.Pointer(file)),
		uintptr(unsafe.Pointer(params)),
		0,
		0, // SW_HIDE
	)
	if ret <= 32 {
		log.Writef("[RDP] ShellExecute runas failed: %d", ret)
	}
}

func (s *RDPSession) configureNonScriptable(password string) {
	if s.rdp == nil {
		return
	}
	nsGUIDs := []string{
		"{C1E6743A-41C1-4A74-832A-0DD06C0C9265}", // IMsTscNonScriptable (base)
		"{4F5331FB-42F5-48A2-9AFD-4743E3F6D3D7}", // IMsRdpClientNonScriptable5
		"{F50FA8AA-1C05-471B-9CB5-3BD7A6FD32BD}", // IMsRdpClientNonScriptable4
		"{B3378D90-0728-45C7-8ED7-B6159FB92219}", // IMsRdpClientNonScriptable3
	}
	unk, err := s.rdp.QueryInterface(ole.IID_IUnknown)
	if err != nil {
		log.Writef("[RDP] QI IUnknown for NonScriptable: %v", err)
		return
	}
	defer unk.Release()
	for _, guid := range nsGUIDs {
		nsGUID := ole.NewGUID(guid)
		nsUnk, err := unk.QueryInterface(nsGUID)
		if err != nil || nsUnk == nil {
			continue
		}
		if password != "" {
			nsUnk.PutProperty("ClearTextPassword", password)
		}
		nsUnk.Release()
		break
	}
}

type point struct{ X, Y int32 }

// splitDomainUser splits a Windows login name of the form "DOMAIN\user"
// (or "MACHINE\user" for a local account) into its domain and user parts.
// The backslash form is what mstsc accepts in its username box, so the same
// syntax is honored here. A name without a backslash — including a UPN such
// as "user@domain" — is returned unchanged with an empty domain.
// Windows limits the domain/computer part to 15 chars, but the split is
// kept lenient: the whole string is treated as the user when no backslash
// is present, and the last backslash wins when several appear (defensive).
func splitDomainUser(user string) (domain, name string) {
	if user == "" {
		return "", ""
	}
	if i := strings.LastIndex(user, `\`); i >= 0 {
		return user[:i], user[i+1:]
	}
	return "", user
}

// positionFromMainWindow calculates the RDP window position and initializes tracking.
func (s *RDPSession) positionFromMainWindow(width, height int) {
	if s.parentHwnd == 0 || s.hwnd == 0 {
		return
	}
	var cr rect
	ret, _, _ := procGetClientRect.Call(s.parentHwnd, uintptr(unsafe.Pointer(&cr)))
	if ret == 0 {
		log.Writef("[RDP] GetClientRect failed, fallback to GetWindowRect")
		var wr rect
		ret2, _, _ := procGetWindowRect.Call(s.parentHwnd, uintptr(unsafe.Pointer(&wr)))
		if ret2 == 0 {
			log.Writef("[RDP] GetWindowRect also failed")
			return
		}
		cr = rect{0, 0, wr.Right - wr.Left, wr.Bottom - wr.Top}
	}
	clientWidth := int(cr.Right - cr.Left)
	clientHeight := int(cr.Bottom - cr.Top)

	// trackX/trackY are PARENT-CLIENT-RELATIVE offsets into the main window. As
	// a WS_CHILD, the RDP window is positioned in the parent's client coordinate
	// space, so these are used directly by placeAtChild — no screen conversion
	// or owner-origin addition is needed, and the window follows the parent
	// automatically when it moves.
	topReserve := 80
	bottomReserve := 32
	sideMargin := 4

	x := sideMargin
	y := topReserve
	w := clientWidth - sideMargin*2
	h := clientHeight - topReserve - bottomReserve

	s.shown = true
	s.placeAtChild(x, y, w, h, SWP_SHOWWINDOW|SWP_NOACTIVATE|SWP_ASYNCWINDOWPOS)

	s.trackX = x
	s.trackY = y
	s.trackW = w
	s.trackH = h
}

// placeAtChild positions the RDP CHILD window at the given parent-client-
// relative offset (offsetX, offsetY) and size, bringing it to the top of the
// main window's child z-order (above the webview) so the ActiveX is visible.
// For a WS_CHILD, position/size are already parent-client-relative — no screen
// origin conversion is needed (the window follows the parent automatically).
// insertAfter=0 is HWND_TOP.
func (s *RDPSession) placeAtChild(offsetX, offsetY, w, h int, flags uintptr) {
	s.mu.Lock()
	hwnd := s.hwnd
	s.mu.Unlock()
	if hwnd == 0 {
		return
	}
	procSetWindowPos.Call(hwnd, 0, // HWND_TOP
		uintptr(offsetX), uintptr(offsetY),
		uintptr(w), uintptr(h),
		flags)
}

func (s *RDPSession) SetPosition(x, y, w, h int) {
	s.mu.Lock()
	if s.hwnd == 0 {
		s.mu.Unlock()
		return
	}
	s.shown = true
	s.trackX = x
	s.trackY = y
	s.trackW = w
	s.trackH = h
	s.mu.Unlock()

	// x/y are PARENT-CLIENT-RELATIVE offsets; placeAtChild positions the child
	// directly in the parent's client coordinate space (no screen conversion).
	// The frontend computes these from the .rdp-area DOM rect, so the RDP child
	// is sized/placed to exactly cover the placeholder region.
	s.placeAtChild(x, y, w, h, SWP_NOACTIVATE|SWP_ASYNCWINDOWPOS)
	// Force ActiveX to recalculate layout and repaint via WM_SIZE.
	s.mu.Lock()
	hwnd := s.hwnd
	s.mu.Unlock()
	if hwnd != 0 {
		lparam := uintptr(h<<16 | w&0xFFFF)
		procPostMessageW.Call(hwnd, WM_SIZE, 0, lparam)
	}
}

// SetFullScreen toggles the ActiveX control's built-in full-screen mode.
// With ContainerHandledFullScreen=false the control renders its own
// connection bar (with a restore button) to exit full screen.
//
// The actual COM PutProperty runs on the message-pump (STA) thread — see
// runMessagePump — because STA COM objects must be called on their owning
// thread; calling from the Wails binding thread deadlocks.
func (s *RDPSession) SetFullScreen(full bool) {
	s.mu.Lock()
	s.fsRequested = true
	s.fsValue = full
	s.mu.Unlock()
}

func (s *RDPSession) Show() {
	s.mu.Lock()
	if s.shown {
		s.mu.Unlock()
		return
	}
	tX := s.trackX
	tY := s.trackY
	tW := s.trackW
	tH := s.trackH
	s.shown = true
	s.mu.Unlock()

	// Bring the child back to HWND_TOP (above the webview) at its tracked
	// parent-client-relative position. placeAtChild passes insertAfter=0
	// (HWND_TOP). The window was merely occluded (Hide only lowered z-order,
	// never moved/resized it), so bringing it back reveals the current frame; a
	// redraw kick makes it repaint immediately without a size change (a 1px
	// resize nudge caused a visible re-scale flicker).
	s.placeAtChild(tX, tY, tW, tH, SWP_SHOWWINDOW|SWP_NOACTIVATE|SWP_ASYNCWINDOWPOS)
	s.mu.Lock()
	hwnd := s.hwnd
	s.mu.Unlock()
	if hwnd != 0 {
		procInvalidateRect.Call(hwnd, 0, 1)
		procRedrawWindow.Call(hwnd, 0, 0, RDW_INVALIDATE|RDW_UPDATENOW|RDW_ALLCHILDREN)
	}
}

func (s *RDPSession) Hide() {
	s.mu.Lock()
	if !s.shown {
		s.mu.Unlock()
		return
	}
	s.shown = false
	s.mu.Unlock()
	s.mu.Lock()
	hwnd := s.hwnd
	s.mu.Unlock()
	if hwnd != 0 {
		// Lower the child to HWND_BOTTOM (below the webview) so an HTML
		// menu/dialog can render over it. This does NOT move or resize the
		// window, so the ActiveX rendering surface stays intact — avoiding the
		// black screen that a move-offscreen hide produces (the webview, which
		// is opaque, covers the child).
		procSetWindowPos.Call(hwnd, 1, // HWND_BOTTOM
			0, 0, 0, 0,
			SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE|SWP_ASYNCWINDOWPOS)
	}
}

// Invalidate forces a repaint of the RDP ActiveX control.
func (s *RDPSession) Invalidate() {
	s.mu.Lock()
	hwnd := s.hwnd
	s.mu.Unlock()
	if hwnd != 0 {
		procInvalidateRect.Call(hwnd, 0, 1)
		// Force a synchronous repaint so the control presents its current frame
		// instead of a black one when re-shown after being occluded.
		procRedrawWindow.Call(hwnd, 0, 0, RDW_INVALIDATE|RDW_UPDATENOW|RDW_ALLCHILDREN)
	}
}

// Snapshot captures the RDP window's current content as a base64-encoded PNG.
// The frontend uses it as a frozen background for .rdp-area while the RDP window
// is hidden under an overlay (menu/dialog), so the area shows a snapshot instead
// of a black placeholder.
func (s *RDPSession) Snapshot() (string, error) {
	s.mu.Lock()
	hwnd := s.hwnd
	s.mu.Unlock()
	if hwnd == 0 {
		return "", fmt.Errorf("RDP window not created")
	}
	var wr rect
	if ret, _, _ := procGetWindowRect.Call(hwnd, uintptr(unsafe.Pointer(&wr))); ret == 0 {
		return "", fmt.Errorf("GetWindowRect failed")
	}
	w := int(wr.Right - wr.Left)
	h := int(wr.Bottom - wr.Top)
	if w <= 0 || h <= 0 {
		return "", fmt.Errorf("bad window size %dx%d", w, h)
	}

	user32 := windows.NewLazySystemDLL("user32.dll")
	gdi32 := windows.NewLazySystemDLL("gdi32.dll")
	procGetDC := user32.NewProc("GetDC")
	procReleaseDC := user32.NewProc("ReleaseDC")
	procBitBlt := gdi32.NewProc("BitBlt")
	procPrintWindow := user32.NewProc("PrintWindow")
	procCreateCompatibleDC := gdi32.NewProc("CreateCompatibleDC")
	procCreateCompatibleBitmap := gdi32.NewProc("CreateCompatibleBitmap")
	procSelectObject := gdi32.NewProc("SelectObject")
	procDeleteObject := gdi32.NewProc("DeleteObject")
	procDeleteDC := gdi32.NewProc("DeleteDC")
	procGetDIBits := gdi32.NewProc("GetDIBits")

	winDC, _, _ := procGetDC.Call(hwnd)
	if winDC == 0 {
		return "", fmt.Errorf("GetDC(hwnd) failed")
	}
	defer procReleaseDC.Call(hwnd, winDC)

	memDC, _, _ := procCreateCompatibleDC.Call(winDC)
	if memDC == 0 {
		return "", fmt.Errorf("CreateCompatibleDC failed")
	}
	defer procDeleteDC.Call(memDC)

	hbm, _, _ := procCreateCompatibleBitmap.Call(winDC, uintptr(w), uintptr(h))
	if hbm == 0 {
		return "", fmt.Errorf("CreateCompatibleBitmap failed")
	}
	defer procDeleteObject.Call(hbm)

	oldObj, _, _ := procSelectObject.Call(memDC, hbm)
	if oldObj == 0 {
		return "", fmt.Errorf("SelectObject failed")
	}
	defer procSelectObject.Call(memDC, oldObj)

	// PrintWindow with PW_RENDERFULLCONTENT renders the window AND its child
	// control into the target DC, which is what actually carries the remote
	// desktop frame (a plain BitBlt from the AtlAxWin DC would capture the empty
	// parent surface). Fall back to BitBlt if PrintWindow reports failure.
	const pwRenderFullContent = 0x00000002
	const srcCopy = 0x00CC0020
	if ret, _, _ := procPrintWindow.Call(hwnd, memDC, pwRenderFullContent); ret == 0 {
		if ret2, _, _ := procBitBlt.Call(memDC, 0, 0, uintptr(w), uintptr(h), winDC, 0, 0, srcCopy); ret2 == 0 {
			return "", fmt.Errorf("PrintWindow failed")
		}
	}

	// DIB header for GetDIBits (top-down 32bpp BGRA).
	type bitmapInfoHeader struct {
		biSize          uint32
		biWidth         int32
		biHeight        int32
		biPlanes        uint16
		biBitCount      uint16
		biCompression   uint32
		biSizeImage     uint32
		biXPelsPerMeter int32
		biYPelsPerMeter int32
		biClrUsed       uint32
		biClrImportant  uint32
	}
	bi := bitmapInfoHeader{
		biSize:     uint32(unsafe.Sizeof(bitmapInfoHeader{})),
		biWidth:    int32(w),
		biHeight:   -int32(h), // negative = top-down rows
		biPlanes:   1,
		biBitCount: 32,
	}
	pix := make([]byte, w*h*4)
	if ret, _, _ := procGetDIBits.Call(memDC, hbm, 0, uintptr(h), uintptr(unsafe.Pointer(&pix[0])), uintptr(unsafe.Pointer(&bi)), 0); ret == 0 {
		return "", fmt.Errorf("GetDIBits failed")
	}

	// BGRA → RGBA, then encode PNG.
	img := &image.RGBA{Pix: make([]byte, w*h*4), Stride: w * 4, Rect: image.Rect(0, 0, w, h)}
	for i := range w * h {
		b := pix[i*4+0]
		g := pix[i*4+1]
		r := pix[i*4+2]
		a := pix[i*4+3]
		img.Pix[i*4+0] = r
		img.Pix[i*4+1] = g
		img.Pix[i*4+2] = b
		img.Pix[i*4+3] = a
	}

	var buf bytes.Buffer
	if err := png.Encode(&buf, img); err != nil {
		return "", err
	}
	return base64.StdEncoding.EncodeToString(buf.Bytes()), nil
}

func (s *RDPSession) Disconnect() error {
	// Post WM_QUIT to the COM STA message pump so it exits cleanly.
	// Do NOT zero s.hwnd here — the defer in Connect() needs it
	// to call DestroyWindow for proper cleanup.
	s.mu.Lock()
	hwnd := s.hwnd
	s.mu.Unlock()

	if hwnd != 0 {
		procPostMessageW.Call(hwnd, 0x0012, 0, 0) // WM_QUIT
	}
	s.setStatus(StatusDisconnected)
	return nil
}

func (s *RDPSession) Resize(cols, rows int) error {
	s.mu.Lock()
	if s.rdp != nil {
		s.rdp.PutProperty("DesktopWidth", cols)
		s.rdp.PutProperty("DesktopHeight", rows)
	}
	s.mu.Unlock()
	return nil
}

func (s *RDPSession) Write(_ []byte) error {
	return nil
}

func (s *RDPSession) IsConnected() bool {
	return s.Status() == StatusConnected
}
