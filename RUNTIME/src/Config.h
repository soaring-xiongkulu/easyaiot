//
// Created by basiclab on 25-10-15.
//

#ifndef CONFIG_H
#define CONFIG_H

#include <string>
#include <vector>
#include <map>
#include <opencv2/opencv.hpp>

struct DeviceStreamConfig {
    std::string deviceId;
    std::string deviceName;
    std::string rtspUrl;
};

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

    int videoWidth{1920};
    int videoHeight{1080};
    int rtmpFps{25};

    float alarmConfidenceThreshold{0.5f};
    int alarmCooldownTime{30};

    std::string taskId;
    int controlPort{8000};

    // VIDEO 平台对接（[video_task]）
    std::string deviceId;
    std::string deviceName;
    std::string taskType{"realtime"};  // realtime | snap | snapshot | patrol
    std::string algorithmName{"detection"};
    std::string heartbeatUrl;
    std::string alertHookUrl;
    std::string logPath;
    std::string alertImageDir;
    int heartbeatIntervalSec{10};
    bool headless{true};
    int frameSkip{8};  // realtime: infer every N frames; snap fallback interval sec

    // snap
    std::string cronExpression;

    // patrol
    std::string patrolMode{"pool"};  // pool | rotate
    int patrolIntervalSec{10};
    int patrolPoolSize{4};

    // multi-device (snap/patrol; realtime may also list primary first)
    std::vector<DeviceStreamConfig> devices;
} Config;

#endif //CONFIG_H
