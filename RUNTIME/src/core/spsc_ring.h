#ifndef RUNTIME_CORE_SPSC_RING_H
#define RUNTIME_CORE_SPSC_RING_H

#include <atomic>
#include <cstddef>
#include <optional>
#include <vector>

namespace runtime {

/**
 * Fixed-capacity SPSC ring. Capacity must be power-of-two.
 * pushDropOldest: when full, overwrite the oldest slot (realtime preference).
 */
template <typename T>
class SpscRing {
public:
    explicit SpscRing(size_t capacityPowerOfTwo)
        : capacity_(nextPow2(capacityPowerOfTwo < 2 ? 2 : capacityPowerOfTwo)),
          mask_(capacity_ - 1),
          slots_(capacity_) {}

    size_t capacity() const { return capacity_; }

    size_t sizeApprox() const {
        const size_t h = head_.load(std::memory_order_acquire);
        const size_t t = tail_.load(std::memory_order_acquire);
        return h - t;
    }

    uint64_t dropped() const { return dropped_.load(std::memory_order_relaxed); }

    bool push(const T& item) {
        const size_t h = head_.load(std::memory_order_relaxed);
        const size_t t = tail_.load(std::memory_order_acquire);
        if (h - t >= capacity_) {
            return false;
        }
        slots_[h & mask_] = item;
        head_.store(h + 1, std::memory_order_release);
        return true;
    }

    bool pushDropOldest(const T& item) {
        T discarded;
        return pushDropOldest(item, discarded);
    }

    /** When full, copies the overwritten oldest value into discarded and returns true in droppedOut. */
    bool pushDropOldest(const T& item, T& discarded, bool* droppedOut = nullptr) {
        const size_t h = head_.load(std::memory_order_relaxed);
        size_t t = tail_.load(std::memory_order_acquire);
        bool dropped = false;
        if (h - t >= capacity_) {
            discarded = slots_[t & mask_];
            tail_.compare_exchange_strong(t, t + 1, std::memory_order_acq_rel);
            dropped_.fetch_add(1, std::memory_order_relaxed);
            dropped = true;
        }
        slots_[h & mask_] = item;
        head_.store(h + 1, std::memory_order_release);
        if (droppedOut) {
            *droppedOut = dropped;
        }
        return true;
    }

    bool pop(T& out) {
        const size_t t = tail_.load(std::memory_order_relaxed);
        const size_t h = head_.load(std::memory_order_acquire);
        if (t == h) {
            return false;
        }
        out = slots_[t & mask_];
        tail_.store(t + 1, std::memory_order_release);
        return true;
    }

private:
    static size_t nextPow2(size_t v) {
        size_t p = 1;
        while (p < v) {
            p <<= 1;
        }
        return p;
    }

    const size_t capacity_;
    const size_t mask_;
    std::vector<T> slots_;
    std::atomic<size_t> head_{0};
    std::atomic<size_t> tail_{0};
    std::atomic<uint64_t> dropped_{0};
};

}  // namespace runtime

#endif
