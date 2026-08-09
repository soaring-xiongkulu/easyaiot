#ifndef YOLOV11_CUSTOM_H
#define YOLOV11_CUSTOM_H

#include <Datatype.h>
#include <memory>
#include <string>
#include <opencv2/opencv.hpp>
#include "Datatype.h"
#include <onnxruntime_cxx_api.h>

class Yolov11Engine
{
public:
    Yolov11Engine();
    ~Yolov11Engine();

    /**
     * Load ONNX model.
     * Default: try CUDA EP first, fall back to CPU on failure.
     */
    int LoadModel(std::string model_path,
                  std::vector<std::string> model_class,
                  bool prefer_gpu = true,
                  bool force_cpu = false,
                  int gpu_device_id = 0);

    int Run(cv::Mat& image, std::vector<DetectObject>& objects);

    /** "cuda" | "cpu" | "none" */
    const std::string& inferEp() const { return inferEp_; }

    /** CAP-INFER-THRESHOLD: align with Python detect_conf / ultralytics conf= (default 0.5). */
    void setScoreThreshold(float threshold);
    float scoreThreshold() const { return scoreThreshold_; }

private:
    int Inference(const cv::Mat& image, std::vector<DetectObject> &objects);
    int createSession(const std::string& model_path, bool use_cuda, int gpu_device_id);

    bool ready_;
    float scoreThreshold_{0.5f};
    std::string inferEp_{"none"};
    Ort::Env onnxEnv{ nullptr };
    Ort::SessionOptions onnxSessionOptions{ nullptr };
    Ort::Session onnxSession{ nullptr };
};

#endif
