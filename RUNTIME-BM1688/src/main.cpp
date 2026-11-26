#include "Config.h"
#include "Pipeline.h"

#include <atomic>
#include <csignal>
#include <cstring>
#include <iostream>
#include <memory>
#include <thread>

#ifndef RUNTIME_VERSION_STR
#define RUNTIME_VERSION_STR "unknown"
#endif

namespace {
std::atomic<bool> gStop{false};
void signalHandler(int) { gStop.store(true); }
}
int main(int argc, char** argv) {
    if (argc == 2 && (std::strcmp(argv[1], "--version") == 0 ||
                      std::strcmp(argv[1], "-V") == 0)) {
        std::cout << "RUNTIME-BM1688 " << RUNTIME_VERSION_STR << '\n';
        return 0;
    }
    if (argc != 2) {
        std::cerr << "用法: " << argv[0] << " <config.ini>\n";
        return 2;
    }

    std::signal(SIGINT, signalHandler);
    std::signal(SIGTERM, signalHandler);
    try {
        auto config = easyaiot::bm1688::ConfigParser::load(argv[1]);
        std::cerr << "============================================================\n"
                  << " EasyAIoT RUNTIME-BM1688 " << RUNTIME_VERSION_STR << "\n"
                  << " Sophon VPU -> BMCV VPSS -> BMRuntime core0/core1\n"
                  << " Strict hardware mode: no ONNX/CPU/software codec fallback\n"
                  << "============================================================\n";
        easyaiot::bm1688::Pipeline pipeline(std::move(config));
        pipeline.start();
        while (pipeline.running() && !gStop.load()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(200));
        }
        pipeline.stop();
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "[RUNTIME-BM1688 FATAL] " << error.what() << '\n';
        return 1;
    }
}
