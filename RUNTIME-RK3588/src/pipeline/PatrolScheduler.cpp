#include "pipeline/PatrolScheduler.h"

#include <algorithm>
#include <chrono>
#include <glog/logging.h>
#include <opencv2/imgproc.hpp>
#if __has_include(<opencv2/geometry.hpp>)
#include <opencv2/geometry.hpp>
#endif

#include "AlgoMqttBus.h"
#include "YoloThreadPool.h"
#include "rk3588/mpp_capture.h"

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
        LOG(ERROR) << "[巡检] 未配置设备";
        running_.store(false);
        return;
    }
    lastPatrolTime_.assign(config_.devices.size(), 0);
    LOG(INFO) << "[巡检] 正在启动调度器，共 " << config_.devices.size() << " 个设备"
              << " 模式=" << config_.patrolMode
              << " 间隔=" << config_.patrolIntervalSec << " 秒"
              << " 并发池大小=" << config_.patrolPoolSize;
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

bool PatrolScheduler::grabOneShot(const DeviceStreamConfig& device, cv::Mat& out,
                                  rk3588::FrameView& source) {
    rk3588::MppCapture capture;
    if (!capture.open(device.rtspUrl, config_.rkMppBufferCount)) {
        LOG(WARNING) << "[巡检] 打开失败，设备=" << device.deviceId;
        return false;
    }
    // Warm up five hardware-decoded frames, retaining only the newest DMA owner.
    for (int i = 0; i < 5; ++i) {
        if (!capture.read(out, source)) return false;
    }
    return capture.read(out, source) && !out.empty();
}

void PatrolScheduler::processDevice(const DeviceStreamConfig& device, const cv::Mat& frame,
                                    const rk3588::FrameView& source) {
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
        pool_->submitTask(source, static_cast<int>(m), inputId, fid);
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
    const bool skipRegionGate = AlgoMqttBus::shouldPublishInferEvent();
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
            LOG(INFO) << "[巡检] 告警，设备=" << device.deviceId
                      << " 检测数=" << alarmDetections.size()
                      << " 区域=" << regionName;
            alarmFn_(alarmDetections, regionName, device.deviceId, device.deviceName, frame);
        }
    }
}

void PatrolScheduler::loop() {
    LOG(INFO) << "[巡检] 调度循环已启动";
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
            LOG(INFO) << "[巡检] 轮转巡检设备=" << device.deviceId;
            cv::Mat frame;
            rk3588::FrameView source;
            if (grabOneShot(device, frame, source)) {
                processDevice(device, frame, source);
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
                LOG(INFO) << "[巡检] 并发池巡检设备=" << device.deviceId;
                cv::Mat frame;
                rk3588::FrameView source;
                if (grabOneShot(device, frame, source)) {
                    processDevice(device, frame, source);
                }
                lastPatrolTime_[idx] = std::time(nullptr);
            }
            // Idle poll
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
        }
    }
    LOG(INFO) << "[巡检] 调度循环已退出";
}

}  // namespace runtime
