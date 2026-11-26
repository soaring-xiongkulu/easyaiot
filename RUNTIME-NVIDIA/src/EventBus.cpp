#include "EventBus.h"

#include <curl/curl.h>
#include <json/json.h>

#include <netdb.h>
#include <sys/socket.h>
#include <unistd.h>

#include <algorithm>
#include <chrono>
#include <cctype>
#include <cstdint>
#include <cstring>
#include <iomanip>
#include <memory>
#include <random>
#include <sstream>
#include <utility>
#include <vector>

namespace easyaiot::nvidia {
namespace {

std::string lower(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return value;
}

std::string uuid() {
    static thread_local std::mt19937_64 random(std::random_device{}());
    std::ostringstream output;
    output << std::hex << random() << random();
    return output.str();
}

std::string utcNow() {
    const auto now = std::chrono::system_clock::now();
    const auto time = std::chrono::system_clock::to_time_t(now);
    std::tm value{};
    gmtime_r(&time, &value);
    std::ostringstream output;
    output << std::put_time(&value, "%Y-%m-%dT%H:%M:%SZ");
    return output.str();
}

std::string compact(const Json::Value& value) {
    Json::StreamWriterBuilder builder;
    builder["indentation"] = "";
    return Json::writeString(builder, value);
}

void appendU16(std::vector<std::uint8_t>& output, std::uint16_t value) {
    output.push_back(static_cast<std::uint8_t>(value >> 8));
    output.push_back(static_cast<std::uint8_t>(value & 0xff));
}

void appendString(std::vector<std::uint8_t>& output, const std::string& value) {
    appendU16(output, static_cast<std::uint16_t>(value.size()));
    output.insert(output.end(), value.begin(), value.end());
}

void appendRemaining(std::vector<std::uint8_t>& output, std::size_t length) {
    do {
        std::uint8_t byte = static_cast<std::uint8_t>(length % 128);
        length /= 128;
        if (length) byte |= 0x80;
        output.push_back(byte);
    } while (length);
}

bool sendAll(int socket, const std::vector<std::uint8_t>& bytes) {
    std::size_t offset = 0;
    while (offset < bytes.size()) {
        const auto sent = ::send(socket, bytes.data() + offset, bytes.size() - offset, MSG_NOSIGNAL);
        if (sent <= 0) return false;
        offset += static_cast<std::size_t>(sent);
    }
    return true;
}

std::pair<std::string, int> parseBroker(std::string value) {
    if (const auto comma = value.find(','); comma != std::string::npos) value.resize(comma);
    if (value.rfind("mqtt://", 0) == 0) value.erase(0, 7);
    if (const auto slash = value.find('/'); slash != std::string::npos) value.resize(slash);
    const auto colon = value.rfind(':');
    if (colon == std::string::npos) return {value, 1883};
    int port = 1883;
    try { port = std::stoi(value.substr(colon + 1)); } catch (...) {}
    return {value.substr(0, colon), port};
}

int connectTcp(const std::string& host, int port) {
    addrinfo hints{};
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    addrinfo* addresses = nullptr;
    if (getaddrinfo(host.c_str(), std::to_string(port).c_str(), &hints, &addresses) != 0) return -1;
    int socket = -1;
    for (auto* address = addresses; address; address = address->ai_next) {
        socket = ::socket(address->ai_family, address->ai_socktype, address->ai_protocol);
        if (socket < 0) continue;
        timeval timeout{5, 0};
        setsockopt(socket, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
        setsockopt(socket, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));
        if (::connect(socket, address->ai_addr, address->ai_addrlen) == 0) break;
        ::close(socket);
        socket = -1;
    }
    freeaddrinfo(addresses);
    return socket;
}

bool mqttPublish(const RuntimeConfig& config, const std::string& topic,
                 const std::string& payload) {
    const auto [host, port] = parseBroker(config.mqttBrokers);
    if (host.empty()) return false;
    const int socket = connectTcp(host, port);
    if (socket < 0) return false;
    std::vector<std::uint8_t> body;
    appendString(body, "MQTT");
    body.push_back(4);
    std::uint8_t flags = 0x02;
    if (!config.mqttUsername.empty()) flags |= 0x80;
    if (!config.mqttPassword.empty()) flags |= 0x40;
    body.push_back(flags);
    appendU16(body, 30);
    appendString(body, config.mqttClientId + "-" + uuid().substr(0, 8));
    if (!config.mqttUsername.empty()) appendString(body, config.mqttUsername);
    if (!config.mqttPassword.empty()) appendString(body, config.mqttPassword);
    std::vector<std::uint8_t> packet{0x10};
    appendRemaining(packet, body.size());
    packet.insert(packet.end(), body.begin(), body.end());
    std::uint8_t ack[4]{};
    if (!sendAll(socket, packet) || ::recv(socket, ack, sizeof(ack), MSG_WAITALL) != 4 || ack[3] != 0) {
        ::close(socket);
        return false;
    }
    body.clear();
    appendString(body, topic);
    appendU16(body, 1);
    body.insert(body.end(), payload.begin(), payload.end());
    packet.assign(1, 0x32);
    appendRemaining(packet, body.size());
    packet.insert(packet.end(), body.begin(), body.end());
    const bool sent = sendAll(socket, packet);
    const bool confirmed = sent && ::recv(socket, ack, sizeof(ack), MSG_WAITALL) == 4 && ack[0] == 0x40;
    ::close(socket);
    return confirmed;
}
}  // namespace

EventBus::EventBus(const RuntimeConfig& config) : config_(config) {
    curl_global_init(CURL_GLOBAL_DEFAULT);
}

bool EventBus::postJson(const std::string& url, const std::string& json) const {
    if (url.empty()) return false;
    CURL* curl = curl_easy_init();
    if (!curl) return false;
    curl_slist* headers = curl_slist_append(nullptr, "Content-Type: application/json");
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, static_cast<long>(json.size()));
    curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT_MS, 3000L);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, 5000L);
    curl_easy_setopt(curl, CURLOPT_NOSIGNAL, 1L);
    const auto result = curl_easy_perform(curl);
    long status = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &status);
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    return result == CURLE_OK && status >= 200 && status < 300;
}

bool EventBus::publishMqtt(const std::string& flatJson) const {
    Json::Value flat;
    Json::CharReaderBuilder readerBuilder;
    std::string errors;
    std::unique_ptr<Json::CharReader> reader(readerBuilder.newCharReader());
    if (!reader->parse(flatJson.data(), flatJson.data() + flatJson.size(), &flat, &errors)) return false;
    Json::Value alert;
    for (const char* key : {"object", "event", "region", "information", "image_path",
                            "record_path", "time", "task_type"}) {
        alert[key] = flat.get(key, "");
    }
    Json::Value payload;
    payload["device_id"] = flat.get("device_id", config_.deviceIdText);
    payload["device_name"] = flat.get("device_name", config_.deviceName);
    payload["task_id"] = flat.get("task_id", config_.taskId);
    payload["task_name"] = flat.get("task_name", config_.algorithmName);
    payload["correlation_id"] = flat.get("correlation_id", uuid());
    payload["timestamp"] = flat.get("time", utcNow());
    payload["time"] = payload["timestamp"];
    payload["task_type"] = "realtime";
    payload["alert"] = alert;
    if (!config_.computeNodeId.empty()) {
        payload["node_id"] = config_.computeNodeId;
        payload["nodeId"] = config_.computeNodeId;
    }
    Json::Value envelope;
    envelope["version"] = "1.0";
    envelope["msgId"] = uuid();
    envelope["msgType"] = "alert.notification";
    envelope["tenant"] = config_.mqttTenant;
    envelope["ts"] = utcNow();
    envelope["payload"] = payload;
    return mqttPublish(config_, "mqtt/iot-alert-notification", compact(envelope));
}

bool EventBus::publishAlert(const std::string& flatAlertJson) const {
    const std::string transport = lower(config_.busTransport);
    if (transport == "mqtt") return publishMqtt(flatAlertJson);
    return postJson(config_.alertHookUrl, flatAlertJson);
}

bool EventBus::postHeartbeat(const std::string& json) const {
    return config_.heartbeatUrl.empty() || postJson(config_.heartbeatUrl, json);
}

}  // namespace easyaiot::nvidia
