#include "BehaviorAnalyzer.h"
#include <algorithm>
#include <numeric>
#include <iostream> // 可选，用于调试输出

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
        if (enable_entrance_exit_detection_) {
            checkZoneEntriesExits(object, pixel_zones);
        }
        if (enable_loitering_detection_) {
            detectLoitering(object);
        }

        // Check for speed and direction changes if we have previous data
        if (enable_speeding_detection_ && previous_objects_.find(object.id) != previous_objects_.end()) {
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

    // 清理 object_zone_status_ 中不再存在的对象的状态
    std::set<int> current_ids;
    for (const auto& obj : objects) {
        current_ids.insert(obj.id);
    }
    for (auto it = object_zone_status_.begin(); it != object_zone_status_.end(); ) {
        if (current_ids.find(it->first) == current_ids.end()) {
            it = object_zone_status_.erase(it);
        } else {
            ++it;
        }
    }
}

void BehaviorAnalyzer::checkZoneEntriesExits(const TrackedObject& object,
                                           const std::vector<ZoneConfig>& zones) {
    cv::Point2f center(object.bbox.x + object.bbox.width / 2.0f,
                      object.bbox.y + object.bbox.height / 2.0f);

    // 获取或初始化该对象的zone状态映射
    auto& zone_status = object_zone_status_[object.id];

    for (const auto& zone : zones) {
        bool currently_in_zone = isInZone(center, zone);
        // 获取该对象在此区域的上一次状态（如果不存在，则默认为false，表示不在区域内）
        bool previously_in_zone = zone_status[zone.id];

        // 处理进入事件：当前在区域内，但之前不在
        if (currently_in_zone && !previously_in_zone) {
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
            // 更新内部状态：标记为已在区域内
            zone_status[zone.id] = true;
        }
        // 处理离开事件：当前不在区域内，但之前在
        else if (!currently_in_zone && previously_in_zone) {
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
            // 更新内部状态：标记为已离开区域
            zone_status[zone.id] = false;
        }
        // 如果状态没有变化（一直在内或一直在外），则不做任何事
    }
}

void BehaviorAnalyzer::detectLoitering(const TrackedObject& object) {
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
            event.location = cv::Point2f(object.bbox.x + object.bbox.width/2.0f,
                                      object.bbox.y + object.bbox.height/2.0f);
            event.timestamp = std::chrono::system_clock::now();
            event.confidence = object.confidence;

            addEvent(event);
            loitering_events_++;
        }
    }
}

void BehaviorAnalyzer::detectSpeeding(const TrackedObject& object, const TrackedObject& previous) {
    // 实现基于对象与上一帧之间的位移和时间差计算速度，并与阈值比较
    // 此处需要你的具体逻辑，例如：
    // float dx = object.bbox.x - previous.bbox.x;
    // float dy = object.bbox.y - previous.bbox.y;
    // float distance = std::sqrt(dx*dx + dy*dy);
    // auto time_diff = std::chrono::duration_cast<std::chrono::milliseconds>(object.timestamp - previous.timestamp).count() / 1000.0f;
    // float speed = distance / time_diff;
    // if (speed > speed_threshold) { ... 生成事件 ... }
    // 由于用户消息中未提供详细实现，此处保留框架
}

void BehaviorAnalyzer::detectCrowding(const std::vector<TrackedObject>& objects) {
    std::map<std::string, int> zone_counts;

    // Count objects in each zone
    for (const auto& object : objects) {
        for (const auto& zone : zones_) {
            cv::Point2f center(object.bbox.x + object.bbox.width / 2.0f,
                             object.bbox.y + object.bbox.height / 2.0f);

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
            event.location = cv::Point2f(0, 0); // 拥挤事件可能没有具体位置，或可计算区域中心点
            event.confidence = 0.8f; // High confidence for crowding

            addEvent(event);
            crowding_events_++;
        }
    }
}

bool BehaviorAnalyzer::isInZone(const cv::Point2f& point, const ZoneConfig& zone) const {
    // 使用射线法或OpenCV的pointPolygonTest判断点是否在多边形区域内
    // 这里是一个简单示例，假设zone.vertices是多边形的顶点
    double result = cv::pointPolygonTest(zone.vertices, point, false);
    return (result >= 0); // 在边界上或内部都算在内
}

void BehaviorAnalyzer::addZone(const ZoneConfig& zone) {
    std::lock_guard<std::mutex> lock(analyzer_mutex_);
    zones_.push_back(zone);
}

void BehaviorAnalyzer::removeZone(const std::string& zone_id) {
    std::lock_guard<std::mutex> lock(analyzer_mutex_);
    zones_.erase(std::remove_if(zones_.begin(), zones_.end(),
                               [&zone_id](const ZoneConfig& zone) { return zone.id == zone_id; }),
                 zones_.end());
}

std::vector<BehaviorEvent> BehaviorAnalyzer::getEvents() const {
    std::lock_guard<std::mutex> lock(analyzer_mutex_);
    return events_;
}

void BehaviorAnalyzer::clearEvents() {
    std::lock_guard<std::mutex> lock(analyzer_mutex_);
    events_.clear();
    // 可选：是否也重置计数器？
    // total_entrances_ = 0;
    // total_exits_ = 0;
    // loitering_events_ = 0;
    // crowding_events_ = 0;
}

void BehaviorAnalyzer::addEvent(const BehaviorEvent& event) {
    events_.push_back(event);
    // 可根据需要在这里添加日志输出或其他处理
    // std::cout << "Event: " << event.message << std::endl;
}