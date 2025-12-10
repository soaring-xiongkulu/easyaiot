/*
 * HTTP Alarm Callback Implementation
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
    
    // 创建HTTP客户端
    std::string baseUrl = host_;
    if (port_ != 80 && port_ != 443) {
        baseUrl = host_ + ":" + std::to_string(port_);
    }
    
    client_ = new httplib::Client(baseUrl.c_str());
    client_->set_connection_timeout(5, 0);  // 5秒超时
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
    // 简单的URL解析
    // 支持格式: http://host:port/path 或 http://host/path
    
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
    
    // 解析host和port
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

std::string AlarmCallback::buildJsonBody(
    int taskId,
    const std::vector<DetectObject>& detections,
    const std::string& regionId,
    const std::string& timestamp
) {
    // ========== 主JSON对象 ==========
    Json::Value root;
    
    // ⭐ 修改为Java驼峰命名格式，匹配AlarmService期望
    root["taskId"] = "task_" + std::to_string(taskId);  // 转为字符串
    root["alarmType"] = "region_intrusion";              // 新增：告警类型
    root["regionName"] = regionId;                       // 驼峰命名
    root["timestamp"] = timestamp;
    root["detectionCount"] = static_cast<int>(detections.size());  // 驼峰命名
    
    // ========== 构建检测结果数组（稍后转为JSON字符串）==========
    Json::Value detectionsArray(Json::arrayValue);
    for (const auto& det : detections) {
        Json::Value detection;
        detection["class_name"] = det.class_name;      // 只保留必要字段
        detection["confidence"] = det.class_score;
        
        // ⭐ 计算中心点坐标（新增）
        int centerX = static_cast<int>((det.x1 + det.x2) / 2.0f);
        int centerY = static_cast<int>((det.y1 + det.y2) / 2.0f);
        detection["centerX"] = centerX;
        detection["centerY"] = centerY;
        
        // bbox保持为数组格式 [x1, y1, x2, y2]
        Json::Value bbox(Json::arrayValue);
        bbox.append(static_cast<int>(det.x1));
        bbox.append(static_cast<int>(det.y1));
        bbox.append(static_cast<int>(det.x2));
        bbox.append(static_cast<int>(det.y2));
        detection["bbox"] = bbox;
        
        detectionsArray.append(detection);
    }
    
    // ⭐ 关键：将detections数组转为JSON字符串（不是直接嵌入数组）
    Json::StreamWriterBuilder compactWriter;
    compactWriter["indentation"] = "";  // 紧凑格式
    root["detectionsJson"] = Json::writeString(compactWriter, detectionsArray);
    
    // ⭐ 可选字段：告警截图URL（暂时留空）
    root["snapshotUrl"] = "";
    
    // ========== 输出最终JSON字符串 ==========
    Json::StreamWriterBuilder writer;
    writer["indentation"] = "";  // 紧凑格式
    return Json::writeString(writer, root);
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
        return true;  // 无检测结果，不发送
    }
    
    // 构建JSON请求体
    std::string jsonBody = buildJsonBody(taskId, detections, regionId, timestamp);
    
    LOG(INFO) << "📤 发送告警回调: task_id=" << taskId 
              << ", region=" << regionId 
              << ", detections=" << detections.size();
    
    // 发送POST请求
    httplib::Headers headers = {
        {"Content-Type", "application/json"}
    };
    
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
    
    LOG(INFO) << "[OK] Alarm callback sent successfully: " << res->body;
    return true;
}

bool AlarmCallback::testConnection() {
    if (!client_) {
        return false;
    }
    
    // 发送一个测试请求（可选）
    LOG(INFO) << "[TEST] Testing callback connection: " << hookUrl_;
    
    // 简单返回true，实际连接会在第一次sendAlarm时测试
    return true;
}
