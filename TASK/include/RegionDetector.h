#pragma once
#include <opencv2/opencv.hpp>
#include <vector>
#include <string>
#include <map>
#include <mutex>
#include <nlohmann/json.hpp>

#include "InferenceEngine.h"

struct PolygonRegion {
    std::string id;
    std::string name;
    std::string type;
    std::vector<cv::Point2f> vertices;
    cv::Scalar color;
    int thickness;
    
    float sensitivity;
    int min_object_size;
    int max_object_size;
    std::vector<std::string> target_classes;
    
    bool enable_intrusion;
    bool enable_loitering;
    bool enable_crowding;
    float loitering_threshold;
    int crowding_threshold;
    
    std::map<int, std::chrono::steady_clock::time_point> object_entries;
    std::map<int, int> object_dwell_times;
};

class RegionDetector {
public:
    RegionDetector();
    
    bool loadConfiguration(const nlohmann::json& config);
    void updateConfiguration(const nlohmann::json& config);
    
    std::vector<std::string> detectRegions(const cv::Point2f& point, const cv::Size& frame_size) const;
    std::vector<std::string> detectRegions(const cv::Rect& bbox, const cv::Size& frame_size) const;
    
    bool isInRegion(const cv::Point2f& point, const std::string& region_id, const cv::Size& frame_size) const;
    bool isInRegion(const cv::Rect& bbox, const std::string& region_id, const cv::Size& frame_size) const;
    
    void drawRegions(cv::Mat& frame, const cv::Size& frame_size) const;
    void updateTracking(const std::vector<Detection>& detections, const cv::Size& frame_size);
    
    std::vector<PolygonRegion> getRegions() const;
    PolygonRegion getRegion(const std::string& region_id) const;
    
    std::map<std::string, int> getRegionCounts() const;
    std::map<std::string, int> getDwellTimes() const;
    
    void resetTracking();

private:
    std::vector<PolygonRegion> regions_;
    mutable std::mutex regions_mutex_;
    
    std::map<std::string, int> region_object_counts_;
    std::map<std::string, std::map<int, int>> region_dwell_times_;
    mutable std::mutex tracking_mutex_;
    
    cv::Point2f normalizedToPixel(const cv::Point2f& norm_point, const cv::Size& frame_size) const;
    std::vector<cv::Point> getPixelVertices(const PolygonRegion& region, const cv::Size& frame_size) const;
    
    bool pointInPolygon(const cv::Point2f& point, const std::vector<cv::Point2f>& vertices) const;
    bool rectangleIntersectsPolygon(const cv::Rect& rect, const std::vector<cv::Point2f>& vertices) const;
    
    // 新增声明：Cohen-Sutherland线段裁剪算法函数
    bool lineIntersectsRectangle(const cv::Point2f& p1, const cv::Point2f& p2, const cv::Rect& rect) const;
    int computeOutCode(const cv::Point2f& point, const cv::Rect& rect) const;

    void updateRegionCounts(const std::vector<Detection>& detections, const cv::Size& frame_size);
    void updateDwellTimes();
    
    PolygonRegion parseRegionConfig(const nlohmann::json& region_config) const;
};