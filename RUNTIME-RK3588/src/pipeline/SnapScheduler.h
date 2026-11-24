#ifndef RUNTIME_PIPELINE_SNAP_SCHEDULER_H
#define RUNTIME_PIPELINE_SNAP_SCHEDULER_H

#include <atomic>
#include <ctime>
#include <functional>
#include <memory>
#include <string>
#include <thread>
#include <vector>

#include <opencv2/opencv.hpp>

#include "Config.h"
#include "Datatype.h"
#include "rk3588/mpp_capture.h"

class YoloThreadPool;

namespace runtime {

/**
 * Snap mode: long-lived MPP decoder per device; fire on cron slot
 * (or every frameSkip seconds when cron is empty).
 */
class SnapScheduler {
public:
    using AlarmFn = std::function<void(const std::vector<DetectObject>&, const std::string& region,
                                       const std::string& deviceId, const std::string& deviceName,
                                       const cv::Mat& frame)>;

    SnapScheduler(Config& config, YoloThreadPool* pool, AlarmFn alarmFn);
    ~SnapScheduler();

    void start();
    void stop();
    void join();
    bool isRunning() const { return running_.load(); }

private:
    void loop();
    bool cronDue(std::time_t now, std::string& slotKey);
    bool ensureCapture(size_t idx);
    bool grabFrame(size_t idx, cv::Mat& out, rk3588::FrameView& source);
    void processDevice(size_t idx, const cv::Mat& frame, const rk3588::FrameView& source);

    Config& config_;
    YoloThreadPool* pool_;
    AlarmFn alarmFn_;
    std::atomic<bool> running_{false};
    std::thread thread_;
    std::string lastSlot_;
    std::time_t lastIntervalFire_{0};
    std::vector<std::unique_ptr<rk3588::MppCapture>> caps_;
    std::atomic<int> frameId_{0};
};

}  // namespace runtime

#endif
