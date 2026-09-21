package k8s

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"net"
	"net/http"
	"os"
	"time"
)

// DialFunc 是 http.Transport.DialContext 的签名，用于把到 apiserver 的
// TCP 拨号劫持到本地回环端口（例如 SSH 隧道的本地转发口）。
type DialFunc func(ctx context.Context, network, addr string) (net.Conn, error)

// BuildClient 根据 kubeconfig + context 名构造 *http.Client 和 base URL。
// 认证信息（token / client cert）通过 transport 层的自定义 RoundTripper 注入。
func BuildClient(kc *Kubeconfig, ctxName string) (*http.Client, string, error) {
	client, base, _, _, err := BuildClientWithDial(kc, ctxName, nil)
	return client, base, err
}

// BuildClientWithDial 同 BuildClient，但可选注入 dialOverride：非 nil 时
// 覆盖 http.Transport.DialContext。TLS 配置保持不变，SNI/证书校验继续按
// kubeconfig 里的 hostname 走，只是底层 TCP 拨到别处。
// 额外返回 token 与 *tls.Config，供 exec 等 WebSocket 场景复用同一套认证/TLS。
func BuildClientWithDial(kc *Kubeconfig, ctxName string, dialOverride DialFunc) (*http.Client, string, string, *tls.Config, error) {
	if kc == nil {
		return nil, "", "", nil, fmt.Errorf("kubeconfig nil")
	}
	ctx, ok := kc.Contexts[ctxName]
	if !ok {
		return nil, "", "", nil, fmt.Errorf("context %q not found", ctxName)
	}
	cluster, ok := kc.Clusters[ctx.Cluster]
	if !ok {
		return nil, "", "", nil, fmt.Errorf("cluster %q not found", ctx.Cluster)
	}
	user, ok := kc.Users[ctx.User]
	if !ok {
		return nil, "", "", nil, fmt.Errorf("user %q not found", ctx.User)
	}

	tlsCfg, err := buildTLSConfig(cluster, user)
	if err != nil {
		return nil, "", "", nil, err
	}
	base := &http.Transport{
		TLSClientConfig:       tlsCfg,
		Proxy:                 http.ProxyFromEnvironment,
		MaxIdleConns:          100,
		MaxIdleConnsPerHost:   10,
		IdleConnTimeout:       90 * time.Second,
		TLSHandshakeTimeout:   10 * time.Second,
		ResponseHeaderTimeout: 30 * time.Second,
		ExpectContinueTimeout: 2 * time.Second,
	}
	if dialOverride != nil {
		base.DialContext = dialOverride
	}
	client := &http.Client{
		Transport: &authRoundTripper{base: base, token: user.Token},
		Timeout:   0, // watch 需要长连接
	}
	return client, cluster.Server, user.Token, tlsCfg, nil
}

func buildTLSConfig(cluster clusterEntry, user userEntry) (*tls.Config, error) {
	cfg := &tls.Config{InsecureSkipVerify: cluster.InsecureSkipTLSVerify}

	// CA: 只有真正装载了 CA 才覆盖系统信任库，否则退回系统根证书。
	if !cluster.InsecureSkipTLSVerify {
		pool := x509.NewCertPool()
		hasCA := false
		if len(cluster.CertificateAuthorityData) > 0 {
			if !pool.AppendCertsFromPEM(cluster.CertificateAuthorityData) {
				return nil, fmt.Errorf("append CA from data failed")
			}
			hasCA = true
		} else if cluster.CertificateAuthorityFile != "" {
			b, err := os.ReadFile(cluster.CertificateAuthorityFile)
			if err != nil {
				return nil, fmt.Errorf("read CA file: %w", err)
			}
			if !pool.AppendCertsFromPEM(b) {
				return nil, fmt.Errorf("append CA from file failed")
			}
			hasCA = true
		}
		if hasCA {
			cfg.RootCAs = pool
		}
	}

	// client cert
	certPEM, keyPEM, err := resolveClientCert(user)
	if err != nil {
		return nil, err
	}
	if (len(certPEM) > 0) != (len(keyPEM) > 0) {
		return nil, fmt.Errorf("client cert requires both certificate and key")
	}
	if len(certPEM) > 0 && len(keyPEM) > 0 {
		pair, err := tls.X509KeyPair(certPEM, keyPEM)
		if err != nil {
			return nil, fmt.Errorf("client cert: %w", err)
		}
		cfg.Certificates = []tls.Certificate{pair}
	}
	return cfg, nil
}

func resolveClientCert(user userEntry) ([]byte, []byte, error) {
	var certPEM, keyPEM []byte
	if len(user.ClientCertificateData) > 0 {
		certPEM = user.ClientCertificateData
	} else if user.ClientCertificateFile != "" {
		b, err := os.ReadFile(user.ClientCertificateFile)
		if err != nil {
			return nil, nil, fmt.Errorf("read client cert: %w", err)
		}
		certPEM = b
	}
	if len(user.ClientKeyData) > 0 {
		keyPEM = user.ClientKeyData
	} else if user.ClientKeyFile != "" {
		b, err := os.ReadFile(user.ClientKeyFile)
		if err != nil {
			return nil, nil, fmt.Errorf("read client key: %w", err)
		}
		keyPEM = b
	}
	return certPEM, keyPEM, nil
}

// authRoundTripper 每次请求前注入 Authorization。Tokens can rotate, so
// a 401 response must surface to a single retry with a refreshed token
// (K8S-01 / K8S-09).
type authRoundTripper struct {
	base        http.RoundTripper
	token       string
	refreshTok  func() (string, error) // optional; called on 401 to fetch a new token
}

func (a *authRoundTripper) RoundTrip(req *http.Request) (*http.Response, error) {
	// Clone the request so the caller's header map is never mutated
	// (K8S-09) — would otherwise block any future 401-retry path.
	req = req.Clone(req.Context())
	if a.token != "" && req.Header.Get("Authorization") == "" {
		req.Header.Set("Authorization", "Bearer "+a.token)
	}
	resp, err := a.base.RoundTrip(req)
	if err != nil {
		return resp, err
	}
	if resp.StatusCode != http.StatusUnauthorized || a.refreshTok == nil {
		return resp, nil
	}
	// Token rotated (or stale). Refresh and retry once.
	resp.Body.Close()
	newToken, rerr := a.refreshTok()
	if rerr != nil || newToken == "" {
		// Surface the original 401; refresh failure shouldn't lose data.
		return a.base.RoundTrip(req.Clone(req.Context()))
	}
	a.token = newToken
	retry := req.Clone(req.Context())
	retry.Header.Set("Authorization", "Bearer "+a.token)
	return a.base.RoundTrip(retry)
}

var _ = time.Second // 保留 time import 便于后续使用
