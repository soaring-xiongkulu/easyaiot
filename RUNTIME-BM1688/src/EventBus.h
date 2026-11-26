#pragma once

#include "Config.h"

#include <string>

namespace easyaiot::bm1688 {

class EventBus {
public:
    explicit EventBus(const RuntimeConfig& config);

    bool publishAlert(const std::string& flatAlertJson, bool snapshot) const;
    bool postHeartbeat(const std::string& json) const;

private:
    bool publishMqtt(const std::string& topic, const std::string& messageType,
                     const std::string& payloadJson) const;
    bool postJson(const std::string& url, const std::string& json) const;
    std::string normalizeAlert(const std::string& flatJson, bool snapshot) const;

    const RuntimeConfig& config_;
};

}  // namespace easyaiot::bm1688
