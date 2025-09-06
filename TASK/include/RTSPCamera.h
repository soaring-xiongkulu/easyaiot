#pragma once

#include "CameraStreamer.h" // 你的基类
#include <opencv2/opencv.hpp>
#include <string>
#include <mutex>
#include <atomic>
#include <chrono>

class RTSPCamera : public CameraStreamer {
public:
    RTSPCamera(const std::string& camera_id, const std::string& rtsp_url);
    ~RTSPCamera() override = default;

    bool initialize() override;
    bool getFrame(cv::Mat& frame) override;
    void start() override;
    void stop() override;
    bool isRunning() const override;
    std::string getStreamInfo() const override;

private:
    std::string rtsp_url;
    cv::VideoCapture video_cap;
    mutable std::mutex cap_mutex;
    std::atomic<bool> connected{false};
    std::atomic<bool> running{false};
    int reconnect_attempts;

    // 视频参数 - 如果在基类中已定义则不需要这里
    double frame_width;
    double frame_height;
    double fps;

    std::chrono::time_point<std::chrono::steady_clock> last_frame_time;

    static const int MAX_RECONNECT_ATTEMPTS = 10;
    static const int RECONNECT_DELAY = 5; // seconds

    bool connect();
    bool reconnect();
};