/*
 * Configuration File Parser Implementation
 */

#include "ConfigParser.h"
#include "AlgoMqttBus.h"
#include <json/json.h>
#include <sstream>
#include <cstdlib>
#include <algorithm>
#include <cctype>

std::string ConfigParser::trim(const std::string& str) {
    const std::string whitespace = " \t\r\n";
    size_t start = str.find_first_not_of(whitespace);
    if (start == std::string::npos) return "";
    size_t end = str.find_last_not_of(whitespace);
    return str.substr(start, end - start + 1);
}

bool ConfigParser::parseBool(const std::string& value) {
    std::string v = trim(value);
    std::transform(v.begin(), v.end(), v.begin(), ::tolower);
    return (v == "true" || v == "1" || v == "yes" || v == "on");
}

int ConfigParser::parseInt(const std::string& value) {
    try {
        return std::stoi(trim(value));
    } catch (...) {
        return 0;
    }
}

float ConfigParser::parseFloat(const std::string& value) {
    try {
        return std::stof(trim(value));
    } catch (...) {
        return 0.0f;
    }
}

bool ConfigParser::parseRegion(const std::string& regionJson, std::vector<cv::Point>& points) {
    try {
        Json::Reader reader;
        Json::Value root;

        if (!reader.parse(regionJson, root)) {
            LOG(ERROR) << "[ERROR] JSON parse failed: " << regionJson;
            return false;
        }

        if (!root.isArray()) {
            LOG(ERROR) << "[ERROR] Region format error, should be array: " << regionJson;
            return false;
        }

        points.clear();
        for (const auto& point : root) {
            if (point.isArray() && point.size() == 2) {
                // Support normalized 0-1 or absolute pixel coords
                double x = point[0].asDouble();
                double y = point[1].asDouble();
                if (x >= 0.0 && x <= 1.0 && y >= 0.0 && y <= 1.0) {
                    // Will be scaled later when video size known; store as 0-10000 fixed
                    points.push_back(cv::Point(static_cast<int>(x * 10000), static_cast<int>(y * 10000)));
                } else {
                    points.push_back(cv::Point(static_cast<int>(x), static_cast<int>(y)));
                }
            }
        }

        return points.size() >= 3;

    } catch (const std::exception& e) {
        LOG(ERROR) << "[ERROR] Parse region exception: " << e.what();
        return false;
    }
}

static void parseDevicesJson(const std::string& json, std::vector<DeviceStreamConfig>& out) {
    Json::Reader reader;
    Json::Value root;
    if (!reader.parse(json, root) || !root.isArray()) {
        return;
    }
    // Replace (not append): ini may list devices_json under both [video] and [video_task]
    out.clear();
    for (const auto& item : root) {
        DeviceStreamConfig d;
        d.deviceId = item.get("device_id", "").asString();
        d.deviceName = item.get("device_name", d.deviceId).asString();
        d.rtspUrl = item.get("rtsp_url", "").asString();
        if (!d.deviceId.empty() && !d.rtspUrl.empty()) {
            out.push_back(d);
        }
    }
}

bool ConfigParser::parse(const std::string& filename, Config& config) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        LOG(ERROR) << "[ERROR] Cannot open config file: " << filename;
        return false;
    }

    std::string line;
    std::string currentSection;
    std::string currentModel;

    while (std::getline(file, line)) {
        line = trim(line);

        if (line.empty() || line[0] == '#' || line[0] == ';') {
            continue;
        }

        if (line[0] == '[' && line[line.length()-1] == ']') {
            currentSection = line.substr(1, line.length()-2);
            currentSection = trim(currentSection);
            LOG(INFO) << "[CONFIG] Reading section: [" << currentSection << "]";
            continue;
        }

        size_t equalPos = line.find('=');
        if (equalPos == std::string::npos) {
            continue;
        }

        std::string key = trim(line.substr(0, equalPos));
        std::string value = trim(line.substr(equalPos + 1));

        if (currentSection == "video") {
            if (key == "rtsp_url") {
                config.rtspUrl = value;
            } else if (key == "rtmp_url") {
                config.rtmpUrl = value;
            } else if (key == "width") {
                config.videoWidth = parseInt(value);
                if (config.videoWidth <= 0) config.videoWidth = 1920;
            } else if (key == "height") {
                config.videoHeight = parseInt(value);
                if (config.videoHeight <= 0) config.videoHeight = 1080;
            } else if (key == "fps") {
                config.rtmpFps = parseInt(value);
                if (config.rtmpFps <= 0) config.rtmpFps = 25;
            } else if (key == "devices_json") {
                parseDevicesJson(value, config.devices);
            }
        }
        else if (currentSection == "ai") {
            if (key == "enable") {
                config.enableAI = parseBool(value);
            } else if (key == "model_path") {
                currentModel = "default";
                config.modelPaths[currentModel] = value;
            } else if (key == "classes_path") {
                if (currentModel.empty()) currentModel = "default";
                config.modelClasses[currentModel] = value;
            } else if (key == "threads") {
                config.threadNums = parseInt(value);
                if (config.threadNums <= 0) config.threadNums = 3;
            } else if (key == "frame_skip") {
                config.frameSkip = parseInt(value);
                if (config.frameSkip <= 0) config.frameSkip = 8;
            } else if (key == "prefer_gpu") {
                config.preferGpu = parseBool(value);
            } else if (key == "force_cpu") {
                config.forceCpu = parseBool(value);
            } else if (key == "gpu_device_id") {
                config.gpuDeviceId = parseInt(value);
                if (config.gpuDeviceId < 0) config.gpuDeviceId = 0;
            } else if (key == "prefer_hwaccel") {
                config.preferHwaccel = parseBool(value);
            } else if (key == "force_soft_av") {
                config.forceSoftAv = parseBool(value);
            } else if (key == "hwaccel_device_id") {
                config.hwaccelDeviceId = parseInt(value);
                if (config.hwaccelDeviceId < 0) config.hwaccelDeviceId = 0;
            } else if (key == "nvenc_preset") {
                if (!value.empty()) config.nvencPreset = value;
            }
        }
        else if (currentSection == "alarm") {
            if (key == "enable") {
                config.enableAlarm = parseBool(value);
            } else if (key == "hook_url") {
                config.hookHttpUrl = value;
            } else if (key == "confidence_threshold") {
                config.alarmConfidenceThreshold = parseFloat(value);
                if (config.alarmConfidenceThreshold <= 0.0f || config.alarmConfidenceThreshold > 1.0f) {
                    config.alarmConfidenceThreshold = 0.5f;
                }
            } else if (key == "cooldown_time") {
                config.alarmCooldownTime = parseInt(value);
                if (config.alarmCooldownTime < 0) {
                    config.alarmCooldownTime = 30;
                }
            } else if (key == "image_dir") {
                config.alertImageDir = value;
            }
        }
        else if (currentSection == "task") {
            if (key == "id") {
                config.taskId = value;
            } else if (key == "control_port") {
                int port = parseInt(value);
                if (port < 8000 || port > 9000) {
                    LOG(ERROR) << "[CONFIG] control_port=" << port
                               << " 超出允许范围 [8000,9000]（与 VIDEO runtime_control_port 一致），"
                               << "回退为 8000；请改 ini 或任务端口";
                    config.controlPort = 8000;
                } else {
                    config.controlPort = port;
                }
            }
        }
        else if (currentSection == "video_task") {
            if (key == "device_id") {
                config.deviceId = value;
            } else if (key == "device_name") {
                config.deviceName = value;
            } else if (key == "task_type") {
                config.taskType = value.empty() ? "realtime" : value;
                if (config.taskType == "snapshot") {
                    config.taskType = "snap";
                }
            } else if (key == "algorithm_name" || key == "event") {
                config.algorithmName = value.empty() ? "detection" : value;
            } else if (key == "heartbeat_url") {
                config.heartbeatUrl = value;
            } else if (key == "alert_hook_url") {
                config.alertHookUrl = value;
                if (config.hookHttpUrl.empty()) {
                    config.hookHttpUrl = value;
                }
            } else if (key == "log_path") {
                config.logPath = value;
            } else if (key == "heartbeat_interval_sec") {
                config.heartbeatIntervalSec = parseInt(value);
                if (config.heartbeatIntervalSec <= 0) {
                    config.heartbeatIntervalSec = 10;
                }
            } else if (key == "headless") {
                config.headless = parseBool(value);
            } else if (key == "cron_expression") {
                config.cronExpression = value;
            } else if (key == "patrol_mode") {
                config.patrolMode = value.empty() ? "pool" : value;
            } else if (key == "patrol_interval_sec") {
                config.patrolIntervalSec = parseInt(value);
                if (config.patrolIntervalSec < 3) config.patrolIntervalSec = 3;
            } else if (key == "patrol_pool_size") {
                config.patrolPoolSize = parseInt(value);
                if (config.patrolPoolSize < 1) config.patrolPoolSize = 1;
                if (config.patrolPoolSize > 16) config.patrolPoolSize = 16;
            } else if (key == "frame_skip") {
                config.frameSkip = parseInt(value);
                if (config.frameSkip <= 0) config.frameSkip = 8;
            } else if (key == "alert_image_dir") {
                config.alertImageDir = value;
            } else if (key == "algo_bus_transport") {
                config.algoBusTransport = value;
            } else if (key == "mqtt_broker_urls") {
                config.mqttBrokerUrls = value;
            } else if (key == "mqtt_username") {
                config.mqttUsername = value;
            } else if (key == "mqtt_password") {
                config.mqttPassword = value;
            } else if (key == "mqtt_client_id") {
                config.mqttClientId = value;
            } else if (key == "mqtt_tenant") {
                config.mqttTenant = value;
            } else if (key == "compute_node_id" || key == "node_id") {
                config.computeNodeId = value;
            } else if (key == "devices_json") {
                parseDevicesJson(value, config.devices);
            }
        }
        else if (currentSection == "mqtt") {
            if (key == "broker_urls" || key == "mqtt_broker_urls") {
                config.mqttBrokerUrls = value;
            } else if (key == "username") {
                config.mqttUsername = value;
            } else if (key == "password") {
                config.mqttPassword = value;
            } else if (key == "client_id") {
                config.mqttClientId = value;
            } else if (key == "tenant") {
                config.mqttTenant = value;
            } else if (key == "algo_bus_transport" || key == "transport") {
                config.algoBusTransport = value;
            }
        }
        else if (currentSection == "features") {
            if (key == "enable_rtmp") {
                config.enableRtmp = parseBool(value);
            } else if (key == "enable_draw") {
                config.enableDrawRtmp = parseBool(value);
            } else if (key == "enable_alarm") {
                config.enableAlarm = parseBool(value);
            }
        }
        else if (currentSection == "regions") {
            std::vector<cv::Point> points;
            if (parseRegion(value, points)) {
                std::string regionName = key.empty() ? "default" : key;
                config.regions[regionName].push_back(points);
                LOG(INFO) << "  [OK] Alarm region '" << regionName << "' loaded: " << points.size() << " points";
            } else {
                LOG(WARNING) << "  [WARNING] Alarm region '" << key << "' parse failed";
            }
        }
    }

    file.close();

    // Ensure primary device stream exists
    if (config.devices.empty() && !config.rtspUrl.empty()) {
        DeviceStreamConfig d;
        d.deviceId = config.deviceId.empty() ? "device" : config.deviceId;
        d.deviceName = config.deviceName.empty() ? d.deviceId : config.deviceName;
        d.rtspUrl = config.rtspUrl;
        config.devices.push_back(d);
    }
    if (config.rtspUrl.empty() && !config.devices.empty()) {
        config.rtspUrl = config.devices.front().rtspUrl;
        if (config.deviceId.empty()) config.deviceId = config.devices.front().deviceId;
        if (config.deviceName.empty()) config.deviceName = config.devices.front().deviceName;
    }

    const std::string tt = config.taskType;
    const bool isForward = (tt == "forward");
    const bool needsPersistentRtsp = (tt == "realtime" || tt == "forward" || tt.empty());
    if (needsPersistentRtsp && config.rtspUrl.empty()) {
        LOG(ERROR) << "[ERROR] Missing required config: rtsp_url";
        return false;
    }
    if (isForward && config.rtmpUrl.empty()) {
        LOG(ERROR) << "[ERROR] forward mode requires rtmp_url";
        return false;
    }
    if ((tt == "snap" || tt == "patrol") && config.devices.empty()) {
        LOG(ERROR) << "[ERROR] snap/patrol requires at least one device stream";
        return false;
    }

    if (isForward) {
        config.enableAI = false;
        config.enableAlarm = false;
        config.enableDrawRtmp = false;
        config.enableRtmp = true;
        LOG(INFO) << "[CONFIG] forward mode: AI/alarm disabled, RTMP copy relay enabled";
    }

    if (config.enableAI && config.modelPaths.empty()) {
        LOG(ERROR) << "[ERROR] AI inference enabled but model path not configured";
        return false;
    }

    if (!config.alertHookUrl.empty()) {
        config.hookHttpUrl = config.alertHookUrl;
    }

    // Env overrides for MQTT event bus / shared alert images (Ceph)
    if (const char* v = std::getenv("ALGO_BUS_TRANSPORT")) {
        if (config.algoBusTransport.empty()) config.algoBusTransport = trim(v);
    }
    if (const char* v = std::getenv("MQTT_BROKER_URLS")) {
        if (config.mqttBrokerUrls.empty()) config.mqttBrokerUrls = trim(v);
    }
    if (const char* v = std::getenv("MQTT_ALGO_USERNAME")) {
        if (config.mqttUsername.empty()) config.mqttUsername = v;
    }
    if (const char* v = std::getenv("MQTT_ALGO_PASSWORD")) {
        if (config.mqttPassword.empty()) config.mqttPassword = v;
    }
    if (const char* v = std::getenv("MQTT_ALGO_CLIENT_ID")) {
        if (config.mqttClientId.empty()) config.mqttClientId = v;
    }
    if (const char* v = std::getenv("MQTT_ALGO_TENANT")) {
        if (config.mqttTenant.empty()) config.mqttTenant = v;
    }
    if (const char* v = std::getenv("COMPUTE_NODE_ID")) {
        if (config.computeNodeId.empty()) config.computeNodeId = trim(v);
    } else if (const char* v = std::getenv("NODE_ID")) {
        if (config.computeNodeId.empty()) config.computeNodeId = trim(v);
    }
    if (const char* v = std::getenv("ALERT_IMAGES_DIR")) {
        std::string dir = trim(v);
        if (!dir.empty()) config.alertImageDir = dir;
    }

    const bool mqttBus = AlgoMqttBus::busEnabled(config);
    if (config.enableAlarm && !mqttBus) {
        LOG(WARNING) << "[CONFIG] Alarm enabled but ALGO_BUS_TRANSPORT disabled "
                     << "(set MQTT_BROKER_URLS + leave ALGO_BUS_TRANSPORT=mqtt)";
    }
    if (config.enableAlarm && config.mqttBrokerUrls.empty()) {
        LOG(WARNING) << "[CONFIG] Alarm enabled but mqtt_broker_urls / MQTT_BROKER_URLS empty";
    }

    if (config.alertImageDir.empty() && !config.logPath.empty()) {
        // default next to log
        size_t slash = config.logPath.find_last_of("/\\");
        config.alertImageDir = (slash == std::string::npos)
            ? "alerts"
            : config.logPath.substr(0, slash) + "/alerts";
    }

    // Environment overrides (deploy / VIDEO daemon)
    if (const char* v = std::getenv("RUNTIME_FORCE_CPU")) {
        if (parseBool(v)) {
            config.forceCpu = true;
            config.preferGpu = false;
        }
    }
    if (const char* v = std::getenv("RUNTIME_PREFER_GPU")) {
        config.preferGpu = parseBool(v);
    }
    if (const char* v = std::getenv("USE_GPU")) {
        // Align with VIDEO python path: empty/true → prefer GPU; false → CPU
        std::string s = trim(v);
        std::transform(s.begin(), s.end(), s.begin(), ::tolower);
        if (s == "false" || s == "0" || s == "no" || s == "off") {
            config.preferGpu = false;
        } else if (!s.empty()) {
            config.preferGpu = true;
        }
    }
    if (const char* v = std::getenv("RUNTIME_GPU_DEVICE_ID")) {
        int id = parseInt(v);
        if (id >= 0) config.gpuDeviceId = id;
    }
    if (config.forceCpu) {
        config.preferGpu = false;
    }

    // hwaccel defaults to same GPU as ORT unless explicitly set in ini
    if (config.hwaccelDeviceId < 0) {
        config.hwaccelDeviceId = config.gpuDeviceId;
    }
    if (const char* v = std::getenv("RUNTIME_FORCE_SOFT_AV")) {
        if (parseBool(v)) {
            config.forceSoftAv = true;
            config.preferHwaccel = false;
        }
    }
    if (const char* v = std::getenv("RUNTIME_PREFER_HWACCEL")) {
        config.preferHwaccel = parseBool(v);
    }
    if (const char* v = std::getenv("RUNTIME_NVENC_PRESET")) {
        std::string s = trim(v);
        if (!s.empty()) config.nvencPreset = s;
    }
    // No GPU for inference → also avoid NVDEC/NVENC contention on CPU-only tasks
    if (config.forceCpu || !config.preferGpu) {
        config.forceSoftAv = true;
        config.preferHwaccel = false;
    }
    if (config.forceSoftAv) {
        config.preferHwaccel = false;
    }

    LOG(INFO) << "[CONFIG] AI prefer_gpu=" << (config.preferGpu ? "true" : "false")
              << " force_cpu=" << (config.forceCpu ? "true" : "false")
              << " gpu_device_id=" << config.gpuDeviceId
              << " prefer_hwaccel=" << (config.preferHwaccel ? "true" : "false")
              << " force_soft_av=" << (config.forceSoftAv ? "true" : "false")
              << " hwaccel_device_id=" << config.hwaccelDeviceId
              << " nvenc_preset=" << config.nvencPreset;

    return true;
}
