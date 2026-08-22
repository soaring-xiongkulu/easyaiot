package nacos

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"
)

// Instance is a Nacos naming instance.
type Instance struct {
	IP     string
	Port   int
	Healthy bool
}

// ListHealthyInstances lists healthy instances for a service.
func ListHealthyInstances(service string) ([]Instance, error) {
	server := strings.TrimSpace(os.Getenv("NACOS_SERVER"))
	if server == "" {
		return nil, fmt.Errorf("NACOS_SERVER empty")
	}
	if service == "" {
		service = getenv("POST_NACOS_SERVICE", "easyaiot-post")
	}
	if !strings.Contains(server, "://") {
		server = "http://" + server
	}
	server = strings.TrimRight(server, "/")
	q := url.Values{}
	q.Set("serviceName", service)
	q.Set("healthyOnly", "true")
	q.Set("groupName", getenv("NACOS_GROUP", "DEFAULT_GROUP"))
	if ns := os.Getenv("NACOS_NAMESPACE"); ns != "" {
		q.Set("namespaceId", ns)
	}
	q.Set("username", getenv("NACOS_USERNAME", "nacos"))
	q.Set("password", getenv("NACOS_PASSWORD", "nacos"))
	u := fmt.Sprintf("%s/nacos/v1/ns/instance/list?%s", server, q.Encode())
	client := &http.Client{Timeout: 3 * time.Second}
	resp, err := client.Get(u)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 300 {
		return nil, fmt.Errorf("nacos list HTTP %d: %s", resp.StatusCode, string(body))
	}
	var raw map[string]any
	if err := json.Unmarshal(body, &raw); err != nil {
		return nil, err
	}
	hosts, _ := raw["hosts"].([]any)
	var out []Instance
	for _, h := range hosts {
		m, ok := h.(map[string]any)
		if !ok {
			continue
		}
		ip, _ := m["ip"].(string)
		port := 0
		switch p := m["port"].(type) {
		case float64:
			port = int(p)
		case string:
			port, _ = strconv.Atoi(p)
		}
		healthy := true
		if v, ok := m["healthy"].(bool); ok {
			healthy = v
		}
		if ip != "" && port > 0 && healthy {
			out = append(out, Instance{IP: ip, Port: port, Healthy: true})
		}
	}
	return out, nil
}
