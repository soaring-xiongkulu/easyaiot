#include "MinIOClient.h"
#include <aws/core/Aws.h>
#include <aws/s3/S3Client.h>
#include <aws/s3/model/PutObjectRequest.h>
#include <aws/s3/model/GetObjectRequest.h>
#include <aws/s3/model/DeleteObjectRequest.h>
#include <aws/s3/model/CreateBucketRequest.h>
#include <aws/core/auth/AWSCredentials.h>
#include <fstream>

MinIOClient::MinIOClient(const std::string& endpoint,
                       const std::string& access_key,
                       const std::string& secret_key,
                       bool use_ssl)
    : endpoint_(endpoint), access_key_(access_key),
      secret_key_(secret_key), use_ssl_(use_ssl),
      initialized_(false) {}

MinIOClient::~MinIOClient() {
    if (initialized_) {
        Aws::ShutdownAPI(options_);
    }
}

bool MinIOClient::initialize() {
    try {
        Aws::SDKOptions options;
        options.loggingOptions.logLevel = Aws::Utils::Logging::LogLevel::Info;
        Aws::InitAPI(options);

        options_ = options;
        initialized_ = true;

        // Create S3 client configuration
        Aws::Client::ClientConfiguration config;
        config.endpointOverride = endpoint_;
        config.scheme = use_ssl_ ? Aws::Http::Scheme::HTTPS : Aws::Http::Scheme::HTTP;
        config.verifySSL = false;

        // Create credentials
        Aws::Auth::AWSCredentials credentials(access_key_, secret_key_);

        // Create S3 client
        s3_client_ = std::make_shared<Aws::S3::S3Client>(
            credentials, config,
            Aws::Client::AWSAuthV4Signer::PayloadSigningPolicy::Never,
            !use_ssl_);

        std::cout << "MinIO client initialized: " << endpoint_ << std::endl;
        return true;

    } catch (const std::exception& e) {
        std::cerr << "Error initializing MinIO client: " << e.what() << std::endl;
        return false;
    }
}

bool MinIOClient::uploadFile(const std::string& bucket_name,
                           const std::string& object_name,
                           const std::string& file_path) {
    if (!initialized_) {
        return false;
    }

    try {
        Aws::S3::Model::PutObjectRequest request;
        request.SetBucket(bucket_name.c_str());
        request.SetKey(object_name.c_str());

        // Open file
        auto input_data = Aws::MakeShared<Aws::FStream>(
            "PutObjectInputStream", file_path.c_str(),
            std::ios_base::in | std::ios_base::binary);

        if (!input_data->is_open()) {
            std::cerr << "Failed to open file: " << file_path << std::endl;
            return false;
        }

        request.SetBody(input_data);

        // Upload file
        auto outcome = s3_client_->PutObject(request);
        if (!outcome.IsSuccess()) {
            std::cerr << "Upload failed: " << outcome.GetError().GetMessage() << std::endl;
            return false;
        }

        std::cout << "File uploaded: " << file_path << " -> "
                  << bucket_name << "/" << object_name << std::endl;
        return true;

    } catch (const std::exception& e) {
        std::cerr << "Error uploading file: " << e.what() << std::endl;
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
        Aws::S3::Model::GetObjectRequest request;
        request.SetBucket(bucket_name.c_str());
        request.SetKey(object_name.c_str());

        // Download file
        auto outcome = s3_client_->GetObject(request);
        if (!outcome.IsSuccess()) {
            std::cerr << "Download failed: " << outcome.GetError().GetMessage() << std::endl;
            return false;
        }

        // Save to local file
        Aws::OFStream output_file;
        output_file.open(file_path, std::ios::out | std::ios::binary);
        if (!output_file.is_open()) {
            std::cerr << "Failed to open output file: " << file_path << std::endl;
            return false;
        }

        output_file << outcome.GetResult().GetBody().rdbuf();
        output_file.close();

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
        Aws::S3::Model::CreateBucketRequest request;
        request.SetBucket(bucket_name.c_str());

        auto outcome = s3_client_->CreateBucket(request);
        if (!outcome.IsSuccess()) {
            // Bucket might already exist
            if (outcome.GetError().GetErrorType() != Aws::S3::S3Errors::BUCKET_ALREADY_OWNED_BY_YOU) {
                std::cerr << "Create bucket failed: " << outcome.GetError().GetMessage() << std::endl;
                return false;
            }
        }

        std::cout << "Bucket created/verified: " << bucket_name << std::endl;
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
        Aws::S3::Model::DeleteObjectRequest request;
        request.SetBucket(bucket_name.c_str());
        request.SetKey(object_name.c_str());

        auto outcome = s3_client_->DeleteObject(request);
        if (!outcome.IsSuccess()) {
            std::cerr << "Delete object failed: " << outcome.GetError().GetMessage() << std::endl;
            return false;
        }

        std::cout << "Object deleted: " << bucket_name << "/" << object_name << std::endl;
        return true;

    } catch (const std::exception& e) {
        std::cerr << "Error deleting object: " << e.what() << std::endl;
        return false;
    }
}