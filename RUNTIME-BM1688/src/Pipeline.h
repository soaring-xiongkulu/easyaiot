#pragma once

#include "BoundedRing.h"
#include "Config.h"
#include "EventBus.h"
#include "SophonEngine.h"

#include <opencv2/core.hpp>
#include <opencv2/videoio.hpp>

#include <atomic>
#include <chrono>
#include <cstdint>
#include <memory>
#include <thread>
#include <vector>

namespace easyaiot::bm1688 {

struct FramePacket {
    std::uint64_t sequence{0};
    std::chrono::steady_clock::time_point capturedAt;
    cv::Mat image;
};

struct FrameResult {
    FramePacket frame;
    std::vector<Detection> detections;
    int coreId{-1};
    double inferenceMs{0};
};

struct RuntimeMetrics {
    std::atomic<std::uint64_t> decoded{0};
    std::atomic<std::uint64_t> dispatched{0};
    std::atomic<std::uint64_t> inferred{0};
    std::atomic<std::uint64_t> detections{0};
    std::atomic<std::uint64_t> alerts{0};
    std::atomic<std::uint64_t> decodeDrops{0};
    std::atomic<std::uint64_t> inferDrops{0};
    std::atomic<std::uint64_t> resultDrops{0};
    std::atomic<std::uint64_t> errors{0};
    std::atomic<double> lastInferenceMs{0};
};

class Pipeline {
public:
    explicit Pipeline(RuntimeConfig config);
    ~Pipeline();

    void start();
    void stop();
    void wait();
    bool running() const noexcept { return running_.load(); }
    std::string healthJson() const;

private:
    struct Lane {
        int coreId{0};
        std::unique_ptr<BoundedRing<FramePacket>> queue;
        std::vector<std::unique_ptr<SophonEngine>> engines;
        std::thread worker;
    };

    void validateHardware() const;
    void decodeLoop();
    void dispatchLoop();
    void inferLoop(Lane& lane);
    void emitLoop();
    void heartbeatLoop();
    void controlLoop();
    std::string makeAlertJson(const FrameResult& result, const std::string& imagePath) const;
    std::string saveAlertImage(const FrameResult& result) const;
    static std::string nowIso();

    RuntimeConfig config_;
    EventBus eventBus_;
    RuntimeMetrics metrics_;
    std::atomic<bool> running_{false};
    std::atomic<bool> started_{false};
    std::chrono::steady_clock::time_point startedAt_;
    std::chrono::steady_clock::time_point lastAlertAt_{};

    BoundedRing<FramePacket> decodeRing_;
    BoundedRing<FrameResult> resultRing_;
    std::vector<std::unique_ptr<Lane>> lanes_;
    std::thread decodeThread_;
    std::thread dispatchThread_;
    std::thread emitThread_;
    std::thread heartbeatThread_;
    std::thread controlThread_;
};

}  // namespace easyaiot::bm1688
