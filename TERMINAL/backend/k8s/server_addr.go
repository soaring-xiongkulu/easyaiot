package k8s

import (
	"fmt"
	"net"
	"net/url"
	"strconv"
)

// ParseServerAddr 从 kubeconfig 的 cluster.Server（例如 "https://foo:6443/path"）
// 解出 host/port，端口缺省时按 scheme 补齐。
func ParseServerAddr(server string) (string, int, error) {
	u, err := url.Parse(server)
	if err != nil {
		return "", 0, fmt.Errorf("parse server url: %w", err)
	}
	if u.Host == "" {
		return "", 0, fmt.Errorf("server url missing host: %q", server)
	}
	host := u.Hostname()
	if host == "" {
		return "", 0, fmt.Errorf("server url missing host: %q", server)
	}
	if p := u.Port(); p != "" {
		port, err := strconv.Atoi(p)
		if err != nil {
			return "", 0, fmt.Errorf("invalid port %q: %w", p, err)
		}
		return host, port, nil
	}
	switch u.Scheme {
	case "https":
		return host, 443, nil
	case "http":
		return host, 80, nil
	default:
		return "", 0, fmt.Errorf("unsupported scheme %q", u.Scheme)
	}
}

// LocalAddr 拼 127.0.0.1:port，避免调用方各处重复。
func LocalAddr(port int) string {
	return net.JoinHostPort("127.0.0.1", strconv.Itoa(port))
}
