#pragma once
#include <string>

class IStorageService {
public:
    virtual ~IStorageService() = default;
    virtual bool saveEvidence(const std::string& camera_id, 
                            const std::string& alert_type, 
                            const std::string& evidence_data) = 0;
};