/*
 * HTTP Alarm Callback Implementation — VIDEO alert hook schema
 */

#include "AlarmCallback.h"
#include <sstream>
#include <iomanip>
#include <chrono>
#include <ctime>

AlarmCallback::AlarmCallback(const std::string& hookUrl)
    : hookUrl_(hookUrl), port_(0), client_(nullptr) {

    if (!parseUrl(hookUrl, host_, port_, path_)) {
        LOG(ERROR) << "[ERROR] Invalid callback URL: " << hookUrl;
        return;
    }

    std::string baseUrl = host_;
    if (port_ != 80 && port_ != 443) {
        baseUrl = host_ + ":" + std::to_string(port_);
    }

    client_ = new httplib::Client(baseUrl.c_str());
    client_->set_connection_timeout(5, 0);
    client_->set_read_timeout(5, 0);
    client_->set_write_timeout(5, 0);

    LOG(INFO) << "[OK] HTTP callback client created: " << baseUrl << path_;
}

AlarmCallback::~AlarmCallback() {
    if (client_) {
        delete client_;
        client_ = nullptr;
    }
}

bool AlarmCallback::parseUrl(const std::string& url, std::string& host, int& port, std::string& path) {
    size_t protocolPos = url.find("://");
    if (protocolPos == std::string::npos) {
        return false;
    }

    std::string urlWithoutProtocol = url.substr(protocolPos + 3);
    size_t pathPos = urlWithoutProtocol.find('/');
    std::string hostPort;

    if (pathPos != std::string::npos) {
        hostPort = urlWithoutProtocol.substr(0, pathPos);
        path = urlWithoutProtocol.substr(pathPos);
    } else {
        hostPort = urlWithoutProtocol;
        path = "/";
    }

    size_t colonPos = hostPort.find(':');
    if (colonPos != std::string::npos) {
        host = hostPort.substr(0, colonPos);
        try {
            port = std::stoi(hostPort.substr(colonPos + 1));
        } catch (...) {
            port = 80;
        }
    } else {
        host = hostPort;
        port = 80;
    }

    return !host.empty();
}

std::string AlarmCallback::buildVideoJsonBody(
    const VideoAlertContext& ctx,
    const std::vector<DetectObject>& detections,
    const std::string& regionId,
    const std::string& timestamp,
    const std::string& imagePath
) {
    Json::Value root;
    std::string primaryObject = detections.empty() ? "object" : detections.front().class_name;
    root["object"] = primaryObject;
    root["event"] = ctx.algorithmName.empty() ? "detection" : ctx.algorithmName;
    root["device_id"] = ctx.deviceId;
    root["device_name"] = ctx.deviceName.empty() ? ctx.deviceId : ctx.deviceName;
    root["task_type"] = ctx.taskType.empty() ? "realtime" : ctx.taskType;
    root["correlation_id"] = ctx.taskId + "_" + timestamp;
    root["time"] = timestamp;
    root["image_path"] = imagePath;
    root["region"] = regionId;

    Json::Value info;
    info["task_id"] = ctx.taskId;
    info["region"] = regionId;
    info["detection_count"] = static_cast<int>(detections.size());
    Json::Value detectionsArray(Json::arrayValue);
    for (const auto& det : detections) {
        Json::Value detection;
        detection["class_name"] = det.class_name;
        detection["confidence"] = det.class_score;
        detection["class_id"] = det.class_id;
        Json::Value bbox(Json::arrayValue);
        bbox.append(static_cast<int>(det.x1));
        bbox.append(static_cast<int>(det.y1));
        bbox.append(static_cast<int>(det.x2));
        bbox.append(static_cast<int>(det.y2));
        detection["bbox"] = bbox;
        detectionsArray.append(detection);
    }
    info["detections"] = detectionsArray;

    Json::StreamWriterBuilder compactWriter;
    compactWriter["indentation"] = "";
    root["information"] = Json::writeString(compactWriter, info);

    Json::StreamWriterBuilder writer;
    writer["indentation"] = "";
    return Json::writeString(writer, root);
}

std::string AlarmCallback::buildLegacyJsonBody(
    int taskId,
    const std::vector<DetectObject>& detections,
    const std::string& regionId,
    const std::string& timestamp
) {
    Json::Value root;
    root["taskId"] = "task_" + std::to_string(taskId);
    root["alarmType"] = "region_intrusion";
    root["regionName"] = regionId;
    root["timestamp"] = timestamp;
    root["detectionCount"] = static_cast<int>(detections.size());

    Json::Value detectionsArray(Json::arrayValue);
    for (const auto& det : detections) {
        Json::Value detection;
        detection["class_name"] = det.class_name;
        detection["confidence"] = det.class_score;
        int centerX = static_cast<int>((det.x1 + det.x2) / 2.0f);
        int centerY = static_cast<int>((det.y1 + det.y2) / 2.0f);
        detection["centerX"] = centerX;
        detection["centerY"] = centerY;
        Json::Value bbox(Json::arrayValue);
        bbox.append(static_cast<int>(det.x1));
        bbox.append(static_cast<int>(det.y1));
        bbox.append(static_cast<int>(det.x2));
        bbox.append(static_cast<int>(det.y2));
        detection["bbox"] = bbox;
        detectionsArray.append(detection);
    }

    Json::StreamWriterBuilder compactWriter;
    compactWriter["indentation"] = "";
    root["detectionsJson"] = Json::writeString(compactWriter, detectionsArray);
    root["snapshotUrl"] = "";

    Json::StreamWriterBuilder writer;
    writer["indentation"] = "";
    return Json::writeString(writer, root);
}

bool AlarmCallback::sendVideoAlert(
    const VideoAlertContext& ctx,
    const std::vector<DetectObject>& detections,
    const std::string& regionId,
    const std::string& timestamp,
    const std::string& imagePath
) {
    if (!client_) {
        LOG(ERROR) << "[ERROR] HTTP client not initialized";
        return false;
    }
    if (detections.empty()) {
        return true;
    }

    std::string jsonBody = buildVideoJsonBody(ctx, detections, regionId, timestamp, imagePath);
    LOG(INFO) << "Sending VIDEO alert hook: device_id=" << ctx.deviceId
              << ", event=" << ctx.algorithmName
              << ", detections=" << detections.size();

    httplib::Headers headers = {{"Content-Type", "application/json"}};
    auto res = client_->Post(path_.c_str(), headers, jsonBody, "application/json");
    if (!res) {
        LOG(ERROR) << "[ERROR] HTTP request failed: " << httplib::to_string(res.error());
        return false;
    }
    if (res->status != 200) {
        LOG(ERROR) << "[ERROR] HTTP response error: status=" << res->status
                   << ", body=" << res->body;
        return false;
    }
    LOG(INFO) << "[OK] VIDEO alert hook accepted";
    return true;
}

bool AlarmCallback::sendAlarm(
    int taskId,
    const std::vector<DetectObject>& detections,
    const std::string& regionId,
    const std::string& timestamp
) {
    if (!client_) {
        LOG(ERROR) << "[ERROR] HTTP client not initialized";
        return false;
    }
    if (detections.empty()) {
        return true;
    }

    std::string jsonBody = buildLegacyJsonBody(taskId, detections, regionId, timestamp);
    httplib::Headers headers = {{"Content-Type", "application/json"}};
    auto res = client_->Post(path_.c_str(), headers, jsonBody, "application/json");
    if (!res) {
        LOG(ERROR) << "[ERROR] HTTP request failed: " << httplib::to_string(res.error());
        return false;
    }
    if (res->status != 200) {
        LOG(ERROR) << "[ERROR] HTTP response error: status=" << res->status;
        return false;
    }
    return true;
}

bool AlarmCallback::testConnection() {
    return client_ != nullptr;
}
