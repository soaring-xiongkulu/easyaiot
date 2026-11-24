#ifndef YOLO_THREAD_POOL_H
#define YOLO_THREAD_POOL_H

#include "YoloEngine.h"
#include "core/spsc_ring.h"
#include "rk3588/frame_view.h"

#include <atomic>
#include <condition_variable>
#include <cstdint>
#include <deque>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

class YoloThreadPool {
public:
    struct ModelSpec {
        std::string key;
        int businessModelId{0};
        std::string modelPath;
        std::vector<std::string> classes;
    };

    YoloThreadPool() = default;
    ~YoloThreadPool();

    int setUp(const std::vector<ModelSpec>& models,
              int workersPerModel = 3,
              size_t queueDepth = 2,
              bool useSram = true,
              bool enablePerfQuery = false,
              float scoreThreshold = 0.25f);
    size_t modelCount() const { return models_.size(); }
    int submitTask(const cv::Mat& img, int modelId, int inputId, int frameId);
    int submitTask(const runtime::rk3588::FrameView& frame,
                   int modelId, int inputId, int frameId);
    int getTargetResult(std::vector<DetectObject>& objects,
                        int modelId, int inputId, int frameId);
    int getTargetImgResult(cv::Mat& img, int modelId, int inputId, int frameId);
    int getTargetResultNonBlock(std::vector<DetectObject>& objects,
                               int modelId, int inputId, int frameId);
    void stopAll();
    std::string inferEp() const;
    std::string modelLayout() const;
    uint64_t droppedTasks() const { return droppedTasks_.load(std::memory_order_relaxed); }
    uint64_t completedTasks() const { return completedTasks_.load(std::memory_order_relaxed); }
    int64_t lastNpuDurationUs() const { return lastNpuDurationUs_.load(std::memory_order_relaxed); }
    double throughputFps() const { return throughputFps_.load(std::memory_order_relaxed); }

private:
    struct Task {
        int modelId{0};
        int inputId{0};
        int frameId{0};
        runtime::rk3588::FrameView frame;
        cv::Mat ownedImage;
    };

    struct Completion {
        int modelId{0};
        int inputId{0};
        int frameId{0};
        int64_t npuDurationUs{0};
        std::vector<DetectObject> detections;
    };

    struct WorkerLane {
        std::shared_ptr<YoloEngine> engine;
        std::unique_ptr<runtime::SpscRing<Task>> taskRing;
        std::unique_ptr<runtime::SpscRing<Completion>> completionRing;
    };

    struct ModelRuntime {
        int businessModelId{0};
        std::vector<std::unique_ptr<WorkerLane>> lanes;
        std::atomic<size_t> nextLane{0};
    };

    struct ResultKey {
        int modelId{0};
        int inputId{0};
        int frameId{0};
    };

    using FrameResults = std::map<int, std::vector<DetectObject>>;
    using InputResults = std::map<int, FrameResults>;
    using ModelResults = std::map<int, InputResults>;

    int submit(Task task);
    void worker(size_t modelIndex, size_t laneIndex);
    void collectCompletions();
    void publishDropped(const Task& task);
    void publishCompletion(Completion completion);
    void storeResult(int modelId, int inputId, int frameId,
                     std::vector<DetectObject> detections);
    bool takeResult(std::vector<DetectObject>& objects,
                    int modelId, int inputId, int frameId);
    bool completionRingsEmpty() const;

    std::vector<std::unique_ptr<ModelRuntime>> models_;
    std::vector<std::thread> workerThreads_;
    std::thread collectorThread_;
    ModelResults results_;
    std::deque<ResultKey> resultOrder_;
    size_t maxResults_{128};
    std::mutex resultsMutex_;
    std::condition_variable resultReady_;
    std::atomic<bool> stop_{false};
    std::atomic<bool> workersDone_{false};
    std::atomic<uint64_t> droppedTasks_{0};
    std::atomic<uint64_t> completedTasks_{0};
    std::atomic<int64_t> lastNpuDurationUs_{0};
    std::atomic<double> throughputFps_{0.0};
};

#endif
