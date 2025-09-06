#pragma once
#include <opencv2/opencv.hpp>
#include <nlohmann/json.hpp>
#include <vector>
#include <map>
#include <string>
#include <mutex>
#include <set>
#include <chrono>

#include "ObjectTracker.h"

enum class BehaviorEventType {
    ENTRANCE,
    EXIT,
    LOITERING,
    CROWDING,
    SPEEDING
};

struct BehaviorEvent {
    int object_id;
    BehaviorEventType type;
    std::string zone_id;
    std::string message;
    cv::Point2f location;
    std::chrono::system_clock::time_point timestamp;
    float confidence;
};

struct ZoneConfig {
    std::string id;
    std::string name;
    std::vector<cv::Point2f> vertices;
    bool enable_loitering;
    float loitering_threshold;
    bool enable_crowding;
    int crowding_threshold;
};

class BehaviorAnalyzer {
public:
    BehaviorAnalyzer(const nlohmann::json& config);

    void analyzeFrame(const cv::Mat& frame, const std::vector<TrackedObject>& objects);
    void addZone(const ZoneConfig& zone);
    void removeZone(const std::string& zone_id);

    std::vector<BehaviorEvent> getEvents() const;
    void clearEvents();

    int getTotalEntrances() const { return total_entrances_; }
    int getTotalExits() const { return total_exits_; }
    int getLoiteringEvents() const { return loitering_events_; }
    int getCrowdingEvents() const { return crowding_events_; }

private:
    std::vector<ZoneConfig> zones_;
    std::map<int, TrackedObject> previous_objects_;
    // 新增：内部状态，用于跟踪每个对象在每个区域的当前状态（true:在区域内, false:在区域外）
    std::map<int, std::map<std::string, bool>> object_zone_status_;
    mutable std::mutex analyzer_mutex_;

    std::vector<BehaviorEvent> events_;
    int total_entrances_{0};
    int total_exits_{0};
    int loitering_events_{0};
    int crowding_events_{0};

    bool enable_loitering_detection_{false};
    bool enable_entrance_exit_detection_{true};
    bool enable_crowding_detection_{false};
    bool enable_speeding_detection_{false};

    float global_loitering_threshold_{30.0f};
    int global_crowding_threshold_{5};

    void checkZoneEntriesExits(const TrackedObject& object, const std::vector<ZoneConfig>& zones);
    void detectLoitering(const TrackedObject& object);
    void detectSpeeding(const TrackedObject& object, const TrackedObject& previous);
    void detectCrowding(const std::vector<TrackedObject>& objects);

    bool isInZone(const cv::Point2f& point, const ZoneConfig& zone) const;
    void addEvent(const BehaviorEvent& event);
};