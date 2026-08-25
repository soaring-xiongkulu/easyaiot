//
// Created by basiclab on 25-10-15.
//

#ifndef CONFIG_H
#define CONFIG_H

#include <string>
#include <vector>
#include <map>
#include <cstdint>
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
    /** 模型加载顺序（ini 出现顺序）；model_path/classes_path 对应键 "default" */
    std::vector<std::string> modelKeys;
    std::map<std::string, std::vector<std::vector<cv::Point>>> regions;
    int threadNums{2};

    int videoWidth{1920};
    int videoHeight{1080};
    int rtmpFps{25};
    /** RTMP ABR bitrate bits/sec; 0 = auto by encode resolution. Accepts ini/env like 4500k. */
    int64_t videoBitRate{0};
    /** Encoder GOP frames; 0 = 2 * fps. */
    int videoGopSize{0};

    float alarmConfidenceThreshold{0.5f};
    int alarmCooldownTime{30};
    /** 告警触发类别；为空时任意检测均可触发（与 VIDEO alert_class_filter.py 一致） */
    std::vector<std::string> alertClassNames;

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
    /** 任务启用人脸匹配：MQTT/Infer 路径下额外向 alertHookUrl 投递 face_feed_only 告警，
     * 由 VIDEO /video/alert/hook 将整帧截图送入人脸抓取队列（RUNTIME 人脸链路桥）。 */
    bool faceMatchingEnabled{false};
    /** 任务启用车牌匹配：MQTT/Infer 路径下额外向 alertHookUrl 投递 plate_feed_only 告警，
     * 由 VIDEO /video/alert/hook 将整帧截图送入车牌抓取队列（RUNTIME 车牌链路桥）。 */
    bool plateMatchingEnabled{false};
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
