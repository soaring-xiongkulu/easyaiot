
#ifndef PREPROCESS_H
#define PREPROCESS_H

#include <opencv2/opencv.hpp>
#include "types/datatype.h"

struct LetterBoxInfo
{
    bool hor;
    int pad;
};

class CPreprocess {
public:
    explicit CPreprocess();
    ~CPreprocess();

public:
    LetterBoxInfo letterbox(const cv::Mat &img, cv::Mat &img_letterbox, float wh_ratio);
    void cvimg2tensor(const cv::Mat &img, int width, int height, tensor_data_s &tensor);

private:
    std::mutex _runMtx;
};


#endif // RK3588_DEMO_PREPROCESS_H
