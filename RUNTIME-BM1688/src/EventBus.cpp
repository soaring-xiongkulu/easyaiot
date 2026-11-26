#include "EventBus.h"

#include <curl/curl.h>
#include <json/json.h>

#include <arpa/inet.h>
#include <netdb.h>
#include <sys/socket.h>
#include <unistd.h>

#include <chrono>
#include <cctype>
#include <cstdint>
#include <cstring>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <memory>
#include <random>
#include <sstream>
#include <utility>
#include <vector>

namespace easyaiot::bm1688 {
namespace {

std::string lower(std::string value) {
    for (auto& c : value) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return value;
}

void appendU16(std::vector<std::uint8_t>& out, std::uint16_t value) {
    out.push_back(static_cast<std::uint8_t>((value >> 8) & 0xff));
    out.push_back(static_cast<std::uint8_t>(value & 0xff));
}

void appendString(std::vector<std::uint8_t>& out, const std::string& value) {
    appendU16(out, static_cast<std::uint16_t>(value.size()));
    out.insert(out.end(), value.begin(), value.end());
}

void appendRemaining(std::vector<std::uint8_t>& out, std::size_t length) {
    do {
        std::uint8_t byte = static_cast<std::uint8_t>(length % 128);
        length /= 128;
        if (length) byte |= 0x80;
        out.push_back(byte);
    } while (length);
}

bool sendAll(int fd, const std::vector<std::uint8_t>& bytes) {
    std::size_t offset = 0;
    while (offset < bytes.size()) {
        const auto count = ::send(fd, bytes.data() + offset, bytes.size() - offset, MSG_NOSIGNAL);
        if (count <= 0) return false;
        offset += static_cast<std::size_t>(count);
    }
    return true;
}

int connectTcp(const std::string& host, int port) {
    addrinfo hints{};
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    addrinfo* results = nullptr;
    if (getaddrinfo(host.c_str(), std::to_string(port).c_str(), &hints, &results) != 0) return -1;
    int fd = -1;
    for (auto* candidate = results; candidate; candidate = candidate->ai_next) {
        fd = ::socket(candidate->ai_family, candidate->ai_socktype, candidate->ai_protocol);
        if (fd < 0) continue;
        timeval timeout{5, 0};
        setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
        setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));
        if (::connect(fd, candidate->ai_addr, candidate->ai_addrlen) == 0) break;
        ::close(fd);
        fd = -1;
    }
    freeaddrinfo(results);
    return fd;
}

std::pair<std::string, int> parseBroker(std::string value) {
    const auto comma = value.find(',');
    if (comma != std::string::npos) value = value.substr(0, comma);
    if (value.rfind("mqtt://", 0) == 0) value.erase(0, 7);
    const auto slash = value.find('/');
    if (slash != std::string::npos) value = value.substr(0, slash);
    const auto colon = value.rfind(':');
    if (colon == std::string::npos) return {value, 1883};
    int port = 1883;
    try { port = std::stoi(value.substr(colon + 1)); } catch (...) {}
    return {value.substr(0, colon), port};
}

std::string uuid() {
    static thread_local std::mt19937_64 generator(std::random_device{}());
    std::ostringstream out;
    out << std::hex << generator() << generator();
    return out.str();
}

std::string utcNow() {
    const auto now = std::chrono::system_clock::now();
    const auto time = std::chrono::system_clock::to_time_t(now);
    std::tm tm{};
    gmtime_r(&time, &tm);
    std::ostringstream out;
    out << std::put_time(&tm, "%Y-%m-%dT%H:%M:%SZ");
    return out.str();
}

std::string jsonString(const Json::Value& value) {
    Json::StreamWriterBuilder writer;
    writer["indentation"] = "";
    return Json::writeString(writer, value);
}

bool mqttPublish(const std::string& host, int port, const std::string& clientId,
                 const std::string& username, const std::string& password,
                 const std::string& topic, const std::string& payload) {
    const int fd = connectTcp(host, port);
    if (fd < 0) return false;

    std::vector<std::uint8_t> body;
    appendString(body, "MQTT");
    body.push_back(4);
    std::uint8_t flags = 0x02;
    if (!username.empty()) flags |= 0x80;
    if (!password.empty()) flags |= 0x40;
    body.push_back(flags);
    appendU16(body, 30);
    appendString(body, clientId);
    if (!username.empty()) appendString(body, username);
    if (!password.empty()) appendString(body, password);
    std::vector<std::uint8_t> connect{0x10};
    appendRemaining(connect, body.size());
    connect.insert(connect.end(), body.begin(), body.end());
    if (!sendAll(fd, connect)) { ::close(fd); return false; }
    std::uint8_t connack[4]{};
    if (::recv(fd, connack, sizeof(connack), MSG_WAITALL) != 4 || connack[3] != 0) {
        ::close(fd);
        return false;
    }

    body.clear();
    appendString(body, topic);
    appendU16(body, 1);
    body.insert(body.end(), payload.begin(), payload.end());
    std::vector<std::uint8_t> publish{0x32};  // QoS1
    appendRemaining(publish, body.size());
    publish.insert(publish.end(), body.begin(), body.end());
    const bool sent = sendAll(fd, publish);
    std::uint8_t ack[4]{};
    const bool acknowledged = sent && ::recv(fd, ack, sizeof(ack), MSG_WAITALL) == 4 && ack[0] == 0x40;
    const std::vector<std::uint8_t> disconnect{0xe0, 0x00};
    sendAll(fd, disconnect);
    ::close(fd);
    return acknowledged;
}

}  // namespace

EventBus::EventBus(const RuntimeConfig& config) : config_(config) {
    curl_global_init(CURL_GLOBAL_DEFAULT);
}

bool EventBus::postJson(const std::string& url, const std::string& json) const {
    if (url.empty()) return false;
    CURL* curl = curl_easy_init();
    if (!curl) return false;
    curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, static_cast<long>(json.size()));
    curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT_MS, 3000L);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, 5000L);
    curl_easy_setopt(curl, CURLOPT_NOSIGNAL, 1L);
    const auto code = curl_easy_perform(curl);
    long status = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &status);
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    return code == CURLE_OK && status >= 200 && status < 300;
}

std::string EventBus::normalizeAlert(const std::string& flatJson, bool snapshot) const {
    Json::Value root;
    Json::CharReaderBuilder builder;
    std::string errors;
    std::unique_ptr<Json::CharReader> reader(builder.newCharReader());
    if (!reader->parse(flatJson.data(), flatJson.data() + flatJson.size(), &root, &errors)) {
        return "{}";
    }
    Json::Value alert;
    alert["object"] = root.get("object", "object");
    alert["event"] = root.get("event", "detection");
    alert["region"] = root.get("region", "");
    alert["information"] = root.get("information", "");
    alert["image_path"] = root.get("image_path", "");
    alert["record_path"] = root.get("record_path", "");
    alert["time"] = root.get("time", utcNow());
    alert["task_type"] = root.get("task_type", snapshot ? "snap" : "realtime");

    Json::Value payload;
    payload["device_id"] = root.get("device_id", config_.deviceIdText);
    payload["device_name"] = root.get("device_name", config_.deviceName);
    payload["task_id"] = root.get("task_id", config_.taskId);
    payload["task_name"] = root.get("task_name", config_.algorithmName);
    payload["correlation_id"] = root.get("correlation_id", uuid());
    payload["timestamp"] = root.get("time", utcNow());
    payload["time"] = root.get("time", utcNow());
    payload["task_type"] = alert["task_type"];
    payload["alert"] = alert;
    if (!config_.computeNodeId.empty()) {
        payload["node_id"] = config_.computeNodeId;
        payload["nodeId"] = config_.computeNodeId;
    }
    return jsonString(payload);
}

bool EventBus::publishMqtt(const std::string& topic, const std::string& messageType,
                           const std::string& payloadJson) const {
    const auto broker = parseBroker(config_.mqttBrokers);
    if (broker.first.empty()) return false;
    Json::Value payload;
    Json::CharReaderBuilder builder;
    std::string errors;
    std::unique_ptr<Json::CharReader> reader(builder.newCharReader());
    if (!reader->parse(payloadJson.data(), payloadJson.data() + payloadJson.size(), &payload, &errors)) {
        return false;
    }
    Json::Value envelope;
    envelope["version"] = "1.0";
    envelope["msgId"] = uuid();
    envelope["msgType"] = messageType;
    envelope["tenant"] = config_.mqttTenant;
    envelope["ts"] = utcNow();
    envelope["payload"] = payload;
    return mqttPublish(broker.first, broker.second,
                       config_.mqttClientId + "-" + uuid().substr(0, 8),
                       config_.mqttUsername, config_.mqttPassword,
                       topic, jsonString(envelope));
}

bool EventBus::publishAlert(const std::string& flatAlertJson, bool snapshot) const {
    const auto transport = lower(config_.busTransport);
    if (transport == "http" || transport == "off" || transport == "0" || transport == "false") {
        return postJson(config_.alertHookUrl, flatAlertJson);
    }
    const std::string payload = normalizeAlert(flatAlertJson, snapshot);
    return publishMqtt(snapshot ? "mqtt/iot-snapshot-alert" : "mqtt/iot-alert-notification",
                       snapshot ? "alert.snapshot" : "alert.notification", payload);
}

bool EventBus::postHeartbeat(const std::string& json) const {
    return config_.heartbeatUrl.empty() || postJson(config_.heartbeatUrl, json);
}

}  // namespace easyaiot::bm1688
