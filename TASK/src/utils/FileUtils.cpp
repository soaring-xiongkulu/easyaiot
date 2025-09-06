#include "FileUtils.h"
#include <fstream>
#include <sstream>
#include <openssl/md5.h>

namespace FileUtils {

bool exists(const std::string& path) {
    return std::filesystem::exists(path);
}

bool createDirectory(const std::string& path) {
    try {
        return std::filesystem::create_directories(path);
    } catch (const std::exception& e) {
        std::cerr << "Error creating directory: " << e.what() << std::endl;
        return false;
    }
}

std::string readFile(const std::string& path) {
    try {
        std::ifstream file(path);
        if (!file.is_open()) {
            throw std::runtime_error("Cannot open file: " + path);
        }
        
        std::stringstream buffer;
        buffer << file.rdbuf();
        return buffer.str();
    } catch (const std::exception& e) {
        std::cerr << "Error reading file: " << e.what() << std::endl;
        return "";
    }
}

bool writeFile(const std::string& path, const std::string& content) {
    try {
        std::ofstream file(path);
        if (!file.is_open()) {
            throw std::runtime_error("Cannot open file for writing: " + path);
        }
        
        file << content;
        file.close();
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error writing file: " << e.what() << std::endl;
        return false;
    }
}

std::string getFileHash(const std::string& path) {
    try {
        std::ifstream file(path, std::ios::binary);
        if (!file.is_open()) {
            throw std::runtime_error("Cannot open file: " + path);
        }
        
        MD5_CTX md5_context;
        MD5_Init(&md5_context);
        
        char buffer[4096];
        while (file.read(buffer, sizeof(buffer))) {
            MD5_Update(&md5_context, buffer, file.gcount());
        }
        
        unsigned char digest[MD5_DIGEST_LENGTH];
        MD5_Final(digest, &md5_context);
        
        char md5_string[33];
        for (int i = 0; i < MD5_DIGEST_LENGTH; ++i) {
            sprintf(&md5_string[i * 2], "%02x", digest[i]);
        }
        
        return std::string(md5_string);
    } catch (const std::exception& e) {
        std::cerr << "Error calculating file hash: " << e.what() << std::endl;
        return "";
    }
}

uint64_t getFileSize(const std::string& path) {
    try {
        return std::filesystem::file_size(path);
    } catch (const std::exception& e) {
        std::cerr << "Error getting file size: " << e.what() << std::endl;
        return 0;
    }
}

std::vector<std::string> listFiles(const std::string& path, const std::string& extension) {
    std::vector<std::string> files;
    
    try {
        for (const auto& entry : std::filesystem::directory_iterator(path)) {
            if (entry.is_regular_file()) {
                if (extension.empty() || entry.path().extension() == extension) {
                    files.push_back(entry.path().string());
                }
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "Error listing files: " << e.what() << std::endl;
    }
    
    return files;
}

bool copyFile(const std::string& source, const std::string& destination) {
    try {
        std::filesystem::copy_file(source, destination, 
                                 std::filesystem::copy_options::overwrite_existing);
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error copying file: " << e.what() << std::endl;
        return false;
    }
}

bool moveFile(const std::string& source, const std::string& destination) {
    try {
        std::filesystem::rename(source, destination);
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error moving file: " << e.what() << std::endl;
        return false;
    }
}

bool deleteFile(const std::string& path) {
    try {
        return std::filesystem::remove(path);
    } catch (const std::exception& e) {
        std::cerr << "Error deleting file: " << e.what() << std::endl;
        return false;
    }
}

std::string getFileExtension(const std::string& path) {
    return std::filesystem::path(path).extension().string();
}

std::string getFileName(const std::string& path) {
    return std::filesystem::path(path).filename().string();
}

std::string getParentPath(const std::string& path) {
    return std::filesystem::path(path).parent_path().string();
}

}