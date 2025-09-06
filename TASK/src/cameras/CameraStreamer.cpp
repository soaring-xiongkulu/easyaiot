#include "CameraStreamer.h"
#include <iostream>

CameraStreamer::CameraStreamer(const std::string& camera_id)
    : camera_id_(camera_id), running_(false), connected_(false),
      frame_width_(0), frame_height_(0), fps_(0) {}

CameraStreamer::~CameraStreamer() {
    stop();
}

bool CameraStreamer::isRunning() const {
    return running_ && connected_;
}

std::string CameraStreamer::getCameraId() const {
    return camera_id_;
}

int CameraStreamer::getFrameWidth() const {
    return frame_width_;
}

int CameraStreamer::getFrameHeight() const {
    return frame_height_;
}

double CameraStreamer::getFPS() const {
    return fps_;
}