#pragma once

#include <chrono>
#include <condition_variable>
#include <cstddef>
#include <mutex>
#include <optional>
#include <stdexcept>
#include <utility>
#include <vector>

namespace easyaiot::bm1688 {

/**
 * Fixed-capacity ring for pipeline stage hand-off.
 *
 * Memory is allocated once. A slow consumer never grows process memory: the
 * producer drops the oldest item and keeps the newest frame, which is the
 * correct latency policy for realtime video.
 */
template <typename T>
class BoundedRing {
public:
    explicit BoundedRing(std::size_t capacity)
        : slots_(capacity), capacity_(capacity) {
        if (capacity == 0) throw std::invalid_argument("ring capacity must be positive");
    }

    BoundedRing(const BoundedRing&) = delete;
    BoundedRing& operator=(const BoundedRing&) = delete;

    bool pushDropOldest(T value, bool* dropped = nullptr) {
        std::unique_lock<std::mutex> lock(mutex_);
        if (closed_) return false;
        bool displaced = size_ == capacity_;
        if (displaced) {
            slots_[head_].reset();
            head_ = (head_ + 1) % capacity_;
            --size_;
        }
        slots_[tail_] = std::move(value);
        tail_ = (tail_ + 1) % capacity_;
        ++size_;
        if (dropped) *dropped = displaced;
        lock.unlock();
        notEmpty_.notify_one();
        return true;
    }

    bool pop(T& out, std::chrono::milliseconds timeout = std::chrono::milliseconds(20)) {
        std::unique_lock<std::mutex> lock(mutex_);
        if (!notEmpty_.wait_for(lock, timeout, [this] { return closed_ || size_ > 0; })) {
            return false;
        }
        if (size_ == 0) return false;
        out = std::move(*slots_[head_]);
        slots_[head_].reset();
        head_ = (head_ + 1) % capacity_;
        --size_;
        return true;
    }

    void close() {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            closed_ = true;
        }
        notEmpty_.notify_all();
    }

    std::size_t size() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return size_;
    }

    std::size_t capacity() const noexcept { return capacity_; }

private:
    mutable std::mutex mutex_;
    std::condition_variable notEmpty_;
    std::vector<std::optional<T>> slots_;
    const std::size_t capacity_;
    std::size_t head_{0};
    std::size_t tail_{0};
    std::size_t size_{0};
    bool closed_{false};
};

}  // namespace easyaiot::bm1688
