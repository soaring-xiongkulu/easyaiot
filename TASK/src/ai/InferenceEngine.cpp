#include "InferenceEngine.h"
#include <fstream>
#include <sstream>

InferenceEngine::InferenceEngine(const std::string& model_path, 
                               const std::vector<std::string>& class_names,
                               float confidence_threshold)
    : class_names(class_names), confidence_threshold(confidence_threshold) {
    loadModel(model_path);
}

bool InferenceEngine::loadModel(const std::string& model_path) {
    try {
        // Check if model file exists
        if (!std::filesystem::exists(model_path)) {
            std::cerr << "Model file not found: " << model_path << std::endl;
            return false;
        }
        
        // Choose loading method based on file extension
        std::string extension = std::filesystem::path(model_path).extension().string();
        
        if (extension == ".onnx") {
            net = cv::dnn::readNetFromONNX(model_path);
        } else if (extension == ".pb") {
            net = cv::dnn::readNetFromTensorflow(model_path);
        } else if (extension == ".pt" || extension == ".pth") {
            // Requires OpenCV DNN module with PyTorch support
            net = cv::dnn::readNetFromTorch(model_path);
        } else {
            std::cerr << "Unsupported model format: " << extension << std::endl;
            return false;
        }
        
        if (net.empty()) {
            std::cerr << "Failed to load model: " << model_path << std::endl;
            return false;
        }
        
        // Set computation backend and target
        net.setPreferableBackend(cv::dnn::DNN_BACKEND_CUDA);
        net.setPreferableTarget(cv::dnn::DNN_TARGET_CUDA);
        
        // Get input layer information
        input_names = net.getUnconnectedOutLayersNames();
        if (!input_names.empty()) {
            input_size = net.getInputMatSize(input_names[0]);
        }
        
        std::cout << "Model loaded successfully: " << model_path << std::endl;
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error loading model: " << e.what() << std::endl;
        return false;
    }
}

std::vector<Detection> InferenceEngine::processFrame(const cv::Mat& frame) {
    std::vector<Detection> detections;
    
    if (net.empty()) {
        std::cerr << "Model not loaded" << std::endl;
        return detections;
    }
    
    try {
        // Preprocess image
        cv::Mat blob;
        cv::dnn::blobFromImage(frame, blob, 1.0/255.0, 
                             cv::Size(input_size.width, input_size.height),
                             cv::Scalar(), true, false);
        
        // Set network input
        net.setInput(blob);
        
        // Forward pass
        std::vector<cv::Mat> outputs;
        net.forward(outputs, input_names);
        
        // Post-process
        detections = postProcess(outputs, frame.size());
        
        return detections;
    } catch (const std::exception& e) {
        std::cerr << "Error processing frame: " << e.what() << std::endl;
        return detections;
    }
}

std::vector<Detection> InferenceEngine::postProcess(const std::vector<cv::Mat>& outputs, 
                                                   const cv::Size& frame_size) {
    std::vector<Detection> detections;
    
    for (const auto& output : outputs) {
        // Parse based on different model output formats
        if (output.dims == 2) { // YOLO format
            parseYOLOOutput(output, frame_size, detections);
        } else if (output.dims == 3) { // SSD format
            parseSSDOutput(output, frame_size, detections);
        }
    }
    
    // Apply non-maximum suppression
    applyNMS(detections);
    
    return detections;
}

void InferenceEngine::parseYOLOOutput(const cv::Mat& output, const cv::Size& frame_size,
                                     std::vector<Detection>& detections) {
    const int rows = output.rows;
    const int dimensions = output.cols;
    
    for (int i = 0; i < rows; ++i) {
        const float* data = output.ptr<float>(i);
        
        // Get class confidence
        cv::Mat scores(1, dimensions - 4, CV_32FC1, const_cast<float*>(data + 4));
        cv::Point class_id_point;
        double confidence;
        cv::minMaxLoc(scores, nullptr, &confidence, nullptr, &class_id_point);
        
        if (confidence > confidence_threshold) {
            int center_x = static_cast<int>(data[0] * frame_size.width);
            int center_y = static_cast<int>(data[1] * frame_size.height);
            int width = static_cast<int>(data[2] * frame_size.width);
            int height = static_cast<int>(data[3] * frame_size.height);
            
            int left = center_x - width / 2;
            int top = center_y - height / 2;
            
            Detection det;
            det.class_id = class_id_point.x;
            det.confidence = static_cast<float>(confidence);
            det.bbox = cv::Rect(left, top, width, height);
            det.label = class_names[det.class_id];
            
            detections.push_back(det);
        }
    }
}

void InferenceEngine::applyNMS(std::vector<Detection>& detections) {
    std::vector<int> indices;
    std::vector<float> confidences;
    std::vector<cv::Rect> boxes;
    
    for (const auto& det : detections) {
        confidences.push_back(det.confidence);
        boxes.push_back(det.bbox);
    }
    
    cv::dnn::NMSBoxes(boxes, confidences, confidence_threshold, 0.4f, indices);
    
    std::vector<Detection> filtered_detections;
    for (int idx : indices) {
        filtered_detections.push_back(detections[idx]);
    }
    
    detections = filtered_detections;
}