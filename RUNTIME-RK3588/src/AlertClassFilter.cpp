#include "AlertClassFilter.h"

#include <algorithm>
#include <cctype>
#include <json/json.h>
#include <unordered_set>

namespace AlertClassFilter {

std::string normalizeClassName(const std::string& className) {
    std::string out;
    out.reserve(className.size());
    for (char ch : className) {
        if (ch == '-') {
            out.push_back('_');
        } else if (ch == ' ') {
            out.push_back('_');
        } else {
            out.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
        }
    }
    return out;
}

std::vector<std::string> parseAlertClassNames(const std::string& raw) {
    std::vector<std::string> result;
    const std::string text = raw;
    if (text.empty()) {
        return result;
    }

    std::vector<std::string> names;
    if (text.front() == '[') {
        Json::Reader reader;
        Json::Value root;
        if (reader.parse(text, root) && root.isArray()) {
            for (const auto& item : root) {
                if (item.isString()) {
                    names.push_back(item.asString());
                } else if (!item.isNull()) {
                    names.push_back(item.asString());
                }
            }
        }
    } else {
        names.push_back(text);
    }

    std::unordered_set<std::string> seen;
    for (const auto& name : names) {
        std::string label = name;
        while (!label.empty() && std::isspace(static_cast<unsigned char>(label.front()))) {
            label.erase(label.begin());
        }
        while (!label.empty() && std::isspace(static_cast<unsigned char>(label.back()))) {
            label.pop_back();
        }
        if (label.empty()) {
            continue;
        }
        const std::string key = normalizeClassName(label);
        if (seen.count(key)) {
            continue;
        }
        seen.insert(key);
        result.push_back(label);
    }
    return result;
}

std::vector<DetectObject> filterDetectionsForAlert(
    const std::vector<DetectObject>& detections,
    const std::vector<std::string>& alertClassNames) {
    if (detections.empty()) {
        return {};
    }
    if (alertClassNames.empty()) {
        return detections;
    }

    std::unordered_set<std::string> allowed;
    allowed.reserve(alertClassNames.size());
    for (const auto& name : alertClassNames) {
        allowed.insert(normalizeClassName(name));
    }

    std::vector<DetectObject> filtered;
    filtered.reserve(detections.size());
    for (const auto& det : detections) {
        if (allowed.count(normalizeClassName(det.class_name))) {
            filtered.push_back(det);
        }
    }
    return filtered;
}

}  // namespace AlertClassFilter
