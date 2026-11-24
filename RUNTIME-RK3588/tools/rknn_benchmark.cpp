#include "YoloThreadPool.h"
#include "rk3588/platform.h"

#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <deque>
#include <fstream>
#include <glog/logging.h>
#include <iostream>
#include <opencv2/imgcodecs.hpp>
#include <string>
#include <thread>
#include <vector>

namespace {

std::vector<std::string> readClasses(const std::string& path) {
    std::vector<std::string> classes;
    if (path.empty()) return classes;
    std::ifstream input(path);
    std::string line;
    while (std::getline(input, line)) {
        if (!line.empty()) classes.push_back(line);
    }
    return classes;
}

void drainReady(YoloThreadPool& pool, std::deque<int>& pending) {
    for (auto iterator = pending.begin(); iterator != pending.end();) {
        std::vector<DetectObject> detections;
        if (pool.getTargetResultNonBlock(detections, 0, 0, *iterator) == 0) {
            iterator = pending.erase(iterator);
        } else {
            ++iterator;
        }
    }
}

void keepLanesBusy(YoloThreadPool& pool,
                   const runtime::rk3588::FrameView& frame,
                   std::deque<int>& pending,
                   int& nextFrameId,
                   size_t inFlight) {
    drainReady(pool, pending);
    while (pending.size() < inFlight) {
        const int frameId = nextFrameId++;
        if (pool.submitTask(frame, 0, 0, frameId) != 0) break;
        pending.push_back(frameId);
    }
}

}  // namespace

int main(int argc, char** argv) {
    google::InitGoogleLogging(argv[0]);
    FLAGS_logtostderr = true;
    if (argc < 3 || argc > 6) {
        std::cerr << "用法: " << argv[0]
                  << " <yolov8n-int8.rknn> <test.jpg> [seconds=15] [target_fps=150] [classes.txt]\n";
        return 64;
    }
    if (!runtime::rk3588::requirePlatform()) return 65;

    const int seconds = argc >= 4 ? std::max(3, std::atoi(argv[3])) : 15;
    const double targetFps = argc >= 5 ? std::max(1.0, std::atof(argv[4])) : 150.0;
    const std::vector<std::string> classes = argc >= 6 ? readClasses(argv[5])
                                                        : std::vector<std::string>{};
    cv::Mat image = cv::imread(argv[2], cv::IMREAD_COLOR);
    if (image.empty()) {
        std::cerr << "BENCH_FAIL: 无法读取测试图片 " << argv[2] << "\n";
        return 66;
    }

    YoloThreadPool pool;
    YoloThreadPool::ModelSpec model;
    model.key = "yolov8n-rk3588-int8";
    model.modelPath = argv[1];
    model.classes = classes;
    if (pool.setUp({model}, 3, 4, true, false, 0.25f) != 0) {
        std::cerr << "BENCH_FAIL: 三核 RKNN 线程池初始化失败\n";
        return 67;
    }

    runtime::rk3588::FrameView frame;
    frame.virtualAddress = image.data;
    frame.width = image.cols;
    frame.height = image.rows;
    frame.widthStride = static_cast<int>(image.step[0] / image.elemSize());
    frame.heightStride = image.rows;
    frame.format = runtime::rk3588::FrameFormat::BGR888;

    std::deque<int> pending;
    int nextFrameId = 1;
    const size_t inFlight = 12;
    const auto warmupEnd = std::chrono::steady_clock::now() + std::chrono::seconds(2);
    while (std::chrono::steady_clock::now() < warmupEnd) {
        keepLanesBusy(pool, frame, pending, nextFrameId, inFlight);
        std::this_thread::sleep_for(std::chrono::microseconds(50));
    }
    const uint64_t completedAtStart = pool.completedTasks();
    const uint64_t droppedAtStart = pool.droppedTasks();
    const auto start = std::chrono::steady_clock::now();
    const auto finish = start + std::chrono::seconds(seconds);
    while (std::chrono::steady_clock::now() < finish) {
        keepLanesBusy(pool, frame, pending, nextFrameId, inFlight);
        std::this_thread::sleep_for(std::chrono::microseconds(50));
    }
    const auto stop = std::chrono::steady_clock::now();
    const uint64_t completed = pool.completedTasks() - completedAtStart;
    const uint64_t dropped = pool.droppedTasks() - droppedAtStart;
    const double elapsed = std::chrono::duration<double>(stop - start).count();
    const double fps = static_cast<double>(completed) / elapsed;

    std::cout << "RK3588_BENCH model=" << argv[1]
              << " workers=3 ring_depth=4"
              << " seconds=" << elapsed
              << " completed=" << completed
              << " dropped=" << dropped
              << " throughput_fps=" << fps
              << " target_fps=" << targetFps << "\n";
    if (dropped != 0 || fps < targetFps) {
        std::cout << "BENCH_FAIL\n";
        return 2;
    }
    std::cout << "BENCH_PASS\n";
    return 0;
}
