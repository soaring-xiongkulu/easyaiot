#include "ObjectTracker.h"
#include <algorithm>
#include <numeric>
#include <iostream>

TrackedObject::TrackedObject(int obj_id, const cv::Rect& box,
                           const std::string& obj_label, float conf)
    : id(obj_id), bbox(box), label(obj_label), confidence(conf),
      age(0), total_visible_count(1), consecutive_invisible_count(0),
      is_confirmed(false), color(cv::Scalar::all(-1)) {
    first_detected_time = std::chrono::steady_clock::now();
    last_update_time = first_detected_time;
    trajectory.push_back(cv::Point2f(box.x + box.width/2.0f,
                                   box.y + box.height/2.0f));
}

void TrackedObject::update(const cv::Rect& new_bbox, float new_confidence) {
    bbox = new_bbox;
    confidence = new_confidence;
    trajectory.push_back(cv::Point2f(new_bbox.x + new_bbox.width/2.0f,
                                    new_bbox.y + new_bbox.height/2.0f));
    total_visible_count++;
    consecutive_invisible_count = 0;
    last_update_time = std::chrono::steady_clock::now();
    age++;
}

void TrackedObject::markInvisible() {
    consecutive_invisible_count++;
    age++;
}

bool TrackedObject::shouldRemove(int max_age) const {
    return consecutive_invisible_count >= max_age;
}

int TrackedObject::getDwellTime(const std::string& zone_id) const {
    auto it = zone_dwell_times.find(zone_id);
    if (it != zone_dwell_times.end()) {
        return it->second;
    }
    return 0;
}

ObjectTracker::ObjectTracker(const std::string& tracker_type,
                           float max_cosine_distance,
                           int max_age,
                           int min_hits)
    : tracker_type_(tracker_type),
      max_cosine_distance_(max_cosine_distance),
      max_age_(max_age),
      min_hits_(min_hits),
      next_id_(1) {}

void ObjectTracker::update(const std::vector<cv::Rect>& detections,
                          const std::vector<std::string>& labels,
                          const std::vector<float>& confidences,
                          const cv::Mat& frame) {
    std::lock_guard<std::mutex> lock(tracker_mutex_);

    // Mark all tracks as unmatched initially
    std::vector<bool> matched_tracks(tracks_.size(), false);
    std::vector<bool> matched_detections(detections.size(), false);

    // First, try to match existing tracks with detections
    for (size_t i = 0; i < detections.size(); ++i) {
        int best_track_idx = findBestMatch(detections[i], matched_tracks, detections);
        if (best_track_idx >= 0) {
            // Update existing track
            auto& track = tracks_[best_track_idx];
            bool updated = track.tracker->update(frame, track.object.bbox);
            if (updated) {
                track.object.update(track.object.bbox, confidences[i]);
            } else {
                track.object.update(detections[i], confidences[i]);
            }
            track.object.label = labels[i];
            track.hit_streak++;
            matched_tracks[best_track_idx] = true;
            matched_detections[i] = true;
        }
    }

    // Create new tracks for unmatched detections
    for (size_t i = 0; i < detections.size(); ++i) {
        if (!matched_detections[i]) {
            createNewTrack(detections[i], labels[i], confidences[i], frame);
        }
    }

    // Update or remove unmatched tracks
    for (size_t i = 0; i < tracks_.size(); ) {
        if (!matched_tracks[i]) {
            tracks_[i].object.markInvisible();
            tracks_[i].hit_streak = std::max(0, tracks_[i].hit_streak - 1);

            if (tracks_[i].object.shouldRemove(max_age_)) {
                tracks_.erase(tracks_.begin() + i);
                matched_tracks.erase(matched_tracks.begin() + i);
                continue;
            }
        }
        i++;
    }

    // Confirm tracks that have enough hits
    for (auto& track : tracks_) {
        if (track.hit_streak >= min_hits_ && !track.object.is_confirmed) {
            track.object.is_confirmed = true;
            // Assign a random color for visualization
            track.object.color = cv::Scalar(rand() % 256, rand() % 256, rand() % 256);
        }
    }

    current_objects_ = std::count_if(tracks_.begin(), tracks_.end(),
                                   [](const TrackData& track) { return track.object.is_confirmed; });
}

int ObjectTracker::findBestMatch(const cv::Rect& detection,
                               std::vector<bool>& matched_tracks,
                               const std::vector<cv::Rect>& all_detections) {
    double best_iou = 0.3; // IoU阈值
    int best_index = -1;

    for (size_t i = 0; i < tracks_.size(); ++i) {
        if (matched_tracks[i]) continue;

        double iou = calculateIoU(tracks_[i].object.bbox, detection);
        if (iou > best_iou) {
            best_iou = iou;
            best_index = i;
        }
    }
    return best_index;
}

double ObjectTracker::calculateIoU(const cv::Rect& rect1, const cv::Rect& rect2) {
    cv::Rect intersection = rect1 & rect2;
    double interArea = intersection.area();
    double unionArea = rect1.area() + rect2.area() - interArea;
    if (unionArea <= 0) return 0;
    return interArea / unionArea;
}

void ObjectTracker::createNewTrack(const cv::Rect& detection, const std::string& label,
                                 float confidence, const cv::Mat& frame) {
    // 使用构造函数直接初始化TrackData
    TrackedObject obj(next_id_++, detection, label, confidence);
    cv::Ptr<cv::Tracker> tracker = createTrackerByType(tracker_type_);

    TrackData new_track(std::move(obj), tracker, true, 1);
    new_track.tracker->init(frame, detection);
    tracks_.push_back(std::move(new_track));
    total_objects_++;
}

cv::Ptr<cv::Tracker> ObjectTracker::createTrackerByType(const std::string& type) const {
    if (type == "CSRT") {
        return cv::TrackerCSRT::create();
    } else if (type == "KCF") {
        return cv::TrackerKCF::create();
    } else {
        std::cerr << "警告: TrackerMOSSE 在 OpenCV 4.x 中已移除，使用 CSRT 替代" << std::endl;
        return cv::TrackerCSRT::create();
    }
}

std::vector<TrackedObject> ObjectTracker::getTrackedObjects() const {
    std::lock_guard<std::mutex> lock(tracker_mutex_);
    std::vector<TrackedObject> objects;
    for (const auto& track : tracks_) {
        if (track.object.is_confirmed) {
            objects.push_back(track.object);
        }
    }
    return objects;
}

void ObjectTracker::reset() {
    std::lock_guard<std::mutex> lock(tracker_mutex_);
    tracks_.clear();
    next_id_ = 1;
    current_objects_ = 0;
    total_objects_ = 0;
}