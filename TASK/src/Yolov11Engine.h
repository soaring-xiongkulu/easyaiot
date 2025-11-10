// @author 翱翔的雄库鲁
// @email andywebjava@163.com
// @wechat EasyAIoT2025

#ifndef YOLOV11_CUSTOM_H
#define YOLOV11_CUSTOM_H

#include <Datatype.h>
#include <memory>
#include <opencv2/opencv.hpp>
#include "Datatype.h"
#include <onnxruntime_cxx_api.h>

class Yolov11Engine
{
public:
    Yolov11Engine();
    ~Yolov11Engine();

    int LoadModel(std::string model_path, std::vector<std::string> model_class);
    int Run(cv::Mat& image, std::vector<DetectObject>& objects);

private:
    int Inference(const cv::Mat& image, std::vector<DetectObject> &objects);

    bool ready_;
    Ort::Env onnxEnv{ nullptr };
    Ort::SessionOptions onnxSessionOptions{ nullptr };
    Ort::Session onnxSession{ nullptr };
};

#endif
