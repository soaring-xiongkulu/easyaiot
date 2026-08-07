//
// Created by basiclab on 25-10-15.
//

#ifndef CONFIG_H
#define CONFIG_H

#include <string>
#include <vector>
#include <map>
#include <opencv2/opencv.hpp>

typedef struct Config {
    std::string rtspUrl;
    std::string rtmpUrl;
    std::string hookHttpUrl;
    bool enableRtmp{false};
    bool enableAI{true};
    bool enableDrawRtmp{true};
    bool enableAlarm{true};
    std::map<std::string, std::string> modelPaths;
    std::map<std::string, std::string> modelClasses;
    std::map<std::string, std::vector<std::vector<cv::Point>>> regions;
    int threadNums{2};
    
    // RTMP推流配置
    int videoWidth{1920};
    int videoHeight{1080};
    int rtmpFps{25};
    
    // 告警配置
    float alarmConfidenceThreshold{0.5f};
    int alarmCooldownTime{30};
    
    // 任务配置
    std::string taskId;
    int controlPort{8000};

    // VIDEO 平台对接（[video_task]）
    std::string deviceId;
    std::string deviceName;
    std::string taskType{"realtime"};
    std::string algorithmName{"detection"};
    std::string heartbeatUrl;
    std::string alertHookUrl;
    std::string logPath;
    int heartbeatIntervalSec{10};
    bool headless{true};
} Config;

#endif //CONFIG_H
