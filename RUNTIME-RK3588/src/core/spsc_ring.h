#ifndef RUNTIME_CORE_SPSC_RING_H
#define RUNTIME_CORE_SPSC_RING_H

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <utility>

namespace runtime {

/**
 * Fixed-capacity lock-free ring.
 *
 * Most pipeline links have one producer and one consumer, but realtime
 * drop-oldest backpressure temporarily makes the producer a second consumer.
 * Per-slot sequence numbers keep that operation safe without a queue mutex.
 */
template <typename T>
class SpscRing {
public:
    explicit SpscRing(size_t requestedCapacity)
        : capacity_(nextPow2(requestedCapacity < 2 ? 2 : requestedCapacity)),
          mask_(capacity_ - 1),
          slots_(new Slot[capacity_]) {
        for (size_t i = 0; i < capacity_; ++i) {
            slots_[i].sequence.store(i, std::memory_order_relaxed);
        }
    }

    SpscRing(const SpscRing&) = delete;
    SpscRing& operator=(const SpscRing&) = delete;

    size_t capacity() const { return capacity_; }

    size_t sizeApprox() const {
        const size_t h = enqueuePosition_.load(std::memory_order_acquire);
        const size_t t = dequeuePosition_.load(std::memory_order_acquire);
        return h - t;
    }

    uint64_t dropped() const { return dropped_.load(std::memory_order_relaxed); }

    bool push(const T& item) { return pushImpl(item); }
    bool push(T&& item) { return pushImpl(std::move(item)); }

    bool pushDropOldest(const T& item) {
        T discarded;
        return pushDropOldest(item, discarded);
    }

    bool pushDropOldest(T&& item) {
        T discarded;
        return pushDropOldest(std::move(item), discarded);
    }

    bool pushDropOldest(const T& item, T& discarded, bool* droppedOut = nullptr) {
        return pushDropOldestImpl(item, discarded, droppedOut);
    }

    bool pushDropOldest(T&& item, T& discarded, bool* droppedOut = nullptr) {
        return pushDropOldestImpl(std::move(item), discarded, droppedOut);
    }

    bool pop(T& out) {
        size_t position = dequeuePosition_.load(std::memory_order_relaxed);
        Slot* slot = nullptr;
        for (;;) {
            slot = &slots_[position & mask_];
            const size_t sequence = slot->sequence.load(std::memory_order_acquire);
            const intptr_t difference = static_cast<intptr_t>(sequence) -
                                        static_cast<intptr_t>(position + 1);
            if (difference == 0) {
                if (dequeuePosition_.compare_exchange_weak(
                        position, position + 1, std::memory_order_relaxed)) {
                    break;
                }
            } else if (difference < 0) {
                return false;
            } else {
                position = dequeuePosition_.load(std::memory_order_relaxed);
            }
        }
        out = std::move(slot->value);
        slot->sequence.store(position + capacity_, std::memory_order_release);
        return true;
    }

private:
    struct Slot {
        std::atomic<size_t> sequence{0};
        T value{};
    };

    template <typename U>
    bool pushImpl(U&& item) {
        size_t position = enqueuePosition_.load(std::memory_order_relaxed);
        Slot* slot = nullptr;
        for (;;) {
            slot = &slots_[position & mask_];
            const size_t sequence = slot->sequence.load(std::memory_order_acquire);
            const intptr_t difference = static_cast<intptr_t>(sequence) -
                                        static_cast<intptr_t>(position);
            if (difference == 0) {
                if (enqueuePosition_.compare_exchange_weak(
                        position, position + 1, std::memory_order_relaxed)) {
                    break;
                }
            } else if (difference < 0) {
                return false;
            } else {
                position = enqueuePosition_.load(std::memory_order_relaxed);
            }
        }
        slot->value = std::forward<U>(item);
        slot->sequence.store(position + 1, std::memory_order_release);
        return true;
    }

    template <typename U>
    bool pushDropOldestImpl(U&& item, T& discarded, bool* droppedOut) {
        bool didDrop = false;
        while (!pushImpl(std::forward<U>(item))) {
            if (pop(discarded)) {
                didDrop = true;
                dropped_.fetch_add(1, std::memory_order_relaxed);
            }
        }
        if (droppedOut) *droppedOut = didDrop;
        return true;
    }

    static size_t nextPow2(size_t value) {
        size_t power = 1;
        while (power < value) power <<= 1;
        return power;
    }

    const size_t capacity_;
    const size_t mask_;
    std::unique_ptr<Slot[]> slots_;
    std::atomic<size_t> enqueuePosition_{0};
    std::atomic<size_t> dequeuePosition_{0};
    std::atomic<uint64_t> dropped_{0};
};

}  // namespace runtime

#endif
