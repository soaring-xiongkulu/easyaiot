#include "ObjectTracker.h"
#include <algorithm>
#include <numeric>

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
            track.tracker->update(frame, track.object.bbox);
            track.object.update(detections[i], confidences[i]);
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

void ObjectTracker::createNewTrack(const cv::Rect& detection, const std::string& label, 
                                 float confidence, const cv::Mat& frame) {
    TrackData new_track;
    new_track.object = TrackedObject(next_id_++, detection, label, confidence);
    
    // Create tracker based on type
    new_track.tracker = createTrackerByType(tracker_type_);
    new_track.tracker->init(frame, detection);
    new_track.is_active = true;
    new_track.hit_streak = 1;
    
    tracks_.push_back(new_track);
    total_objects_++;
}

cv::Ptr<cv::Tracker> ObjectTracker::createTrackerByType(const std::string& type) const {
    if (type == "CSRT") {
        return cv::TrackerCSRT::create();
    } else if (type == "KCF") {
        return cv::TrackerKCF::create();
    } else if (type == "MOSSE") {
        return cv::TrackerMOSSE::create();
    } else {
        return cv::TrackerCSRT::create(); // Default
    }
}