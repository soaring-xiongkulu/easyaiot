#pragma once
#include "InferenceEngine.h"
#include <opencv2/opencv.hpp>

class PersonDetector : public InferenceEngine {
public:
    PersonDetector(const std::string& model_path, float confidence_threshold = 0.5f);

    std::vector<Detection> detect(const cv::Mat& frame);
    bool isPerson(const Detection& detection) const;
    std::vector<cv::Rect> getPersonBoundingBoxes(const cv::Mat& frame);
};