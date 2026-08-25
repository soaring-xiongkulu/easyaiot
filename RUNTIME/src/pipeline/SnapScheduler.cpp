#include "pipeline/SnapScheduler.h"

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <glog/logging.h>
#include <opencv2/geometry.hpp>
#include <sstream>

#include "AlgoMqttBus.h"
#include "YoloThreadPool.h"

namespace runtime {

namespace {

bool looksNormalized(const std::vector<cv::Point>& polygon) {
    if (polygon.empty()) {
        return false;
    }
    for (const auto& p : polygon) {
        if (p.x < 0 || p.y < 0 || p.x > 10000 || p.y > 10000) {
            return false;
        }
    }
    return true;
}

std::vector<cv::Point> scalePolygon(const std::vector<cv::Point>& polygon, int width, int height) {
    if (!looksNormalized(polygon)) {
        return polygon;
    }
    std::vector<cv::Point> scaled;
    scaled.reserve(polygon.size());
    for (const auto& p : polygon) {
        scaled.emplace_back(static_cast<int>(p.x * width / 10000.0),
                            static_cast<int>(p.y * height / 10000.0));
    }
    return scaled;
}

bool pointInRegions(const Config& config, int cx, int cy, int width, int height, std::string& regionName) {
    if (config.regions.empty()) {
        regionName = "全画面";
        return true;
    }
    cv::Point2f center(static_cast<float>(cx), static_cast<float>(cy));
    for (const auto& regionPair : config.regions) {
        for (const auto& polygon : regionPair.second) {
            if (polygon.size() < 3) {
                continue;
            }
            auto scaled = scalePolygon(polygon, width, height);
            if (cv::pointPolygonTest(scaled, center, false) >= 0) {
                regionName = regionPair.first;
                return true;
            }
        }
    }
    return false;
}

bool matchCronField(const std::string& field, int value) {
    if (field == "*" || field.empty()) {
        return true;
    }
    if (field.size() >= 3 && field[0] == '*' && field[1] == '/') {
        int step = std::atoi(field.c_str() + 2);
        return step > 0 && (value % step) == 0;
    }
    int num = std::atoi(field.c_str());
    return num == value;
}

bool parseCronFields(const std::string& expr, std::string& minute, std::string& hour) {
    std::istringstream iss(expr);
    std::string rest;
    if (!(iss >> minute >> hour)) {
        return false;
    }
    // Remaining day/month/dow ignored (expect "* * *")
    return true;
}

}  // namespace

SnapScheduler::SnapScheduler(Config& config, YoloThreadPool* pool, AlarmFn alarmFn)
    : config_(config), pool_(pool), alarmFn_(std::move(alarmFn)) {}

SnapScheduler::~SnapScheduler() {
    stop();
    join();
    for (auto& cap : caps_) {
        if (cap.isOpened()) {
            cap.release();
        }
    }
}

void SnapScheduler::start() {
    if (running_.exchange(true)) {
        return;
    }
    if (config_.devices.empty()) {
        LOG(ERROR) << "[SNAP] no devices configured";
        running_.store(false);
        return;
    }
    caps_.resize(config_.devices.size());
    LOG(INFO) << "[SNAP] starting scheduler for " << config_.devices.size() << " device(s)"
              << " cron=\"" << config_.cronExpression << "\""
              << " frameSkip=" << config_.frameSkip << "s";
    thread_ = std::thread(&SnapScheduler::loop, this);
}

void SnapScheduler::stop() {
    running_.store(false);
}

void SnapScheduler::join() {
    if (thread_.joinable()) {
        thread_.join();
    }
}

bool SnapScheduler::cronDue(std::time_t now, std::string& slotKey) {
    std::tm tm{};
    localtime_r(&now, &tm);
    char buf[32];
    std::snprintf(buf, sizeof(buf), "%04d%02d%02d%02d%02d",
                  tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday, tm.tm_hour, tm.tm_min);
    slotKey = buf;
    if (slotKey == lastSlot_) {
        return false;
    }

    std::string minute;
    std::string hour;
    if (!parseCronFields(config_.cronExpression, minute, hour)) {
        return false;
    }
    if (!matchCronField(minute, tm.tm_min) || !matchCronField(hour, tm.tm_hour)) {
        return false;
    }
    return true;
}

bool SnapScheduler::ensureCapture(size_t idx) {
    if (idx >= caps_.size() || idx >= config_.devices.size()) {
        return false;
    }
    auto& cap = caps_[idx];
    if (cap.isOpened()) {
        return true;
    }
    const auto& device = config_.devices[idx];
    LOG(INFO) << "[SNAP] opening stream device=" << device.deviceId << " url=" << device.rtspUrl;
    if (!cap.open(device.rtspUrl, cv::CAP_FFMPEG)) {
        LOG(WARNING) << "[SNAP] open failed device=" << device.deviceId;
        return false;
    }
    cap.set(cv::CAP_PROP_BUFFERSIZE, 1);
    return true;
}

bool SnapScheduler::grabFrame(size_t idx, cv::Mat& out) {
    if (!ensureCapture(idx)) {
        return false;
    }
    auto& cap = caps_[idx];
    cv::Mat frame;
    if (!cap.read(frame) || frame.empty()) {
        LOG(WARNING) << "[SNAP] read failed, reopening device=" << config_.devices[idx].deviceId;
        cap.release();
        if (!ensureCapture(idx)) {
            return false;
        }
        if (!caps_[idx].read(frame) || frame.empty()) {
            return false;
        }
    }
    out = frame;
    return true;
}

void SnapScheduler::processDevice(size_t idx, const cv::Mat& frame) {
    if (!pool_ || !config_.enableAI) {
        return;
    }
    const auto& device = config_.devices[idx];
    int fid = frameId_.fetch_add(1, std::memory_order_relaxed);
    int inputId = static_cast<int>(idx);

    // 多模型：每帧提交全部模型，合并各模型检测结果
    const size_t modelCount = pool_->modelCount();
    for (size_t m = 0; m < modelCount; ++m) {
        pool_->submitTask(frame, static_cast<int>(m), inputId, fid);
    }
    std::vector<DetectObject> detections;
    for (size_t m = 0; m < modelCount; ++m) {
        std::vector<DetectObject> modelDets;
        if (pool_->getTargetResult(modelDets, static_cast<int>(m), inputId, fid) != 0) {
            return;
        }
        detections.insert(detections.end(), modelDets.begin(), modelDets.end());
    }

    std::vector<DetectObject> alarmDetections;
    std::string regionName = "全画面";
    const bool skipRegionGate = AlgoMqttBus::postEnabled();
    for (const auto& det : detections) {
        if (config_.enableAlarm && det.class_score < config_.alarmConfidenceThreshold) {
            continue;
        }
        if (!skipRegionGate) {
            int cx = (static_cast<int>(det.x1) + static_cast<int>(det.x2)) / 2;
            int cy = (static_cast<int>(det.y1) + static_cast<int>(det.y2)) / 2;
            std::string matched;
            if (!pointInRegions(config_, cx, cy, frame.cols, frame.rows, matched)) {
                continue;
            }
            regionName = matched;
        }
        alarmDetections.push_back(det);
    }

    if (!alarmDetections.empty() && alarmFn_ && config_.enableAlarm) {
        LOG(INFO) << "[SNAP] alarm device=" << device.deviceId
                  << " dets=" << alarmDetections.size()
                  << " region=" << regionName;
        alarmFn_(alarmDetections, regionName, device.deviceId, device.deviceName, frame);
    }
}

void SnapScheduler::loop() {
    LOG(INFO) << "[SNAP] loop started";
    while (running_.load()) {
        std::time_t now = std::time(nullptr);
        bool fire = false;
        std::string slotKey;

        if (config_.cronExpression.empty()) {
            int interval = std::max(1, config_.frameSkip);
            if (lastIntervalFire_ == 0 || (now - lastIntervalFire_) >= interval) {
                fire = true;
                lastIntervalFire_ = now;
            }
        } else if (cronDue(now, slotKey)) {
            fire = true;
            lastSlot_ = slotKey;
            LOG(INFO) << "[SNAP] cron slot fired: " << slotKey;
        }

        if (fire) {
            for (size_t i = 0; i < config_.devices.size() && running_.load(); ++i) {
                cv::Mat frame;
                if (!grabFrame(i, frame)) {
                    continue;
                }
                processDevice(i, frame);
            }
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }
    LOG(INFO) << "[SNAP] loop exit";
}

}  // namespace runtime
