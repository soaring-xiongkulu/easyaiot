#pragma once
#include <nlohmann/json.hpp>
#include <string>
#include <map>
#include <vector>
#include <mutex>

struct SystemConfig {
    std::string log_level;
    int max_processing_threads;
    int frame_queue_size;
    int alert_queue_size;
    std::string data_directory;
    int max_storage_days;
    int health_check_interval;
};

struct MQTTConfig {
    bool enabled;
    std::string broker_url;
    std::string client_id;
    std::string username;
    std::string password;
    int qos_level;
    bool retain_messages;
    std::map<std::string, std::string> topics;
};

struct MinioConfig {
    bool enabled;
    std::string endpoint;
    std::string access_key;
    std::string secret_key;
    bool secure;
    std::string bucket_name;
    std::string region;
    std::string alert_images_path;
    std::string alert_videos_path;
    std::string model_storage_path;
};

struct StreamingConfig {
    std::string rtmp_server;
    std::string hls_server;
    std::string webrtc_server;
};

class ConfigurationManager {
public:
    static ConfigurationManager& getInstance();

    bool loadSystemConfig(const std::string& config_path);
    bool loadCameraConfig(const std::string& camera_id, const std::string& config_path);
    bool loadModelConfig(const std::string& model_id, const std::string& config_path);
    bool loadZoneConfig(const std::string& zone_id, const std::string& config_path);

    SystemConfig getSystemConfig() const;
    MQTTConfig getMQTTConfig() const;
    MinioConfig getMinioConfig() const;
    StreamingConfig getStreamingConfig() const;

    nlohmann::json getCameraConfig(const std::string& camera_id) const;
    nlohmann::json getModelConfig(const std::string& model_id) const;
    nlohmann::json getZoneConfig(const std::string& zone_id) const;

    std::vector<std::string> getEnabledCameras() const;

private:
    ConfigurationManager() = default;
    ~ConfigurationManager() = default;

    SystemConfig system_config_;
    MQTTConfig mqtt_config_;
    MinioConfig minio_config_;
    StreamingConfig streaming_config_;

    std::map<std::string, nlohmann::json> camera_configs_;
    std::map<std::string, nlohmann::json> model_configs_;
    std::map<std::string, nlohmann::json> zone_configs_;

    mutable std::mutex config_mutex_;
};