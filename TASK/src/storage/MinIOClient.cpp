#include "MinIOClient.h"
#include <miniocpp/client.h>
#include <miniocpp/credentials.h>
#include <fstream>
#include <iostream>
#include <sstream>

MinIOClient::MinIOClient(const std::string& endpoint,
                         const std::string& access_key,
                         const std::string& secret_key,
                         bool use_ssl)
    : endpoint_(endpoint), access_key_(access_key),
      secret_key_(secret_key), use_ssl_(use_ssl),
      initialized_(false) {}

MinIOClient::~MinIOClient() = default;

bool MinIOClient::initialize() {
    try {
        // 创建S3基础URL
        minio::s3::BaseUrl base_url(endpoint_, use_ssl_);

        // 创建凭证提供者
        auto provider = std::make_shared<minio::creds::StaticProvider>(
            access_key_, secret_key_, "");

        // 创建S3客户端
        client_ = std::make_shared<minio::s3::Client>(base_url, provider.get());

        initialized_ = true;
        std::cout << "MinIO client initialized: " << endpoint_ << std::endl;
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error initializing MinIO client: " << e.what() << std::endl;
        return false;
    }
}

bool MinIOClient::putObject(const std::string& bucket_name,
                           const std::string& object_name,
                           const std::string& data) {
    if (!initialized_) {
        std::cerr << "MinIO client not initialized" << std::endl;
        return false;
    }

    try {
        // 将字符串数据转换为流
        std::istringstream data_stream(data);

        // 创建上传参数 - 使用正确的构造函数
        minio::s3::PutObjectArgs args(data_stream, data.size(), 0);
        args.bucket = bucket_name;
        args.object = object_name;

        // 执行上传
        auto response = client_->PutObject(args);
        if (!response) {
            std::cerr << "Upload failed: " << response.Error().String() << std::endl;
            return false;
        }
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error uploading object: " << e.what() << std::endl;
        return false;
    }
}

bool MinIOClient::downloadFile(const std::string& bucket_name,
                             const std::string& object_name,
                             const std::string& file_path) {
    if (!initialized_) {
        return false;
    }

    try {
        // 下载对象到文件
        minio::s3::DownloadObjectArgs args;
        args.bucket = bucket_name;
        args.object = object_name;
        args.filename = file_path;
        args.overwrite = true; // 允许覆盖现有文件

        auto resp = client_->DownloadObject(args);
        if (!resp) {
            std::cerr << "Download failed: " << resp.Error().String() << std::endl;
            return false;
        }

        std::cout << "File downloaded: " << bucket_name << "/" << object_name
                  << " -> " << file_path << std::endl;
        return true;

    } catch (const std::exception& e) {
        std::cerr << "Error downloading file: " << e.what() << std::endl;
        return false;
    }
}

bool MinIOClient::createBucket(const std::string& bucket_name) {
    if (!initialized_) {
        return false;
    }

    try {
        // 检查桶是否存在
        minio::s3::BucketExistsArgs args;
        args.bucket = bucket_name;

        auto resp = client_->BucketExists(args);
        if (!resp) {
            std::cerr << "Bucket existence check failed: " << resp.Error().String() << std::endl;
            return false;
        }

        if (resp.exist) {
            std::cout << "Bucket already exists: " << bucket_name << std::endl;
            return true;
        }

        // 创建桶
        minio::s3::MakeBucketArgs make_args;
        make_args.bucket = bucket_name;

        auto make_resp = client_->MakeBucket(make_args);
        if (!make_resp) {
            std::cerr << "Create bucket failed: " << make_resp.Error().String() << std::endl;
            return false;
        }

        std::cout << "Bucket created: " << bucket_name << std::endl;
        return true;

    } catch (const std::exception& e) {
        std::cerr << "Error creating bucket: " << e.what() << std::endl;
        return false;
    }
}

bool MinIOClient::deleteObject(const std::string& bucket_name,
                             const std::string& object_name) {
    if (!initialized_) {
        return false;
    }

    try {
        // 删除对象
        minio::s3::RemoveObjectArgs args;
        args.bucket = bucket_name;
        args.object = object_name;

        auto resp = client_->RemoveObject(args);
        if (!resp) {
            std::cerr << "Delete object failed: " << resp.Error().String() << std::endl;
            return false;
        }

        std::cout << "Object deleted: " << bucket_name << "/" << object_name << std::endl;
        return true;

    } catch (const std::exception& e) {
        std::cerr << "Error deleting object: " << e.what() << std::endl;
        return false;
    }
}