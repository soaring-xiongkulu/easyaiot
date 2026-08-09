#include "pipeline/PatrolScheduler.h"

#include <algorithm>
#include <cctype>
#include <chrono>
#include <cstdio>
#include <glog/logging.h>
#include <opencv2/imgproc.hpp>

#include "Yolov11ThreadPool.h"

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

std::string formatUtcIso(std::time_t t) {
    std::tm tm{};
#if defined(_WIN32)
    gmtime_s(&tm, &t);
#else
    gmtime_r(&t, &tm);
#endif
    char buf[32];
    std::snprintf(buf, sizeof(buf), "%04d-%02d-%02dT%02d:%02d:%02dZ",
                  tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday,
                  tm.tm_hour, tm.tm_min, tm.tm_sec);
    return buf;
}

}  // namespace

PatrolScheduler::PatrolScheduler(Config& config, Yolov11ThreadPool* pool, AlarmFn alarmFn)
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
              << " pool_size=" << config_.patrolPoolSize
              << " focus=" << (config_.focusDeviceId.empty() ? "(none)" : config_.focusDeviceId);
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

std::unordered_map<std::string, std::unordered_map<std::string, std::string>>
PatrolScheduler::deviceProgressSnapshot() const {
    std::lock_guard<std::mutex> lock(progressMu_);
    return deviceProgress_;
}

size_t PatrolScheduler::findDeviceIndex(const std::string& deviceId) const {
    for (size_t i = 0; i < config_.devices.size(); ++i) {
        if (config_.devices[i].deviceId == deviceId) {
            return i;
        }
    }
    return static_cast<size_t>(-1);
}

bool PatrolScheduler::grabOneShot(const DeviceStreamConfig& device, cv::Mat& out) {
    cv::VideoCapture cap;
    if (!cap.open(device.rtspUrl, cv::CAP_FFMPEG)) {
        LOG(WARNING) << "[PATROL] open failed device=" << device.deviceId;
        return false;
    }
    cap.set(cv::CAP_PROP_BUFFERSIZE, 1);

    cv::Mat frame;
    // Align with Python PATROL_READ_WARMUP_FRAMES default=3, then take 1 frame.
    constexpr int kWarmup = 3;
    for (int i = 0; i < kWarmup; ++i) {
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

std::vector<size_t> PatrolScheduler::devicesDue(std::time_t now,
                                                int intervalSec,
                                                const std::vector<size_t>& candidates) const {
    std::vector<size_t> due;
    due.reserve(candidates.size());
    for (size_t idx : candidates) {
        if (idx >= lastPatrolTime_.size()) {
            continue;
        }
        if (lastPatrolTime_[idx] == 0 || (now - lastPatrolTime_[idx]) >= intervalSec) {
            due.push_back(idx);
        }
    }
    return due;
}

void PatrolScheduler::processDevice(size_t idx) {
    if (idx >= config_.devices.size()) {
        return;
    }
    const auto& device = config_.devices[idx];
    cv::Mat frame;
    if (!grabOneShot(device, frame)) {
        std::lock_guard<std::mutex> lock(progressMu_);
        auto& entry = deviceProgress_[device.deviceId];
        entry["last_result"] = "open_failed";
        entry["last_patrol_at"] = formatUtcIso(std::time(nullptr));
        return;
    }

    totalPatrols.fetch_add(1, std::memory_order_relaxed);
    const std::time_t now = std::time(nullptr);
    lastPatrolTime_[idx] = now;
    parityRecorder_.recordScheduleEvent("patrol", device.deviceId, "", now);
    parityRecorder_.maybeFlush(config_.logPath);

    int detCount = 0;
    if (pool_ && config_.enableAI) {
        int fid = frameId_.fetch_add(1, std::memory_order_relaxed);
        int inputId = static_cast<int>(idx) + 1;

        pool_->submitTask(frame, inputId, fid);
        std::vector<DetectObject> detections;
        if (pool_->getTargetResult(detections, inputId, fid) == 0) {
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
            detCount = static_cast<int>(alarmDetections.size());
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
    }

    {
        std::lock_guard<std::mutex> lock(progressMu_);
        auto& entry = deviceProgress_[device.deviceId];
        entry["last_patrol_at"] = formatUtcIso(now);
        entry["last_result"] = detCount > 0 ? "detected" : "ok";
        entry["detection_count"] = std::to_string(detCount);
    }
}

void PatrolScheduler::processDeviceById(const std::string& deviceId) {
    size_t idx = findDeviceIndex(deviceId);
    if (idx == static_cast<size_t>(-1)) {
        return;
    }
    processDevice(idx);
}

void PatrolScheduler::runBatch(const std::vector<size_t>& indices) {
    if (indices.empty()) {
        return;
    }
    // Parallel per-device threads like Python _run_patrol_batch.
    std::vector<std::thread> threads;
    threads.reserve(indices.size());
    for (size_t idx : indices) {
        threads.emplace_back([this, idx]() { processDevice(idx); });
    }
    for (auto& t : threads) {
        if (t.joinable()) {
            t.join();
        }
    }
}

void PatrolScheduler::loop() {
    LOG(INFO) << "[PATROL] loop started";
    const size_t n = config_.devices.size();
    const int baseInterval = std::max(3, config_.patrolIntervalSec);
    std::string mode = config_.patrolMode;
    std::transform(mode.begin(), mode.end(), mode.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });

    size_t focusIdx = static_cast<size_t>(-1);
    if (!config_.focusDeviceId.empty()) {
        focusIdx = findDeviceIndex(config_.focusDeviceId);
    }
    const bool hybridMode = (mode == "hybrid" && focusIdx != static_cast<size_t>(-1));
    if (mode == "hybrid" && !hybridMode) {
        LOG(WARNING) << "[PATROL] hybrid requested but focus_device_id missing/invalid; falling back to pool";
    }

    std::vector<size_t> allIdx(n);
    for (size_t i = 0; i < n; ++i) {
        allIdx[i] = i;
    }
    std::vector<size_t> backgroundIdx;
    for (size_t i = 0; i < n; ++i) {
        if (i != focusIdx) {
            backgroundIdx.push_back(i);
        }
    }

    while (running_.load()) {
        std::time_t now = std::time(nullptr);

        if (mode == "rotate") {
            int interval = std::max(3, baseInterval / static_cast<int>(std::max<size_t>(1, n)));
            size_t idx = rotateIdx_ % n;
            rotateIdx_++;
            const auto& device = config_.devices[idx];
            LOG(INFO) << "[PATROL] rotate device=" << device.deviceId;
            processDevice(idx);
            for (int slept = 0; slept < interval && running_.load(); ++slept) {
                std::this_thread::sleep_for(std::chrono::seconds(1));
            }
        } else if (hybridMode) {
            // CAP-PATROL-HYBRID: focus at interval/2; background pool at full interval.
            const int focusInterval = std::max(3, baseInterval / 2);
            const int poolSize = std::max(1, config_.patrolPoolSize);
            const int bgPool = std::max(1, poolSize - 1);

            auto focusDue = devicesDue(now, focusInterval, {focusIdx});
            if (!focusDue.empty()) {
                LOG(INFO) << "[PATROL] hybrid focus device=" << config_.devices[focusIdx].deviceId
                          << " interval=" << focusInterval;
                processDevice(focusIdx);
            }
            auto bgDue = devicesDue(now, baseInterval, backgroundIdx);
            if (!bgDue.empty()) {
                const size_t take = std::min(bgDue.size(), static_cast<size_t>(bgPool));
                std::vector<size_t> batch(bgDue.begin(), bgDue.begin() + static_cast<std::ptrdiff_t>(take));
                LOG(INFO) << "[PATROL] hybrid background batch size=" << batch.size();
                runBatch(batch);
            }
            if (focusDue.empty() && bgDue.empty()) {
                std::this_thread::sleep_for(std::chrono::milliseconds(500));
            } else {
                std::this_thread::sleep_for(std::chrono::milliseconds(300));
            }
        } else {
            // pool mode (default)
            const int poolSize = std::max(1, config_.patrolPoolSize);
            auto due = devicesDue(now, baseInterval, allIdx);
            if (due.empty()) {
                std::this_thread::sleep_for(std::chrono::milliseconds(500));
                continue;
            }
            const size_t take = std::min(due.size(), static_cast<size_t>(poolSize));
            std::vector<size_t> batch(due.begin(), due.begin() + static_cast<std::ptrdiff_t>(take));
            LOG(INFO) << "[PATROL] pool batch size=" << batch.size();
            runBatch(batch);
            std::this_thread::sleep_for(std::chrono::milliseconds(300));
        }
    }
    parityRecorder_.writeToFile(config_.logPath);
    LOG(INFO) << "[PATROL] loop exit";
}

}  // namespace runtime
