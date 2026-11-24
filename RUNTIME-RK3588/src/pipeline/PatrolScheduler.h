#ifndef RUNTIME_PIPELINE_PATROL_SCHEDULER_H
#define RUNTIME_PIPELINE_PATROL_SCHEDULER_H

#include <atomic>
#include <ctime>
#include <functional>
#include <string>
#include <thread>
#include <vector>

#include <opencv2/opencv.hpp>

#include "Config.h"
#include "Datatype.h"

class YoloThreadPool;

namespace runtime {

/**
 * Patrol mode: short-connect grab (~5 warmup + 1 frame), then close.
 * Modes: pool (batch due devices) | rotate (one device at a time).
 */
class PatrolScheduler {
public:
    using AlarmFn = std::function<void(const std::vector<DetectObject>&, const std::string& region,
                                       const std::string& deviceId, const std::string& deviceName,
                                       const cv::Mat& frame)>;

    std::atomic<uint64_t> totalPatrols{0};
    std::atomic<uint64_t> totalDetections{0};

    PatrolScheduler(Config& config, YoloThreadPool* pool, AlarmFn alarmFn);
    ~PatrolScheduler();

    void start();
    void stop();
    void join();
    bool isRunning() const { return running_.load(); }

private:
    void loop();
    bool grabOneShot(const DeviceStreamConfig& device, cv::Mat& out);
    void processDevice(const DeviceStreamConfig& device, const cv::Mat& frame);

    Config& config_;
    YoloThreadPool* pool_;
    AlarmFn alarmFn_;
    std::atomic<bool> running_{false};
    std::thread thread_;
    std::vector<std::time_t> lastPatrolTime_;
    size_t rotateIdx_{0};
    std::atomic<int> frameId_{0};
};

}  // namespace runtime

#endif
