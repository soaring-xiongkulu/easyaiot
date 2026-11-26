#include "Config.h"
#include "Pipeline.h"

#include <atomic>
#include <chrono>
#include <csignal>
#include <cstring>
#include <iostream>
#include <thread>

#ifndef RUNTIME_VERSION_STR
#define RUNTIME_VERSION_STR "unknown"
#endif

namespace {
std::atomic<bool> stopRequested{false};
void signalHandler(int) { stopRequested.store(true); }
}

int main(int argc, char** argv) {
    if (argc == 2 && (std::strcmp(argv[1], "--version") == 0 ||
                      std::strcmp(argv[1], "-V") == 0)) {
        std::cout << "RUNTIME-NVIDIA " << RUNTIME_VERSION_STR << '\n';
        return 0;
    }
    if (argc != 2) {
        std::cerr << "用法: " << argv[0] << " <config.ini>\n";
        return 2;
    }
    std::signal(SIGINT, signalHandler);
    std::signal(SIGTERM, signalHandler);
    try {
        auto config = easyaiot::nvidia::ConfigParser::load(argv[1]);
        std::cerr << "============================================================\n"
                  << " EasyAIoT RUNTIME-NVIDIA " << RUNTIME_VERSION_STR << "\n"
                  << " NVDEC surface -> CUDA preprocess -> TensorRT enqueueV3\n"
                  << " Strict hardware mode: no ONNX/CPU/software codec fallback\n"
                  << "============================================================\n";
        easyaiot::nvidia::Pipeline pipeline(std::move(config));
        pipeline.start();
        while (pipeline.running() && !stopRequested.load()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(200));
        }
        pipeline.stop();
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "[RUNTIME-NVIDIA FATAL] " << error.what() << '\n';
        return 1;
    }
}
