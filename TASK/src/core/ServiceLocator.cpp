#include "ServiceLocator.h"
#include "ConfigurationManager.h"
#include <iostream>

ServiceLocator& ServiceLocator::getInstance() {
    static ServiceLocator instance;
    return instance;
}

void ServiceLocator::initializeServices() {
    std::lock_guard<std::mutex> lock(services_mutex_);
    
    auto& config_manager = ConfigurationManager::getInstance();
    
    // Initialize MQTT client
    auto mqtt_config = config_manager.getMQTTConfig();
    if (mqtt_config.enabled) {
        mqtt_client_ = std::make_shared<MQTTClient>(
            mqtt_config.broker_url,
            mqtt_config.client_id,
            mqtt_config.username,
            mqtt_config.password
        );
        
        if (mqtt_client_->connect()) {
            std::cout << "MQTT client connected successfully" << std::endl;
            mqtt_initialized_ = true;
        } else {
            std::cerr << "Failed to connect MQTT client" << std::endl;
            mqtt_client_.reset();
        }
    }
    
    // Initialize MinIO client
    auto minio_config = config_manager.getMinioConfig();
    if (minio_config.enabled) {
        minio_client_ = std::make_shared<MinIOClient>(
            minio_config.endpoint,
            minio_config.access_key,
            minio_config.secret_key,
            minio_config.secure
        );
        
        if (minio_client_->initialize()) {
            std::cout << "MinIO client initialized successfully" << std::endl;
            minio_initialized_ = true;
            
            // Create required buckets
            minio_client_->createBucket(minio_config.bucket_name);
        } else {
            std::cerr << "Failed to initialize MinIO client" << std::endl;
            minio_client_.reset();
        }
    }
    
    services_ready_ = (mqtt_client_ != nullptr || !mqtt_config.enabled) &&
                     (minio_client_ != nullptr || !minio_config.enabled);
}

void ServiceLocator::shutdownServices() {
    std::lock_guard<std::mutex> lock(services_mutex_);
    
    if (mqtt_client_) {
        mqtt_client_->disconnect();
        mqtt_client_.reset();
    }
    
    if (minio_client_) {
        minio_client_.reset();
    }
    
    services_ready_ = false;
    mqtt_initialized_ = false;
    minio_initialized_ = false;
}

std::shared_ptr<MQTTClient> ServiceLocator::getMQTTClient() {
    std::lock_guard<std::mutex> lock(services_mutex_);
    return mqtt_client_;
}

std::shared_ptr<MinIOClient> ServiceLocator::getMinIOClient() {
    std::lock_guard<std::mutex> lock(services_mutex_);
    return minio_client_;
}

bool ServiceLocator::areServicesReady() const {
    std::lock_guard<std::mutex> lock(services_mutex_);
    return services_ready_;
}

std::string ServiceLocator::getServiceStatus() const {
    std::lock_guard<std::mutex> lock(services_mutex_);
    
    std::string status;
    status += "MQTT: " + std::string(mqtt_initialized_ ? "Connected" : "Disconnected") + "\n";
    status += "MinIO: " + std::string(minio_initialized_ ? "Connected" : "Disconnected") + "\n";
    status += "Overall: " + std::string(services_ready_ ? "Ready" : "Not Ready");
    
    return status;
}