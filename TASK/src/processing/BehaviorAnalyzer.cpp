#include "BehaviorAnalyzer.h"
#include <algorithm>
#include <numeric>

BehaviorAnalyzer::BehaviorAnalyzer(const nlohmann::json& config) {
    // Parse configuration
    if (config.contains("behavior_analysis")) {
        auto behavior_config = config["behavior_analysis"];
        
        enable_loitering_detection_ = behavior_config.value("loitering_detection", false);
        enable_entrance_exit_detection_ = behavior_config.value("entrance_exit_detection", true);
        enable_crowding_detection_ = behavior_config.value("crowding_detection", false);
        enable_speeding_detection_ = behavior_config.value("speeding_detection", false);
        
        global_loitering_threshold_ = behavior_config.value("loitering_threshold", 30.0f);
        global_crowding_threshold_ = behavior_config.value("crowding_threshold", 5);
    }
}

void BehaviorAnalyzer::analyzeFrame(const cv::Mat& frame, 
                                  const std::vector<TrackedObject>& objects) {
    std::lock_guard<std::mutex> lock(analyzer_mutex_);
    
    // Convert normalized coordinates to pixel coordinates
    std::vector<ZoneConfig> pixel_zones;
    cv::Size frame_size(frame.cols, frame.rows);
    
    for (const auto& zone : zones_) {
        ZoneConfig pixel_zone = zone;
        for (auto& vertex : pixel_zone.vertices) {
            vertex.x *= frame_size.width;
            vertex.y *= frame_size.height;
        }
        pixel_zones.push_back(pixel_zone);
    }
    
    // Analyze each object
    for (const auto& object : objects) {
        checkZoneEntriesExits(object, pixel_zones);
        detectLoitering(object);
        
        // Check for speed and direction changes if we have previous data
        if (previous_objects_.find(object.id) != previous_objects_.end()) {
            detectSpeeding(object, previous_objects_[object.id]);
        }
    }
    
    // Detect crowding in zones
    if (enable_crowding_detection_) {
        detectCrowding(objects);
    }
    
    // Update previous objects
    previous_objects_.clear();
    for (const auto& object : objects) {
        previous_objects_[object.id] = object;
    }
}

void BehaviorAnalyzer::checkZoneEntriesExits(const TrackedObject& object, 
                                           const std::vector<ZoneConfig>& zones) {
    cv::Point2f center(object.bbox.x + object.bbox.width/2.0f,
                      object.bbox.y + object.bbox.height/2.0f);
    
    for (const auto& zone : zones) {
        bool currently_in_zone = isInZone(center, zone);
        
        // Check zone entry/exit history
        auto& entries = object.zone_entries;
        auto& exits = object.zone_exits;
        
        if (currently_in_zone) {
            // Object entered zone
            if (entries.find(zone.id) == entries.end() || entries[zone.id] == 0) {
                BehaviorEvent event;
                event.object_id = object.id;
                event.type = BehaviorEventType::ENTRANCE;
                event.zone_id = zone.id;
                event.message = "Object entered " + zone.name;
                event.location = center;
                event.timestamp = std::chrono::system_clock::now();
                event.confidence = object.confidence;
                
                addEvent(event);
                total_entrances_++;
            }
        } else {
            // Object exited zone
            if (entries.find(zone.id) != entries.end() && entries[zone.id] > 0 &&
                (exits.find(zone.id) == exits.end() || exits[zone.id] == 0)) {
                BehaviorEvent event;
                event.object_id = object.id;
                event.type = BehaviorEventType::EXIT;
                event.zone_id = zone.id;
                event.message = "Object exited " + zone.name;
                event.location = center;
                event.timestamp = std::chrono::system_clock::now();
                event.confidence = object.confidence;
                
                addEvent(event);
                total_exits_++;
            }
        }
    }
}

void BehaviorAnalyzer::detectLoitering(const TrackedObject& object) {
    if (!enable_loitering_detection_) return;
    
    for (const auto& [zone_id, dwell_time] : object.zone_dwell_times) {
        float threshold = global_loitering_threshold_;
        
        // Check if zone has specific threshold
        for (const auto& zone : zones_) {
            if (zone.id == zone_id && zone.enable_loitering) {
                threshold = zone.loitering_threshold;
                break;
            }
        }
        
        if (dwell_time > threshold) {
            BehaviorEvent event;
            event.object_id = object.id;
            event.type = BehaviorEventType::LOITERING;
            event.zone_id = zone_id;
            event.message = "Object loitering in zone for " + 
                           std::to_string(dwell_time) + " seconds";
            event.location = cv::Point(object.bbox.x + object.bbox.width/2,
                                      object.bbox.y + object.bbox.height/2);
            event.timestamp = std::chrono::system_clock::now();
            event.confidence = object.confidence;
            
            addEvent(event);
            loitering_events_++;
        }
    }
}

void BehaviorAnalyzer::detectCrowding(const std::vector<TrackedObject>& objects) {
    std::map<std::string, int> zone_counts;
    
    // Count objects in each zone
    for (const auto& object : objects) {
        for (const auto& zone : zones_) {
            cv::Point2f center(object.bbox.x + object.bbox.width/2.0f,
                             object.bbox.y + object.bbox.height/2.0f);
            
            if (isInZone(center, zone)) {
                zone_counts[zone.id]++;
            }
        }
    }
    
    // Check for crowding
    for (const auto& [zone_id, count] : zone_counts) {
        int threshold = global_crowding_threshold_;
        
        for (const auto& zone : zones_) {
            if (zone.id == zone_id && zone.enable_crowding) {
                threshold = zone.crowding_threshold;
                break;
            }
        }
        
        if (count > threshold) {
            BehaviorEvent event;
            event.type = BehaviorEventType::CROWDING;
            event.zone_id = zone_id;
            event.message = "Crowding detected in zone: " + 
                           std::to_string(count) + " objects";
            event.timestamp = std::chrono::system_clock::now();
            event.confidence = 0.8f; // High confidence for crowding
            
            addEvent(event);
            crowding_events_++;
        }
    }
}