#ifndef RK3588_DEMO_YOLOV8_CUSTOM_H
#define RK3588_DEMO_YOLOV8_CUSTOM_H

#include "engine/engine.h"

#include <memory>

#include <opencv2/opencv.hpp>
#include "process/preprocess.h"
#include "types/datatype.h"

class Yolov11Engine
{
public:
    Yolov11Engine();
    ~Yolov11Engine();

    int LoadModel(const char *model_path);

    int Run(const cv::Mat &img, std::vector<Detection> &objects);

private:
    int Preprocess(const cv::Mat &img, const std::string process_type, cv::Mat &image_letterbox);
    int Inference();
    int Postprocess(const cv::Mat &img, std::vector<Detection> &objects);

    bool ready_;
    LetterBoxInfo letterbox_info_;
    tensor_data_s input_tensor_;
    std::vector<tensor_data_s> output_tensors_;
    bool want_float_;
    std::vector<int32_t> out_zps_;
    std::vector<float> out_scales_;
    std::shared_ptr<NNEngine> engine_;
};

#endif // RK3588_DEMO_YOLOV8_CUSTOM_H
