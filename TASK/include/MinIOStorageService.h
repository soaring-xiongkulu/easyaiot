#pragma once
#include "IStorageService.h"
#include <memory>

class MinIOClient; // 前向声明

class MinIOStorageService : public IStorageService {
public:
    MinIOStorageService(std::shared_ptr<MinIOClient> minio_client);

    bool saveEvidence(const std::string& camera_id,
                     const std::string& alert_type,
                     const std::string& evidence_data) override;

private:
    std::shared_ptr<MinIOClient> minio_client_;
};