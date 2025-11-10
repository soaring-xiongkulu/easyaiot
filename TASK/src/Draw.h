
// @author 翱翔的雄库鲁
// @email andywebjava@163.com
// @wechat EasyAIoT2025

#ifndef RK3588_DEMO_CV_DRAW_H
#define RK3588_DEMO_CV_DRAW_H

#include <opencv2/opencv.hpp>

#include "Datatype.h"

// draw detections on img
void DrawDetections(cv::Mat& img, const std::vector<DetectObject>& objects);

#endif //RK3588_DEMO_CV_DRAW_H
