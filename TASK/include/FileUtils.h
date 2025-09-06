#pragma once
#include <string>
#include <vector>

namespace FileUtils {
    bool fileExists(const std::string& path);
    bool createDirectory(const std::string& path);
    bool deleteFile(const std::string& path);
    bool deleteDirectory(const std::string& path);

    std::string readFile(const std::string& path);
    bool writeFile(const std::string& path, const std::string& content);

    std::vector<std::string> listFiles(const std::string& path, bool recursive = false);
    std::vector<std::string> listDirectories(const std::string& path, bool recursive = false);

    uint64_t getFileSize(const std::string& path);
    uint64_t getDirectorySize(const std::string& path);

    std::string getFileExtension(const std::string& path);
    std::string getFileName(const std::string& path);
    std::string getParentPath(const std::string& path);
}