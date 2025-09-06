#include "VehicleDetector.h"

VehicleDetector::VehicleDetector(const std::string& model_path,
                               float confidence_threshold)
    : InferenceEngine(model_path,
                    {"car", "motorcycle", "bus", "truck"},
                    confidence_threshold) {}

std::vector<Detection> VehicleDetector::detect(const cv::Mat& frame) {
    return processFrame(frame);
}

std::vector<cv::Rect> VehicleDetector::getVehicleBoundingBoxes(const cv::Mat& frame) {
    auto detections = detect(frame);
    std::vector<cv::Rect> boxes;

    for (const auto& detection : detections) {
        boxes.push_back(detection.bbox);
    }

    return boxes;
}

std::vector<cv::Rect> VehicleDetector::getVehicleBoundingBoxesByType(const cv::Mat& frame,
                                                                   const std::string& vehicle_type) {
    auto detections = detect(frame);
    std::vector<cv::Rect> boxes;

    for (const auto& detection : detections) {
        if (detection.label == vehicle_type) {
            boxes.push_back(detection.bbox);
        }
    }

    return boxes;
}