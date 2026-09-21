package session

// TunnelMode is the kind of SSH port forwarding a tunnel performs.
//
// It is a stable, non-localized enum persisted to disk and shown (as-is) in the
// picker. The UI never translates these values; only their descriptions go
// through i18n.
type TunnelMode string

const (
	// TunnelLocal forwards a local listening port to a destination host:port
	// reached from the exit SSH connection (ssh -L).
	TunnelLocal TunnelMode = "local"
	// TunnelRemote listens on the exit host and forwards back to a local
	// destination host:port (ssh -R).
	TunnelRemote TunnelMode = "remote"
	// TunnelDynamic runs a local SOCKS5 proxy whose connections egress through
	// the exit SSH connection (ssh -D). The SOCKS5 server runs on this machine;
	// nothing is installed on the server.
	TunnelDynamic TunnelMode = "dynamic"
)

// SocksProxy is an optional upstream proxy used as the entry point of a tunnel's
// chain: the first SSH hop is dialed through this proxy instead of directly.
type SocksProxy struct {
	Kind string `json:"kind"` // "socks5" | "http"
	Host string `json:"host"`
	Port int    `json:"port"`
	User string `json:"user,omitempty"`
	Pass string `json:"pass,omitempty"`
}

// Tunnel is one user-configured SSH tunnel. The proxy chain is implicit: it
// recurses the exit connection's own jump host (ConnectionConfig.TunnelSSHConnID)
// — no jump host means a single hop straight to the exit.
type Tunnel struct {
	ID        string     `json:"id"`
	Name      string     `json:"name"`
	Mode      TunnelMode `json:"mode"`
	SSHConnID string     `json:"sshConnId"` // exit SSH connection (ConnectionConfig.ID)

	// ListenHost/ListenPort: local bind for local/dynamic; remote bind for remote.
	ListenHost string `json:"listenHost,omitempty"` // default 127.0.0.1
	ListenPort int    `json:"listenPort"`

	// Target: destination for local; local service to forward back to for remote.
	// Unused for dynamic (SOCKS5 picks the destination per request).
	TargetHost string `json:"targetHost,omitempty"`
	TargetPort int    `json:"targetPort,omitempty"`

	Upstream  *SocksProxy `json:"upstream,omitempty"`
	AutoStart bool        `json:"autoStart,omitempty"`
	GroupID   string      `json:"groupId,omitempty"`
	SortOrder int         `json:"sortOrder,omitempty"`
}

// TunnelGroup is a display grouping in the tunnels panel (like connection groups).
type TunnelGroup struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	SortOrder int    `json:"sortOrder,omitempty"`
}

// TunnelStoreData is the persisted shape of tunnels.json.
type TunnelStoreData struct {
	Version int           `json:"version"`
	Groups  []TunnelGroup `json:"groups"`
	Tunnels []Tunnel      `json:"tunnels"`
}

// TunnelStatus is a tunnel's runtime lifecycle state (not persisted).
type TunnelStatus string

const (
	TunnelStopped TunnelStatus = "stopped"
	TunnelRunning TunnelStatus = "running"
	TunnelError   TunnelStatus = "error"
)

// TunnelState is the runtime state of a tunnel, pushed to the frontend via the
// "tunnel:state" event.
type TunnelState struct {
	ID        string       `json:"id"`
	Status    TunnelStatus `json:"status"`
	LocalPort int          `json:"localPort,omitempty"` // effective listen port once running
	Error     string       `json:"error,omitempty"`
}
