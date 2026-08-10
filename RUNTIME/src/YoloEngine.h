#ifndef YOLO_ENGINE_H
#define YOLO_ENGINE_H

#include "Datatype.h"
#include <memory>
#include <string>
#include <vector>
#include <opencv2/opencv.hpp>
#include <onnxruntime_cxx_api.h>

/**
 * Ultralytics YOLO detect engine (ONNX Runtime).
 * Supports:
 *  - YOLOv8 / YOLO11 classic detect export: [1, 4+C, N] → NMS
 *  - YOLO26 end2end export: [1, N, 6] = [x1,y1,x2,y2,conf,cls] (no NMS)
 *  - .pt paths: auto-export to sibling .onnx via RUNTIME/scripts/ensure_onnx_model.py
 */
class YoloEngine {
public:
    YoloEngine();
    ~YoloEngine();

    int LoadModel(std::string model_path,
                  std::vector<std::string> model_class,
                  bool prefer_gpu = true,
                  bool force_cpu = false,
                  int gpu_device_id = 0);

    int Run(cv::Mat& image, std::vector<DetectObject>& objects);

    /** "cuda" | "cpu" | "none" */
    const std::string& inferEp() const { return inferEp_; }
    /** "detect" | "end2end" | "unknown" */
    const std::string& modelLayout() const { return modelLayout_; }
    const std::string& loadedOnnxPath() const { return loadedOnnxPath_; }

    void setScoreThreshold(float threshold);

private:
    int Inference(const cv::Mat& image, std::vector<DetectObject>& objects);
    int createSession(const std::string& model_path, bool use_cuda, int gpu_device_id);
    static std::string ensureOnnxPath(const std::string& model_path);
    void loadNamesFromOnnxMetadata();
    void detectLayoutFromOutputShape(const std::vector<int64_t>& dims);

    bool ready_{false};
    bool end2end_{false};
    std::string inferEp_{"none"};
    std::string modelLayout_{"unknown"};
    std::string loadedOnnxPath_;
    float scoreThreshold_{0.25f};
    float nmsThreshold_{0.45f};

    Ort::Env onnxEnv{nullptr};
    Ort::SessionOptions onnxSessionOptions{nullptr};
    Ort::Session onnxSession{nullptr};
};

#endif
