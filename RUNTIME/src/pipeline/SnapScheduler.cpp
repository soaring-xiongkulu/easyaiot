#include "pipeline/SnapScheduler.h"

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <glog/logging.h>
#include <opencv2/imgproc.hpp>
#include <sstream>

#include "Yolov11ThreadPool.h"
#include "cron/CronUtils.h"
#include "win_compat.h"

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

}  // namespace

SnapScheduler::SnapScheduler(Config& config, Yolov11ThreadPool* pool, AlarmFn alarmFn)
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
              << " frameSkip=" << config_.frameSkip << "s"
              << " (CAP-CRON-SNAP: Asia/Shanghai 6-field)";
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

bool SnapScheduler::cronDueForDevice(size_t idx, std::time_t now, std::string& slotKey) {
    bool inWindow = false;
    double offset = 0.0;
    std::time_t fireEpoch = 0;
    if (!cron::slotForTime(config_.cronExpression, now, inWindow, slotKey, offset, fireEpoch)) {
        return false;
    }
    if (!inWindow || slotKey.empty()) {
        return false;
    }
    const std::string& deviceId = config_.devices[idx].deviceId;
    auto it = lastSlotByDevice_.find(deviceId);
    if (it != lastSlotByDevice_.end() && it->second == slotKey) {
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

void SnapScheduler::processDevice(size_t idx, const cv::Mat& frame, const std::string& slotKey) {
    if (!pool_ || !config_.enableAI) {
        return;
    }
    const auto& device = config_.devices[idx];
    int fid = frameId_.fetch_add(1, std::memory_order_relaxed);
    int inputId = static_cast<int>(idx);

    pool_->submitTask(frame, inputId, fid);
    std::vector<DetectObject> detections;
    if (pool_->getTargetResult(detections, inputId, fid) != 0) {
        return;
    }

    std::vector<DetectObject> alarmDetections;
    std::string regionName = "全画面";
    for (const auto& det : detections) {
        if (config_.enableAlarm && det.class_score < config_.alarmConfidenceThreshold) {
            continue;
        }
        int cx = (static_cast<int>(det.x1) + static_cast<int>(det.x2)) / 2;
        int cy = (static_cast<int>(det.y1) + static_cast<int>(det.y2)) / 2;
        std::string matched;
        if (!pointInRegions(config_, cx, cy, frame.cols, frame.rows, matched)) {
            continue;
        }
        regionName = matched;
        alarmDetections.push_back(det);
    }

    if (!alarmDetections.empty() && alarmFn_ && config_.enableAlarm) {
        LOG(INFO) << "[SNAP] alarm device=" << device.deviceId
                  << " dets=" << alarmDetections.size()
                  << " region=" << regionName
                  << " slot=" << slotKey;
        alarmFn_(alarmDetections, regionName, device.deviceId, device.deviceName, frame);
    }
}

void SnapScheduler::loop() {
    LOG(INFO) << "[SNAP] loop started";
    while (running_.load()) {
        std::time_t now = std::time(nullptr);

        if (config_.cronExpression.empty()) {
            // CAP-CRON-NO-FALLBACK: no cron → frameSkip-second interval (product: differs from
            // Python ~0.1s continuous extract; intentional cpp sampling interval).
            int interval = std::max(1, config_.frameSkip);
            if (lastIntervalFire_ == 0 || (now - lastIntervalFire_) >= interval) {
                lastIntervalFire_ = now;
                for (size_t i = 0; i < config_.devices.size() && running_.load(); ++i) {
                    cv::Mat frame;
                    if (!grabFrame(i, frame)) {
                        continue;
                    }
                    const std::string slotKey = "interval_" + std::to_string(now);
                    parityRecorder_.recordScheduleEvent(
                        "snap_interval", config_.devices[i].deviceId, slotKey, now);
                    processDevice(i, frame, slotKey);
                }
                parityRecorder_.maybeFlush(config_.logPath);
            }
        } else {
            // Per-device cron window + slot dedupe (Python should_extract_frame_by_cron).
            for (size_t i = 0; i < config_.devices.size() && running_.load(); ++i) {
                std::string slotKey;
                if (!cronDueForDevice(i, now, slotKey)) {
                    continue;
                }
                cv::Mat frame;
                if (!grabFrame(i, frame)) {
                    continue;
                }
                lastSlotByDevice_[config_.devices[i].deviceId] = slotKey;
                LOG(INFO) << "[SNAP] cron slot fired device=" << config_.devices[i].deviceId
                          << " slot=" << slotKey;
                parityRecorder_.recordScheduleEvent(
                    "cron_slot", config_.devices[i].deviceId, slotKey, now);
                processDevice(i, frame, slotKey);
                parityRecorder_.maybeFlush(config_.logPath);
            }
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }
    parityRecorder_.writeToFile(config_.logPath);
    LOG(INFO) << "[SNAP] loop exit";
}

}  // namespace runtime
