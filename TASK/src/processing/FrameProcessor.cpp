#include "FrameProcessor.h"
#include <chrono>
#include <thread>

FrameProcessor::FrameProcessor(const std::string& camera_id)
    : camera_id_(camera_id), enabled_(false), initialized_(false),
      frames_processed_(0), objects_detected_(0), alerts_triggered_(0),
      average_processing_time_(0.0) {}

FrameProcessor::~FrameProcessor() {
    stop();
}

bool FrameProcessor::initialize(const nlohmann::json& config) {
    if (initialized_) {
        return true;
    }
    
    try {
        std::lock_guard<std::mutex> lock(config_mutex_);
        current_config_ = config;
        
        // Initialize AI models
        if (config.contains("ai_models")) {
            for (const auto& model_config : config["ai_models"]) {
                std::string model_id = model_config["model_id"];
                std::string config_path = model_config["config_path"];
                
                // Load model configuration
                auto& config_manager = ConfigurationManager::getInstance();
                auto model_config_data = config_manager.getModelConfig(model_id);
                
                if (!model_config_data.empty()) {
                    auto inference_engine = std::make_shared<InferenceEngine>(
                        model_config_data["local_path"],
                        model_config_data["class_names"],
                        model_config_data.value("confidence_threshold", 0.5f)
                    );
                    
                    if (inference_engine->isModelLoaded()) {
                        ai_models_[model_id] = inference_engine;
                    }
                }
            }
        }
        
        // Initialize object tracker
        if (config.contains("tracking")) {
            auto tracking_config = config["tracking"];
            object_tracker_ = std::make_unique<ObjectTracker>(
                tracking_config.value("tracker_type", "CSRT"),
                tracking_config.value("max_cosine_distance", 0.2f),
                tracking_config.value("max_age", 30),
                tracking_config.value("min_hits", 3)
            );
        }
        
        // Initialize behavior analyzer
        if (config.contains("behavior_analysis")) {
            behavior_analyzer_ = std::make_unique<BehaviorAnalyzer>(config);
        }
        
        // Initialize region detector
        if (config.contains("regions")) {
            region_detector_ = std::make_unique<RegionDetector>();
            for (const auto& region_config : config["regions"]) {
                std::string region_id = region_config["region_id"];
                std::string config_path = region_config["config_path"];
                
                auto& config_manager = ConfigurationManager::getInstance();
                auto zone_config = config_manager.getZoneConfig(region_id);
                
                if (!zone_config.empty()) {
                    region_detector_->addZone(zone_config);
                }
            }
        }
        
        initialized_ = true;
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error initializing frame processor for camera " 
                  << camera_id_ << ": " << e.what() << std::endl;
        return false;
    }
}

void FrameProcessor::processFrame(cv::Mat& frame) {
    if (!enabled_ || !initialized_) {
        return;
    }
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    try {
        // Apply basic frame processing
        applyFrameProcessing(frame);
        
        // Run AI inference
        std::vector<Detection> detections;
        runInference(frame, detections);
        
        // Update object tracker
        if (object_tracker_ && !detections.empty()) {
            std::vector<cv::Rect> boxes;
            std::vector<std::string> labels;
            std::vector<float> confidences;
            
            for (const auto& detection : detections) {
                boxes.push_back(detection.bbox);
                labels.push_back(detection.label);
                confidences.push_back(detection.confidence);
            }
            
            object_tracker_->update(boxes, labels, confidences, frame);
        }
        
        // Analyze regions and behavior
        if (region_detector_ && behavior_analyzer_) {
            analyzeRegions(frame, detections);
            
            // Get tracked objects for behavior analysis
            auto tracked_objects = object_tracker_->getTrackedObjects();
            behavior_analyzer_->analyzeFrame(frame, tracked_objects);
            
            // Handle any generated alerts
            auto events = behavior_analyzer_->getEvents();
            handleAlerts(events);
        }
        
        // Draw results on frame
        drawResults(frame, detections, behavior_analyzer_->getEvents());
        
        // Update statistics
        auto end_time = std::chrono::high_resolution_clock::now();
        double processing_time = std::chrono::duration<double, std::milli>(
            end_time - start_time).count();
        
        updateStatistics(processing_time);
        
    } catch (const std::exception& e) {
        std::cerr << "Error processing frame for camera " 
                  << camera_id_ << ": " << e.what() << std::endl;
    }
}

void FrameProcessor::runInference(cv::Mat& frame, std::vector<Detection>& detections) {
    for (auto& [model_id, model] : ai_models_) {
        auto model_detections = model->processFrame(frame);
        detections.insert(detections.end(), 
                         model_detections.begin(), model_detections.end());
    }
    objects_detected_ += detections.size();
}

void FrameProcessor::analyzeRegions(const cv::Mat& frame, 
                                  const std::vector<Detection>& detections) {
    region_detector_->updateTracking(detections, frame.size());
    
    // Check for region violations
    auto region_counts = region_detector_->getRegionCounts();
    for (const auto& [region_id, count] : region_counts) {
        if (count > 0) {
            nlohmann::json alert_data = {
                {"camera_id", camera_id_},
                {"region_id", region_id},
                {"object_count", count},
                {"timestamp", TimeUtils::getCurrentMillis()}
            };
            
            if (alert_callback_) {
                alert_callback_("region_violation", alert_data);
            }
        }
    }
}