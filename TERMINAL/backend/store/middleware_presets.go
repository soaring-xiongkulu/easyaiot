package store

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"

	"easyaiot/terminal/backend/session"
)

// Built-in "EasyAIoT Middleware" quick-access presets: one connection-group
// seeded into the connection store on first run so a fresh install can reach
// every middleware the EasyAIoT platform ships (databases, cache, S3, Docker,
// dashboards) with a double-click. Entries are ordinary connections with
// deterministic IDs — users can edit, move, favorite or delete them like any
// other connection.
//
// Hosts default to localhost (desktop deployment, middleware ports published
// on the host). The web/server deployment inside Docker sets
// EASYAIOT_MIDDLEWARE_HOST (host.docker.internal) via docker-compose.yml;
// per-service overrides (EASYAIOT_<SERVICE>_HOST) win over the global one.

const (
	// MiddlewarePresetsVersion bumps when the built-in roster changes: the
	// next start re-authors every preset connection (deterministic ID =
	// seeded by us) from the current roster — hosts, remarks and credentials
	// — and re-adds deleted ones. This is how roster fixes reach deployments
	// that seeded an earlier roster (v1 seeded before presets carried
	// passwords, leaving entries that could never authenticate). Only absent
	// IDs are restored between bumps, so day-to-day user edits to a preset
	// survive. User-created connections are never touched by either path.
	MiddlewarePresetsVersion = 3

	// marker file recording the highest seeded version, so a user who deleted
	// the group is not re-seeded on every start.
	middlewarePresetsMarker = "middleware-presets.json"

	// MiddlewarePresetGroupID is the deterministic group ID the presets land in.
	MiddlewarePresetGroupID = "preset-easyaiot-middleware"

	// MiddlewarePresetIDPrefix marks every seeded connection (the start page's
	// middleware section filters on it).
	MiddlewarePresetIDPrefix = "preset-easyaiot-"
)

type middlewarePresetMarkerData struct {
	Version int `json:"version"`
}

// EnsureMiddlewarePresets idempotently seeds the preset group + connections.
// Best-effort by callers: when the credential vault is locked the password
// fields cannot be encrypted yet, Save fails, and seeding retries on the next
// unlock/start. Returns nil when the marker already matches the version.
// The bool reports whether the store was modified (seeds added or an older
// marker triggered a roster refresh), so callers can push the change to
// listeners whose in-memory copy would otherwise stale-write over it.
func EnsureMiddlewarePresets(dataDir string, cs *ConnectionStore, uiLang string) (bool, error) {
	if cs == nil {
		return false, nil
	}
	markerPath := filepath.Join(dataDir, middlewarePresetsMarker)
	refresh := false
	if b, err := os.ReadFile(markerPath); err == nil {
		var m middlewarePresetMarkerData
		if json.Unmarshal(b, &m) == nil {
			if m.Version >= MiddlewarePresetsVersion {
				return false, nil
			}
			// Marker from an earlier roster version: refresh existing preset
			// entries below instead of only backfilling absent ones.
			refresh = true
		}
	}

	data, err := cs.Load()
	if err != nil {
		return false, fmt.Errorf("load connections: %w", err)
	}

	changed := false
	groupExists := false
	for _, g := range data.Groups {
		if g.ID == MiddlewarePresetGroupID {
			groupExists = true
			break
		}
	}
	if !groupExists {
		data.Groups = append(data.Groups, session.ConnectionGroup{
			ID:   MiddlewarePresetGroupID,
			Name: middlewareGroupName(uiLang),
		})
		changed = true
	}

	// ID → index into data.Connections. Refresh mutates through the index
	// rather than a captured pointer: the appends below can reallocate the
	// backing array and leave pointers pointing at the old copy.
	existing := make(map[string]int, len(data.Connections))
	for i, c := range data.Connections {
		existing[c.ID] = i
	}
	gid := MiddlewarePresetGroupID
	for _, p := range MiddlewarePresets() {
		p.GroupId = &gid
		if idx, ok := existing[p.ID]; ok {
			// Present: touch it only on a version-bump refresh. Between bumps
			// the entry may carry user edits and is left alone.
			if refresh && !reflect.DeepEqual(data.Connections[idx], p) {
				data.Connections[idx] = p
				changed = true
			}
			continue
		}
		data.Connections = append(data.Connections, p)
		changed = true
	}

	if changed {
		if err := cs.Save(data); err != nil {
			return false, fmt.Errorf("save seeded presets: %w", err)
		}
	}
	b, err := json.Marshal(middlewarePresetMarkerData{Version: MiddlewarePresetsVersion})
	if err != nil {
		return changed, err
	}
	return changed, atomicWriteFile(markerPath, b, 0644)
}

// middlewareGroupName localizes the preset group name; unknown languages fall
// back to English (same convention as the tray labels in main.go).
func middlewareGroupName(lang string) string {
	switch lang {
	case "zh-CN":
		return "EasyAIoT 中间件"
	case "zh-TW":
		return "EasyAIoT 中間件"
	default:
		return "EasyAIoT Middleware"
	}
}

// middlewareHost resolves the target host for one middleware service:
// EASYAIOT_<SERVICE>_HOST override, then EASYAIOT_MIDDLEWARE_HOST, then
// localhost.
func middlewareHost(service string) string {
	if v := strings.TrimSpace(os.Getenv("EASYAIOT_" + service + "_HOST")); v != "" {
		return v
	}
	if v := strings.TrimSpace(os.Getenv("EASYAIOT_MIDDLEWARE_HOST")); v != "" {
		return v
	}
	return "localhost"
}

// middlewareURL builds an http URL for a dashboard preset. An override that
// already carries a scheme is treated as a complete base URL (its own port
// wins); a bare host gets the service's default port. The service's path
// suffix (/nacos) is appended unless the override already ends with it, so
// users can paste either the bare base or the full console address.
func middlewareURL(service string, port int, path string) string {
	host := middlewareHost(service)
	if strings.Contains(host, "://") {
		base := strings.TrimSuffix(host, "/")
		if path != "" && strings.HasSuffix(base, path) {
			return base
		}
		return base + path
	}
	return fmt.Sprintf("http://%s:%d%s", host, port, path)
}

// s3Endpoint mirrors the new-connection form's S3 Endpoint field: a full URL.
// Bare-host overrides still get the RustFS S3 API port.
func s3Endpoint(service string, port int) string {
	host := middlewareHost(service)
	if strings.Contains(host, "://") {
		return strings.TrimSuffix(host, "/")
	}
	return fmt.Sprintf("http://%s:%d", host, port)
}

// preset builds one seeded connection with the shared defaults filled in.
func preset(id, name, remark, typ, host string, port int, mutate func(*session.ConnectionConfig)) session.ConnectionConfig {
	c := session.ConnectionConfig{
		ID:       MiddlewarePresetIDPrefix + id,
		Name:     name,
		Remark:   remark,
		Type:     typ,
		Host:     host,
		Port:     port,
		AuthType: "password",
	}
	if mutate != nil {
		mutate(&c)
	}
	return c
}

// MiddlewarePresets returns the built-in roster, resolved against the current
// environment. Deterministic IDs make seeding and version upgrades idempotent.
func MiddlewarePresets() []session.ConnectionConfig {
	return []session.ConnectionConfig{
		// ── In-app interactive clients ──
		preset("postgres", "PostgreSQL", "EasyAIoT 主业务 PostgreSQL · 一条连接浏览全部库（iot-device20 / iot-node20 / iot-visualize20 / iot-flow20 / iot-message20 / iot-gb2818120 / iot-ai20 / iot-video20 / iot-transform20 / ruoyi-vue-pro20），默认打开 iot-device20",
			"database", middlewareHost("POSTGRES"), 5432, func(c *session.ConnectionConfig) {
				c.User = "postgres"
				c.Password = "iot45722414822"
				c.DBType = "postgres"
				c.DBName = "iot-device20"
			}),
		preset("mysql", "MySQL", "EasyAIoT 辅助 MySQL（.scripts/mysql）",
			"database", middlewareHost("MYSQL"), 3306, func(c *session.ConnectionConfig) {
				c.User = "root"
				c.Password = "iot45722414822"
				c.DBType = "mysql"
			}),
		preset("redis", "Redis", "EasyAIoT 缓存 / 会话 · db0",
			"redis", middlewareHost("REDIS"), 6379, func(c *session.ConnectionConfig) {
				c.Password = "basiclab@iot975248395"
			}),
		preset("rustfs-s3", "RustFS (S3)", "S3 兼容对象存储 · 桶: snap-space / dataset / iot / sam-models · 控制台 :9001",
			"s3", s3Endpoint("RUSTFS", 9000), 9000, func(c *session.ConnectionConfig) {
				c.User = "minioadmin"
				c.Password = "basiclab@iot975248395"
				c.S3Region = "us-east-1"
				c.S3URLStyle = "path"
			}),
		preset("docker", "Docker", "本机容器管理 · postgres-server / redis-server / kafka-server / emqx-server / nacos-server / rustfs-server / tdengine-server / milvus-server / srs-server / zlmediakit-server …",
			"container", "localhost", 0, func(c *session.ConnectionConfig) {
				c.ContainerTransport = "local"
				c.ContainerRuntime = "docker"
			}),
		preset("tdengine", "TDengine", "时序库 iot_device · root/taosdata · 打开即进入容器内 taos shell",
			"local", "localhost", 0, func(c *session.ConnectionConfig) {
				c.PostLoginScript = "docker exec -it tdengine-server taos"
			}),
		preset("kafka", "Kafka", "localhost:9092（容器网络内）· 9094（宿主 EXTERNAL listener）· 打开即进入容器内 CLI",
			"local", "localhost", 0, func(c *session.ConnectionConfig) {
				c.PostLoginScript = "docker exec -it kafka-server bash"
			}),

		// ── Web dashboards (double-click opens the system browser) ──
		preset("nacos", "Nacos Console", "注册/配置中心 · nacos / basiclab@iot78475418754 · 命名空间 public",
			"url", middlewareURL("NACOS", 8848, "/nacos"), 8848, nil),
		preset("emqx", "EMQX Dashboard", "MQTT Broker · 管理台 admin / basiclab@iot6874125784 · MQTT 客户端 emqx / 123456 @ :1883",
			"url", middlewareURL("EMQX", 18083, ""), 18083, nil),
		preset("rustfs-console", "RustFS Console", "对象存储控制台 · minioadmin / basiclab@iot975248395",
			"url", middlewareURL("RUSTFS", 9001, ""), 9001, nil),
		preset("nodered", "Node-RED", "规则流引擎 · http 无需登录",
			"url", middlewareURL("NODERED", 1880, ""), 1880, nil),
		preset("fuxa", "FUXA SCADA", "Web SCADA 组态 · admin / 123456",
			"url", middlewareURL("FUXA", 1881, ""), 1881, nil),
		preset("zlmediakit", "ZLMediaKit", "GB28181 流媒体 · API secret: AdJQu9CMnwZvCc139s8lF0F9dhk6sNXG",
			"url", middlewareURL("ZLMEDIAKIT", 6080, ""), 6080, nil),
		preset("srs", "SRS Streaming", "RTMP/WebRTC 流媒体 · RTMP :1935 · HTTP-FLV/HLS :8080 · API :1985 · WebRTC :8000/udp",
			"url", middlewareURL("SRS", 8080, ""), 8080, nil),
	}
}
