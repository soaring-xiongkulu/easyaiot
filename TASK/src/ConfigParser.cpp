/*
 * Configuration File Parser Implementation
 */

#include "ConfigParser.h"
#include <json/json.h>

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
                int x = point[0].asInt();
                int y = point[1].asInt();
                points.push_back(cv::Point(x, y));
            }
        }
        
        return points.size() >= 3;  // At least 3 points required for polygon
        
    } catch (const std::exception& e) {
        LOG(ERROR) << "[ERROR] Parse region exception: " << e.what();
        return false;
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
    std::string currentModel;  // Current model name (for multi-model config)
    
    while (std::getline(file, line)) {
        // Trim whitespace
        line = trim(line);
        
        // Skip empty lines and comments
        if (line.empty() || line[0] == '#' || line[0] == ';') {
            continue;
        }
        
        // Parse section name [section]
        if (line[0] == '[' && line[line.length()-1] == ']') {
            currentSection = line.substr(1, line.length()-2);
            currentSection = trim(currentSection);
            LOG(INFO) << "[CONFIG] Reading section: [" << currentSection << "]";
            continue;
        }
        
        // Parse key-value pair key=value
        size_t equalPos = line.find('=');
        if (equalPos == std::string::npos) {
            continue;
        }
        
        std::string key = trim(line.substr(0, equalPos));
        std::string value = trim(line.substr(equalPos + 1));
        
        // Parse config based on section and key name
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
            }
        }
        else if (currentSection == "ai") {
            if (key == "enable") {
                config.enableAI = parseBool(value);
            } else if (key == "model_path") {
                // Default model path
                currentModel = "default";
                config.modelPaths[currentModel] = value;
            } else if (key == "classes_path") {
                if (currentModel.empty()) currentModel = "default";
                config.modelClasses[currentModel] = value;
            } else if (key == "threads") {
                config.threadNums = parseInt(value);
                if (config.threadNums <= 0) config.threadNums = 3;
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
                    config.alarmConfidenceThreshold = 0.5f;  // 默认值
                }
            } else if (key == "cooldown_time") {
                config.alarmCooldownTime = parseInt(value);
                if (config.alarmCooldownTime < 0) {
                    config.alarmCooldownTime = 30;  // 默认30秒
                }
            }
        }
        else if (currentSection == "task") {
            if (key == "id") {
                config.taskId = value;
            } else if (key == "control_port") {
                config.controlPort = parseInt(value);
                if (config.controlPort < 8000 || config.controlPort > 9000) {
                    config.controlPort = 8000;  // 默认8000
                }
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
            // Alarm region configuration
            // Format: area_center=[[100,200],[300,400],[500,600]]
            std::vector<cv::Point> points;
            if (parseRegion(value, points)) {
                // ✅ 使用配置文件中的区域名称（key），而不是currentModel
                std::string regionName = key.empty() ? "default" : key;
                config.regions[regionName].push_back(points);
                LOG(INFO) << "  [OK] Alarm region '" << regionName << "' loaded: " << points.size() << " points";
            } else {
                LOG(WARNING) << "  [WARNING] Alarm region '" << key << "' parse failed";
            }
        }
    }
    
    file.close();
    
    // 楠岃瘉蹇呴渶閰嶇疆
    if (config.rtspUrl.empty()) {
        LOG(ERROR) << "[ERROR] Missing required config: rtsp_url";
        return false;
    }
    
    if (config.enableAI && config.modelPaths.empty()) {
        LOG(ERROR) << "[ERROR] AI inference enabled but model path not configured";
        return false;
    }
    
    if (config.enableAlarm && config.hookHttpUrl.empty()) {
        LOG(ERROR) << "[ERROR] Alarm detection enabled but callback URL not configured";
        return false;
    }
    
    return true;
}
