#pragma once
#include <opencv2/opencv.hpp>
#include <string>
#include <mutex>
#include <atomic>

class CameraStreamer {
public:
    CameraStreamer(const std::string& camera_id);
    virtual ~CameraStreamer();

    virtual bool initialize() = 0;
    virtual bool getFrame(cv::Mat& frame) = 0;
    virtual void start() = 0;
    virtual void stop() = 0;
    virtual bool isRunning() const = 0;
    virtual std::string getStreamInfo() const = 0;

    std::string getCameraId() const;
    int getFrameWidth() const;
    int getFrameHeight() const;
    double getFPS() const;

protected:
    std::string camera_id_;
    std::atomic<bool> running_{false};
    std::atomic<bool> connected_{false};
    int frame_width_{0};
    int frame_height_{0};
    double fps_{0};
};