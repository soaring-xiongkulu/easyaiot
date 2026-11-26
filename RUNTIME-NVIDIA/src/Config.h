#pragma once

#include <string>
#include <vector>

namespace easyaiot::nvidia {

struct ModelConfig {
    int id{-2};
    std::string path;
    std::string classesPath;
};

struct RuntimeConfig {
    std::string source;
    int width{1920};
    int height{1080};
    int fps{25};
    int frameSkip{1};
    float confidence{0.5F};
    float nmsThreshold{0.45F};
    std::vector<ModelConfig> models;

    int cudaDevice{0};
    int inferStreams{2};
    int decoderSurfaces{16};
    int decodeQueueDepth{8};
    int inferQueueDepth{4};
    int resultQueueDepth{64};
    bool zeroCopy{true};
    bool preallocate{true};
    bool cudaGraph{true};
    bool requireNvdec{true};
    bool requireNvenc{false};
    std::string decoder{"h264_cuvid,hevc_cuvid,av1_cuvid"};

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
    int cooldownSec{30};

    std::string busTransport{"mqtt"};
    std::string mqttBrokers;
    std::string mqttUsername;
    std::string mqttPassword;
    std::string mqttClientId{"runtime-nvidia"};
    std::string mqttTenant{"default"};
    std::string computeNodeId;
};

class ConfigParser {
public:
    static RuntimeConfig load(const std::string& path);
};

}  // namespace easyaiot::nvidia
