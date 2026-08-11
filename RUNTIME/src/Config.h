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
    std::string alertHookUrl;  // deprecated: events use MQTT; kept for HTTP fallback
    std::string logPath;
    std::string alertImageDir;
    int heartbeatIntervalSec{10};
    bool headless{true};
    int frameSkip{8};  // realtime: infer every N frames; snap fallback interval sec

    // Algorithm event bus (MQTT → iot-sink); heartbeat stays HTTP → VIDEO
    std::string algoBusTransport;  // empty/mqtt default; http/off disables
    std::string mqttBrokerUrls;
    std::string mqttUsername;
    std::string mqttPassword;
    std::string mqttClientId;
    std::string mqttTenant;
    std::string computeNodeId;

    // snap
    std::string cronExpression;

    // patrol
    std::string patrolMode{"pool"};  // pool | rotate
    int patrolIntervalSec{10};
    int patrolPoolSize{4};

    // multi-device (snap/patrol; realtime may also list primary first)
    std::vector<DeviceStreamConfig> devices;

    // AI execution backend: prefer CUDA EP, fallback CPU
    bool preferGpu{true};
    bool forceCpu{false};
    int gpuDeviceId{0};

    // FFmpeg NVDEC/NVENC (NVIDIA); soft fallback on failure
    bool preferHwaccel{true};
    bool forceSoftAv{false};
    int hwaccelDeviceId{-1};  // <0 → use gpuDeviceId after parse
    std::string nvencPreset{"p3"};
} Config;

#endif //CONFIG_H
