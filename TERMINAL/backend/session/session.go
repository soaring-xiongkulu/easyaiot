package session

import (
	"context"
	"fmt"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

type SessionStatus string

const (
	StatusConnecting   SessionStatus = "connecting"
	StatusConnected    SessionStatus = "connected"
	StatusDisconnected SessionStatus = "disconnected"
	StatusError        SessionStatus = "error"
)

// disconnectNotice formats a red disconnect prompt with the local time it
// happened, so users can tell when a remote host dropped them. See issue #367.
func disconnectNotice(msg string) []byte {
	ts := time.Now().Format("2006-01-02 15:04:05")
	return []byte(fmt.Sprintf("\r\n\x1b[31m%s (%s) Press Enter to reconnect.\x1b[0m\r\n", msg, ts))
}

type ConnectionGroup struct {
	ID       string  `json:"id"`
	Name     string  `json:"name"`
	ParentId *string `json:"parentId,omitempty"`
}

type ConnectionConfig struct {
	ID       string `json:"id"`
	Name     string `json:"name"`
	Remark   string `json:"remark,omitempty"`
	Type     string `json:"type"`
	Host     string `json:"host"`
	Port     int    `json:"port"`
	User     string `json:"user"`
	AuthType string `json:"authType"`
	// AuthType "agent" uses SSH_AUTH_SOCK on Unix. On Windows it uses Pageant,
	// falling back to the Windows OpenSSH agent named pipe.
	// AuthType "kerberos" uses the local Kerberos credential cache and
	// SSH gssapi-with-mic; no password or private key is persisted.
	// KerberosRealm is appended to the host service principal when Host is an
	// IP address, producing host/<ip>@<REALM>. Domain-name targets keep their
	// existing canonicalization behavior.
	KerberosRealm string `json:"kerberosRealm,omitempty"`
	// IdentityId references a saved Identity (see identity.go). When set with
	// AuthType "identity", MaterializeIdentity resolves and injects the
	// credentials at connect time.
	IdentityId string `json:"identityId,omitempty"`
	// Password is stored in plaintext JSON. Will be migrated to OS keychain in a future iteration.
	Password string `json:"password,omitempty"`
	KeyPath  string `json:"keyPath,omitempty"`
	// KeyContent holds the inline private-key text (PEM) for authType "keyText".
	// When set, the connection authenticates from the text directly instead of
	// reading KeyPath from disk. Encrypted at rest and normalized across cloud
	// sync exactly like passwords so it stays portable across devices (#720).
	KeyContent string  `json:"keyContent,omitempty"`
	GroupId    *string `json:"groupId,omitempty"`
	// RDP-specific fields
	RdpFixedWidth  int  `json:"rdpFixedWidth,omitempty"`
	RdpFixedHeight int  `json:"rdpFixedHeight,omitempty"`
	RdpSmartSizing bool `json:"rdpSmartSizing"`
	RdpEnableNLA   bool `json:"rdpEnableNLA"`
	// RdpDomain is the Windows domain (or computer name for local accounts)
	// sent to the RDP ActiveX control's Domain property. When empty, a
	// "DOMAIN\user" prefix in User is used as a fallback, mirroring the
	// username syntax mstsc accepts.
	RdpDomain string `json:"rdpDomain,omitempty"`
	// RdpAdminSession connects to the remote console (admin) session, the
	// equivalent of "mstsc /admin". Mapped to the ActiveX
	// IMsRdpClientAdvancedSettings8::ConnectToAdministerServer property.
	RdpAdminSession bool `json:"rdpAdminSession"`
	// Local terminal shell path
	ShellPath string `json:"shellPath,omitempty"`
	// Working directory for local terminal (defaults to user home directory if empty)
	Cwd string `json:"cwd,omitempty"`
	// Serial port configuration
	SerialPort     string  `json:"serialPort,omitempty"`
	SerialBaudRate int     `json:"serialBaudRate,omitempty"`
	SerialDataBits int     `json:"serialDataBits,omitempty"`
	SerialStopBits float64 `json:"serialStopBits,omitempty"`
	SerialParity   string  `json:"serialParity,omitempty"`
	// Database-specific fields
	DBType   string `json:"dbType,omitempty"`   // "mysql", "postgres", "rqlite", "oracle", "sqlserver", "redis", "mongodb", "elasticsearch"
	DBName   string `json:"dbName,omitempty"`   // default database name
	DBParams string `json:"dbParams,omitempty"` // extra DSN query parameters, e.g. "sslmode=require&connect_timeout=30"
	// Elasticsearch / OpenSearch fields
	EsUseSSL     bool   `json:"esUseSsl,omitempty"`     // use HTTPS
	EsPathPrefix string `json:"esPathPrefix,omitempty"` // optional path prefix, e.g. "/es"
	EsSkipVerify bool   `json:"esSkipVerify,omitempty"` // insecureSkipVerify for self-signed certs
	// Redis Sentinel fields (only used when RedisMode == "sentinel")
	RedisMode        string `json:"redisMode,omitempty"`        // ""/"standalone"(default) | "sentinel"
	RedisMasterName  string `json:"redisMasterName,omitempty"`  // Sentinel primary group name, e.g. "mymaster"
	RedisSentinels   string `json:"redisSentinels,omitempty"`   // comma-separated sentinel host:port list
	SentinelUser     string `json:"sentinelUser,omitempty"`     // Sentinel ACL user (optional)
	SentinelPassword string `json:"sentinelPassword,omitempty"` // Sentinel requirepass (optional)
	// RedisKeySeparator splits keys into a folder tree in the Redis browser.
	// Defaults to ":" when empty; set to a character that never appears in
	// keys to disable grouping (flat list).
	RedisKeySeparator string `json:"redisKeySeparator,omitempty"`
	// SSH post-login script: commands to execute after successful login
	PostLoginScript string `json:"postLoginScript,omitempty"`
	// Post-login expect/send automation: interactive steps executed after login.
	PostLoginExpectSteps []PostLoginExpectStep `json:"postLoginExpectSteps,omitempty"`
	// SSH tunnel: reference to an existing SSH connection used as a jump host.
	// When set, the connection goes through local port forwarding:
	//   127.0.0.1:auto-port → tunnel SSH → target Host:Port
	TunnelSSHConnID string `json:"tunnelSSHConnId,omitempty"`
	// Proxy: reference to a saved Proxy (see proxy.go). When set, the
	// first-hop TCP dial goes through this SOCKS5/HTTP proxy instead of
	// connecting directly.
	ProxyId string `json:"proxyId,omitempty"`
	// Proxy is the resolved runtime proxy for this connect attempt. Populated
	// by materializeProxy at connect time; never persisted.
	Proxy             *SocksProxy `json:"-"`
	TunnelSSHUser     string      `json:"tunnelSSHUser,omitempty"`
	TunnelSSHPassword string      `json:"tunnelSSHPassword,omitempty"`
	// SFTP max concurrent transfers (0 = unlimited)
	SftpMaxConcurrency int `json:"sftpMaxConcurrency,omitempty"`
	// FileTransferProto selects the file-transfer protocol used by the SSH
	// connection's companion file panel and "connect SFTP/SCP" actions:
	// "" / "sftp" (default) | "scp" — for hosts without an SFTP subsystem.
	FileTransferProto string `json:"fileTransferProto,omitempty"`
	// Initial terminal size reported by the frontend BEFORE the
	// SSH/local PTY is created. Without this the backend starts the
	// remote shell with the default 80x24 and Claude Code draws tables
	// at that width; by the time the frontend's fitAddon measures the
	// actual xterm cols and sends SessionResize, several lines are
	// already wrapped at 80 cols and the rest at the real cols — table
	// borders drift apart. 0/0 means "use default"; otherwise fed into
	// SetPendingSize before Connect so getInitialSize picks them up.
	InitialCols int `json:"initialCols,omitempty"`
	InitialRows int `json:"initialRows,omitempty"`
	// FTP-specific fields
	FtpEncryption string `json:"ftpEncryption,omitempty"` // "none"(default) | "auto" | "required"
	FtpPassive    bool   `json:"ftpPassive"`              // passive mode (default true)
	FtpEncoding   string `json:"ftpEncoding,omitempty"`   // "utf-8" | "gbk" | "shift-jis" | "latin-1"
	// FtpSkipVerify opts in to tls.Config.InsecureSkipVerify for FTPS connections.
	// Defaults to false (verify enabled). Off by default preserves backwards
	// compatibility for users today who rely on it for self-signed certs —
	// but the toggle now exists so the choice is explicit, and a one-shot
	// session-log warning fires on connect when it is enabled.
	FtpSkipVerify bool `json:"ftpSkipVerify,omitempty"`
	// VNC-specific fields (issue #95)
	// VncShared is forwarded to noVNC's RFB constructor as `shared`.
	// true (default) — the new client may connect alongside other clients.
	// false — the server will typically disconnect other clients on connect.
	VncShared bool `json:"vncShared,omitempty"`
	// VncRepeaterID is forwarded to noVNC's RFB constructor as `repeaterID`.
	// Empty (default) — direct connection to the VNC server.
	// Non-empty — connect via an UltraVNC-compatible repeater using the given ID.
	VncRepeaterID string `json:"vncRepeaterID,omitempty"`
	// SMB-specific fields
	SmbDomain string `json:"smbDomain,omitempty"`
	SmbShare  string `json:"smbShare,omitempty"`
	// S3-specific fields
	S3Region string `json:"s3Region,omitempty"`
	S3Bucket string `json:"s3Bucket,omitempty"`
	// S3URLStyle chooses URL addressing for S3 requests against a custom
	// endpoint. "" / "virtual" (default) uses virtual-hosted style
	// (https://bucket.endpoint/key) — required by Alibaba Cloud OSS,
	// Tencent COS and Huawei OBS; they reject path-style requests with
	// "SecondLevelDomainForbidden" (issue #452). "path" uses path-style
	// (https://endpoint/bucket/key) for AWS S3 and MinIO.
	S3URLStyle string `json:"s3UrlStyle,omitempty"`
	// Terminal character encoding for ssh/telnet:
	// "" / "utf-8"(default) | "gbk" | "gb2312" | "gb18030" | "big5" | "shift-jis" | "euc-jp" | "euc-kr"
	Encoding string `json:"encoding,omitempty"`
	// X11Forwarding enables SSH X11 forwarding (ssh -X semantics). Sends an
	// "x11-req" global request after RequestPty; accepts "x11" channels from
	// the server and bridges them to the local X server at $DISPLAY. If
	// $DISPLAY is unset, xauth is missing, or the local X server is
	// unreachable the connection still succeeds and a yellow warning is
	// emitted in the terminal (silent degradation). Trusted mode is used as
	// fallback when MIT-MAGIC-COOKIE-1 cannot be read from $XAUTHORITY.
	X11Forwarding bool `json:"x11Forwarding,omitempty"`
	// AgentForwarding exposes the local SSH agent to the remote SSH session
	// (the equivalent of OpenSSH's -A option). The private keys remain in the
	// local agent; only signing requests are forwarded.
	AgentForwarding bool `json:"agentForwarding,omitempty"`
	// ShellIntegration injects OSC-7 cwd reporting into supported remote SSH
	// shells at startup. It changes how the remote shell starts, so it can be
	// turned off — but it defaults to ON: a nil field (historical configs and
	// fresh JSON) means enabled; only an explicit false opts out. When off,
	// enabling "follow terminal path" in the file sidebar injects the hook at
	// click time instead (with a confirmation dialog, see InjectCwdHook).
	ShellIntegration *bool `json:"shellIntegration,omitempty"`
	// Backspace key byte sequence for terminal-stream types (ssh/telnet/serial).
	// The translation happens on the frontend in applyBackspaceKey before the
	// byte hits SessionWrite, so the backend does not read this field — it is
	// kept here so the Wails binding reflects the full connection contract.
	// ""(default) | "del"(0x7F) | "bs"(0x08) | "vt220"(ESC[3~)
	BackspaceKey string `json:"backspaceKey,omitempty"`
	// Telnet-specific fields
	// TelnetNegotiationMode controls who initiates option negotiation.
	// "active" (default) — client sends WILL/DO after connect.
	// "passive" — client only responds to server negotiation.
	TelnetNegotiationMode string `json:"telnetNegotiationMode,omitempty"`
	// LocalEcho echoes typed characters locally when the remote side doesn't.
	LocalEcho bool `json:"localEcho,omitempty"`
	// TelnetSendMode: "character" (default) — each keystroke sent immediately.
	// "line" — buffer until Enter, send the whole line.
	TelnetSendMode string `json:"telnetSendMode,omitempty"`
	// NewlineMode: "cr" (default) — Enter sends \r. "crlf" — Enter sends \r\n.
	NewlineMode string `json:"newlineMode,omitempty"`
	// K8s-specific fields
	K8sConfigPath   string `json:"k8sConfigPath,omitempty"`   // File 模式：kubeconfig 文件路径
	K8sConfigInline string `json:"k8sConfigInline,omitempty"` // Inline 模式：kubeconfig YAML 全文（明文存储，同其他连接密码策略）
	K8sContext      string `json:"k8sContext,omitempty"`      // 选中的 context 名，为空则用 current-context
	K8sNamespace    string `json:"k8sNamespace,omitempty"`    // 默认 namespace，"" = all
	K8sInsecureTls  bool   `json:"k8sInsecureTls,omitempty"`  // 覆盖 kubeconfig 中的 insecure-skip-tls-verify
	// Container-specific fields
	ContainerTransport string `json:"containerTransport,omitempty"` // "ssh" | "local"
	ContainerSSHConnID string `json:"containerSSHConnId,omitempty"` // 引用的 SSH 连接（transport=ssh）
	ContainerRuntime   string `json:"containerRuntime,omitempty"`   // "docker" | "podman" | "nerdctl"
	// LogOnConnect, when true, tells the App layer to enable the
	// session output log automatically the first time this panel binds
	// a session. It has no effect on later reconnects — a manually
	// stopped log stays stopped for the life of the panel.
	LogOnConnect bool `json:"logOnConnect,omitempty"`
	// X11Desktop fields. Used when Type == "x11-desktop".
	// This type carries its own SSH credentials (Host, Port, User,
	// AuthType, Password, KeyPath) and connects directly — it no
	// longer references a separate SSH connection. X11 forward is
	// forced on automatically (this type is meaningless without it).
	//   DesktopType — "gnome" | "kde" | "xfce" | "mate" | "cinnamon" |
	//                 "openbox" | "custom". Mapped to a built-in command or
	//                 to CustomCmd verbatim.
	//   CustomCmd   — only used when DesktopType == "custom". The string is
	//                 passed to sshd verbatim (so it goes through
	//                 /bin/sh -c on the remote).
	X11DesktopDesktopType string `json:"x11DesktopDesktopType,omitempty"`
	X11DesktopCustomCmd   string `json:"x11DesktopCustomCmd,omitempty"`
	// Saved-workspace fields. Used when Type == "workspace": the config is a
	// named, persisted workspace snapshot living in the connection tree.
	// Members hold only a ConnectionID reference — host credentials re-resolve
	// through the normal connection decryption path at connect time, so no
	// secret is ever duplicated here.
	WorkspaceMembers []SavedWorkspaceMember    `json:"workspaceMembers,omitempty"`
	WorkspaceLayout  *SavedWorkspaceLayoutNode `json:"workspaceLayout,omitempty"`
}

// SavedWorkspaceMember is one terminal slot inside a saved workspace.
type SavedWorkspaceMember struct {
	// ID is the stable member identity; saved-layout leaves reference it.
	// The frontend reuses the source panel's id, so a re-save of the same
	// live workspace keeps ids stable.
	ID string `json:"id"`
	// ConnectionID references the saved host the member connects to; empty
	// for self-contained members (local/wsl terminals).
	ConnectionID string `json:"connectionId,omitempty"`
	// Type is the terminal panel kind (ssh/local/wsl/telnet/serial/...).
	Type string `json:"type"`
	// Title is the display title saved from the live panel.
	Title string `json:"title"`
	// ShellPath recreates local/wsl members (wsl://<distro> carries the distro).
	ShellPath string `json:"shellPath,omitempty"`
}

// SavedWorkspaceLayoutNode mirrors the frontend LayoutNode with the leaf
// panelId replaced by the stable member ID (runtime panel ids are ephemeral).
type SavedWorkspaceLayoutNode struct {
	Type      string                     `json:"type"` // "leaf" | "split"
	MemberID  string                     `json:"memberId,omitempty"`
	Direction string                     `json:"direction,omitempty"` // "horizontal" | "vertical"
	Children  []SavedWorkspaceLayoutNode `json:"children,omitempty"`
	Sizes     []float64                  `json:"sizes,omitempty"`
}

// ConnectionStoreData is the top-level structure persisted to connections.json.
// shellIntegrationEnabled reports whether startup shell integration (the
// silent bootstrap that changes how the remote shell starts) should run.
// nil = enabled: the default-on toggle and historical configs.
func (c ConnectionConfig) shellIntegrationEnabled() bool {
	return c.ShellIntegration == nil || *c.ShellIntegration
}

type ConnectionStoreData struct {
	Groups      []ConnectionGroup  `json:"groups"`
	Connections []ConnectionConfig `json:"connections"`
}

type SessionInfo struct {
	ID     string        `json:"id"`
	Type   string        `json:"type"`
	Title  string        `json:"title"`
	Status SessionStatus `json:"status"`
	// ProxyAddr is the local WebSocket URL for VNC/SPICE sessions whose
	// client (noVNC / spice-html5) connects through the WebSocket↔TCP proxy.
	// Returned synchronously from CreateSession so the frontend can start
	// the RFB/SPICE client without racing the session:status event.
	ProxyAddr string `json:"proxyAddr,omitempty"`
}

type Session interface {
	ID() string
	Type() string
	Title() string
	Status() SessionStatus

	Connect(config ConnectionConfig) error
	Disconnect() error
	IsConnected() bool
	Resize(cols, rows int) error
	// SetPendingSize stashes cols/rows to be applied at Connect time, for
	// the deferred-start flow where the frontend mounts the xterm and
	// measures the real size AFTER CreateSession has already created the
	// session object but BEFORE SessionStart runs Connect.
	SetPendingSize(cols, rows int)

	Write(data []byte) error
	SetOnDataCallback(cb func([]byte))
	SetOnBinaryCallback(cb func([]byte))
	SetOnStatusChangeCallback(cb func(SessionStatus))
	SetZmodemMode(bool)
	EndZmodem([]byte)
	IsZmodemMode() bool
}

type baseSession struct {
	id               string
	sessionType      string
	title            string
	status           SessionStatus
	onDataCallback   func([]byte)
	onBinaryCallback func([]byte)
	onStatusCallback func(SessionStatus)
	mu               sync.RWMutex
	pendingCols      int
	pendingRows      int
	zmodemMode       bool
	zmodemTimer      *time.Timer
	zmodemDeadline   time.Time
	zmodemGeneration uint64
	lastReadTime     atomic.Int64
	// outputLogWriter, if non-nil, receives a copy of every byte emitted
	// via emitData. It is set by the App layer and lives longer than any
	// single session — a reconnect re-uses the same underlying logger by
	// installing the same writer on the new session.
	outputLogWriter func([]byte)
	// logOnConnect mirrors ConnectionConfig.LogOnConnect so the App
	// layer can query it via AutoLogOnConnect() and decide whether to
	// enable the log the first time this session binds to a panel.
	logOnConnect   bool
	logSessionName string
	logHost        string
	// idleSignal is sent-to (non-blocking) every time RecordReadActivity
	// runs. waitIdle subscribes to this channel to avoid the busy-loop
	// that previously woke every 50ms; see F-017. idleSignalOnce makes
	// the channel lazy-allocated so we don't have to touch every
	// baseSession constructor.
	idleSignal     chan struct{}
	idleSignalOnce sync.Once
}

func (s *baseSession) ID() string            { return s.id }
func (s *baseSession) Type() string          { return s.sessionType }
func (s *baseSession) Title() string         { return s.title }
func (s *baseSession) Status() SessionStatus { s.mu.RLock(); defer s.mu.RUnlock(); return s.status }

func (s *baseSession) SetOnDataCallback(cb func([]byte)) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.onDataCallback = cb
}

func (s *baseSession) SetOnStatusChangeCallback(cb func(SessionStatus)) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.onStatusCallback = cb
}

func (s *baseSession) setStatus(st SessionStatus) {
	s.mu.Lock()
	s.status = st
	cb := s.onStatusCallback
	s.mu.Unlock()
	if cb != nil {
		cb(st)
	}
}

func (s *baseSession) emitData(data []byte) {
	s.mu.RLock()
	w := s.outputLogWriter
	cb := s.onDataCallback
	s.mu.RUnlock()
	if w != nil {
		w(data)
	}
	if cb != nil {
		cb(data)
	}
}

// SetOutputLogWriter installs (or clears with nil) the sink that
// receives each byte emitted via emitData. Ownership of the underlying
// logger lives at the App layer so it can outlive any single session
// and survive reconnects.
func (s *baseSession) SetOutputLogWriter(w func([]byte)) {
	s.mu.Lock()
	s.outputLogWriter = w
	s.mu.Unlock()
}

// SetLogOnConnect records the per-connection auto-log preference so
// the App layer can read it via AutoLogOnConnect(). Each session type
// calls this from Connect based on ConnectionConfig.LogOnConnect.
func (s *baseSession) SetLogOnConnect(v bool) { s.logOnConnect = v }

// AutoLogOnConnect reports whether this session was created from a
// connection configured to start logging automatically.
func (s *baseSession) AutoLogOnConnect() bool { return s.logOnConnect }

// SetLogIdentity records the connection fields used by the session-log
// filename template. It is called before Connect, so auto-logging can use the
// original configured name and host even while the connection is starting.
func (s *baseSession) SetLogIdentity(name, host string) {
	s.mu.Lock()
	s.logSessionName = name
	s.logHost = host
	s.mu.Unlock()
}

func (s *baseSession) LogIdentity() (name, host string) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.logSessionName, s.logHost
}

func (s *baseSession) SetPendingSize(cols, rows int) {
	s.mu.Lock()
	s.pendingCols = cols
	s.pendingRows = rows
	s.mu.Unlock()
}

func (s *baseSession) GetPendingSize() (cols, rows int) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.pendingCols, s.pendingRows
}

func (s *baseSession) getInitialSize(defCols, defRows int) (int, int) {
	cols, rows := s.GetPendingSize()
	if cols <= 0 {
		cols = defCols
	}
	if rows <= 0 {
		rows = defRows
	}
	return cols, rows
}

func (s *baseSession) SetZmodemMode(v bool) {
	s.mu.Lock()
	s.setZmodemModeLocked(v)
	s.mu.Unlock()
}

// EndZmodem leaves binary mode and emits terminal bytes that followed the
// protocol's final handshake through the normal text-output path. Session
// types with an output decoder can override this method.
func (s *baseSession) EndZmodem(trailing []byte) {
	s.mu.Lock()
	s.setZmodemModeLocked(false)
	w := s.outputLogWriter
	cb := s.onDataCallback
	s.mu.Unlock()
	if w != nil && len(trailing) > 0 {
		w(trailing)
	}
	if cb != nil && len(trailing) > 0 {
		cb(trailing)
	}
}

// This is only a final safety net for an abandoned frontend transfer. Keep it
// longer than the frontend protocol watchdog so file-picker interaction is not
// mistaken for a stalled transfer.
var zmodemModeTimeout = 2 * time.Minute

func (s *baseSession) setZmodemModeLocked(v bool) {
	s.zmodemGeneration++
	s.zmodemMode = v
	if s.zmodemTimer != nil {
		s.zmodemTimer.Stop()
		s.zmodemTimer = nil
	}
	if !v {
		s.zmodemDeadline = time.Time{}
		return
	}
	generation := s.zmodemGeneration
	s.zmodemDeadline = time.Now().Add(zmodemModeTimeout)
	s.zmodemTimer = time.AfterFunc(zmodemModeTimeout, func() {
		s.mu.Lock()
		if s.zmodemMode && s.zmodemGeneration == generation {
			s.zmodemMode = false
			s.zmodemTimer = nil
			s.zmodemDeadline = time.Time{}
		}
		s.mu.Unlock()
	})
}

func (s *baseSession) IsZmodemMode() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.zmodemMode
}

func (s *baseSession) SetOnBinaryCallback(cb func([]byte)) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.onBinaryCallback = cb
}

func (s *baseSession) emitBinary(data []byte) {
	s.mu.Lock()
	cb := s.onBinaryCallback
	if s.zmodemMode {
		s.setZmodemModeLocked(true)
	}
	s.mu.Unlock()
	if cb != nil {
		cb(data)
	}
}

// looksLikeZmodemHeader reports whether data contains a ZMODEM frame header.
// A real header is ZPAD ZPAD ZDLE frame-type: `**` `\x18` `[A-C]`. The ZDLE
// (0x18) control byte is mandatory and effectively never appears in ordinary
// terminal output, so requiring it avoids false positives — e.g. vim rendering
// a file whose content contains `**` followed by a long hex string, which used
// to trip a looser heuristic and flip the session into binary mode, crashing
// the remote shell (issue #242).
func looksLikeZmodemHeader(data []byte) bool {
	for i := 0; i+3 < len(data); i++ {
		if data[i] == '*' && data[i+1] == '*' && data[i+2] == 0x18 &&
			data[i+3] >= 'A' && data[i+3] <= 'C' {
			return true
		}
	}
	return false
}

// RecordReadActivity updates the last-read timestamp for idle detection.
// Each session's readLoop should call this whenever data is received.
func (s *baseSession) RecordReadActivity() {
	s.lastReadTime.Store(time.Now().UnixNano())
	// Non-blocking signal to any waitIdle goroutine. A 1-slot buffer is
	// enough: waitIdle only cares that "something happened since the last
	// tick"; coalescing repeated signals is fine.
	ch, _ := s.idleSignalCh()
	select {
	case ch <- struct{}{}:
	default:
	}
}

// idleSignalCh returns the lazy-allocated idle signal channel.
func (s *baseSession) idleSignalCh() (chan struct{}, bool) {
	s.idleSignalOnce.Do(func() {
		s.idleSignal = make(chan struct{}, 1)
	})
	return s.idleSignal, true
}

// idleSince reports how long since the last read activity. Returns -1 if no
// read has ever been recorded. Used for disconnect diagnostics.
func (s *baseSession) idleSince() time.Duration {
	ns := s.lastReadTime.Load()
	if ns == 0 {
		return -1
	}
	return time.Since(time.Unix(0, ns))
}

// waitIdle blocks until no read activity has occurred for the given idle
// duration, or the overall timeout expires. It returns true on idle detection.
// Implemented with a 1-slot signal channel + idle timer instead of a 50ms
// busy loop; RecordReadActivity pushes to the channel so we only wake when
// there is something to check (F-017).
func (s *baseSession) waitIdle(timeout, idle time.Duration) bool {
	deadline := time.Now().Add(timeout)
	ch, _ := s.idleSignalCh()
	for {
		last := time.Unix(0, s.lastReadTime.Load())
		if !last.IsZero() && time.Since(last) >= idle {
			return true
		}
		remaining := time.Until(deadline)
		if remaining <= 0 {
			return false
		}
		// Cap the inner wait so a stream of activity can't starve the
		// deadline check; idle granularity is the dominant signal.
		wait := idle
		if wait > remaining {
			wait = remaining
		}
		select {
		case <-ch:
			// Activity happened — re-check the timestamp on next loop.
		case <-time.After(wait):
			// Either we sat idle past `idle`, or the deadline is close;
			// fall through and let the timestamp check decide.
		}
	}
}

// RunPostLoginScript sends each non-empty line of script after the terminal
// output goes idle, and waits for idle between commands. Stops early if ctx
// is cancelled or isConnected returns false.
func (s *baseSession) RunPostLoginScript(ctx context.Context, script string, send func([]byte), isConnected func() bool) {
	if strings.TrimSpace(script) == "" {
		return
	}
	// Wait for shell to finish initialization.
	if !s.waitIdle(5*time.Second, 300*time.Millisecond) {
		return
	}
	lines := strings.Split(script, "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		select {
		case <-ctx.Done():
			return
		default:
		}
		if !isConnected() {
			return
		}
		send([]byte(line + "\r"))
		// Wait for command output to settle.
		if !s.waitIdle(3*time.Second, 300*time.Millisecond) {
			return
		}
	}
}
