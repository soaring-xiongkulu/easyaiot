//
// Created by basiclab on 25-10-15.
//

#ifndef CONFIG_H
#define CONFIG_H

#include <string>
#include <vector>
#include <map>
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
    
    // RTMP推流配置
    int videoWidth;
    int videoHeight;
    int rtmpFps;
    
    // 告警配置
    float alarmConfidenceThreshold;
    int alarmCooldownTime;
    
    // 任务配置
    std::string taskId;        // 任务ID
    int controlPort;           // HTTP控制端口（8000+taskId）
} Config;

#endif //CONFIG_H
