#include "FrameProcessor.h"
#include <chrono>
#include <thread>
#include <iostream>
#include <algorithm>
#include <nlohmann/json.hpp>
#include <vector>
#include <string>
#include "ConfigurationManager.h"
#include "TimeUtils.h"

// 自定义类型序列化支持
void to_json(nlohmann::json& j, const Detection& detection) {
    j = nlohmann::json{
        {"label", detection.label},
        {"confidence", detection.confidence},
        {"bbox_x", detection.bbox.x},
        {"bbox_y", detection.bbox.y},
        {"bbox_width", detection.bbox.width},
        {"bbox_height", detection.bbox.height}
    };
}

void to_json(nlohmann& j, const BehaviorEvent& event) {
    j = nlohmann::json{
        {"type", event.type},
        {"timestamp", event.timestamp},
        {"object_id", event.object_id},
        {"confidence", event.confidence}
    };
}

FrameProcessor::FrameProcessor(const std::string& camera_id)
    : camera_id_(camera_id), enabled_(false), initialized_(false),
      frames_processed_(0), objects_detected_(0), alerts_triggered_(0),
      average_processing_time_(0.0), processing_(false) {}

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
            for (const auto& model_config : config[""]) {
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
                        ai_models_[model] = inference_engine;
                    }
                }
            }
        }

        // Initialize object tracker
        if (config.contains("tracking")) {
            auto tracking_config = config["tracking"];
            object_tracker_ = std::make_unique<ObjectTracker>(
                tracking_config.value("tracker_type", "CSRT"),
                tracking_config("max_cosine_distance", 0.),
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
        (object_tracker_ && !detections.empty()) {
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
            auto tracked_objects = object_tracker_->getTrackObjects();
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
                  << camera_id << ": " << e.what() << std::endl;
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

void FrameProcessor::stop() {
    if (processing_) {
        processing_ = false;
        enabled_ = false;

        // Notify processing thread (if frames are waiting to be processed)
        queue_cv_.notify_all();

        // Wait for processing thread to finish
        if (processing_thread_.joinable()) {
            processing_thread_.join();
        }
    }

    cleanupResources();
}

void FrameProcessor::cleanupResources() {
    // Clean up AI models
    ai_models_.clear();

    // Reset other resources
    object_tracker_.reset();
    behavior_analyzer_.reset();
    region_detector_.reset();

    // Clear frame queue
    std::lock_guard<std::mutex> lock(queue_mutex_);
    std::queue<cv::Mat> empty;
    std::swap(frame_queue_, empty);

    initialized_ = false;
}

void FrameProcessor::setEnabled(bool enabled) {
    if (enabled && !enabled_) {
        enabled_ = true;
        processing_ = true;
        processing_thread_ = std::thread(&FrameProcessor::processingLoop, this);
    } else if (!enabled && enabled_) {
        stop();
    }
}

void FrameProcessor::processingLoop() {
    while (processing_) {
        cv::Mat frame;
        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            queue_cv_.wait_for(lock, std::chrono::milliseconds(100),
                [this]() { return !frame_queue_.empty() || !processing_; });

            if (!processing_) break;

            if (!frame_queue_.empty()) {
                frame = frame_queue_.front();
                frame_queue_.pop();
            }
        }

        if (!frame.empty()) {
            processFrame(frame);

            if (frame_callback_) {
                nlohmann::json metadata = {
                    {"camera_id", camera_id_},
                    {"timestamp", TimeUtils::getCurrentMillis()}
                };
                frame_callback_(frame, metadata);
            }
        }
    }
}

void FrameProcessor::registerAlertCallback(
    std::function<void(const std::string&, const nlohmann::json&)> callback) {
    alert_callback_ = callback;
}

void FrameProcessor::registerFrameCallback(
    std::function<void(const cv::Mat&, const nlohmann::json&)> callback) {
    frame_callback_ = callback;
}

void FrameProcessor::updateConfiguration(const nlohmann::json& config) {
    std::lock_guard<std::mutex> lock(config_mutex_);
    current_config_ = config;

    // Reinitialize with new configuration
    initialized_ = false;
    initialize(config);
}

nlohmann::json FrameProcessor::getStatistics() const {
    nlohmann::json j;
    j["camera_id"] = camera_id_;
    j["frames_processed"] = frames_processed_;
    j["objects_detected"] = objects_detected_;
    j["alerts_triggered"] = alerts_triggered_;
    j["average_processing_time_ms"] = average_processing_time_;
    j["enabled"] = enabled_;
    j["initialized"] = initialized_;
    return j;
}

void FrameProcessor::applyFrameProcessing(c::Mat& frame) {
    // Basic frame processing operations
    // You can add operations like resize, normalize, etc.
}

void FrameProcessor::handleAlerts(const std::vector<BehaviorEvent>& events) {
    for (const auto& event : events) {
        alerts_triggered_++;

        nlohmann::json alert_data = {
            {"camera_id", camera_id_},
            {"event_type", event.type},
            {"timestamp", event.timestamp},
            {"object_id", event.object_id},
            {"confidence", event.confidence}
        };

        if (alert_callback_) {
            alert_callback_(event.type, alert_data);
        }
    }
}

void FrameProcessor::drawResults(cv::Mat& frame,
                               const std::vector<Detection>& detections,
                               const std::vector<BehaviorEvent>& events) {
    // Draw detection boxes
    for (const auto& detection : detections) {
        cv::rectangle(frame, detection.bbox, cv::Scalar(0, 255, 0), 2);
        std::string label = detection.label + " " + std::to_string(detection.confidence).substr(0, 4);
        cv::putText(frame, label, cv::Point(detection.bbox.x, detection.bbox.y - 5),
                   cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(0, 255, 0), 1);
    }

    // Draw event information
    for (const auto& event : events) {
        std::string event_text = event.type + " (ID: " + std::to_string(event.object_id) + ")";
        cv::putText(frame, event_text, cv::Point(10, 30 + 20 * (&event - &events[0])),
                   cv::FONT_HERSHEY, 0.7, cv::Scalar(0, 0, 255), 2);
    }

    // Draw FPS information
    std::string fps_text = "FPS: " + std::to_string(1000.0 / average_processing_time_).substr(0, 5);
    cv::putText(frame, fps_text, cv::Point(frame.cols - 150, 30),
               cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(255, 255, 255), 2);
}

void FrameProcessor::updateStatistics(double processing_time) {
    frames_processed_++;

    // Update average processing time using exponential moving average
    average_processing_time_ = 0.9 * average_processing_time_ + 0.1 * processing_time;
}