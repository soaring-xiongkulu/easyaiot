#include "Config.h"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <unordered_map>

namespace easyaiot::nvidia {
namespace {
using Section = std::unordered_map<std::string, std::string>;
using Ini = std::unordered_map<std::string, Section>;

std::string trim(std::string value) {
    auto notSpace = [](unsigned char c) { return !std::isspace(c); };
    value.erase(value.begin(), std::find_if(value.begin(), value.end(), notSpace));
    value.erase(std::find_if(value.rbegin(), value.rend(), notSpace).base(), value.end());
    return value;
}

Ini parseIni(const std::string& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open config: " + path);
    Ini ini;
    std::string section;
    for (std::string line; std::getline(input, line);) {
        line = trim(line);
        if (line.empty() || line[0] == '#' || line[0] == ';') continue;
        if (line.front() == '[' && line.back() == ']') {
            section = trim(line.substr(1, line.size() - 2));
            continue;
        }
        const auto equal = line.find('=');
        if (equal != std::string::npos) {
            ini[section][trim(line.substr(0, equal))] = trim(line.substr(equal + 1));
        }
    }
    return ini;
}

std::string get(const Ini& ini, const std::string& section, const std::string& key,
                const std::string& fallback = {}) {
    const auto sit = ini.find(section);
    if (sit == ini.end()) return fallback;
    const auto kit = sit->second.find(key);
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

bool hasEngineExtension(const std::string& path) {
    const auto extension = std::filesystem::path(path).extension().string();
    return extension == ".engine" || extension == ".plan";
}
}  // namespace

RuntimeConfig ConfigParser::load(const std::string& path) {
    const Ini ini = parseIni(path);
    RuntimeConfig config;
    config.source = get(ini, "video", "rtsp_url");
    config.width = std::max(1, integer(ini, "video", "width", 1920));
    config.height = std::max(1, integer(ini, "video", "height", 1080));
    config.fps = std::max(1, integer(ini, "video", "fps", 25));
    config.frameSkip = std::max(1, integer(ini, "ai", "frame_skip", 1));
    config.confidence = decimal(ini, "alarm", "confidence_threshold", 0.5F);
    config.nmsThreshold = decimal(ini, "ai", "nms_threshold", 0.45F);

    for (int index = 0; index < 64; ++index) {
        const std::string suffix = index == 0 ? "" : "_" + std::to_string(index);
        const std::string model = get(ini, "ai", "model_path" + suffix);
        if (model.empty()) continue;
        ModelConfig item;
        item.path = model;
        item.classesPath = get(ini, "ai", "classes_path" + suffix,
                               get(ini, "ai", "classes_path"));
        item.id = integer(ini, "ai", "model_id" + suffix, index == 0 ? -2 : index);
        config.models.push_back(std::move(item));
    }

    config.cudaDevice = std::max(0, integer(ini, "nvidia", "cuda_device", 0));
    config.inferStreams = std::clamp(integer(ini, "nvidia", "infer_streams", 2), 1, 16);
    config.decoderSurfaces = std::clamp(integer(ini, "nvidia", "decoder_surfaces", 16), 8, 64);
    config.decodeQueueDepth = std::clamp(integer(ini, "nvidia", "decode_queue_depth", 8), 1, 256);
    config.inferQueueDepth = std::clamp(integer(ini, "nvidia", "infer_queue_depth", 4), 1, 64);
    config.resultQueueDepth = std::clamp(integer(ini, "nvidia", "result_queue_depth", 64), 1, 1024);
    config.zeroCopy = boolean(ini, "nvidia", "zero_copy", true);
    config.preallocate = boolean(ini, "nvidia", "preallocate", true);
    config.cudaGraph = boolean(ini, "nvidia", "cuda_graph", true);
    config.requireNvdec = boolean(ini, "nvidia", "require_nvdec", true);
    config.requireNvenc = boolean(ini, "nvidia", "require_nvenc", false);
    config.decoder = get(ini, "nvidia", "decoder", config.decoder);

    config.enableRtmp = boolean(ini, "features", "enable_rtmp", false);
    config.enableAlarm = boolean(ini, "features", "enable_alarm",
                                 boolean(ini, "alarm", "enable", true));
    config.alertHookUrl = get(ini, "alarm", "alert_hook_url");
    config.cooldownSec = std::max(0, integer(ini, "alarm", "cooldown_time", 30));
    config.taskId = integer(ini, "task", "id", 0);
    config.controlPort = integer(ini, "task", "control_port", 8000);
    config.taskType = get(ini, "video_task", "task_type", "realtime");
    config.deviceIdText = get(ini, "video_task", "device_id");
    config.deviceName = get(ini, "video_task", "device_name");
    config.algorithmName = get(ini, "video_task", "algorithm_name", "yolov8");
    config.heartbeatUrl = get(ini, "video_task", "heartbeat_url");
    config.heartbeatIntervalSec = std::max(1, integer(ini, "video_task", "heartbeat_interval_sec", 10));
    config.logPath = get(ini, "video_task", "log_path");
    config.computeNodeId = get(ini, "video_task", "compute_node_id");
    config.busTransport = get(ini, "video_task", "algo_bus_transport",
                              get(ini, "mqtt", "transport", "mqtt"));
    config.mqttBrokers = get(ini, "mqtt", "broker_urls",
                             get(ini, "video_task", "mqtt_broker_urls"));
    config.mqttUsername = get(ini, "mqtt", "username");
    config.mqttPassword = get(ini, "mqtt", "password");
    config.mqttClientId = get(ini, "mqtt", "client_id", "runtime-nvidia");
    config.mqttTenant = get(ini, "mqtt", "tenant", "default");

    if (config.source.empty()) throw std::runtime_error("[video] rtsp_url is required");
    if (config.models.empty()) throw std::runtime_error("[ai] at least one TensorRT engine is required");
    for (const auto& model : config.models) {
        if (!hasEngineExtension(model.path)) {
            throw std::runtime_error("RUNTIME-NVIDIA accepts .engine/.plan only: " + model.path);
        }
        if (!std::filesystem::is_regular_file(model.path)) {
            throw std::runtime_error("TensorRT engine does not exist: " + model.path);
        }
        if (model.classesPath.empty() || !std::filesystem::is_regular_file(model.classesPath)) {
            throw std::runtime_error("classes file does not exist: " + model.classesPath);
        }
    }
    if (config.taskType != "realtime") {
        throw std::runtime_error("RUNTIME-NVIDIA currently accepts realtime tasks only");
    }
    if (!config.zeroCopy || !config.preallocate || !config.requireNvdec) {
        throw std::runtime_error(
            "strict mode requires zero_copy/preallocate/require_nvdec=true; fallback is forbidden");
    }
    if (config.enableRtmp || config.requireNvenc) {
        throw std::runtime_error(
            "NVENC output is not enabled in this build; keep enable_rtmp/require_nvenc=false instead of falling back to software encode");
    }
    return config;
}

}  // namespace easyaiot::nvidia
