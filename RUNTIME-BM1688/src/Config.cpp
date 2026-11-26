#include "Config.h"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <filesystem>
#include <sstream>
#include <stdexcept>
#include <unordered_map>

namespace easyaiot::bm1688 {
namespace {

using Section = std::unordered_map<std::string, std::string>;
using Ini = std::unordered_map<std::string, Section>;

std::string trim(std::string value) {
    auto notSpace = [](unsigned char c) { return !std::isspace(c); };
    value.erase(value.begin(), std::find_if(value.begin(), value.end(), notSpace));
    value.erase(std::find_if(value.rbegin(), value.rend(), notSpace).base(), value.end());
    return value;
}

std::string get(const Ini& ini, const std::string& section, const std::string& key,
                const std::string& fallback = {}) {
    auto sit = ini.find(section);
    if (sit == ini.end()) return fallback;
    auto kit = sit->second.find(key);
    return kit == sit->second.end() ? fallback : kit->second;
}

int integer(const Ini& ini, const std::string& section, const std::string& key, int fallback) {
    const auto value = get(ini, section, key);
    if (value.empty()) return fallback;
    try { return std::stoi(value); } catch (...) { return fallback; }
}

float decimal(const Ini& ini, const std::string& section, const std::string& key, float fallback) {
    const auto value = get(ini, section, key);
    if (value.empty()) return fallback;
    try { return std::stof(value); } catch (...) { return fallback; }
}

bool boolean(const Ini& ini, const std::string& section, const std::string& key, bool fallback) {
    auto value = get(ini, section, key);
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    if (value.empty()) return fallback;
    if (value == "1" || value == "true" || value == "yes" || value == "on") return true;
    if (value == "0" || value == "false" || value == "no" || value == "off") return false;
    return fallback;
}

std::vector<int> parseInts(const std::string& value) {
    std::vector<int> values;
    std::stringstream stream(value);
    std::string item;
    while (std::getline(stream, item, ',')) {
        try { values.push_back(std::stoi(trim(item))); } catch (...) {}
    }
    return values;
}

Ini parseIni(const std::string& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open config: " + path);
    Ini ini;
    std::string section;
    std::string line;
    while (std::getline(input, line)) {
        line = trim(line);
        if (line.empty() || line[0] == '#' || line[0] == ';') continue;
        if (line.front() == '[' && line.back() == ']') {
            section = trim(line.substr(1, line.size() - 2));
            continue;
        }
        const auto equal = line.find('=');
        if (equal == std::string::npos) continue;
        ini[section][trim(line.substr(0, equal))] = trim(line.substr(equal + 1));
    }
    return ini;
}

}  // namespace

RuntimeConfig ConfigParser::load(const std::string& path) {
    const Ini ini = parseIni(path);
    RuntimeConfig config;
    config.source = get(ini, "video", "rtsp_url");
    config.rtmpUrl = get(ini, "video", "rtmp_url");
    config.width = integer(ini, "video", "width", config.width);
    config.height = integer(ini, "video", "height", config.height);
    config.fps = integer(ini, "video", "fps", config.fps);
    config.frameSkip = std::max(1, integer(ini, "ai", "frame_skip", config.frameSkip));
    config.confidence = decimal(ini, "alarm", "confidence_threshold", config.confidence);
    config.nmsThreshold = decimal(ini, "ai", "nms_threshold", config.nmsThreshold);

    for (int index = 0; index < 32; ++index) {
        const std::string suffix = index == 0 ? "" : "_" + std::to_string(index);
        ModelConfig model;
        model.path = get(ini, "ai", "model_path" + suffix);
        if (model.path.empty()) break;
        model.classesPath = get(ini, "ai", "classes_path" + suffix);
        model.id = integer(ini, "ai", "model_id" + suffix, index == 0 ? -2 : index);
        config.models.push_back(std::move(model));
    }

    config.deviceId = integer(ini, "bm1688", "device_id", 0);
    config.coreIds = parseInts(get(ini, "bm1688", "core_ids", "0,1"));
    config.decodeQueueDepth = std::clamp(integer(ini, "bm1688", "decode_queue_depth", 8), 2, 64);
    config.inferQueueDepth = std::clamp(integer(ini, "bm1688", "infer_queue_depth", 4), 1, 32);
    config.resultQueueDepth = std::clamp(integer(ini, "bm1688", "result_queue_depth", 64), 4, 512);
    config.preallocate = boolean(ini, "bm1688", "preallocate", true);
    config.zeroCopy = boolean(ini, "bm1688", "zero_copy", true);
    config.useVpp = boolean(ini, "bm1688", "use_vpp", true);
    config.decoder = get(ini, "bm1688", "decoder", config.decoder);

    config.enableRtmp = boolean(ini, "features", "enable_rtmp", false);
    config.enableAlarm = boolean(ini, "features", "enable_alarm",
                                 boolean(ini, "alarm", "enable", true));
    config.alertHookUrl = get(ini, "alarm", "alert_hook_url",
                              get(ini, "video_task", "alert_hook_url"));
    config.heartbeatUrl = get(ini, "video_task", "heartbeat_url");
    config.heartbeatIntervalSec = std::max(3, integer(ini, "video_task", "heartbeat_interval_sec", 10));
    config.controlPort = integer(ini, "task", "control_port", 8000);
    config.taskId = integer(ini, "task", "id", 0);
    config.taskType = get(ini, "video_task", "task_type", "realtime");
    config.deviceIdText = get(ini, "video_task", "device_id");
    config.deviceName = get(ini, "video_task", "device_name", config.deviceIdText);
    config.algorithmName = get(ini, "video_task", "algorithm_name", "yolov8");
    config.logPath = get(ini, "video_task", "log_path");
    config.alertImageDir = get(ini, "video_task", "alert_image_dir");
    config.cooldownSec = std::max(0, integer(ini, "alarm", "cooldown_time", 30));

    config.busTransport = get(ini, "video_task", "algo_bus_transport",
                              get(ini, "mqtt", "transport", "mqtt"));
    config.mqttBrokers = get(ini, "mqtt", "broker_urls",
                             get(ini, "video_task", "mqtt_broker_urls"));
    config.mqttUsername = get(ini, "mqtt", "username");
    config.mqttPassword = get(ini, "mqtt", "password");
    config.mqttClientId = get(ini, "mqtt", "client_id", "runtime-bm1688");
    config.mqttTenant = get(ini, "mqtt", "tenant", "default");
    config.computeNodeId = get(ini, "video_task", "compute_node_id");

    if (config.source.empty()) throw std::runtime_error("[video] rtsp_url is required");
    if (config.models.empty()) throw std::runtime_error("[ai] at least one .bmodel is required");
    for (const auto& model : config.models) {
        if (model.path.size() < 7 || model.path.substr(model.path.size() - 7) != ".bmodel") {
            throw std::runtime_error("BM1688 accepts .bmodel only: " + model.path);
        }
        if (!std::filesystem::is_regular_file(model.path)) {
            throw std::runtime_error("BModel does not exist: " + model.path);
        }
        if (model.classesPath.empty() || !std::filesystem::is_regular_file(model.classesPath)) {
            throw std::runtime_error("classes file does not exist: " + model.classesPath);
        }
    }
    std::sort(config.coreIds.begin(), config.coreIds.end());
    config.coreIds.erase(std::unique(config.coreIds.begin(), config.coreIds.end()), config.coreIds.end());
    if (config.coreIds != std::vector<int>({0, 1})) {
        throw std::runtime_error("RUNTIME-BM1688 strict mode requires core_ids=0,1");
    }
    for (int core : config.coreIds) {
        if (core < 0 || core > 1) throw std::runtime_error("BM1688 core id must be 0 or 1");
    }
    if (config.taskType != "realtime") {
        throw std::runtime_error("RUNTIME-BM1688 currently accepts realtime tasks only");
    }
    if (!config.zeroCopy || !config.useVpp || !config.preallocate) {
        throw std::runtime_error("RUNTIME-BM1688 strict mode requires zero_copy/use_vpp/preallocate=true");
    }
    return config;
}

}  // namespace easyaiot::bm1688
