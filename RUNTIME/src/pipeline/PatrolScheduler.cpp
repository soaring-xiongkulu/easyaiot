#include "pipeline/PatrolScheduler.h"

#include <algorithm>
#include <chrono>
#include <glog/logging.h>
#include <opencv2/geometry.hpp>

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

}  // namespace

PatrolScheduler::PatrolScheduler(Config& config, YoloThreadPool* pool, AlarmFn alarmFn)
    : config_(config), pool_(pool), alarmFn_(std::move(alarmFn)) {}

PatrolScheduler::~PatrolScheduler() {
    stop();
    join();
}

void PatrolScheduler::start() {
    if (running_.exchange(true)) {
        return;
    }
    if (config_.devices.empty()) {
        LOG(ERROR) << "[PATROL] no devices configured";
        running_.store(false);
        return;
    }
    lastPatrolTime_.assign(config_.devices.size(), 0);
    LOG(INFO) << "[PATROL] starting scheduler for " << config_.devices.size() << " device(s)"
              << " mode=" << config_.patrolMode
              << " interval=" << config_.patrolIntervalSec << "s"
              << " pool_size=" << config_.patrolPoolSize;
    thread_ = std::thread(&PatrolScheduler::loop, this);
}

void PatrolScheduler::stop() {
    running_.store(false);
}

void PatrolScheduler::join() {
    if (thread_.joinable()) {
        thread_.join();
    }
}

bool PatrolScheduler::grabOneShot(const DeviceStreamConfig& device, cv::Mat& out) {
    cv::VideoCapture cap;
    if (!cap.open(device.rtspUrl, cv::CAP_FFMPEG)) {
        LOG(WARNING) << "[PATROL] open failed device=" << device.deviceId;
        return false;
    }
    cap.set(cv::CAP_PROP_BUFFERSIZE, 1);

    cv::Mat frame;
    // Warm up ~5 frames then take one good frame
    for (int i = 0; i < 5; ++i) {
        if (!cap.read(frame)) {
            cap.release();
            return false;
        }
    }
    if (!cap.read(frame) || frame.empty()) {
        cap.release();
        return false;
    }
    out = frame.clone();
    cap.release();
    return true;
}

void PatrolScheduler::processDevice(const DeviceStreamConfig& device, const cv::Mat& frame) {
    totalPatrols.fetch_add(1, std::memory_order_relaxed);
    if (!pool_ || !config_.enableAI) {
        return;
    }

    int fid = frameId_.fetch_add(1, std::memory_order_relaxed);
    // Use device index hash as input_id to avoid collisions across concurrent pool batches
    int inputId = 1;
    for (size_t i = 0; i < config_.devices.size(); ++i) {
        if (config_.devices[i].deviceId == device.deviceId) {
            inputId = static_cast<int>(i) + 1;
            break;
        }
    }

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

    if (!alarmDetections.empty()) {
        totalDetections.fetch_add(alarmDetections.size(), std::memory_order_relaxed);
        if (alarmFn_ && config_.enableAlarm) {
            LOG(INFO) << "[PATROL] alarm device=" << device.deviceId
                      << " dets=" << alarmDetections.size()
                      << " region=" << regionName;
            alarmFn_(alarmDetections, regionName, device.deviceId, device.deviceName, frame);
        }
    }
}

void PatrolScheduler::loop() {
    LOG(INFO) << "[PATROL] loop started";
    const size_t n = config_.devices.size();
    const int baseInterval = std::max(3, config_.patrolIntervalSec);
    const bool rotateMode = (config_.patrolMode == "rotate");

    while (running_.load()) {
        std::time_t now = std::time(nullptr);

        if (rotateMode) {
            int interval = std::max(3, baseInterval / static_cast<int>(std::max<size_t>(1, n)));
            size_t idx = rotateIdx_ % n;
            rotateIdx_++;
            const auto& device = config_.devices[idx];
            LOG(INFO) << "[PATROL] rotate device=" << device.deviceId;
            cv::Mat frame;
            if (grabOneShot(device, frame)) {
                processDevice(device, frame);
            }
            for (int slept = 0; slept < interval && running_.load(); ++slept) {
                std::this_thread::sleep_for(std::chrono::seconds(1));
            }
        } else {
            // pool mode: take up to pool_size devices that are due
            const int poolSize = std::max(1, config_.patrolPoolSize);
            std::vector<size_t> due;
            due.reserve(n);
            for (size_t i = 0; i < n; ++i) {
                if (lastPatrolTime_[i] == 0 || (now - lastPatrolTime_[i]) >= baseInterval) {
                    due.push_back(i);
                }
            }
            const size_t take = std::min(due.size(), static_cast<size_t>(poolSize));
            for (size_t k = 0; k < take && running_.load(); ++k) {
                size_t idx = due[k];
                const auto& device = config_.devices[idx];
                LOG(INFO) << "[PATROL] pool device=" << device.deviceId;
                cv::Mat frame;
                if (grabOneShot(device, frame)) {
                    processDevice(device, frame);
                }
                lastPatrolTime_[idx] = std::time(nullptr);
            }
            // Idle poll
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
        }
    }
    LOG(INFO) << "[PATROL] loop exit";
}

}  // namespace runtime
