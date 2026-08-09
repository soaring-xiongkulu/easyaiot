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

    // detect_conf (VIDEO confidence_threshold): used as YOLO/ONNX score_threshold.
    // Python oracle applies the same value to ultralytics conf= / ONNXInference conf_threshold;
    // there is no separate alarm conf — alarm filter uses the same threshold.
    float detectConfidenceThreshold{0.5f};
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
    std::string patrolMode{"pool"};  // pool | rotate | hybrid
    int patrolIntervalSec{10};
    int patrolPoolSize{4};

    // multi-device (snap/patrol; realtime may also list primary first)
    std::vector<DeviceStreamConfig> devices;

    // AI execution backend: prefer CUDA EP, fallback CPU
    bool preferGpu{true};
    bool forceCpu{false};
    int gpuDeviceId{0};

    // [tracking] — parsed for contract; frame-in impl Phase 4
    bool trackingEnabled{false};
    float trackingSimilarityThreshold{0.2f};
    int trackingMaxAge{25};
    float trackingSmoothAlpha{0.25f};

    // [motion_gate]
    bool motionGateEnabled{false};
    std::string motionGateConfigJson;

    // [alert_filter] / [hook] — hook passthrough + future frame-in filter
    std::string alertClassNamesJson;
    bool faceDetectionEnabled{true};
    bool plateDetectionEnabled{true};

    // [matching] / [post_process] / [pose] — VIDEO frame-post (logged unsupported in C++)
    bool faceMatchingEnabled{false};
    bool plateMatchingEnabled{false};
    bool postProcessEnabled{false};
    bool poseAnalysisEnabled{false};
    bool poseIntentEnabled{false};
    bool samSupplementEnabled{false};

    // [defense] — VIDEO consumes
    std::string defenseMode{"half"};
    std::string defenseScheduleJson;

    // [patrol_extra]
    std::string focusDeviceId;

    // Extra ONNX paths beyond [ai] model_path (CAP-MULTI-MODEL)
    std::vector<std::string> extraModelPaths;

    // [stream_src] — CAP-GB28181-SRC (VIDEO resolves; C++ consumes resolved URL)
    bool gb28181Enabled{false};
    bool gb28181Resolved{false};
    std::string streamOriginalSource;
    std::string streamResolvedUrl;

    // [encoder] — CAP-NVENC-AUTO (try NVENC → software fallback + quality profile)
    bool nvencAuto{false};
    bool qualityAutoDowngrade{false};
    std::string qualityProfile{"high"};

    // Declared in ini [unsupported] or derived at parse time (G-2.3)
    std::vector<std::string> unsupportedCaps;
} Config;

#endif //CONFIG_H
