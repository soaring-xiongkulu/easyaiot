#pragma once
#include "ObjectTracker.h"
#include "BehaviorAnalyzer.h"
#include "RegionDetector.h"
#include "InferenceEngine.h"
#include <atomic>
#include <condition_variable>
#include <queue>
#include <mutex>
#include <thread>

class FrameProcessor {
public:
    FrameProcessor(const std::string& camera_id);
    ~FrameProcessor();
    
    bool initialize(const nlohmann::json& config);
    void processFrame(cv::Mat& frame);
    void setEnabled(bool enabled);
    
    void updateConfiguration(const nlohmann::json& config);
    nlohmann::json getStatistics() const;
    
    void registerAlertCallback(std::function<void(const std::string&, const nlohmann::json&)> callback);
    void registerFrameCallback(std::function<void(const cv::Mat&, const nlohmann::json&)> callback);

private:
    std::string camera_id_;
    std::atomic<bool> enabled_{false};
    std::atomic<bool> initialized_{false};
    
    std::unique_ptr<ObjectTracker> object_tracker_;
    std::unique_ptr<BehaviorAnalyzer> behavior_analyzer_;
    std::unique_ptr<RegionDetector> region_detector_;
    std::map<std::string, std::shared_ptr<InferenceEngine>> ai_models_;
    
    std::queue<cv::Mat> frame_queue_;
    mutable std::mutex queue_mutex_;
    std::condition_variable queue_cv_;

    std::thread processing_thread_;
    std::atomic<bool> processing_{false};
    
    std::function<void(const std::string&, const nlohmann::json&)> alert_callback_;
    std::function<void(const cv::Mat&, const nlohmann::json&)> frame_callback_;
    
    nlohmann::json current_config_;
    mutable std::mutex config_mutex_;
    
    uint64_t frames_processed_{0};
    uint64_t objects_detected_{0};
    uint64_t alerts_triggered_{0};
    double average_processing_time_{0.0};
    
    void processingLoop();
    void applyFrameProcessing(cv::Mat& frame);
    void runInference(cv::Mat& frame, std::vector<Detection>& detections);
    void analyzeRegions(const cv::Mat& frame, const std::vector<Detection>& detections);
    void handleAlerts(const std::vector<BehaviorEvent>& events);
    
    void drawResults(cv::Mat& frame, const std::vector<Detection>& detections, 
                   const std::vector<BehaviorEvent>& events);
    
    void updateStatistics(double processing_time);
    void cleanupResources();
};
