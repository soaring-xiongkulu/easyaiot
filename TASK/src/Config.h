//
// Created by basiclab on 25-10-15.
//
// @author 翱翔的雄库鲁
// @email andywebjava@163.com
// @wechat EasyAIoT2025

#ifndef CONFIG_H
#define CONFIG_H

#include <string>
#include <vector>
#include <opencv2/opencv.hpp>

typedef struct Config {
    std::string rtspUrl;
    std::string rtmpUrl;
    std::string hookHttpUrl;
    bool enableRtmp;
    bool enableAI;
    bool enableDrawRtmp;
    bool enableAlarm;
    std::map<std::string, std::string> modelPaths;
    std::map<std::string, std::string> modelClasses;
    std::map<std::string, std::vector<std::vector<cv::Point>>> regions;
    int threadNums;
} Config;

#endif //CONFIG_H
