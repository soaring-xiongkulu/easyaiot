#include "PersonDetector.h"

PersonDetector::PersonDetector(const std::string& model_path,
                             float confidence_threshold)
    : InferenceEngine(model_path, {"person"}, confidence_threshold) {}

std::vector<Detection> PersonDetector::detect(const cv::Mat& frame) {
    return processFrame(frame);
}

bool PersonDetector::isPerson(const Detection& detection) const {
    return detection.class_id == 0; // Assuming person is class 0
}

std::vector<cv::Rect> PersonDetector::getPersonBoundingBoxes(const cv::Mat& frame) {
    auto detections = detect(frame);
    std::vector<cv::Rect> boxes;

    for (const auto& detection : detections) {
        if (isPerson(detection)) {
            boxes.push_back(detection.bbox);
        }
    }

    return boxes;
}