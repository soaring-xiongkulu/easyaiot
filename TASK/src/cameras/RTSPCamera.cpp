#include "RTSPCamera.h"
#include <iostream>
#include <chrono>
#include <thread>

// 定义静态常量（如果链接时需要）
const int RTSPCamera::MAX_RECONNECT_ATTEMPTS;
const int RTSPCamera::RECONNECT_DELAY;

RTSPCamera::RTSPCamera(const std::string& camera_id, const std::string& rtsp_url)
    : CameraStreamer(camera_id),
      rtsp_url(rtsp_url),
      reconnect_attempts(0),
      frame_width(0),
      frame_height(0),
      fps(0) {}

bool RTSPCamera::initialize() {
    return connect();
}

bool RTSPCamera::connect() {
    try {
        std::lock_guard<std::mutex> lock(cap_mutex);

        // 设置RTSP传输协议为TCP
        cv::VideoCapture cap(rtsp_url, cv::CAP_FFMPEG);
        if (!cap.isOpened()) {
            std::cerr << "Failed to open RTSP stream: " << rtsp_url << std::endl;
            return false;
        }

        video_cap = std::move(cap);
        connected = true;
        reconnect_attempts = 0;

        // 获取视频参数
        frame_width = video_cap.get(cv::CAP_PROP_FRAME_WIDTH);
        frame_height = video_cap.get(cv::CAP_PROP_FRAME_HEIGHT);
        fps = video_cap.get(cv::CAP_PROP_FPS);

        std::cout << "Connected to camera " << getCameraId() // 假设基类有getCameraId()方法
                  << " (" << frame_width << "x" << frame_height
                  << " @ " << fps << "fps)" << std::endl;

        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error connecting to camera " << getCameraId()
                  << ": " << e.what() << std::endl;
        return false;
    }
}

bool RTSPCamera::getFrame(cv::Mat& frame) {
    if (!connected && !reconnect()) {
        return false;
    }

    try {
        std::lock_guard<std::mutex> lock(cap_mutex);
        if (video_cap.read(frame)) {
            if (frame.empty()) {
                std::cerr << "Received empty frame from camera " << getCameraId() << std::endl;
                return false;
            }
            last_frame_time = std::chrono::steady_clock::now();
            return true;
        } else {
            std::cerr << "Failed to read frame from camera " << getCameraId() << std::endl;
            connected = false;
            return reconnect();
        }
    } catch (const std::exception& e) {
        std::cerr << "Error reading frame from camera " << getCameraId()
                  << ": " << e.what() << std::endl;
        connected = false;
        return false;
    }
}

bool RTSPCamera::reconnect() {
    if (reconnect_attempts >= MAX_RECONNECT_ATTEMPTS) {
        std::cerr << "Max reconnect attempts reached for camera " << getCameraId() << std::endl;
        return false;
    }

    std::this_thread::sleep_for(std::chrono::seconds(RECONNECT_DELAY));
    reconnect_attempts++;

    std::cout << "Attempting to reconnect to camera " << getCameraId()
              << " (attempt " << reconnect_attempts << ")" << std::endl;

    return connect();
}

void RTSPCamera::start() {
    running = true;
    // RTSP摄像头不需要单独的采集线程，帧在getFrame中按需获取
}

void RTSPCamera::stop() {
    running = false;
    std::lock_guard<std::mutex> lock(cap_mutex);
    if (video_cap.isOpened()) {
        video_cap.release();
    }
    connected = false;
}

bool RTSPCamera::isRunning() const {
    return running && connected;
}

std::string RTSPCamera::getStreamInfo() const {
    return "RTSP Stream: " + rtsp_url;
}