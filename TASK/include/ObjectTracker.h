#pragma once
#include <opencv2/opencv.hpp>
#include <opencv2/tracking.hpp>
#include <vector>
#include <string>
#include <map>
#include <chrono>
#include <mutex>

struct TrackedObject {
    int id;
    cv::Rect bbox;
    std::string label;
    float confidence;

    int age;
    int total_visible_count;
    int consecutive_invisible_count;
    bool is_confirmed;
    cv::Scalar color;

    std::chrono::steady_clock::time_point first_detected_time;
    std::chrono::steady_clock::time_point last_update_time;
    std::vector<cv::Point2f> trajectory;

    std::map<std::string, int> zone_entries;
    std::map<std::string, int> zone_exits;
    std::map<std::string, float> zone_dwell_times;

    TrackedObject(int obj_id, const cv::Rect& box, const std::string& obj_label, float conf);

    void update(const cv::Rect& new_bbox, float new_confidence);
    void markInvisible();
    bool shouldRemove(int max_age) const;
    int getDwellTime(const std::string& zone_id) const;
};

struct TrackData {
    TrackedObject object;
    cv::Ptr<cv::Tracker> tracker;
    bool is_active;
    int hit_streak;
};

class ObjectTracker {
public:
    ObjectTracker(const std::string& tracker_type = "CSRT",
                 float max_cosine_distance = 0.2f,
                 int max_age = 30,
                 int min_hits = 3);

    void update(const std::vector<cv::Rect>& detections,
               const std::vector<std::string>& labels,
               const std::vector<float>& confidences,
               const cv::Mat& frame);

    std::vector<TrackedObject> getTrackedObjects() const;
    int getCurrentObjectCount() const { return current_objects_; }
    int getTotalObjectCount() const { return total_objects_; }

    void reset();

private:
    std::vector<TrackData> tracks_;
    std::string tracker_type_;
    float max_cosine_distance_;
    int max_age_;
    int min_hits_;
    int next_id_;
    int current_objects_{0};
    int total_objects_{0};
    mutable std::mutex tracker_mutex_;

    int findBestMatch(const cv::Rect& detection,
                     std::vector<bool>& matched_tracks,
                     const std::vector<cv::Rect>& detections);
    void createNewTrack(const cv::Rect& detection, const std::string& label,
                       float confidence, const cv::Mat& frame);
    cv::Ptr<cv::Tracker> createTrackerByType(const std::string& type) const;
};