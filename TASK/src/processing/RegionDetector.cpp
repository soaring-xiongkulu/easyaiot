#include "RegionDetector.h"
#include <algorithm>
#include <iostream>

RegionDetector::RegionDetector() {}

bool RegionDetector::loadConfiguration(const nlohmann::json& config) {
    std::lock_guard<std::mutex> lock(regions_mutex_);

    try {
        regions_.clear();

        if (config.contains("regions")) {
            for (const auto& region_config : config["regions"]) {
                PolygonRegion region = parseRegionConfig(region_config);
                regions_.push_back(region);
            }
        }

        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error loading region configuration: " << e.what() << std::endl;
        return false;
    }
}

void RegionDetector::updateConfiguration(const nlohmann::json& config) {
    loadConfiguration(config);
}

std::vector<std::string> RegionDetector::detectRegions(const cv::Point2f& point, const cv::Size& frame_size) const {
    std::vector<std::string> region_ids;
    std::lock_guard<std::mutex> lock(regions_mutex_);

    for (const auto& region : regions_) {
        if (isInRegion(point, region.id, frame_size)) {
            region_ids.push_back(region.id);
        }
    }

    return region_ids;
}

std::vector<std::string> RegionDetector::detectRegions(const cv::Rect& bbox, const cv::Size& frame_size) const {
    std::vector<std::string> region_ids;
    std::lock_guard<std::mutex> lock(regions_mutex_);

    for (const auto& region : regions_) {
        if (isInRegion(bbox, region.id, frame_size)) {
            region_ids.push_back(region.id);
        }
    }

    return region_ids;
}

bool RegionDetector::isInRegion(const cv::Point2f& point, const std::string& region_id, const cv::Size& frame_size) const {
    std::lock_guard<std::mutex> lock(regions_mutex_);

    for (const auto& region : regions_) {
        if (region.id == region_id) {
            cv::Point2f pixel_point = normalizedToPixel(point, frame_size);
            return pointInPolygon(pixel_point, region.vertices);
        }
    }

    return false;
}

bool RegionDetector::isInRegion(const cv::Rect& bbox, const std::string& region_id, const cv::Size& frame_size) const {
    std::lock_guard<std::mutex> lock(regions_mutex_);

    for (const auto& region : regions_) {
        if (region.id == region_id) {
            return rectangleIntersectsPolygon(bbox, region.vertices);
        }
    }

    return false;
}

void RegionDetector::drawRegions(cv::Mat& frame, const cv::Size& frame_size) const {
    std::lock_guard<std::mutex> lock(regions_mutex_);

    for (const auto& region : regions_) {
        std::vector<cv::Point> pixel_vertices = getPixelVertices(region, frame_size);

        // Draw polygon
        if (pixel_vertices.size() >= 3) {
            cv::polylines(frame, pixel_vertices, true, region.color, region.thickness);
        }

        // Draw region name
        if (!pixel_vertices.empty()) {
            cv::Point text_position = pixel_vertices[0];
            cv::putText(frame, region.name, text_position,
                       cv::FONT_HERSHEY_SIMPLEX, 0.5, region.color, 1);
        }
    }
}

void RegionDetector::updateTracking(const std::vector<Detection>& detections, const cv::Size& frame_size) {
    updateRegionCounts(detections, frame_size);
    updateDwellTimes();
}

std::vector<PolygonRegion> RegionDetector::getRegions() const {
    std::lock_guard<std::mutex> lock(regions_mutex_);
    return regions_;
}

PolygonRegion RegionDetector::getRegion(const std::string& region_id) const {
    std::lock_guard<std::mutex> lock(regions_mutex_);

    for (const auto& region : regions_) {
        if (region.id == region_id) {
            return region;
        }
    }

    return PolygonRegion();
}

std::map<std::string, int> RegionDetector::getRegionCounts() const {
    std::lock_guard<std::mutex> lock(tracking_mutex_);
    return region_object_counts_;
}

std::map<std::string, int> RegionDetector::getDwellTimes() const {
    std::lock_guard<std::mutex> lock(tracking_mutex_);

    std::map<std::string, int> dwell_times;
    for (const auto& [region_id, object_times] : region_dwell_times_) {
        int total_time = 0;
        for (const auto& [object_id, time] : object_times) {
            total_time += time;
        }
        dwell_times[region_id] = total_time;
    }

    return dwell_times;
}

void RegionDetector::resetTracking() {
    std::lock_guard<std::mutex> lock(tracking_mutex_);
    region_object_counts_.clear();
    region_dwell_times_.clear();
}

// Helper methods
cv::Point2f RegionDetector::normalizedToPixel(const cv::Point2f& norm_point, const cv::Size& frame_size) const {
    return cv::Point2f(norm_point.x * frame_size.width, norm_point.y * frame_size.height);
}

std::vector<cv::Point> RegionDetector::getPixelVertices(const PolygonRegion& region, const cv::Size& frame_size) const {
    std::vector<cv::Point> pixel_vertices;

    for (const auto& vertex : region.vertices) {
        cv::Point2f pixel_vertex = normalizedToPixel(vertex, frame_size);
        pixel_vertices.emplace_back(static_cast<int>(pixel_vertex.x), static_cast<int>(pixel_vertex.y));
    }

    return pixel_vertices;
}

bool RegionDetector::pointInPolygon(const cv::Point2f& point, const std::vector<cv::Point2f>& vertices) const {
    int i, j, nvert = vertices.size();
    bool c = false;

    for (i = 0, j = nvert - 1; i < nvert; j = i++) {
        if (((vertices[i].y > point.y) != (vertices[j].y > point.y)) &&
            (point.x < (vertices[j].x - vertices[i].x) * (point.y - vertices[i].y) /
             (vertices[j].y - vertices[i].y) + vertices[i].x)) {
            c = !c;
        }
    }

    return c;
}

bool RegionDetector::rectangleIntersectsPolygon(const cv::Rect& rect, const std::vector<cv::Point2f>& vertices) const {
    // Check if any corner of the rectangle is inside the polygon
    cv::Point2f corners[4] = {
        cv::Point2f(rect.x, rect.y),
        cv::Point2f(rect.x + rect.width, rect.y),
        cv::Point2f(rect.x + rect.width, rect.y + rect.height),
        cv::Point2f(rect.x, rect.y + rect.height)
    };

    for (const auto& corner : corners) {
        if (pointInPolygon(corner, vertices)) {
            return true;
        }
    }

    // Check if any edge of the polygon intersects the rectangle
    int nvert = vertices.size();
    for (int i = 0, j = nvert - 1; i < nvert; j = i++) {
        cv::Point2f v1 = vertices[j];
        cv::Point2f v2 = vertices[i];

        // Check if the polygon edge intersects the rectangle
        if (lineIntersectsRectangle(v1, v2, rect)) {
            return true;
        }
    }

    return false;
}

// Cohen-Sutherland线段裁剪算法函数实现
bool RegionDetector::lineIntersectsRectangle(const cv::Point2f& p1, const cv::Point2f& p2, const cv::Rect& rect) const {
    // Cohen-Sutherland line clipping algorithm
    int code1 = computeOutCode(p1, rect);
    int code2 = computeOutCode(p2, rect);

    if (code1 == 0 && code2 == 0) {
        return true; // Both points inside rectangle
    }

    if (code1 & code2) {
        return false; // Both points on same side of rectangle
    }

    return true; // Line may intersect rectangle
}

int RegionDetector::computeOutCode(const cv::Point2f& point, const cv::Rect& rect) const {
    int code = 0;

    if (point.x < rect.x) code |= 1; // Left
    if (point.x > rect.x + rect.width) code |= 2; // Right
    if (point.y < rect.y) code |= 4; // Bottom
    if (point.y > rect.y + rect.height) code |= 8; // Top

    return code;
}

void RegionDetector::updateRegionCounts(const std::vector<Detection>& detections, const cv::Size& frame_size) {
    std::lock_guard<std::mutex> lock(tracking_mutex_);
    region_object_counts_.clear();

    for (const auto& detection : detections) {
        cv::Point2f center(detection.bbox.x + detection.bbox.width / 2.0f,
                          detection.bbox.y + detection.bbox.height / 2.0f);

        for (const auto& region : regions_) {
            if (pointInPolygon(center, region.vertices)) {
                region_object_counts_[region.id]++;
            }
        }
    }
}

void RegionDetector::updateDwellTimes() {
    std::lock_guard<std::mutex> lock(tracking_mutex_);
    auto now = std::chrono::steady_clock::now();

    // Update dwell times for objects in regions
    for (auto& region : regions_) {
        for (auto& [object_id, entry_time] : region.object_entries) {
            auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - entry_time).count();
            region.object_dwell_times[object_id] = elapsed;

            // Update global dwell times
            region_dwell_times_[region.id][object_id] = elapsed;
        }
    }
}

PolygonRegion RegionDetector::parseRegionConfig(const nlohmann::json& region_config) const {
    PolygonRegion region;

    region.id = region_config.value("id", "");
    region.name = region_config.value("name", "");
    region.type = region_config.value("type", "polygon");

    // Parse vertices
    if (region_config.contains("vertices")) {
        for (const auto& vertex : region_config["vertices"]) {
            cv::Point2f point;
            point.x = vertex.value("x", 0.0f);
            point.y = vertex.value("y", 0.0f);
            region.vertices.push_back(point);
        }
    }

    // Parse color
    if (region_config.contains("color")) {
        auto color = region_config["color"];
        region.color = cv::Scalar(
            color.value("b", 0),
            color.value("g", 255),
            color.value("r", 0)
        );
    } else {
        region.color = cv::Scalar(0, 255, 0); // Default green
    }

    region.thickness = region_config.value("thickness", 2);
    region.sensitivity = region_config.value("sensitivity", 0.5f);
    region.min_object_size = region_config.value("min_object_size", 10);
    region.max_object_size = region_config.value("max_object_size", 1000);

    // Parse target classes
    if (region_config.contains("target_classes")) {
        for (const auto& class_name : region_config["target_classes"]) {
            region.target_classes.push_back(class_name);
        }
    }

    region.enable_intrusion = region_config.value("enable_intrusion", false);
    region.enable_loitering = region_config.value("enable_loitering", false);
    region.enable_crowding = region_config.value("enable_crowding", false);
    region.loitering_threshold = region_config.value("loitering_threshold", 30.0f);
    region.crowding_threshold = region_config.value("crowding_threshold", 5);

    return region;
}