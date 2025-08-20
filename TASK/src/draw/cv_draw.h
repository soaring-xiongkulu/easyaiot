

#ifndef RK3588_DEMO_CV_DRAW_H
#define RK3588_DEMO_CV_DRAW_H

#include <opencv2/opencv.hpp>

#include "types/datatype.h"

// draw detections on img
void DrawDetections(cv::Mat& img, const std::vector<Detection>& objects);

#endif //RK3588_DEMO_CV_DRAW_H
