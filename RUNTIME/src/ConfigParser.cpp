/*
 * Configuration File Parser Implementation
 */

#include "ConfigParser.h"
#include "motion/MotionGate.h"
#include <json/json.h>
#include <sstream>
#include <cstdlib>

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
            }
        }
        else if (currentSection == "alarm") {
            if (key == "enable") {
                config.enableAlarm = parseBool(value);
            } else if (key == "hook_url") {
                config.hookHttpUrl = value;
            } else if (key == "confidence_threshold" || key == "detect_conf") {
                // CAP-INFER-THRESHOLD: VIDEO writes task.detect_conf → confidence_threshold.
                // Same value drives inference score_threshold and alarm confidence filter (Python parity).
                float conf = parseFloat(value);
                if (conf <= 0.0f || conf > 1.0f) {
                    conf = 0.5f;
                }
                config.detectConfidenceThreshold = conf;
                config.alarmConfidenceThreshold = conf;
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
                config.controlPort = parseInt(value);
                if (config.controlPort < 8000 || config.controlPort > 9000) {
                    config.controlPort = 8000;
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
            } else if (key == "devices_json") {
                parseDevicesJson(value, config.devices);
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
        else if (currentSection == "tracking") {
            if (key == "enabled") {
                config.trackingEnabled = parseBool(value);
            } else if (key == "similarity_threshold") {
                config.trackingSimilarityThreshold = parseFloat(value);
            } else if (key == "max_age") {
                config.trackingMaxAge = parseInt(value);
            } else if (key == "smooth_alpha") {
                config.trackingSmoothAlpha = parseFloat(value);
            }
        }
        else if (currentSection == "motion_gate") {
            if (key == "enabled") {
                config.motionGateEnabled = parseBool(value);
            } else if (key == "config_json") {
                config.motionGateConfigJson = value;
            }
        }
        else if (currentSection == "alert_filter" || currentSection == "hook") {
            if (key == "alert_class_names") {
                config.alertClassNamesJson = value;
            } else if (key == "face_detection_enabled") {
                config.faceDetectionEnabled = parseBool(value);
            } else if (key == "plate_detection_enabled") {
                config.plateDetectionEnabled = parseBool(value);
            }
        }
        else if (currentSection == "matching") {
            if (key == "face_matching_enabled") {
                config.faceMatchingEnabled = parseBool(value);
            } else if (key == "plate_matching_enabled") {
                config.plateMatchingEnabled = parseBool(value);
            }
        }
        else if (currentSection == "post_process") {
            if (key == "enabled") {
                config.postProcessEnabled = parseBool(value);
            }
        }
        else if (currentSection == "pose") {
            if (key == "analysis_enabled") {
                config.poseAnalysisEnabled = parseBool(value);
            } else if (key == "intent_enabled") {
                config.poseIntentEnabled = parseBool(value);
            }
        }
        else if (currentSection == "sam") {
            if (key == "supplement_enabled") {
                config.samSupplementEnabled = parseBool(value);
            }
        }
        else if (currentSection == "defense") {
            if (key == "mode") {
                config.defenseMode = value.empty() ? "half" : value;
            } else if (key == "schedule_json") {
                config.defenseScheduleJson = value;
            }
        }
        else if (currentSection == "patrol_extra") {
            if (key == "focus_device_id") {
                config.focusDeviceId = value;
            }
        }
        else if (currentSection == "models") {
            if (key == "extra_paths") {
                Json::Reader reader;
                Json::Value root;
                if (reader.parse(value, root) && root.isArray()) {
                    config.extraModelPaths.clear();
                    for (const auto& item : root) {
                        if (item.isString() && !item.asString().empty()) {
                            config.extraModelPaths.push_back(item.asString());
                        }
                    }
                }
            }
        }
        else if (currentSection == "stream_src") {
            if (key == "gb28181_enabled") {
                config.gb28181Enabled = parseBool(value);
            } else if (key == "gb28181_resolved") {
                config.gb28181Resolved = parseBool(value);
            } else if (key == "original_source") {
                config.streamOriginalSource = value;
            } else if (key == "resolved_url") {
                config.streamResolvedUrl = value;
            }
        }
        else if (currentSection == "encoder") {
            if (key == "nvenc_auto") {
                config.nvencAuto = parseBool(value);
            } else if (key == "quality_auto_downgrade") {
                config.qualityAutoDowngrade = parseBool(value);
            } else if (key == "quality_profile") {
                config.qualityProfile = value.empty() ? "high" : value;
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
        else if (currentSection == "contract" || currentSection == "unsupported") {
            // VIDEO-declared capabilities. Implemented frame-in / VIDEO-owned CAPs must
            // not remain as WARNING unsupported even if stale ini still lists them.
            static const char* kImplementedOrVideoOwned[] = {
                "CAP-TRACKING",
                "CAP-MOTION-GATE",
                "CAP-ALERT-CLASS-FILTER",
                "CAP-FACE-FILTER",
                "CAP-PLATE-FILTER",
                "CAP-FACE-MATCH",
                "CAP-PLATE-MATCH",
                "CAP-POST-PROCESS",
                "CAP-POSE",
                "CAP-DEFENSE",
                "CAP-PATROL-HYBRID",
                "CAP-PATROL-ROTATE",
                "CAP-MULTI-MODEL",
                "CAP-SNAP-SPACE",
                "CAP-GB28181-SRC",
                "CAP-NVENC-AUTO",
            };
            bool implemented = false;
            for (const char* known : kImplementedOrVideoOwned) {
                if (key == known) {
                    implemented = true;
                    break;
                }
            }
            if (implemented) {
                LOG(INFO) << "[CONFIG] cap=" << key
                          << " listed in [unsupported] but is implemented/VIDEO-owned; ignoring";
            } else if (!key.empty() && parseBool(value)) {
                config.unsupportedCaps.push_back(key);
                LOG(WARNING) << "[CONFIG] unsupported/deferred [" << currentSection << "] "
                             << key << "=" << value;
            } else {
                LOG(WARNING) << "[CONFIG] unsupported/deferred [" << currentSection << "] "
                             << key << "=" << value;
            }
        }
        else if (!currentSection.empty()) {
            LOG(WARNING) << "[CONFIG] unknown ini key ignored (no silent support): ["
                         << currentSection << "] " << key << "=" << value;
        }
    }

    file.close();

    // Ensure primary device stream exists
    if (!config.streamResolvedUrl.empty()) {
        // Prefer VIDEO-resolved pull URL (CAP-GB28181-SRC / stream adapter)
        config.rtspUrl = config.streamResolvedUrl;
    }
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
    // Reject silent gb28181:// passthrough into OpenCV/FFmpeg
    if (config.rtspUrl.size() >= 10) {
        std::string scheme = config.rtspUrl.substr(0, 10);
        std::transform(scheme.begin(), scheme.end(), scheme.begin(), ::tolower);
        if (scheme == "gb28181://") {
            LOG(ERROR) << "[ERROR] CAP-GB28181-SRC: rtsp_url still gb28181:// — "
                          "VIDEO must resolve before RUNTIME launch";
            return false;
        }
    }

    const std::string tt = config.taskType;
    const bool needsPersistentRtsp = (tt == "realtime" || tt.empty());
    if (needsPersistentRtsp && config.rtspUrl.empty()) {
        LOG(ERROR) << "[ERROR] Missing required config: rtsp_url";
        return false;
    }
    if ((tt == "snap" || tt == "patrol") && config.devices.empty()) {
        LOG(ERROR) << "[ERROR] snap/patrol requires at least one device stream";
        return false;
    }

    if (config.enableAI && config.modelPaths.empty()) {
        LOG(ERROR) << "[ERROR] AI inference enabled but model path not configured";
        return false;
    }

    if (!config.alertHookUrl.empty()) {
        config.hookHttpUrl = config.alertHookUrl;
    }

    if (config.enableAlarm && config.hookHttpUrl.empty()) {
        LOG(ERROR) << "[ERROR] Alarm detection enabled but callback URL not configured";
        return false;
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

    LOG(INFO) << "[CONFIG] AI prefer_gpu=" << (config.preferGpu ? "true" : "false")
              << " force_cpu=" << (config.forceCpu ? "true" : "false")
              << " gpu_device_id=" << config.gpuDeviceId;

    // G-2.3: derive unsupported caps — only truly unimplemented / product-vetoed.
    // Implemented frame-in CAPs and VIDEO-owned frame-post CAPs must NOT land here.
    auto addCap = [&](const std::string& cap) {
        if (std::find(config.unsupportedCaps.begin(), config.unsupportedCaps.end(), cap)
            == config.unsupportedCaps.end()) {
            config.unsupportedCaps.push_back(cap);
        }
    };
    if (config.trackingEnabled) {
        LOG(INFO) << "[CONFIG] CAP-TRACKING enabled similarity_threshold="
                  << config.trackingSimilarityThreshold << " max_age=" << config.trackingMaxAge;
    }
    if (config.motionGateEnabled) {
        LOG(INFO) << "[CONFIG] CAP-MOTION-GATE enabled config_json="
                  << (config.motionGateConfigJson.empty() ? "{}" : config.motionGateConfigJson);
    }
    if (!config.alertClassNamesJson.empty() && config.alertClassNamesJson != "[]") {
        LOG(INFO) << "[CONFIG] CAP-ALERT-CLASS-FILTER enabled names=" << config.alertClassNamesJson;
    }
    // CAP-FACE-FILTER / CAP-PLATE-FILTER: flags always honored in AlertFilters
    LOG(INFO) << "[CONFIG] CAP-FACE-FILTER face_detection_enabled="
              << (config.faceDetectionEnabled ? "true" : "false");
    LOG(INFO) << "[CONFIG] CAP-PLATE-FILTER plate_detection_enabled="
              << (config.plateDetectionEnabled ? "true" : "false");
    // VIDEO frame-post ownership (not C++ unsupported)
    if (config.faceMatchingEnabled) {
        LOG(INFO) << "[CONFIG] CAP-FACE-MATCH owned_by=VIDEO (hook post-orchestration)";
    }
    if (config.plateMatchingEnabled) {
        LOG(INFO) << "[CONFIG] CAP-PLATE-MATCH owned_by=VIDEO (hook post-orchestration)";
    }
    if (config.postProcessEnabled) {
        LOG(INFO) << "[CONFIG] CAP-POST-PROCESS owned_by=VIDEO (hook post-orchestration)";
    }
    if (config.poseAnalysisEnabled || config.poseIntentEnabled) {
        LOG(INFO) << "[CONFIG] CAP-POSE owned_by=VIDEO (hook post-orchestration)";
    }
    if (config.samSupplementEnabled) {
        addCap("CAP-SAM-TASK");
    }
    if (!config.defenseScheduleJson.empty() && config.defenseScheduleJson != "{}") {
        LOG(INFO) << "[CONFIG] CAP-DEFENSE enabled mode=" << config.defenseMode
                  << " schedule_json=" << config.defenseScheduleJson;
    }
    // CAP-PATROL-HYBRID implemented in PatrolScheduler (focus interval/2 + background pool).
    if (config.patrolMode == "hybrid" || !config.focusDeviceId.empty()) {
        LOG(INFO) << "[CONFIG] CAP-PATROL-HYBRID enabled mode=" << config.patrolMode
                  << " focus_device_id=" << config.focusDeviceId;
    }
    if (config.patrolMode == "rotate") {
        LOG(INFO) << "[CONFIG] CAP-PATROL-ROTATE enabled";
    }
    if (!config.extraModelPaths.empty()) {
        LOG(INFO) << "[CONFIG] CAP-MULTI-MODEL enabled extra_count="
                  << config.extraModelPaths.size();
    }
    if (config.gb28181Enabled) {
        if (config.gb28181Resolved && !config.streamResolvedUrl.empty()) {
            LOG(INFO) << "[CONFIG] CAP-GB28181-SRC enabled original="
                      << config.streamOriginalSource
                      << " resolved=" << config.streamResolvedUrl;
        } else {
            addCap("CAP-GB28181-SRC");
            LOG(WARNING) << "[CONFIG] CAP-GB28181-SRC requested but unresolved "
                            "(no silent success)";
        }
    }
    if (config.nvencAuto || config.qualityAutoDowngrade) {
        LOG(INFO) << "[CONFIG] CAP-NVENC-AUTO enabled nvenc_auto="
                  << (config.nvencAuto ? "true" : "false")
                  << " quality_auto_downgrade="
                  << (config.qualityAutoDowngrade ? "true" : "false")
                  << " quality_profile=" << config.qualityProfile;
    }
    for (const auto& cap : config.unsupportedCaps) {
        LOG(WARNING) << "[CONFIG] unsupported cap=" << cap
                     << " (declared in ini or derived from enabled task fields)";
    }

    return true;
}
