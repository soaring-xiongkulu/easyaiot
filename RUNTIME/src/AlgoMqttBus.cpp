/*
 * Minimal MQTT 3.1.1 publisher (CONNECT + PUBLISH QoS1) — no external MQTT SDK.
 */

#include "AlgoMqttBus.h"

#include <glog/logging.h>
#include <httplib.h>
#include <json/json.h>

#include <arpa/inet.h>
#include <netdb.h>
#include <sys/socket.h>
#include <unistd.h>

#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <memory>
#include <random>
#include <sstream>
#include <thread>

namespace {

bool transportDisabled(const std::string& raw) {
    std::string v = raw;
    for (auto& c : v) {
        if (c >= 'A' && c <= 'Z') c = static_cast<char>(c - 'A' + 'a');
    }
    return v == "http" || v == "off" || v == "0" || v == "false" || v == "no";
}

std::string trimCopy(const std::string& s) {
    size_t b = 0;
    while (b < s.size() && (s[b] == ' ' || s[b] == '\t')) ++b;
    size_t e = s.size();
    while (e > b && (s[e - 1] == ' ' || s[e - 1] == '\t')) --e;
    return s.substr(b, e - b);
}

void appendU16(std::vector<uint8_t>& out, uint16_t v) {
    out.push_back(static_cast<uint8_t>((v >> 8) & 0xff));
    out.push_back(static_cast<uint8_t>(v & 0xff));
}

void appendMqttString(std::vector<uint8_t>& out, const std::string& s) {
    appendU16(out, static_cast<uint16_t>(s.size()));
    out.insert(out.end(), s.begin(), s.end());
}

void encodeRemainingLength(std::vector<uint8_t>& out, size_t len) {
    do {
        uint8_t byte = static_cast<uint8_t>(len % 128);
        len /= 128;
        if (len > 0) byte |= 0x80;
        out.push_back(byte);
    } while (len > 0);
}

bool sendAll(int fd, const uint8_t* data, size_t len) {
    size_t sent = 0;
    while (sent < len) {
        ssize_t n = ::send(fd, data + sent, len - sent, 0);
        if (n <= 0) return false;
        sent += static_cast<size_t>(n);
    }
    return true;
}

bool recvExact(int fd, uint8_t* data, size_t len) {
    size_t got = 0;
    while (got < len) {
        ssize_t n = ::recv(fd, data + got, len - got, 0);
        if (n <= 0) return false;
        got += static_cast<size_t>(n);
    }
    return true;
}

int tcpConnect(const std::string& host, int port) {
    struct addrinfo hints {};
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    struct addrinfo* res = nullptr;
    std::string portStr = std::to_string(port);
    if (getaddrinfo(host.c_str(), portStr.c_str(), &hints, &res) != 0 || !res) {
        return -1;
    }
    int fd = -1;
    for (auto* p = res; p; p = p->ai_next) {
        fd = ::socket(p->ai_family, p->ai_socktype, p->ai_protocol);
        if (fd < 0) continue;
        struct timeval tv {};
        tv.tv_sec = 5;
        tv.tv_usec = 0;
        setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
        setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
        if (::connect(fd, p->ai_addr, p->ai_addrlen) == 0) {
            break;
        }
        ::close(fd);
        fd = -1;
    }
    freeaddrinfo(res);
    return fd;
}

bool mqttPublishOnce(const std::string& host,
                     int port,
                     const std::string& clientId,
                     const std::string& username,
                     const std::string& password,
                     const std::string& topic,
                     const std::string& payload) {
    int fd = tcpConnect(host, port);
    if (fd < 0) {
        LOG(WARNING) << "[AlgoMqttBus] TCP connect failed " << host << ":" << port;
        return false;
    }

    // CONNECT
    std::vector<uint8_t> vh;
    appendMqttString(vh, "MQTT");
    vh.push_back(0x04);  // protocol level 4 (3.1.1)
    uint8_t flags = 0x02;  // clean session
    if (!username.empty()) flags |= 0x80;
    if (!password.empty()) flags |= 0x40;
    vh.push_back(flags);
    appendU16(vh, 30);  // keepalive
    appendMqttString(vh, clientId);
    if (!username.empty()) appendMqttString(vh, username);
    if (!password.empty()) appendMqttString(vh, password);

    std::vector<uint8_t> connectPkt;
    connectPkt.push_back(0x10);
    encodeRemainingLength(connectPkt, vh.size());
    connectPkt.insert(connectPkt.end(), vh.begin(), vh.end());
    if (!sendAll(fd, connectPkt.data(), connectPkt.size())) {
        ::close(fd);
        return false;
    }

    uint8_t connack[4];
    if (!recvExact(fd, connack, 4) || connack[0] != 0x20 || connack[3] != 0x00) {
        LOG(WARNING) << "[AlgoMqttBus] CONNACK failed broker=" << host << ":" << port;
        ::close(fd);
        return false;
    }

    // PUBLISH QoS1
    static std::atomic<uint16_t> packetIdGen{1};
    uint16_t packetId = packetIdGen.fetch_add(1);
    if (packetId == 0) packetId = packetIdGen.fetch_add(1);

    std::vector<uint8_t> pubVar;
    appendMqttString(pubVar, topic);
    appendU16(pubVar, packetId);
    pubVar.insert(pubVar.end(), payload.begin(), payload.end());

    std::vector<uint8_t> pubPkt;
    pubPkt.push_back(0x32);  // PUBLISH QoS1
    encodeRemainingLength(pubPkt, pubVar.size());
    pubPkt.insert(pubPkt.end(), pubVar.begin(), pubVar.end());
    if (!sendAll(fd, pubPkt.data(), pubPkt.size())) {
        ::close(fd);
        return false;
    }

    // PUBACK
    uint8_t puback[4];
    if (!recvExact(fd, puback, 4) || (puback[0] & 0xF0) != 0x40) {
        LOG(WARNING) << "[AlgoMqttBus] PUBACK missing/failed topic=" << topic;
        ::close(fd);
        return false;
    }

    // DISCONNECT
    uint8_t disc[2] = {0xE0, 0x00};
    sendAll(fd, disc, 2);
    ::close(fd);
    return true;
}

}  // namespace

bool AlgoMqttBus::busEnabled(const Config& config) {
    std::string transport = config.algoBusTransport;
    if (transport.empty()) {
        const char* env = std::getenv("ALGO_BUS_TRANSPORT");
        transport = env ? env : "";
    }
    return !transportDisabled(transport);
}

std::vector<std::pair<std::string, int>> AlgoMqttBus::resolveBrokers(const Config& config) {
    std::string raw = config.mqttBrokerUrls;
    if (raw.empty()) {
        const char* env = std::getenv("MQTT_BROKER_URLS");
        raw = env ? env : "";
    }
    std::vector<std::pair<std::string, int>> out;
    std::stringstream ss(raw);
    std::string part;
    while (std::getline(ss, part, ',')) {
        part = trimCopy(part);
        if (part.empty()) continue;
        if (part.rfind("tcp://", 0) == 0) part = part.substr(6);
        if (part.rfind("mqtt://", 0) == 0) part = part.substr(7);
        size_t colon = part.rfind(':');
        if (colon != std::string::npos && colon + 1 < part.size()) {
            try {
                int port = std::stoi(part.substr(colon + 1));
                out.emplace_back(part.substr(0, colon), port);
            } catch (...) {
                out.emplace_back(part, 1883);
            }
        } else {
            out.emplace_back(part, 1883);
        }
    }
    return out;
}

std::string AlgoMqttBus::makeUuid() {
    static thread_local std::mt19937_64 rng{std::random_device{}()};
    std::uniform_int_distribution<uint64_t> dist;
    uint64_t a = dist(rng);
    uint64_t b = dist(rng);
    char buf[40];
    std::snprintf(buf, sizeof(buf), "%08x-%04x-%04x-%04x-%012llx",
                  static_cast<unsigned>((a >> 32) & 0xffffffffu),
                  static_cast<unsigned>((a >> 16) & 0xffffu),
                  static_cast<unsigned>((a & 0x0fff) | 0x4000),
                  static_cast<unsigned>(((b >> 48) & 0x3fff) | 0x8000),
                  static_cast<unsigned long long>(b & 0xffffffffffffull));
    return std::string(buf);
}

std::string AlgoMqttBus::utcNowIso() {
    using clock = std::chrono::system_clock;
    auto now = clock::now();
    std::time_t t = clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()) % 1000;
    std::tm tm {};
    gmtime_r(&t, &tm);
    char buf[64];
    std::snprintf(buf, sizeof(buf), "%04d-%02d-%02dT%02d:%02d:%02d.%03lldZ",
                  tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday,
                  tm.tm_hour, tm.tm_min, tm.tm_sec,
                  static_cast<long long>(ms.count()));
    return std::string(buf);
}

std::string AlgoMqttBus::normalizeAlertPayload(const std::string& flatAlertJson,
                                               bool snapshot,
                                               const Config& config) {
    Json::Value root;
    Json::CharReaderBuilder rb;
    std::string errs;
    std::unique_ptr<Json::CharReader> reader(rb.newCharReader());
    if (!reader->parse(flatAlertJson.data(), flatAlertJson.data() + flatAlertJson.size(), &root, &errs)) {
        LOG(ERROR) << "[AlgoMqttBus] invalid alert json: " << errs;
        return "{}";
    }

    const std::string defaultTaskType = snapshot ? "snap" : "realtime";
    Json::Value payload;
    if (root.isMember("alert") && root["alert"].isObject()) {
        payload = root;
        if (!payload["alert"].isMember("task_type")) {
            payload["alert"]["task_type"] = payload.get("task_type", defaultTaskType).asString();
        }
    } else {
        Json::Value alert;
        alert["object"] = root.get("object", "object");
        alert["event"] = root.get("event", "detection");
        alert["region"] = root.get("region", "");
        alert["information"] = root.get("information", "");
        alert["image_path"] = root.isMember("image_path") ? root["image_path"] : root.get("imagePath", "");
        alert["record_path"] = root.isMember("record_path") ? root["record_path"] : root.get("recordPath", "");
        alert["time"] = root.get("time", "");
        alert["task_type"] = root.get("task_type", defaultTaskType).asString();

        payload["device_id"] = root.isMember("device_id") ? root["device_id"] : root.get("deviceId", "");
        payload["device_name"] = root.isMember("device_name") ? root["device_name"] : root.get("deviceName", "");
        payload["task_id"] = root.isMember("task_id") ? root["task_id"] : root.get("taskId", config.taskId);
        payload["task_name"] = root.isMember("task_name") ? root["task_name"] : root.get("taskName", "");
        payload["correlation_id"] = root.isMember("correlation_id") ? root["correlation_id"] : root.get("correlationId", "");
        payload["timestamp"] = root.isMember("timestamp") ? root["timestamp"] : root.get("time", "");
        payload["time"] = root.get("time", "");
        payload["task_type"] = alert["task_type"];
        payload["alert"] = alert;
    }

    std::string nodeId = config.computeNodeId;
    if (nodeId.empty()) {
        const char* env = std::getenv("COMPUTE_NODE_ID");
        if (!env || !*env) env = std::getenv("NODE_ID");
        if (env && *env) nodeId = env;
    }
    if (!nodeId.empty()) {
        payload["node_id"] = nodeId;
        payload["nodeId"] = nodeId;
    }

    Json::StreamWriterBuilder wb;
    wb["indentation"] = "";
    return Json::writeString(wb, payload);
}

bool AlgoMqttBus::publishRaw(const Config& config,
                             const std::string& topic,
                             const std::string& msgType,
                             const std::string& payloadJson) {
    if (!busEnabled(config)) return false;
    auto brokers = resolveBrokers(config);
    if (brokers.empty()) {
        LOG(WARNING) << "[AlgoMqttBus] MQTT_BROKER_URLS empty, skip topic=" << topic;
        return false;
    }

    std::string tenant = config.mqttTenant;
    if (tenant.empty()) {
        const char* env = std::getenv("MQTT_ALGO_TENANT");
        tenant = env && *env ? env : "default";
    }
    std::string username = config.mqttUsername;
    if (username.empty()) {
        const char* env = std::getenv("MQTT_ALGO_USERNAME");
        if (env) username = env;
    }
    std::string password = config.mqttPassword;
    if (password.empty()) {
        const char* env = std::getenv("MQTT_ALGO_PASSWORD");
        if (env) password = env;
    }
    std::string clientBase = config.mqttClientId;
    if (clientBase.empty()) {
        const char* env = std::getenv("MQTT_ALGO_CLIENT_ID");
        clientBase = env && *env ? env : "algo-runtime-bus";
    }
    std::string clientId = clientBase + "-pub-" + makeUuid().substr(0, 8);

    Json::Value envelope;
    envelope["version"] = "1.0";
    envelope["msgId"] = makeUuid();
    envelope["msgType"] = msgType;
    envelope["tenant"] = tenant;
    envelope["ts"] = utcNowIso();
    {
        Json::Value payload;
        Json::CharReaderBuilder rb;
        std::string errs;
        std::unique_ptr<Json::CharReader> reader(rb.newCharReader());
        if (!reader->parse(payloadJson.data(), payloadJson.data() + payloadJson.size(), &payload, &errs)) {
            LOG(ERROR) << "[AlgoMqttBus] payload parse failed: " << errs;
            return false;
        }
        envelope["payload"] = payload;
    }
    Json::StreamWriterBuilder wb;
    wb["indentation"] = "";
    std::string body = Json::writeString(wb, envelope);

    for (const auto& bp : brokers) {
        if (mqttPublishOnce(bp.first, bp.second, clientId, username, password, topic, body)) {
            LOG(INFO) << "[AlgoMqttBus] published topic=" << topic
                      << " broker=" << bp.first << ":" << bp.second;
            return true;
        }
    }
    LOG(ERROR) << "[AlgoMqttBus] all brokers failed topic=" << topic;
    return false;
}

bool AlgoMqttBus::publishAlert(const Config& config, const std::string& flatAlertJson, bool snapshot) {
    std::string payload = normalizeAlertPayload(flatAlertJson, snapshot, config);
    const char* topic = snapshot ? "mqtt/iot-snapshot-alert" : "mqtt/iot-alert-notification";
    const char* msgType = snapshot ? "alert.snapshot" : "alert.notification";
    return publishRaw(config, topic, msgType, payload);
}

bool AlgoMqttBus::publishPostProcess(const Config& config, const std::string& payloadJson) {
    return publishRaw(config, "mqtt/iot-post-process-request", "post_process.request", payloadJson);
}

bool AlgoMqttBus::postEnabled() {
    const char* env = std::getenv("POST_ENABLED");
    // v1.7 default true when unset for Phase1 cutover; empty treated as true
    if (!env || !*env) return true;
    std::string v(env);
    for (auto& c : v) {
        if (c >= 'A' && c <= 'Z') c = static_cast<char>(c - 'A' + 'a');
    }
    return v == "1" || v == "true" || v == "yes" || v == "on";
}

bool AlgoMqttBus::postFailoverOpen() {
    const char* env = std::getenv("POST_FAILOVER_OPEN");
    if (!env || !*env) return true;
    std::string v(env);
    for (auto& c : v) {
        if (c >= 'A' && c <= 'Z') c = static_cast<char>(c - 'A' + 'a');
    }
    return v == "1" || v == "true" || v == "yes" || v == "on";
}

std::string AlgoMqttBus::postBaseUrl() {
    const char* env = std::getenv("POST_BASE_URL");
    std::string u = (env && *env) ? env : "";
    while (!u.empty() && (u.back() == '/' || u.back() == ' ')) u.pop_back();
    return u;
}

int AlgoMqttBus::healthIntervalSec() {
    const char* env = std::getenv("POST_HEALTH_INTERVAL_SEC");
    if (!env || !*env) return 5;
    int n = std::atoi(env);
    return n > 0 ? n : 5;
}

int AlgoMqttBus::healthFailThreshold() {
    const char* env = std::getenv("POST_HEALTH_FAIL_THRESHOLD");
    if (!env || !*env) return 3;
    int n = std::atoi(env);
    return n > 0 ? n : 3;
}

namespace {
std::atomic<bool> g_postReady{true};
std::atomic<int> g_failStreak{0};
std::atomic<int> g_okStreak{0};
std::atomic<bool> g_healthStarted{false};

bool parseHttpUrlParts(const std::string& url, std::string& host, int& port, std::string& path) {
    // minimal http://host:port/path
    std::string u = url;
    if (u.rfind("http://", 0) == 0) u = u.substr(7);
    else if (u.rfind("https://", 0) == 0) u = u.substr(8);
    path = "/";
    auto slash = u.find('/');
    std::string hostPort = slash == std::string::npos ? u : u.substr(0, slash);
    if (slash != std::string::npos) path = u.substr(slash);
    auto colon = hostPort.rfind(':');
    if (colon != std::string::npos) {
        host = hostPort.substr(0, colon);
        port = std::atoi(hostPort.substr(colon + 1).c_str());
        if (port <= 0) port = 80;
    } else {
        host = hostPort;
        port = 80;
    }
    return !host.empty();
}

std::string envOr(const char* key, const char* def) {
    const char* v = std::getenv(key);
    if (v && *v) return std::string(v);
    return std::string(def);
}

bool probeReadyzAt(const std::string& base) {
    std::string host;
    int port = 80;
    std::string unusedPath = "/";
    if (!parseHttpUrlParts(base, host, port, unusedPath)) return false;
    httplib::Client cli(host, port);
    cli.set_connection_timeout(2, 0);
    cli.set_read_timeout(2, 0);
    auto res = cli.Get("/readyz");
    if (!res || res->status != 200) return false;
    Json::Value root;
    Json::CharReaderBuilder rb;
    std::string errs;
    std::unique_ptr<Json::CharReader> reader(rb.newCharReader());
    if (reader->parse(res->body.data(), res->body.data() + res->body.size(), &root, &errs)) {
        if (root.isMember("ready")) return root["ready"].asBool();
    }
    return true;
}

/** v1.9: Nacos list healthy_only for POST service; empty NACOS_SERVER → skip. */
bool nacosHasHealthyPost() {
    std::string server = envOr("NACOS_SERVER", "");
    if (server.empty()) return false;
    if (server.rfind("http://", 0) != 0 && server.rfind("https://", 0) != 0) {
        server = "http://" + server;
    }
    while (!server.empty() && server.back() == '/') server.pop_back();

    std::string host;
    int port = 8848;
    std::string path;
    if (!parseHttpUrlParts(server, host, port, path)) return false;

    std::string service = envOr("POST_NACOS_SERVICE", "easyaiot-post");
    std::string group = envOr("NACOS_GROUP", "DEFAULT_GROUP");
    std::string ns = envOr("NACOS_NAMESPACE", "");
    std::string user = envOr("NACOS_USERNAME", "nacos");
    std::string pass = envOr("NACOS_PASSWORD", "nacos");

    std::ostringstream qs;
    qs << "/nacos/v1/ns/instance/list?serviceName=" << httplib::detail::encode_query_param(service)
       << "&healthyOnly=true&groupName=" << httplib::detail::encode_query_param(group)
       << "&username=" << httplib::detail::encode_query_param(user)
       << "&password=" << httplib::detail::encode_query_param(pass);
    if (!ns.empty()) {
        qs << "&namespaceId=" << httplib::detail::encode_query_param(ns);
    }

    httplib::Client cli(host, port);
    cli.set_connection_timeout(2, 0);
    cli.set_read_timeout(2, 0);
    auto res = cli.Get(qs.str().c_str());
    if (!res || res->status != 200) return false;

    Json::Value root;
    Json::CharReaderBuilder rb;
    std::string errs;
    std::unique_ptr<Json::CharReader> reader(rb.newCharReader());
    if (!reader->parse(res->body.data(), res->body.data() + res->body.size(), &root, &errs)) {
        return false;
    }
    const Json::Value& hosts = root["hosts"];
    if (!hosts.isArray()) return false;
    for (const auto& h : hosts) {
        if (!h.isObject()) continue;
        bool healthy = true;
        if (h.isMember("healthy") && h["healthy"].isBool()) healthy = h["healthy"].asBool();
        std::string ip = h.get("ip", "").asString();
        int p = h.get("port", 0).asInt();
        if (healthy && !ip.empty() && p > 0) return true;
    }
    return false;
}
}  // namespace

bool AlgoMqttBus::probePostReady() {
    // v1.9 主路径：Nacos healthy 实例数 > 0
    if (nacosHasHealthyPost()) {
        return true;
    }
    // 静态兜底抽检 /readyz
    std::string base = postBaseUrl();
    if (base.empty()) return false;
    return probeReadyzAt(base);
}

void AlgoMqttBus::ensureHealthProbe() {
    if (!postEnabled()) return;
    bool expected = false;
    if (!g_healthStarted.compare_exchange_strong(expected, true)) return;

    // initial probe
    bool ok = probePostReady();
    if (!ok) {
        g_failStreak.store(healthFailThreshold());
        g_postReady.store(false);
        LOG(WARNING) << "[POST-HEALTH] initial readyz failed → bypass if FAILOVER_OPEN";
    } else {
        g_postReady.store(true);
    }

    std::thread([]() {
        const int thr = healthFailThreshold();
        const int interval = healthIntervalSec();
        while (true) {
            bool ok = probePostReady();
            if (ok) {
                g_failStreak.store(0);
                int okSt = g_okStreak.fetch_add(1) + 1;
                if (!g_postReady.load() && okSt >= thr) {
                    g_postReady.store(true);
                    LOG(INFO) << "[POST-HEALTH] recovered → exit bypass";
                }
            } else {
                g_okStreak.store(0);
                int fs = g_failStreak.fetch_add(1) + 1;
                if (g_postReady.load() && fs >= thr) {
                    g_postReady.store(false);
                    LOG(WARNING) << "[POST-HEALTH] failed " << thr << "x → bypass";
                }
            }
            std::this_thread::sleep_for(std::chrono::seconds(interval));
        }
    }).detach();
}

bool AlgoMqttBus::postIsReady() {
    ensureHealthProbe();
    return g_postReady.load();
}

bool AlgoMqttBus::postInBypass() {
    if (!postEnabled()) return false;
    if (!postFailoverOpen()) return false;
    return !postIsReady();
}

bool AlgoMqttBus::shouldPublishInferEvent() {
    if (!postEnabled()) return false;
    if (postFailoverOpen() && !postIsReady()) return false;
    return true;
}

bool AlgoMqttBus::publishBytes(const Config& config, const std::string& topic, const std::string& body, int /*qos*/) {
    if (!busEnabled(config)) return false;
    auto brokers = resolveBrokers(config);
    if (brokers.empty()) {
        LOG(WARNING) << "[AlgoMqttBus] MQTT_BROKER_URLS empty, skip topic=" << topic;
        return false;
    }
    std::string username = config.mqttUsername;
    if (username.empty()) {
        const char* env = std::getenv("MQTT_ALGO_USERNAME");
        if (env) username = env;
    }
    std::string password = config.mqttPassword;
    if (password.empty()) {
        const char* env = std::getenv("MQTT_ALGO_PASSWORD");
        if (env) password = env;
    }
    std::string clientBase = config.mqttClientId;
    if (clientBase.empty()) {
        const char* env = std::getenv("MQTT_ALGO_CLIENT_ID");
        clientBase = env && *env ? env : "algo-runtime-bus";
    }
    std::string clientId = clientBase + "-infer-" + makeUuid().substr(0, 8);

    for (const auto& bp : brokers) {
        if (mqttPublishOnce(bp.first, bp.second, clientId, username, password, topic, body)) {
            LOG(INFO) << "[AlgoMqttBus] InferEvent published topic=" << topic
                      << " broker=" << bp.first << ":" << bp.second;
            return true;
        }
    }
    LOG(ERROR) << "[AlgoMqttBus] InferEvent publish failed topic=" << topic;
    return false;
}

bool AlgoMqttBus::publishInferEvent(const Config& config, const std::string& inferEventJson) {
    const char* topicEnv = std::getenv("TOPIC_INFER_EVENT");
    std::string topic = (topicEnv && *topicEnv) ? topicEnv : "mqtt/iot-infer-event";
    return publishBytes(config, topic, inferEventJson, 1);
}
