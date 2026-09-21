package importer

import (
	"bytes"
	"strconv"
	"strings"

	"github.com/kevinburke/ssh_config"
	"easyaiot/terminal/backend/session"
)

// NOTE: corrected against ssh_config v1.2.0's real API — Host.Patterns is a
// []*Pattern slice (not Host.Pattern), Node exposes String() not Value(), and
// there is no ParsePort (use strconv.Atoi).
func parseOpenSSH(data []byte) (*ImportResult, error) {
	cfg, err := ssh_config.Decode(bytes.NewReader(data))
	if err != nil {
		return nil, err
	}
	res := &ImportResult{}
	seen := map[string]bool{}
	for _, host := range cfg.Hosts {
		for _, pat := range host.Patterns {
			name := pat.String()
			// Skip wildcard/negated patterns (also skips the implicit "Host *").
			if name == "" || strings.ContainsAny(name, "*?!") {
				continue
			}
			if seen[name] {
				continue
			}
			seen[name] = true
			hostname, _ := cfg.Get(name, "HostName")
			portStr, _ := cfg.Get(name, "Port")
			user, _ := cfg.Get(name, "User")
			keyPath, _ := cfg.Get(name, "IdentityFile")
			port := 22
			if p, err := strconv.Atoi(portStr); err == nil && p > 0 {
				port = p
			}
			conn := session.ConnectionConfig{
				ID: newConnectionID(), Name: name, Type: "ssh", Host: hostname, Port: port, User: user,
			}
			if keyPath != "" {
				conn.AuthType = "key"
				conn.KeyPath = keyPath
			} else {
				conn.AuthType = "password"
			}
			res.Connections = append(res.Connections, conn)
		}
	}
	return res, nil
}
