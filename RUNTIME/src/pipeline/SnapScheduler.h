#ifndef RUNTIME_PIPELINE_SNAP_SCHEDULER_H
#define RUNTIME_PIPELINE_SNAP_SCHEDULER_H

#include <atomic>
#include <ctime>
#include <functional>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>

#include <opencv2/opencv.hpp>

#include "Config.h"
#include "Datatype.h"
#include "parity/ParityRecorder.h"

class Yolov11ThreadPool;

namespace runtime {

/**
 * Snap mode: long-lived VideoCapture per device; fire on cron slot
 * (6-field Asia/Shanghai second-level, aligned with VIDEO cron_utils)
 * or every frameSkip seconds when cron is empty.
 */
class SnapScheduler {
public:
    using AlarmFn = std::function<void(const std::vector<DetectObject>&, const std::string& region,
                                       const std::string& deviceId, const std::string& deviceName,
                                       const cv::Mat& frame)>;

    SnapScheduler(Config& config, Yolov11ThreadPool* pool, AlarmFn alarmFn);
    ~SnapScheduler();

    void start();
    void stop();
    void join();
    bool isRunning() const { return running_.load(); }

private:
    void loop();
    bool cronDueForDevice(size_t idx, std::time_t now, std::string& slotKey);
    bool ensureCapture(size_t idx);
    bool grabFrame(size_t idx, cv::Mat& out);
    void processDevice(size_t idx, const cv::Mat& frame, const std::string& slotKey);

    Config& config_;
    Yolov11ThreadPool* pool_;
    AlarmFn alarmFn_;
    ParityRecorder parityRecorder_;
    std::atomic<bool> running_{false};
    std::thread thread_;
    // Per-device last captured cron slot (Python device_last_extract_cron_time)
    std::unordered_map<std::string, std::string> lastSlotByDevice_;
    std::time_t lastIntervalFire_{0};
    std::vector<cv::VideoCapture> caps_;
    std::atomic<int> frameId_{0};
};

}  // namespace runtime

#endif
