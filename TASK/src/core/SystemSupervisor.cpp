#include "SystemSupervisor.h"
#include <filesystem>
#include <chrono>

SystemSupervisor::SystemSupervisor()
    : config_manager_(ConfigurationManager::getInstance()),
      service_locator_(ServiceLocator::getInstance()) {}

SystemSupervisor::~SystemSupervisor() {
    stop();
    shutdown();
}

bool SystemSupervisor::initialize() {
    if (initialized_) {
        return true;
    }
    
    // Load system configuration
    if (!config_manager_.loadSystemConfig("config/system_config.json")) {
        std::cerr << "Failed to load system configuration" << std::endl;
        return false;
    }
    
    // Load camera configurations
    loadCameraConfigurations();
    
    // Initialize shared services
    service_locator_.initializeServices();
    
    // Initialize camera streamers and processors
    initializeCameraStreamers();
    initializeFrameProcessors();
    
    initialized_ = true;
    return true;
}

void SystemSupervisor::loadCameraConfigurations() {
    enabled_cameras_.clear();
    
    // Load all camera configuration files from config/cameras directory
    for (const auto& entry : std::filesystem::directory_iterator("config/cameras")) {
        if (entry.path().extension() == ".json") {
            std::string camera_id = entry.path().stem().string();
            if (config_manager_.loadCameraConfig(camera_id, entry.path().string())) {
                auto config = config_manager_.getCameraConfig(camera_id);
                if (config.value("enabled", false)) {
                    enabled_cameras_.push_back(camera_id);
                }
            }
        }
    }
}

void SystemSupervisor::initializeCameraStreamers() {
    for (const auto& camera_id : enabled_cameras_) {
        auto config = config_manager_.getCameraConfig(camera_id);
        std::string source_type = config.value("source_type", "rtsp");
        
        std::unique_ptr<CameraStreamer> streamer;
        
        if (source_type == "rtsp") {
            std::string rtsp_url = config.value("rtsp_url", "");
            streamer = std::make_unique<RTSPCamera>(camera_id, rtsp_url);
        } else if (source_type == "usb") {
            int device_index = config.value("device_index", 0);
            streamer = std::make_unique<USBCamera>(camera_id, device_index);
        }
        
        if (streamer && streamer->initialize()) {
            camera_streamers_[camera_id] = std::move(streamer);
        }
    }
}

void SystemSupervisor::initializeFrameProcessors() {
    for (const auto& camera_id : enabled_cameras_) {
        auto config = config_manager_.getCameraConfig(camera_id);
        
        auto processor = std::make_unique<FrameProcessor>(camera_id);
        if (processor->initialize(config)) {
            frame_processors_[camera_id] = std::move(processor);
        }
    }
}

void SystemSupervisor::start() {
    if (!initialized_ || running_) {
        return;
    }
    
    running_ = true;
    
    // Start all camera streamers
    for (auto& [camera_id, streamer] : camera_streamers_) {
        streamer->start();
    }
    
    // Start processing thread
    processing_thread_ = std::thread(&SystemSupervisor::processingLoop, this);
    
    // Start health check thread
    health_check_thread_ = std::thread(&SystemSupervisor::healthCheckLoop, this);
    
    std::cout << "System started with " << camera_streamers_.size() << " cameras" << std::endl;
}

void SystemSupervisor::processingLoop() {
    while (running_) {
        for (auto& [camera_id, streamer] : camera_streamers_) {
            cv::Mat frame;
            if (streamer->getFrame(frame)) {
                auto processor_it = frame_processors_.find(camera_id);
                if (processor_it != frame_processors_.end()) {
                    processor_it->second->processFrame(frame);
                }
            }
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

void SystemSupervisor::healthCheckLoop() {
    auto& config_manager = ConfigurationManager::getInstance();
    auto system_config = config_manager.getSystemConfig();
    
    while (running_) {
        std::this_thread::sleep_for(
            std::chrono::seconds(system_config.health_check_interval));
        
        // Check camera status
        for (auto& [camera_id, streamer] : camera_streamers_) {
            if (!streamer->isRunning()) {
                std::cerr << "Camera " << camera_id << " is not running, attempting restart..." << std::endl;
                handleCameraFailure(camera_id);
            }
        }
        
        // Check service status
        if (!service_locator_.areServicesReady()) {
            std::cerr << "Services are not ready, attempting reinitialization..." << std::endl;
            service_locator_.initializeServices();
        }
        
        // Cleanup resources
        cleanupInactiveModels();
    }
}

void SystemSupervisor::handleCameraFailure(const std::string& camera_id) {
    auto streamer_it = camera_streamers_.find(camera_id);
    if (streamer_it != camera_streamers_.end()) {
        // Stop and restart the camera
        streamer_it->second->stop();
        
        // Reinitialize camera
        auto config = config_manager_.getCameraConfig(camera_id);
        std::string source_type = config.value("source_type", "rtsp");
        
        std::unique_ptr<CameraStreamer> new_streamer;
        
        if (source_type == "rtsp") {
            std::string rtsp_url = config.value("rtsp_url", "");
            new_streamer = std::make_unique<RTSPCamera>(camera_id, rtsp_url);
        } else if (source_type == "usb") {
            int device_index = config.value("device_index", 0);
            new_streamer = std::make_unique<USBCamera>(camera_id, device_index);
        }
        
        if (new_streamer && new_streamer->initialize()) {
            camera_streamers_[camera_id] = std::move(new_streamer);
            camera_streamers_[camera_id]->start();
            std::cout << "Camera " << camera_id << " restarted successfully" << std::endl;
        }
    }
}