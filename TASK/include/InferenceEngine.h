#pragma once
#include <opencv2/opencv.hpp>
#include <opencv2/dnn.hpp>
#include <vector>
#include <string>

struct Detection {
    int class_id;
    float confidence;
    cv::Rect bbox;
    std::string label;
};

class InferenceEngine {
public:
    InferenceEngine(const std::string& model_path,
                   const std::vector<std::string>& class_names,
                   float confidence_threshold = 0.5f);

    bool loadModel(const std::string& model_path);
    std::vector<Detection> processFrame(const cv::Mat& frame);

    void setConfidenceThreshold(float threshold);
    float getConfidenceThreshold() const;

    std::vector<std::string> getClassNames() const;
    bool isModelLoaded() const;

private:
    cv::dnn::Net net;
    std::vector<std::string> class_names;
    float confidence_threshold;

    std::vector<std::string> input_names;
    cv::Size input_size;

    std::vector<Detection> postProcess(const std::vector<cv::Mat>& outputs, const cv::Size& frame_size);
    void parseYOLOOutput(const cv::Mat& output, const cv::Size& frame_size, std::vector<Detection>& detections);
    void parseSSDOutput(const cv::Mat& output, const cv::Size& frame_size, std::vector<Detection>& detections);
    void applyNMS(std::vector<Detection>& detections);
};