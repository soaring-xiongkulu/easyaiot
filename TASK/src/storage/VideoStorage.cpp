#include "VideoStorage.h"
#include <filesystem>
#include <chrono>

VideoStorage::VideoStorage(const std::string& storage_path,
                         int max_storage_days)
    : storage_path_(storage_path), max_storage_days_(max_storage_days) {
    std::filesystem::create_directories(storage_path_);
}

bool VideoStorage::saveVideo(const std::string& camera_id,
                           const std::vector<cv::Mat>& frames,
                           double fps,
                           const std::string& event_type) {
    if (frames.empty()) {
        return false;
    }

    try {
        // Create filename with timestamp
        auto now = std::chrono::system_clock::now();
        auto timestamp = std::chrono::system_clock::to_time_t(now);
        char time_str[100];
        std::strftime(time_str, sizeof(time_str), "%Y%m%d_%H%M%S", std::localtime(&timestamp));

        std::string filename = camera_id + "_" + event_type + "_" + time_str + ".avi";
        std::string full_path = storage_path_ + "/" + filename;

        // Initialize video writer
        cv::Size frame_size = frames[0].size();
        cv::VideoWriter writer(full_path,
                              cv::VideoWriter::fourcc('M', 'J', 'P', 'G'),
                              fps, frame_size);

        if (!writer.isOpened()) {
            std::cerr << "Failed to open video writer: " << full_path << std::endl;
            return false;
        }

        // Write frames
        for (const auto& frame : frames) {
            writer.write(frame);
        }

        writer.release();

        // Add to storage index
        VideoMetadata metadata;
        metadata.filename = filename;
        metadata.camera_id = camera_id;
        metadata.event_type = event_type;
        metadata.timestamp = now;
        metadata.duration = frames.size() / fps;

        std::lock_guard<std::mutex> lock(storage_mutex_);
        video_index_.push_back(metadata);

        std::cout << "Video saved: " << full_path << " (" << frames.size() << " frames)" << std::endl;
        return true;

    } catch (const std::exception& e) {
        std::cerr << "Error saving video: " << e.what() << std::endl;
        return false;
    }
}

std::vector<VideoMetadata> VideoStorage::getVideosByCamera(const std::string& camera_id) const {
    std::vector<VideoMetadata> result;
    std::lock_guard<std::mutex> lock(storage_mutex_);

    for (const auto& metadata : video_index_) {
        if (metadata.camera_id == camera_id) {
            result.push_back(metadata);
        }
    }

    return result;
}

std::vector<VideoMetadata> VideoStorage::getVideosByEvent(const std::string& event_type) const {
    std::vector<VideoMetadata> result;
    std::lock_guard<std::mutex> lock(storage_mutex_);

    for (const auto& metadata : video_index_) {
        if (metadata.event_type == event_type) {
            result.push_back(metadata);
        }
    }

    return result;
}

void VideoStorage::cleanupOldVideos() {
    auto now = std::chrono::system_clock::now();
    std::vector<VideoMetadata> to_keep;

    {
        std::lock_guard<std::mutex> lock(storage_mutex_);

        for (const auto& metadata : video_index_) {
            auto age = std::chrono::duration_cast<std::chrono::hours>(
                now - metadata.timestamp).count() / 24;

            if (age <= max_storage_days_) {
                to_keep.push_back(metadata);
            } else {
                // Delete file
                std::string file_path = storage_path_ + "/" + metadata.filename;
                if (std::filesystem::exists(file_path)) {
                    std::filesystem::remove(file_path);
                }
            }
        }

        video_index_ = to_keep;
    }

    std::cout << "Video storage cleanup completed. " << to_keep.size()
              << " videos retained." << std::endl;
}