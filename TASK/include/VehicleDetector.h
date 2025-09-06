#pragma once
#include "InferenceEngine.h"
#include <opencv2/opencv.hpp>

class VehicleDetector : public InferenceEngine {
public:
    VehicleDetector(const std::string& model_path, float confidence_threshold = 0.5f);

    std::vector<Detection> detect(const cv::Mat& frame);
    std::vector<cv::Rect> getVehicleBoundingBoxes(const cv::Mat& frame);
    std::vector<cv::Rect> getVehicleBoundingBoxesByType(const cv::Mat& frame, const std::string& vehicle_type);
};