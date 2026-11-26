#pragma once

#include "Config.h"

#include <string>

namespace easyaiot::nvidia {

class EventBus {
public:
    explicit EventBus(const RuntimeConfig& config);
    bool publishAlert(const std::string& flatAlertJson) const;
    bool postHeartbeat(const std::string& json) const;

private:
    bool postJson(const std::string& url, const std::string& json) const;
    bool publishMqtt(const std::string& payloadJson) const;
    const RuntimeConfig& config_;
};

}  // namespace easyaiot::nvidia
