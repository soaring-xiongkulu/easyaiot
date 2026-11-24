#include "core/spsc_ring.h"

#include <atomic>
#include <cstdint>
#include <iostream>
#include <thread>

namespace {

bool preservesOrderUnderContention() {
    constexpr int kItems = 200000;
    runtime::SpscRing<int> ring(1024);
    std::atomic<bool> producerDone{false};
    std::atomic<bool> valid{true};

    std::thread producer([&] {
        for (int value = 0; value < kItems; ++value) {
            while (!ring.push(value)) std::this_thread::yield();
        }
        producerDone.store(true, std::memory_order_release);
    });
    std::thread consumer([&] {
        int expected = 0;
        while (!producerDone.load(std::memory_order_acquire) || ring.sizeApprox() != 0) {
            int value = -1;
            if (!ring.pop(value)) {
                std::this_thread::yield();
                continue;
            }
            if (value != expected++) valid.store(false, std::memory_order_relaxed);
        }
        if (expected != kItems) valid.store(false, std::memory_order_relaxed);
    });
    producer.join();
    consumer.join();
    return valid.load(std::memory_order_relaxed);
}

bool dropsOnlyOldestValues() {
    runtime::SpscRing<int> ring(4);
    for (int value = 1; value <= 10; ++value) ring.pushDropOldest(value);
    if (ring.dropped() != 6 || ring.sizeApprox() != 4) return false;
    for (int expected = 7; expected <= 10; ++expected) {
        int value = 0;
        if (!ring.pop(value) || value != expected) return false;
    }
    int ignored = 0;
    return !ring.pop(ignored);
}

}  // namespace

int main() {
    if (!preservesOrderUnderContention()) {
        std::cerr << "RING_TEST_FAIL: order/contention\n";
        return 1;
    }
    if (!dropsOnlyOldestValues()) {
        std::cerr << "RING_TEST_FAIL: drop-oldest\n";
        return 2;
    }
    std::cout << "RING_TEST_PASS\n";
    return 0;
}
