#include "MinIOStorageService.h"

#include "MinIOClient.h"
#include "TimeUtils.h"

MinIOStorageService::MinIOStorageService(std::shared_ptr<MinIOClient> minio_client) 
    : minio_client_(minio_client) {}

bool MinIOStorageService::saveEvidence(const std::string& camera_id, 
                     const std::string& alert_type, 
                     const std::string& evidence_data) {
    if (!minio_client_) return false;
    
    // 生成唯一的对象名
    std::string object_name = "evidence/" + camera_id + "/" + 
                            alert_type + "/" + 
                            std::to_string(TimeUtils::getCurrentMillis()) + ".dat";
    
    // 调用putObject上传数据
    return minio_client_->putObject("evidence-bucket", object_name, evidence_data);
}