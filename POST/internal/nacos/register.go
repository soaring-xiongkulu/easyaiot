package nacos

import (
	"fmt"
	"io"
	"log/slog"
	"net"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

// Registrar registers POST instance to Nacos after ready.
type Registrar struct {
	Server    string
	Namespace string
	Username  string
	Password  string
	Service   string
	IP        string
	Port      int
	Group     string

	mu       sync.Mutex
	registered bool
	stopCh   chan struct{}
	client   *http.Client
}

func NewRegistrarFromEnv(httpAddr string) *Registrar {
	server := strings.TrimSpace(os.Getenv("NACOS_SERVER"))
	if server == "" {
		return nil
	}
	port := 8089
	if strings.HasPrefix(httpAddr, ":") {
		if p, err := strconv.Atoi(strings.TrimPrefix(httpAddr, ":")); err == nil {
			port = p
		}
	}
	ip := strings.TrimSpace(os.Getenv("POD_IP"))
	if ip == "" {
		ip = strings.TrimSpace(os.Getenv("HOST_IP"))
	}
	if ip == "" {
		ip = detectLocalIP()
	}
	return &Registrar{
		Server:    server,
		Namespace: os.Getenv("NACOS_NAMESPACE"),
		Username:  getenv("NACOS_USERNAME", "nacos"),
		Password:  getenv("NACOS_PASSWORD", "nacos"),
		Service:   getenv("POST_NACOS_SERVICE", "easyaiot-post"),
		IP:        ip,
		Port:      port,
		Group:     getenv("NACOS_GROUP", "DEFAULT_GROUP"),
		stopCh:    make(chan struct{}),
		client:    &http.Client{Timeout: 5 * time.Second},
	}
}

func getenv(k, d string) string {
	if v := strings.TrimSpace(os.Getenv(k)); v != "" {
		return v
	}
	return d
}

func detectLocalIP() string {
	conn, err := net.Dial("udp", "8.8.8.8:80")
	if err != nil {
		return "127.0.0.1"
	}
	defer conn.Close()
	return conn.LocalAddr().(*net.UDPAddr).IP.String()
}

func (r *Registrar) baseURL() string {
	s := r.Server
	if !strings.Contains(s, "://") {
		s = "http://" + s
	}
	return strings.TrimRight(s, "/")
}

func (r *Registrar) Register() error {
	if r == nil {
		return nil
	}
	q := url.Values{}
	q.Set("serviceName", r.Service)
	q.Set("ip", r.IP)
	q.Set("port", strconv.Itoa(r.Port))
	q.Set("healthy", "true")
	q.Set("enable", "true")
	q.Set("weight", "1")
	q.Set("ephemeral", "true")
	q.Set("groupName", r.Group)
	if r.Namespace != "" {
		q.Set("namespaceId", r.Namespace)
	}
	q.Set("username", r.Username)
	q.Set("password", r.Password)
	u := fmt.Sprintf("%s/nacos/v1/ns/instance?%s", r.baseURL(), q.Encode())
	req, err := http.NewRequest(http.MethodPost, u, nil)
	if err != nil {
		return err
	}
	resp, err := r.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 300 {
		return fmt.Errorf("nacos register HTTP %d: %s", resp.StatusCode, string(body))
	}
	r.mu.Lock()
	r.registered = true
	r.mu.Unlock()
	slog.Info("nacos_registered", "service", r.Service, "ip", r.IP, "port", r.Port)
	go r.beatLoop()
	return nil
}

func (r *Registrar) beatLoop() {
	t := time.NewTicker(5 * time.Second)
	defer t.Stop()
	for {
		select {
		case <-r.stopCh:
			return
		case <-t.C:
			_ = r.beat()
		}
	}
}

func (r *Registrar) beat() error {
	q := url.Values{}
	q.Set("serviceName", r.Service)
	q.Set("ip", r.IP)
	q.Set("port", strconv.Itoa(r.Port))
	q.Set("ephemeral", "true")
	q.Set("groupName", r.Group)
	if r.Namespace != "" {
		q.Set("namespaceId", r.Namespace)
	}
	q.Set("username", r.Username)
	q.Set("password", r.Password)
	// beat body: lightweight JSON
	beat := fmt.Sprintf(`{"serviceName":"%s","ip":"%s","port":%d,"ephemeral":true}`, r.Service, r.IP, r.Port)
	u := fmt.Sprintf("%s/nacos/v1/ns/instance/beat?%s", r.baseURL(), q.Encode())
	req, err := http.NewRequest(http.MethodPut, u, strings.NewReader("beat="+url.QueryEscape(beat)))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	resp, err := r.client.Do(req)
	if err != nil {
		slog.Warn("nacos_beat_failed", "err", err)
		return err
	}
	defer resp.Body.Close()
	io.Copy(io.Discard, resp.Body)
	return nil
}

func (r *Registrar) Deregister() {
	if r == nil {
		return
	}
	r.mu.Lock()
	ok := r.registered
	r.mu.Unlock()
	if !ok {
		return
	}
	close(r.stopCh)
	q := url.Values{}
	q.Set("serviceName", r.Service)
	q.Set("ip", r.IP)
	q.Set("port", strconv.Itoa(r.Port))
	q.Set("groupName", r.Group)
	if r.Namespace != "" {
		q.Set("namespaceId", r.Namespace)
	}
	q.Set("username", r.Username)
	q.Set("password", r.Password)
	u := fmt.Sprintf("%s/nacos/v1/ns/instance?%s", r.baseURL(), q.Encode())
	req, _ := http.NewRequest(http.MethodDelete, u, nil)
	resp, err := r.client.Do(req)
	if err != nil {
		slog.Warn("nacos_deregister_failed", "err", err)
		return
	}
	defer resp.Body.Close()
	io.Copy(io.Discard, resp.Body)
	slog.Info("nacos_deregistered", "service", r.Service, "ip", r.IP, "port", r.Port)
}
