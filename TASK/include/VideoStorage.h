#pragma once
#include <opencv2/opencv.hpp>
#include <string>
#include <vector>
#include <map>
#include <mutex>
#include <chrono>

struct VideoMetadata {
    std::string filename;
    std::string camera_id;
    std::string event_type;
    std::chrono::system_clock::time_point timestamp;
    double duration; // in seconds
};

class VideoStorage {
public:
    VideoStorage(const std::string& storage_path, int max_storage_days = 30);

    bool saveVideo(const std::string& camera_id,
                  const std::vector<cv::Mat>& frames,
                  double fps,
                  const std::string& event_type);

    std::vector<VideoMetadata> getVideosByCamera(const std::string& camera_id) const;
    std::vector<VideoMetadata> getVideosByEvent(const std::string& event_type) const;
    void cleanupOldVideos();

private:
    std::string storage_path_;
    int max_storage_days_;
    std::vector<VideoMetadata> video_index_;
    mutable std::mutex storage_mutex_;
};