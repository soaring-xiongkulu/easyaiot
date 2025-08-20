// 预处理

#ifndef RK3588_DEMO_PREPROCESS_H
#define RK3588_DEMO_PREPROCESS_H

#include <opencv2/opencv.hpp>
#include "types/datatype.h"

struct LetterBoxInfo
{
    bool hor;
    int pad;
};

LetterBoxInfo letterbox(const cv::Mat &img, cv::Mat &img_letterbox, float wh_ratio);
void cvimg2tensor(const cv::Mat &img, uint32_t width, uint32_t height, tensor_data_s &tensor);

#endif // RK3588_DEMO_PREPROCESS_H
