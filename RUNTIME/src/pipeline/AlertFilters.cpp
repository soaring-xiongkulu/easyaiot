#include "pipeline/AlertFilters.h"

#include <algorithm>
#include <cctype>
#include <chrono>
#include <ctime>
#include <json/json.h>
#include <glog/logging.h>

namespace runtime {
namespace {

std::string toLowerCopy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return s;
}

int parseHmToMinutes(const std::string& hm) {
    // HH:MM
    if (hm.size() < 4) {
        return -1;
    }
    const auto colon = hm.find(':');
    if (colon == std::string::npos) {
        return -1;
    }
    try {
        int h = std::stoi(hm.substr(0, colon));
        int m = std::stoi(hm.substr(colon + 1));
        if (h < 0 || h > 23 || m < 0 || m > 59) {
            return -1;
        }
        return h * 60 + m;
    } catch (...) {
        return -1;
    }
}

}  // namespace

std::string normalizeClassName(const std::string& name) {
    std::string out;
    out.reserve(name.size());
    for (unsigned char c : name) {
        if (c == '-' || c == ' ') {
            out.push_back('_');
        } else {
            out.push_back(static_cast<char>(std::tolower(c)));
        }
    }
    // trim
    size_t a = out.find_first_not_of(" \t\r\n");
    if (a == std::string::npos) {
        return "";
    }
    size_t b = out.find_last_not_of(" \t\r\n");
    return out.substr(a, b - a + 1);
}

std::vector<std::string> parseAlertClassNames(const std::string& jsonOrList) {
    std::vector<std::string> result;
    if (jsonOrList.empty()) {
        return result;
    }
    Json::Reader reader;
    Json::Value root;
    if (reader.parse(jsonOrList, root) && root.isArray()) {
        for (const auto& item : root) {
            if (!item.isString()) {
                continue;
            }
            std::string label = item.asString();
            size_t a = label.find_first_not_of(" \t\r\n");
            if (a == std::string::npos) {
                continue;
            }
            size_t b = label.find_last_not_of(" \t\r\n");
            label = label.substr(a, b - a + 1);
            if (!label.empty()) {
                result.push_back(label);
            }
        }
        return result;
    }
    // fallback: comma-separated or single token
    std::string cur;
    for (char ch : jsonOrList) {
        if (ch == ',' || ch == ';') {
            auto n = normalizeClassName(cur);
            if (!n.empty()) {
                result.push_back(cur);
            }
            cur.clear();
        } else {
            cur.push_back(ch);
        }
    }
    if (!cur.empty()) {
        size_t a = cur.find_first_not_of(" \t\r\n");
        if (a != std::string::npos) {
            size_t b = cur.find_last_not_of(" \t\r\n");
            result.push_back(cur.substr(a, b - a + 1));
        }
    }
    return result;
}

bool isFaceClass(const std::string& className) {
    const std::string n = normalizeClassName(className);
    static const char* kws[] = {"face", "facial", "person_face", "人脸"};
    for (const char* kw : kws) {
        if (n.find(normalizeClassName(kw)) != std::string::npos) {
            return true;
        }
    }
    return false;
}

bool isPlateClass(const std::string& className) {
    const std::string n = normalizeClassName(className);
    static const char* kws[] = {"plate", "license_plate", "licence_plate", "car_plate", "车牌"};
    for (const char* kw : kws) {
        if (n.find(normalizeClassName(kw)) != std::string::npos) {
            return true;
        }
    }
    return false;
}

std::vector<DetectObject> filterDetectionsForAlert(
    const std::vector<DetectObject>& detections,
    const Config& config) {
    std::vector<DetectObject> kept;
    kept.reserve(detections.size());

    const auto whitelist = parseAlertClassNames(config.alertClassNamesJson);
    std::vector<std::string> allowedNorm;
    allowedNorm.reserve(whitelist.size());
    for (const auto& w : whitelist) {
        allowedNorm.push_back(normalizeClassName(w));
    }

    for (const auto& det : detections) {
        if (!config.faceDetectionEnabled && isFaceClass(det.class_name)) {
            continue;
        }
        if (!config.plateDetectionEnabled && isPlateClass(det.class_name)) {
            continue;
        }
        if (!allowedNorm.empty()) {
            const std::string n = normalizeClassName(det.class_name);
            if (std::find(allowedNorm.begin(), allowedNorm.end(), n) == allowedNorm.end()) {
                continue;
            }
        }
        kept.push_back(det);
    }
    return kept;
}

bool isDefenseArmed(const Config& config) {
    const std::string& raw = config.defenseScheduleJson;
    if (raw.empty() || raw == "{}" || raw == "null") {
        return true;
    }

    Json::Reader reader;
    Json::Value root;
    if (!reader.parse(raw, root) || !root.isObject()) {
        LOG(WARNING) << "[DEFENSE] schedule_json parse failed; treating as armed (fail-open)";
        return true;
    }

    if (root.isMember("active") && root["active"].isBool()) {
        const bool active = root["active"].asBool();
        if (!active) {
            LOG(INFO) << "[DEFENSE] CAP-DEFENSE active=false → skip alerts mode="
                      << config.defenseMode;
        }
        return active;
    }

    if (!root.isMember("windows") || !root["windows"].isArray() || root["windows"].empty()) {
        return true;
    }

    using clock = std::chrono::system_clock;
    const std::time_t now = clock::to_time_t(clock::now());
    std::tm localTm{};
#ifdef _WIN32
    localtime_s(&localTm, &now);
#else
    localtime_r(&now, &localTm);
#endif
    const int minutes = localTm.tm_hour * 60 + localTm.tm_min;
    // tm_wday: 0=Sunday … 6=Saturday
    const int wday = localTm.tm_wday;

    for (const auto& win : root["windows"]) {
        if (!win.isObject()) {
            continue;
        }
        bool dayOk = true;
        if (win.isMember("days") && win["days"].isArray() && !win["days"].empty()) {
            dayOk = false;
            for (const auto& d : win["days"]) {
                if (d.isInt() && d.asInt() == wday) {
                    dayOk = true;
                    break;
                }
            }
        }
        if (!dayOk) {
            continue;
        }
        const int start = parseHmToMinutes(win.get("start", "00:00").asString());
        const int end = parseHmToMinutes(win.get("end", "23:59").asString());
        if (start < 0 || end < 0) {
            continue;
        }
        if (start <= end) {
            if (minutes >= start && minutes <= end) {
                return true;
            }
        } else {
            // overnight window
            if (minutes >= start || minutes <= end) {
                return true;
            }
        }
    }

    LOG(INFO) << "[DEFENSE] CAP-DEFENSE outside schedule windows → skip alerts mode="
              << config.defenseMode;
    return false;
}

}  // namespace runtime
