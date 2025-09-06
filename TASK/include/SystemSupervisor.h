#pragma once
#include "ConfigurationManager.h"
#include "ServiceLocator.h"
#include "CameraStreamer.h"
#include "FrameProcessor.h"
#include <vector>
#include <map>
#include <thread>
#include <atomic>

class SystemSupervisor {
public:
    SystemSupervisor();
    ~SystemSupervisor();

    bool initialize();
    void start();
    void stop();
    void shutdown();

    std::map<std::string, std::string> getStatus() const;

private:
    ConfigurationManager& config_manager_;
    ServiceLocator& service_locator_;

    std::vector<std::string> enabled_cameras_;
    std::map<std::string, std::unique_ptr<CameraStreamer>> camera_streamers_;
    std::map<std::string, std::unique_ptr<FrameProcessor>> frame_processors_;

    std::thread processing_thread_;
    std::thread health_check_thread_;
    std::atomic<bool> running_{false};
    std::atomic<bool> initialized_{false};

    void loadCameraConfigurations();
    void initializeCameraStreamers();
    void initializeFrameProcessors();

    void processingLoop();
    void healthCheckLoop();
    void handleCameraFailure(const std::string& camera_id);
    void cleanupInactiveModels();
};