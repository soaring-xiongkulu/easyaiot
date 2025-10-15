#include "preprocess.h"
#include "im2d.h"
#include "rga.h"
#include "opencv2/core/types.hpp"


CPreprocess::CPreprocess() {
};

CPreprocess::~CPreprocess() {
}

LetterBoxInfo CPreprocess::letterbox(const cv::Mat &img, cv::Mat &img_letterbox, float wh_ratio) {
    if (img.channels() != 3) {
        printf("img has to be 3 channels\n");
        exit(-1);
    }
    float img_width = img.cols;
    float img_height = img.rows;

    int letterbox_width = 0;
    int letterbox_height = 0;

    LetterBoxInfo info;
    int padding_hor = 0;
    int padding_ver = 0;

    if (img_width / img_height > wh_ratio) {
        info.hor = false;
        letterbox_width = img_width;
        letterbox_height = img_width / wh_ratio;
        info.pad = (letterbox_height - img_height) / 2.f;
        padding_hor = 0;
        padding_ver = info.pad;
    } else {
        info.hor = true;
        letterbox_width = img_height * wh_ratio;
        letterbox_height = img_height;
        info.pad = (letterbox_width - img_width) / 2.f;
        padding_hor = info.pad;
        padding_ver = 0;
    }
    // 使用cv::copyMakeBorder函数进行填充边界
    cv::copyMakeBorder(img, img_letterbox, padding_ver, padding_ver, padding_hor, padding_hor, cv::BORDER_CONSTANT,
                       cv::Scalar(0, 0, 0));
    return info;
}


void CPreprocess::cvimg2tensor(const cv::Mat &img, int width, int height, tensor_data_s &tensor) {
    std::lock_guard<std::mutex> lck(_runMtx);
    if (img.channels() != 3)
    {
        printf("img has to be 3 channels\n");
        exit(-1);
    }
    cv::Mat img_rgb;
    cv::cvtColor(img, img_rgb, cv::COLOR_BGR2RGB);
    cv::Mat img_resized;
    resize(img_rgb, img_resized, cv::Size(width, height), 0, 0, cv::INTER_LINEAR);
    memcpy(tensor.data, img_resized.data, tensor.attr.size);
}