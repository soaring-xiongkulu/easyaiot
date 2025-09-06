#pragma once
#include <string>
#include <filesystem>

class ModelDownloader {
public:
    ModelDownloader();
    ~ModelDownloader();

    bool downloadModel(const std::string& model_id,
                      const std::string& model_url,
                      const std::string& local_path);

private:
    bool downloadFile(const std::string& url, const std::string& local_path);
};