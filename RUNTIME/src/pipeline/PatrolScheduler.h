#ifndef RUNTIME_PIPELINE_PATROL_SCHEDULER_H
#define RUNTIME_PIPELINE_PATROL_SCHEDULER_H

#include <atomic>
#include <ctime>
#include <functional>
#include <mutex>
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
 * Patrol mode: short-connect grab (warmup + 1 frame), then close.
 * Modes: pool | rotate | hybrid (focus half-interval + background pool).
 * Aligned with VIDEO patrol_algorithm_service.patrol_scheduler_worker.
 */
class PatrolScheduler {
public:
    using AlarmFn = std::function<void(const std::vector<DetectObject>&, const std::string& region,
                                       const std::string& deviceId, const std::string& deviceName,
                                       const cv::Mat& frame)>;

    std::atomic<uint64_t> totalPatrols{0};
    std::atomic<uint64_t> totalDetections{0};

    PatrolScheduler(Config& config, Yolov11ThreadPool* pool, AlarmFn alarmFn);
    ~PatrolScheduler();

    void start();
    void stop();
    void join();
    bool isRunning() const { return running_.load(); }

    /** Snapshot of per-device progress for heartbeat (CAP-PATROL-PROGRESS totals stay here;
     *  rich UI hub remains VIDEO). */
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> deviceProgressSnapshot() const;

private:
    void loop();
    bool grabOneShot(const DeviceStreamConfig& device, cv::Mat& out);
    void processDevice(size_t idx);
    void processDeviceById(const std::string& deviceId);
    void runBatch(const std::vector<size_t>& indices);
    std::vector<size_t> devicesDue(std::time_t now, int intervalSec, const std::vector<size_t>& candidates) const;
    size_t findDeviceIndex(const std::string& deviceId) const;

    Config& config_;
    Yolov11ThreadPool* pool_;
    AlarmFn alarmFn_;
    ParityRecorder parityRecorder_;
    std::atomic<bool> running_{false};
    std::thread thread_;
    std::vector<std::time_t> lastPatrolTime_;
    size_t rotateIdx_{0};
    std::atomic<int> frameId_{0};
    mutable std::mutex progressMu_;
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> deviceProgress_;
};

}  // namespace runtime

#endif
