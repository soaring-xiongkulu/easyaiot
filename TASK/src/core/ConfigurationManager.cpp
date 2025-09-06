#include "ConfigurationManager.h"
#include <fstream>
#include <iostream>
#include <filesystem>

ConfigurationManager& ConfigurationManager::getInstance() {
    static ConfigurationManager instance;
    return instance;
}

bool ConfigurationManager::loadSystemConfig(const std::string& config_path) {
    std::lock_guard<std::mutex> lock(config_mutex_);
    
    try {
        std::ifstream config_file(config_path);
        if (!config_file.is_open()) {
            std::cerr << "Failed to open system config file: " << config_path << std::endl;
            return false;
        }
        
        nlohmann::json config_data;
        config_file >> config_data;
        config_file.close();
        
        // Parse system configuration
        if (config_data.contains("system")) {
            auto system = config_data["system"];
            system_config_.log_level = system.value("log_level", "info");
            system_config_.max_processing_threads = system.value("max_processing_threads", 4);
            system_config_.frame_queue_size = system.value("frame_queue_size", 100);
            system_config_.alert_queue_size = system.value("alert_queue_size", 1000);
            system_config_.data_directory = system.value("data_directory", "/var/lib/smart_surveillance");
            system_config_.max_storage_days = system.value("max_storage_days", 30);
            system_config_.health_check_interval = system.value("health_check_interval", 30);
        }
        
        // Parse MQTT configuration
        if (config_data.contains("mqtt")) {
            auto mqtt = config_data["mqtt"];
            mqtt_config_.enabled = mqtt.value("enabled", false);
            mqtt_config_.broker_url = mqtt.value("broker_url", "tcp://localhost:1883");
            mqtt_config_.client_id = mqtt.value("client_id", "surveillance_system");
            mqtt_config_.username = mqtt.value("username", "");
            mqtt_config_.password = mqtt.value("password", "");
            mqtt_config_.qos_level = mqtt.value("qos_level", 1);
            mqtt_config_.retain_messages = mqtt.value("retain_messages", true);
            
            if (mqtt.contains("topics")) {
                mqtt_config_.topics["alerts"] = mqtt["topics"].value("alerts", "surveillance/alerts");
                mqtt_config_.topics["events"] = mqtt["topics"].value("events", "surveillance/events");
                mqtt_config_.topics["status"] = mqtt["topics"].value("status", "surveillance/status");
                mqtt_config_.topics["control"] = mqtt["topics"].value("control", "surveillance/control");
            }
        }
        
        // Parse MinIO configuration
        if (config_data.contains("minio")) {
            auto minio = config_data["minio"];
            minio_config_.enabled = minio.value("enabled", false);
            minio_config_.endpoint = minio.value("endpoint", "localhost:9000");
            minio_config_.access_key = minio.value("access_key", "minioadmin");
            minio_config_.secret_key = minio.value("secret_key", "minioadmin");
            minio_config_.secure = minio.value("secure", false);
            minio_config_.bucket_name = minio.value("bucket_name", "surveillance-data");
            minio_config_.region = minio.value("region", "us-east-1");
            minio_config_.alert_images_path = minio.value("alert_images_path", "alerts/images");
            minio_config_.alert_videos_path = minio.value("alert_videos_path", "alerts/videos");
            minio_config_.model_storage_path = minio.value("model_storage_path", "models");
        }
        
        // Parse streaming configuration
        if (config_data.contains("streaming")) {
            auto streaming = config_data["streaming"];
            streaming_config_.rtmp_server = streaming.value("rtmp_server", "rtmp://localhost:1935/live");
            streaming_config_.hls_server = streaming.value("hls_server", "http://localhost:8080/hls");
            streaming_config_.webrtc_server = streaming.value("webrtc_server", "http://localhost:8889/webrtc");
        }
        
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error loading system configuration: " << e.what() << std::endl;
        return false;
    }
}

bool ConfigurationManager::loadCameraConfig(const std::string& camera_id, const std::string& config_path) {
    std::lock_guard<std::mutex> lock(config_mutex_);
    
    try {
        std::ifstream config_file(config_path);
        if (!config_file.is_open()) {
            std::cerr << "Failed to open camera config file: " << config_path << std::endl;
            return false;
        }
        
        nlohmann::json config_data;
        config_file >> config_data;
        config_file.close();
        
        camera_configs_[camera_id] = config_data;
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error loading camera configuration: " << e.what() << std::endl;
        return false;
    }
}

SystemConfig ConfigurationManager::getSystemConfig() const {
    std::lock_guard<std::mutex> lock(config_mutex_);
    return system_config_;
}

MQTTConfig ConfigurationManager::getMQTTConfig() const {
    std::lock_guard<std::mutex> lock(config_mutex_);
    return mqtt_config_;
}

MinioConfig ConfigurationManager::getMinioConfig() const {
    std::lock_guard<std::mutex> lock(config_mutex_);
    return minio_config_;
}

StreamingConfig ConfigurationManager::getStreamingConfig() const {
    std::lock_guard<std::mutex> lock(config_mutex_);
    return streaming_config_;
}

nlohmann::json ConfigurationManager::getCameraConfig(const std::string& camera_id) const {
    std::lock_guard<std::mutex> lock(config_mutex_);
    auto it = camera_configs_.find(camera_id);
    if (it != camera_configs_.end()) {
        return it->second;
    }
    return nlohmann::json();
}

std::vector<std::string> ConfigurationManager::getEnabledCameras() const {
    std::lock_guard<std::mutex> lock(config_mutex_);
    std::vector<std::string> enabled_cameras;
    
    for (const auto& [camera_id, config] : camera_configs_) {
        if (config.value("enabled", false)) {
            enabled_cameras.push_back(camera_id);
        }
    }
    
    return enabled_cameras;
}