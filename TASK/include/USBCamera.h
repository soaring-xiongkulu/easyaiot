#pragma once
#include "CameraStreamer.h"
#include <opencv2/opencv.hpp>
#include <string>
#include <mutex>

class USBCamera : public CameraStreamer {
public:
    USBCamera(const std::string& camera_id, int device_index);
    ~USBCamera() override = default;

    bool initialize() override;
    bool getFrame(cv::Mat& frame) override;
    void start() override;
    void stop() override;
    bool isRunning() const override;
    std::string getStreamInfo() const override;

private:
    int device_index_;
    cv::VideoCapture video_cap_;
    mutable std::mutex cap_mutex_;
};