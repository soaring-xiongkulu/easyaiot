#pragma once
#include <string>
#include <memory>

class MinIOClient {
public:
    MinIOClient(const std::string& endpoint,
               const std::string& access_key,
               const std::string& secret_key,
               bool secure = false);
    ~MinIOClient();

    bool initialize();
    bool uploadFile(const std::string& bucket_name,
                   const std::string& object_name,
                   const std::string& file_path);
    bool downloadFile(const std::string& bucket_name,
                     const std::string& object_name,
                     const std::string& file_path);
    bool createBucket(const std::string& bucket_name);
    bool deleteObject(const std::string& bucket_name,
                     const std::string& object_name);

private:
    std::string endpoint_;
    std::string access_key_;
    std::string secret_key_;
    bool secure_;
    bool initialized_{false};

    // AWS S3 client (MinIO is S3 compatible)
    std::shared_ptr<void> s3_client_; // Using void* to avoid including AWS headers here
};