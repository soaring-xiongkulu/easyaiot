#pragma once

#include <string>
#include <vector>

namespace easyaiot::bm1688 {

struct ModelConfig {
    int id{-2};
    std::string path;
    std::string classesPath;
};

struct RuntimeConfig {
    std::string source;
    std::string rtmpUrl;
    int width{1920};
    int height{1080};
    int fps{25};
    int frameSkip{1};
    float confidence{0.5F};
    float nmsThreshold{0.45F};
    std::vector<ModelConfig> models;

    int deviceId{0};
    std::vector<int> coreIds{0, 1};
    int decodeQueueDepth{8};
    int inferQueueDepth{4};
    int resultQueueDepth{64};
    bool preallocate{true};
    bool zeroCopy{true};
    bool useVpp{true};
    std::string decoder{"h264_bm,hevc_bm"};

    bool enableRtmp{false};
    bool enableAlarm{true};
    std::string alertHookUrl;
    std::string heartbeatUrl;
    int heartbeatIntervalSec{10};
    int controlPort{8000};
    int taskId{0};
    std::string taskType{"realtime"};
    std::string deviceIdText;
    std::string deviceName;
    std::string algorithmName{"yolov8"};
    std::string logPath;
    std::string alertImageDir;
    int cooldownSec{30};

    std::string busTransport{"mqtt"};
    std::string mqttBrokers;
    std::string mqttUsername;
    std::string mqttPassword;
    std::string mqttClientId;
    std::string mqttTenant{"default"};
    std::string computeNodeId;
};

class ConfigParser {
public:
    static RuntimeConfig load(const std::string& path);
};

}  // namespace easyaiot::bm1688
