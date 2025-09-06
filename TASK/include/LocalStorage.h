#pragma once
#include <nlohmann/json.hpp>
#include <opencv2/opencv.hpp>
#include <string>
#include <vector>

class LocalStorage {
public:
    LocalStorage(const std::string& base_path);

    bool saveImage(const std::string& filename, const cv::Mat& image);
    bool saveJson(const std::string& filename, const nlohmann::json& data);
    nlohmann::json loadJson(const std::string& filename);

    std::vector<std::string> listFiles(const std::string& directory);
    bool deleteFile(const std::string& filepath);
    uint64_t getStorageUsage() const;

private:
    std::string base_path_;
};