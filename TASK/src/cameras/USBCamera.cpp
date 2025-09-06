#include "USBCamera.h"
#include <iostream>

USBCamera::USBCamera(const std::string& camera_id, int device_index)
    : CameraStreamer(camera_id), device_index_(device_index) {}

bool USBCamera::initialize() {
    try {
        std::lock_guard<std::mutex> lock(cap_mutex_);

        video_cap_.open(device_index_);
        if (!video_cap_.isOpened()) {
            std::cerr << "Failed to open USB camera: " << device_index_ << std::endl;
            return false;
        }

        // Set camera properties
        video_cap_.set(cv::CAP_PROP_FRAME_WIDTH, 1280);
        video_cap_.set(cv::CAP_PROP_FRAME_HEIGHT, 720);
        video_cap_.set(cv::CAP_PROP_FPS, 30);

        frame_width_ = video_cap_.get(cv::CAP_PROP_FRAME_WIDTH);
        frame_height_ = video_cap_.get(cv::CAP_PROP_FRAME_HEIGHT);
        fps_ = video_cap_.get(cv::CAP_PROP_FPS);

        connected_ = true;

        std::cout << "USB Camera initialized: " << camera_id_
                  << " (" << frame_width_ << "x" << frame_height_
                  << " @ " << fps_ << "fps)" << std::endl;

        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error initializing USB camera: " << e.what() << std::endl;
        return false;
    }
}

bool USBCamera::getFrame(cv::Mat& frame) {
    if (!connected_) {
        return false;
    }

    try {
        std::lock_guard<std::mutex> lock(cap_mutex_);
        if (video_cap_.read(frame)) {
            if (frame.empty()) {
                return false;
            }
            return true;
        }
    } catch (const std::exception& e) {
        std::cerr << "Error reading frame from USB camera: " << e.what() << std::endl;
    }

    return false;
}

void USBCamera::start() {
    running_ = true;
}

void USBCamera::stop() {
    running_ = false;
    if (video_cap_.isOpened()) {
        video_cap_.release();
    }
    connected_ = false;
}

std::string USBCamera::getStreamInfo() const {
    return "USB Camera: /dev/video" + std::to_string(device_index_);
}