/*
 * TASK Module - Main Entry Point
 * Features: RTSP Stream + YOLOv11 Inference + Alarm Detection + HTTP Callback
 */

#include <iostream>
#include <string>
#include <csignal>
#include <glog/logging.h>
#include "Manage.h"
#include "Config.h"
#include "ConfigParser.h"

// Global Server instance pointer (for signal handling)
Server* g_server = nullptr;

void printUsage(const char* program) {
    std::cout << "\n";
    std::cout << "============================================\n";
    std::cout << "  TASK Module - AI Real-time Inference\n";
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
    std::cout << "╔════════════════════════════════════════════════════════╗\n";
    std::cout << "║                                                        ║\n";
    std::cout << "║     ████████╗ █████╗ ███████╗██╗  ██╗                ║\n";
    std::cout << "║     ╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝                ║\n";
    std::cout << "║        ██║   ███████║███████╗█████╔╝                 ║\n";
    std::cout << "║        ██║   ██╔══██║╚════██║██╔═██╗                 ║\n";
    std::cout << "║        ██║   ██║  ██║███████║██║  ██╗                ║\n";
    std::cout << "║        ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝                ║\n";
    std::cout << "║                                                        ║\n";
    std::cout << "║          AI Real-time Inference System                ║\n";
    std::cout << "║              Version 1.0.0 - Windows                  ║\n";
    std::cout << "║                                                        ║\n";
    std::cout << "╚════════════════════════════════════════════════════════╝\n";
    std::cout << "\n";
}

int main(int argc, char* argv[]) {
    // Display welcome banner
    printBanner();
    
    // Check arguments
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <config_file.ini>" << std::endl;
        printUsage(argv[0]);
        return -1;
    }
    
    std::string config_file = argv[1];
    
    // Initialize logging system
    google::InitGoogleLogging(argv[0]);
    FLAGS_logtostderr = true;  // Output to stderr
    FLAGS_colorlogtostderr = true;  // Colored output
    FLAGS_minloglevel = 0;  // INFO level and above
    
    LOG(INFO) << "============================================================";
    LOG(INFO) << "[STARTING] TASK module initializing...";
    LOG(INFO) << "[CONFIG] Config file: " << config_file;
    LOG(INFO) << "============================================================";
    
    // 解析配置文件
    Config config;
    ConfigParser parser;
    
    if (!parser.parse(config_file, config)) {
        LOG(ERROR) << "[ERROR] Config file parse failed: " << config_file;
        LOG(ERROR) << "[ERROR] Please check config file format";
        google::ShutdownGoogleLogging();
        return -1;
    }
    
    LOG(INFO) << "[OK] Config file parsed successfully";
    LOG(INFO) << "";
    LOG(INFO) << "Configuration:";
    LOG(INFO) << "  - RTSP URL: " << config.rtspUrl;
    LOG(INFO) << "  - RTMP URL: " << (config.enableRtmp ? config.rtmpUrl : "Disabled");
    LOG(INFO) << "  - Hook URL: " << (config.enableAlarm ? config.hookHttpUrl : "Disabled");
    LOG(INFO) << "  - Thread count: " << config.threadNums;
    LOG(INFO) << "  - AI inference: " << (config.enableAI ? "Enabled" : "Disabled");
    LOG(INFO) << "  - RTMP stream: " << (config.enableRtmp ? "Enabled" : "Disabled");
    LOG(INFO) << "  - Alarm detection: " << (config.enableAlarm ? "Enabled" : "Disabled");
    LOG(INFO) << "  - Draw boxes: " << (config.enableDrawRtmp ? "Enabled" : "Disabled");
    LOG(INFO) << "";
    
    // Create Server instance
    try {
        g_server = new Server(config);
        
        LOG(INFO) << "[STARTING] Starting TASK service...";
        
        if (!g_server->start()) {
            LOG(ERROR) << "[ERROR] TASK service start failed";
            delete g_server;
            google::ShutdownGoogleLogging();
            return -1;
        }
        
        LOG(INFO) << "[OK] TASK service started successfully!";
        LOG(INFO) << "";
        LOG(INFO) << "============================================================";
        LOG(INFO) << "System running... Press Ctrl+C to exit";
        LOG(INFO) << "============================================================";
        LOG(INFO) << "";
        
        // Wait for shutdown signal
        g_server->waitForShutdown();
        
        LOG(INFO) << "";
        LOG(INFO) << "============================================================";
        LOG(INFO) << "[SHUTDOWN] Received exit signal, shutting down...";
        LOG(INFO) << "============================================================";
        
        // Stop service
        g_server->stop();
        delete g_server;
        g_server = nullptr;
        
        LOG(INFO) << "[OK] Service shutdown safely";
        LOG(INFO) << "Goodbye!";
        
    } catch (const std::exception& e) {
        LOG(ERROR) << "[EXCEPTION] " << e.what();
        if (g_server) {
            delete g_server;
            g_server = nullptr;
        }
        google::ShutdownGoogleLogging();
        return -1;
    }
    
    // 关闭日志系统
    google::ShutdownGoogleLogging();
    
    return 0;
}
