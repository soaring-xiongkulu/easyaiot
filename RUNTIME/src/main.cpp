/*
 * RUNTIME Module - Main Entry Point
 * Features: RTSP pull + decode + YOLO infer + VIDEO alert hook (ring pipeline)
 */

#include <iostream>
#include <string>
#include <cstring>
#include <csignal>
#include <glog/logging.h>
#include "Manage.h"
#include "Config.h"
#include "ConfigParser.h"

#ifndef RUNTIME_VERSION_STR
#define RUNTIME_VERSION_STR "unknown"
#endif

Server* g_server = nullptr;

void printUsage(const char* program) {
    std::cout << "\n";
    std::cout << "============================================\n";
    std::cout << "  RUNTIME - AI Real-time Inference Worker\n";
    std::cout << "============================================\n";
    std::cout << "\nUsage:\n";
    std::cout << "  " << program << " <config.ini>\n";
    std::cout << "  " << program << " --version\n";
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
    std::cout << "  Version " << RUNTIME_VERSION_STR << "\n";
    std::cout << "============================================\n";
    std::cout << "\n";
}

int main(int argc, char* argv[]) {
    if (argc >= 2 && (std::strcmp(argv[1], "--version") == 0
                      || std::strcmp(argv[1], "-V") == 0
                      || std::strcmp(argv[1], "-v") == 0)) {
        std::cout << "RUNTIME " << RUNTIME_VERSION_STR << std::endl;
        return 0;
    }

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
    LOG(INFO) << "[启动] RUNTIME 模块初始化中...";
    LOG(INFO) << "[版本] " << RUNTIME_VERSION_STR;
    LOG(INFO) << "[配置] 配置文件: " << config_file;
    LOG(INFO) << "============================================================";

    Config config;
    ConfigParser parser;

    if (!parser.parse(config_file, config)) {
        LOG(ERROR) << "[错误] 配置文件解析失败: " << config_file;
        google::ShutdownGoogleLogging();
        return -1;
    }

    LOG(INFO) << "[成功] 配置文件解析成功";
    LOG(INFO) << "  - RTSP 地址: " << config.rtspUrl;
    LOG(INFO) << "  - 任务类型: " << config.taskType;
    LOG(INFO) << "  - RTMP 地址: " << (config.rtmpUrl.empty() ? "无" : config.rtmpUrl);
    LOG(INFO) << "  - 告警回调: " << (config.enableAlarm ? config.hookHttpUrl : "已禁用");
    LOG(INFO) << "  - 心跳: " << (config.heartbeatUrl.empty() ? "已禁用" : config.heartbeatUrl);
    LOG(INFO) << "  - 设备: " << config.deviceId << " / " << config.deviceName;
    LOG(INFO) << "  - 无界面模式: " << (config.headless ? "开启" : "关闭");

    try {
        g_server = new Server(config);

        LOG(INFO) << "[启动] RUNTIME 服务启动中...";

        if (!g_server->start()) {
            LOG(ERROR) << "[错误] RUNTIME 服务启动失败";
            delete g_server;
            google::ShutdownGoogleLogging();
            return -1;
        }

        LOG(INFO) << "[成功] RUNTIME 服务启动成功！";
        g_server->waitForShutdown();

        LOG(INFO) << "[关闭] 收到退出信号，正在关闭...";
        g_server->stop();
        delete g_server;
        g_server = nullptr;
        LOG(INFO) << "[成功] 服务已安全关闭";
    } catch (const std::exception& e) {
        LOG(ERROR) << "[异常] " << e.what();
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
