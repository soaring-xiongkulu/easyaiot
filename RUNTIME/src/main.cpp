/*
 * RUNTIME Module - Main Entry Point
 * Features: RTSP pull + decode + YOLO infer + VIDEO alert hook (ring pipeline)
 */

#include <iostream>
#include <string>
#include <csignal>
#include <glog/logging.h>
#include "Manage.h"
#include "Config.h"
#include "ConfigParser.h"

Server* g_server = nullptr;

void printUsage(const char* program) {
    std::cout << "\n";
    std::cout << "============================================\n";
    std::cout << "  RUNTIME - AI Real-time Inference Worker\n";
    std::cout << "============================================\n";
    std::cout << "\nUsage:\n";
    std::cout << "  " << program << " <config.ini>\n";
    std::cout << "\nExample:\n";
    std::cout << "  " << program << " config/task_123.ini\n";
    std::cout << "\nRefer to: config/config.example.ini\n";
    std::cout << "============================================\n\n";
}

void printBanner() {
    std::cout << "\n";
    std::cout << "============================================\n";
    std::cout << "  EasyAIoT RUNTIME\n";
    std::cout << "  C++ frame pipeline for VIDEO executor=cpp\n";
    std::cout << "  Version 2.0.0\n";
    std::cout << "============================================\n";
    std::cout << "\n";
}

int main(int argc, char* argv[]) {
    printBanner();

    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <config_file.ini>" << std::endl;
        printUsage(argv[0]);
        return -1;
    }

    std::string config_file = argv[1];

    google::InitGoogleLogging(argv[0]);
    FLAGS_logtostderr = true;
    FLAGS_colorlogtostderr = true;
    FLAGS_minloglevel = 0;

    LOG(INFO) << "============================================================";
    LOG(INFO) << "[STARTING] RUNTIME module initializing...";
    LOG(INFO) << "[CONFIG] Config file: " << config_file;
    LOG(INFO) << "============================================================";

    Config config;
    ConfigParser parser;

    if (!parser.parse(config_file, config)) {
        LOG(ERROR) << "[ERROR] Config file parse failed: " << config_file;
        google::ShutdownGoogleLogging();
        return -1;
    }

    LOG(INFO) << "[OK] Config file parsed successfully";
    LOG(INFO) << "  - RTSP URL: " << config.rtspUrl;
    LOG(INFO) << "  - Alert hook: " << (config.enableAlarm ? config.hookHttpUrl : "Disabled");
    LOG(INFO) << "  - Heartbeat: " << (config.heartbeatUrl.empty() ? "Disabled" : config.heartbeatUrl);
    LOG(INFO) << "  - Device: " << config.deviceId << " / " << config.deviceName;
    LOG(INFO) << "  - Headless: " << (config.headless ? "true" : "false");

    try {
        g_server = new Server(config);

        LOG(INFO) << "[STARTING] Starting RUNTIME service...";

        if (!g_server->start()) {
            LOG(ERROR) << "[ERROR] RUNTIME service start failed";
            delete g_server;
            google::ShutdownGoogleLogging();
            return -1;
        }

        LOG(INFO) << "[OK] RUNTIME service started successfully!";
        g_server->waitForShutdown();

        LOG(INFO) << "[SHUTDOWN] Received exit signal, shutting down...";
        g_server->stop();
        delete g_server;
        g_server = nullptr;
        LOG(INFO) << "[OK] Service shutdown safely";
    } catch (const std::exception& e) {
        LOG(ERROR) << "[EXCEPTION] " << e.what();
        if (g_server) {
            delete g_server;
            g_server = nullptr;
        }
        google::ShutdownGoogleLogging();
        return -1;
    }

    google::ShutdownGoogleLogging();
    return 0;
}
