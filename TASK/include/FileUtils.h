#ifndef FILE_UTILS_H
#define FILE_UTILS_H

#include <cstdint>
#include <string>
#include <vector>

namespace FileUtils {

    bool exists(const std::string& path);
    bool createDirectory(const std::string& path);
    std::string readFile(const std::string& path);
    bool writeFile(const std::string& path, const std::string& content);
    std::string getFileHash(const std::string& path);
    uint64_t getFileSize(const std::string& path);
    std::vector<std::string> listFiles(const std::string& path, const std::string& extension = "");
    bool copyFile(const std::string& source, const std::string& destination);
    bool moveFile(const std::string& source, const std::string& destination);
    bool deleteFile(const std::string& path);
    std::string getFileExtension(const std::string& path);
    std::string getFileName(const std::string& path);
    std::string getParentPath(const std::string& path);

} // namespace FileUtils

#endif