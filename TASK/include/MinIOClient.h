#ifndef MINIO_CLIENT_H
#define MINIO_CLIENT_H

#include <string>
#include <memory>

// 前向声明minio::s3::Client
namespace minio {
    namespace s3 {
        class Client;
    } // namespace s3

    namespace creds {
        class StaticProvider;
    } // namespace creds
} // namespace minio

class MinIOClient {
public:
    MinIOClient(const std::string& endpoint,
                const std::string& access_key,
                const std::string& secret_key,
                bool use_ssl = false);

    ~MinIOClient();

    bool initialize();
    bool uploadFile(const std::string& bucket_name,
                   const std::string& object_name,
                   const std::string& file_path);
    bool putObject(const std::string& bucket_name,
                   const std::string& object_name,
                   const std::string& data); // 添加这个方法
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
    bool use_ssl_;
    bool initialized_;
    std::shared_ptr<minio::s3::Client> client_;
    std::shared_ptr<minio::creds::StaticProvider> provider_;
};

#endif // MINIO_CLIENT_H