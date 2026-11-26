#pragma once

#include "BoundedRing.h"
#include "Config.h"
#include "EventBus.h"
#include "NvDecoder.h"
#include "TensorRtEngine.h"

#include <atomic>
#include <chrono>
#include <cstdint>
#include <memory>
#include <string>
#include <thread>
#include <vector>

namespace easyaiot::nvidia {

struct FrameResult {
    std::uint64_t sequence{0};
    std::vector<Detection> detections;
    int lane{0};
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
    bool running() const noexcept { return running_.load(); }
    std::string healthJson() const;

private:
    struct Lane {
        int id{0};
        std::unique_ptr<BoundedRing<DeviceFrame>> queue;
        std::vector<std::unique_ptr<TensorRtSession>> sessions;
        std::thread worker;
    };

    void validateHardware();
    void decodeLoop();
    void dispatchLoop();
    void inferLoop(Lane& lane);
    void emitLoop();
    void heartbeatLoop();
    void controlLoop();
    std::string makeAlertJson(const FrameResult& result) const;
    static std::string nowIso();

    RuntimeConfig config_;
    EventBus eventBus_;
    RuntimeMetrics metrics_;
    std::atomic<bool> running_{false};
    std::atomic<bool> started_{false};
    std::chrono::steady_clock::time_point startedAt_{};
    std::chrono::steady_clock::time_point lastAlertAt_{};
    std::string gpuName_;
    int computeMajor_{0};
    int computeMinor_{0};
    std::size_t enginePlanBytes_{0};
    std::size_t preallocatedIoBytes_{0};

    std::vector<std::unique_ptr<TensorRtModel>> models_;
    BoundedRing<DeviceFrame> decodeRing_;
    BoundedRing<FrameResult> resultRing_;
    std::vector<std::unique_ptr<Lane>> lanes_;
    std::thread decodeThread_;
    std::thread dispatchThread_;
    std::thread emitThread_;
    std::thread heartbeatThread_;
    std::thread controlThread_;
};

}  // namespace easyaiot::nvidia
