package config

import (
	"bufio"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

// Config holds POST runtime configuration from environment.
type Config struct {
	MQTTBroker         string
	MQTTUsername       string
	MQTTPassword       string
	MQTTClientIDPrefix string
	MQTTShareGroup     string

	TopicInferEvent  string
	TopicLegacyAlert string
	TopicSnapshotAlert string
	TopicAlertFinal  string
	TopicTaskSync    string
	TopicTrace       string

	PublishOptionalFinal bool

	DatabaseURL string

	TaskCacheTTL   time.Duration
	HTTPAddr       string
	AdminToken     string
	Debug          bool
	DebugHTTP      bool
	Enabled        bool
	InstanceID     string
	Timezone       string

	NacosServer    string
	NacosNamespace string
	NacosUsername  string
	NacosPassword  string
	NacosService   string

	UserScriptURL      string
	PluginHTTPTimeout  time.Duration
}

func getenv(key, def string) string {
	if v := strings.TrimSpace(os.Getenv(key)); v != "" {
		return v
	}
	return def
}

func getenvBool(key string, def bool) bool {
	v := strings.TrimSpace(os.Getenv(key))
	if v == "" {
		return def
	}
	switch strings.ToLower(v) {
	case "1", "true", "yes", "on":
		return true
	case "0", "false", "no", "off":
		return false
	default:
		return def
	}
}

func getenvInt(key string, def int) int {
	v := strings.TrimSpace(os.Getenv(key))
	if v == "" {
		return def
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return def
	}
	return n
}

// Load reads configuration from environment variables.
// 本地 IDEA/`go run` 不会自动带 Docker env_file，因此先尝试加载 POST/.env（不覆盖已有环境变量）。
func Load() Config {
	loadDotEnv()

	host, _ := os.Hostname()
	pid := os.Getpid()
	prefix := getenv("MQTT_CLIENT_ID_PREFIX", "post")
	instance := getenv("POST_INSTANCE_ID", prefix+"-"+host+"-"+strconv.Itoa(pid))

	ttlSec := getenvInt("TASK_CACHE_TTL_SEC", 300)
	if ttlSec < 60 {
		ttlSec = 60
	}

	return Config{
		MQTTBroker:         getenv("MQTT_BROKER", "tcp://127.0.0.1:1883"),
		MQTTUsername:       os.Getenv("MQTT_USERNAME"),
		MQTTPassword:       os.Getenv("MQTT_PASSWORD"),
		MQTTClientIDPrefix: prefix,
		MQTTShareGroup:     getenv("MQTT_SHARE_GROUP", "post"),

		TopicInferEvent:    getenv("TOPIC_INFER_EVENT", "mqtt/iot-infer-event"),
		TopicLegacyAlert:   getenv("TOPIC_LEGACY_ALERT", "mqtt/iot-alert-notification"),
		TopicSnapshotAlert: getenv("TOPIC_SNAPSHOT_ALERT", "mqtt/iot-snapshot-alert"),
		TopicAlertFinal:    getenv("TOPIC_ALERT_FINAL", "mqtt/iot-alert-final"),
		TopicTaskSync:      getenv("TOPIC_TASK_SYNC", "mqtt/iot-post-task-sync"),
		TopicTrace:         getenv("TOPIC_POST_TRACE", "mqtt/iot-post-trace"),

		PublishOptionalFinal: getenvBool("POST_PUBLISH_OPTIONAL_FINAL", false),

		DatabaseURL: NormalizePostgresURL(os.Getenv("DATABASE_URL")),

		TaskCacheTTL: time.Duration(ttlSec) * time.Second,
		HTTPAddr:     getenv("POST_HTTP_ADDR", ":8089"),
		AdminToken:   os.Getenv("POST_ADMIN_TOKEN"),
		Debug:        getenvBool("POST_DEBUG", false),
		DebugHTTP:    getenvBool("POST_DEBUG_HTTP", true),
		Enabled:      getenvBool("POST_ENABLED", true),
		InstanceID:   instance,
		Timezone:     getenv("TZ", "Asia/Shanghai"),

		NacosServer:    os.Getenv("NACOS_SERVER"),
		NacosNamespace: os.Getenv("NACOS_NAMESPACE"),
		NacosUsername:  getenv("NACOS_USERNAME", "nacos"),
		NacosPassword:  getenv("NACOS_PASSWORD", "nacos"),
		NacosService:   getenv("POST_NACOS_SERVICE", "easyaiot-post"),

		UserScriptURL:     os.Getenv("USER_SCRIPT_URL"),
		PluginHTTPTimeout: time.Duration(getenvInt("PLUGIN_HTTP_TIMEOUT_MS", 2000)) * time.Millisecond,
	}
}

func loadDotEnv() {
	seen := map[string]struct{}{}
	var cands []string
	if wd, err := os.Getwd(); err == nil {
		cands = append(cands,
			filepath.Join(wd, ".env"),
			filepath.Join(wd, "..", ".env"),
			filepath.Join(wd, "..", "..", ".env"),
		)
	}
	cands = append(cands, "POST/.env")
	for _, p := range cands {
		abs, err := filepath.Abs(p)
		if err != nil {
			continue
		}
		if _, ok := seen[abs]; ok {
			continue
		}
		seen[abs] = struct{}{}
		applyDotEnvFile(abs)
	}
}

// applyDotEnvFile sets KEY=VALUE from a dotenv file without overriding existing env.
func applyDotEnvFile(path string) {
	f, err := os.Open(path)
	if err != nil {
		return
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if strings.HasPrefix(line, "export ") {
			line = strings.TrimSpace(strings.TrimPrefix(line, "export "))
		}
		i := strings.IndexByte(line, '=')
		if i <= 0 {
			continue
		}
		key := strings.TrimSpace(line[:i])
		val := strings.TrimSpace(line[i+1:])
		if key == "" {
			continue
		}
		if len(val) >= 2 {
			if (val[0] == '"' && val[len(val)-1] == '"') || (val[0] == '\'' && val[len(val)-1] == '\'') {
				val = val[1 : len(val)-1]
			}
		}
		if os.Getenv(key) != "" {
			continue
		}
		_ = os.Setenv(key, val)
	}
}

// NormalizePostgresURL 补齐本地 Postgres 常用参数。
// lib/pq 默认 sslmode=require，而本仓库 Docker Postgres 未开 SSL，会导致
// "pq: SSL is not enabled on the server"。未显式指定时改为 disable。
func NormalizePostgresURL(raw string) string {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return raw
	}
	lower := strings.ToLower(raw)
	if strings.Contains(lower, "sslmode=") {
		return raw
	}
	if strings.Contains(raw, "://") {
		if strings.Contains(raw, "?") {
			return raw + "&sslmode=disable"
		}
		return raw + "?sslmode=disable"
	}
	return raw + " sslmode=disable"
}
