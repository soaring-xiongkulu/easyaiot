#include "LocalStorage.h"
#include <filesystem>
#include <fstream>

LocalStorage::LocalStorage(const std::string& base_path)
    : base_path_(base_path) {
    std::filesystem::create_directories(base_path_ + "/images");
    std::filesystem::create_directories(base_path_ + "/videos");
    std::filesystem::create_directories(base_path_ + "/logs");
    std::filesystem::create_directories(base_path_ + "/config");
}

bool LocalStorage::saveImage(const std::string& filename, const cv::Mat& image) {
    try {
        std::string full_path = base_path_ + "/images/" + filename;
        return cv::imwrite(full_path, image);
    } catch (const std::exception& e) {
        std::cerr << "Error saving image: " << e.what() << std::endl;
        return false;
    }
}

bool LocalStorage::saveJson(const std::string& filename, const nlohmann::json& data) {
    try {
        std::string full_path = base_path_ + "/config/" + filename;
        std::ofstream file(full_path);
        file << data.dump(4);
        file.close();
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error saving JSON: " << e.what() << std::endl;
        return false;
    }
}

nlohmann::json LocalStorage::loadJson(const std::string& filename) {
    try {
        std::string full_path = base_path_ + "/config/" + filename;
        if (!std::filesystem::exists(full_path)) {
            return nlohmann::json();
        }

        std::ifstream file(full_path);
        nlohmann::json data;
        file >> data;
        file.close();
        return data;
    } catch (const std::exception& e) {
        std::cerr << "Error loading JSON: " << e.what() << std::endl;
        return nlohmann::json();
    }
}

std::vector<std::string> LocalStorage::listFiles(const std::string& directory) {
    std::vector<std::string> files;
    std::string full_path = base_path_ + "/" + directory;

    if (!std::filesystem::exists(full_path)) {
        return files;
    }

    for (const auto& entry : std::filesystem::directory_iterator(full_path)) {
        if (entry.is_regular_file()) {
            files.push_back(entry.path().filename().string());
        }
    }

    return files;
}

bool LocalStorage::deleteFile(const std::string& filepath) {
    try {
        std::string full_path = base_path_ + "/" + filepath;
        if (std::filesystem::exists(full_path)) {
            return std::filesystem::remove(full_path);
        }
        return false;
    } catch (const std::exception& e) {
        std::cerr << "Error deleting file: " << e.what() << std::endl;
        return false;
    }
}

uint64_t LocalStorage::getStorageUsage() const {
    uint64_t total_size = 0;

    for (const auto& entry : std::filesystem::recursive_directory_iterator(base_path_)) {
        if (entry.is_regular_file()) {
            total_size += std::filesystem::file_size(entry.path());
        }
    }

    return total_size;
}