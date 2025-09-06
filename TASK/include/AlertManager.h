#pragma once
#include <nlohmann/json.hpp>
#include <string>
#include <map>
#include <vector>
#include <chrono>
#include <mutex>

struct AlertRule {
    std::string type;
    bool enabled;
    float threshold;
    int cooldown;
    std::vector<std::string> actions;
};

class AlertManager {
public:
    AlertManager();

    void initialize(const nlohmann::json& config);
    void handleAlert(const std::string& camera_id,
                    const std::string& alert_type,
                    const nlohmann::json& details);

    void setEnabled(bool enabled) { enabled_ = enabled; }
    bool isEnabled() const { return enabled_; }

    std::map<std::string, int> getAlertStatistics() const;
    void resetStatistics();

private:
    std::map<std::string, AlertRule> alert_rules_;
    std::map<std::string, std::chrono::steady_clock::time_point> last_alert_times_;
    std::map<std::string, int> alert_counts_;

    nlohmann::json config_;
    mutable std::mutex config_mutex_;
    mutable std::mutex alert_mutex_;

    bool enabled_{true};
    bool initialized_{false};
    int alert_count_{0};

    void executeActions(const std::string& alert_type, const nlohmann::json& alert_message);
    void sendMQTTAlert(const nlohmann::json& alert_message);
    void logAlert(const nlohmann::json& alert_message);
    void sendEmailAlert(const nlohmann::json& alert_message);
    void saveEvidence(const nlohmann::json& alert_message);
};