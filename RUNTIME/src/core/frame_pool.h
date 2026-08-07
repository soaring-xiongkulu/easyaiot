#ifndef RUNTIME_CORE_FRAME_POOL_H
#define RUNTIME_CORE_FRAME_POOL_H

#include <atomic>
#include <cstdint>
#include <mutex>
#include <opencv2/opencv.hpp>
#include <string>
#include <vector>

#include "Datatype.h"

namespace runtime {

enum class PixelFormat : uint8_t {
    BGR24 = 0,
    NV12 = 1,
    YUV420P = 2,
};

struct FrameSlot {
    uint64_t seq{0};
    int64_t ptsNs{0};
    int64_t captureNs{0};
    int width{0};
    int height{0};
    PixelFormat format{PixelFormat::BGR24};
    int poolIndex{-1};
    cv::Mat bgr;  // owned pixel buffer (pool slot)
};

struct InferResult {
    uint64_t seq{0};
    int64_t ptsNs{0};
    int64_t inferNs{0};
    std::vector<DetectObject> detections;
    std::string regionName;
    cv::Mat snapshot;  // optional small copy for evidence
};

/**
 * Pre-allocated BGR frame slots. Queue only carries FrameSlot handles (poolIndex).
 */
class FramePool {
public:
    FramePool() = default;

    void reset(size_t count, int width, int height) {
        std::lock_guard<std::mutex> lock(mu_);
        width_ = width;
        height_ = height;
        slots_.assign(count, FrameSlot{});
        free_.clear();
        free_.reserve(count);
        for (size_t i = 0; i < count; ++i) {
            slots_[i].poolIndex = static_cast<int>(i);
            slots_[i].width = width;
            slots_[i].height = height;
            slots_[i].bgr = cv::Mat(height, width, CV_8UC3);
            free_.push_back(static_cast<int>(i));
        }
    }

    FrameSlot* acquire() {
        std::lock_guard<std::mutex> lock(mu_);
        if (free_.empty()) {
            return nullptr;
        }
        int idx = free_.back();
        free_.pop_back();
        return &slots_[idx];
    }

    void release(int poolIndex) {
        if (poolIndex < 0) {
            return;
        }
        std::lock_guard<std::mutex> lock(mu_);
        if (poolIndex >= static_cast<int>(slots_.size())) {
            return;
        }
        free_.push_back(poolIndex);
    }

    FrameSlot* at(int poolIndex) {
        if (poolIndex < 0 || poolIndex >= static_cast<int>(slots_.size())) {
            return nullptr;
        }
        return &slots_[poolIndex];
    }

    size_t freeCount() const {
        std::lock_guard<std::mutex> lock(mu_);
        return free_.size();
    }

private:
    mutable std::mutex mu_;
    int width_{0};
    int height_{0};
    std::vector<FrameSlot> slots_;
    std::vector<int> free_;
};

struct PipelineMetrics {
    std::atomic<uint64_t> packetsIn{0};
    std::atomic<uint64_t> framesDecoded{0};
    std::atomic<uint64_t> framesDropped{0};
    std::atomic<uint64_t> inferIn{0};
    std::atomic<uint64_t> inferOut{0};
    std::atomic<uint64_t> alarmsEmitted{0};
    std::atomic<uint64_t> lastLatencyMs{0};
};

}  // namespace runtime

#endif
