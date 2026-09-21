package session

// Proxy is a reusable outbound proxy (SOCKS5/HTTP) stored in proxies.json,
// mirroring Identity in the credential vault. Pass is decrypted in memory and
// encrypted at rest. Enabled is a tri-state: nil (missing in old JSON) counts
// as enabled so existing stores keep working after upgrade.
type Proxy struct {
	ID      string `json:"id"`
	Name    string `json:"name"`
	Kind    string `json:"kind"` // "socks5" | "http"
	Host    string `json:"host"`
	Port    int    `json:"port"`
	User    string `json:"user,omitempty"`
	Pass    string `json:"pass,omitempty"`
	Enabled *bool  `json:"enabled,omitempty"`
}

// IsActive reports whether the proxy should be honored on connect. A disabled
// proxy is skipped silently: connections referencing it dial directly.
func (p *Proxy) IsActive() bool { return p.Enabled == nil || *p.Enabled }

// ProxyStoreData is the top-level shape of proxies.json.
type ProxyStoreData struct {
	Proxies []Proxy `json:"proxies"`
}

// ProxyResolver resolves a Proxy ID into the runtime SocksProxy dial struct
// (Kind/Host/Port/User/Pass), consumed directly by dialFirstHop.
type ProxyResolver func(id string) (SocksProxy, bool)

// ProxyIDSystem is the sentinel proxy reference selecting the OS system proxy
// (registry/system config, PAC scripts, HTTP(S)_PROXY env fallback), resolved
// at connect/request time against the actual target and never persisted as a
// concrete proxy. Saved proxy IDs are generated as "px-..." so it never
// collides. An empty reference stays "dial direct".
const ProxyIDSystem = "system"
