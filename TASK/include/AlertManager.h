#pragma once
#include <string>
#include <map>
#include <mutex>
#include <atomic>
#include <chrono>
#include <set>
#include <nlohmann/json.hpp>
#include "IMessageSender.h"
#include "IStorageService.h"

struct AlertRule {
    std::string type;
    bool enabled;
    std::string severity; // 告警级别: P0, P1, P2, ...
    float threshold;
    int cooldown;
    std::vector<std::string> actions;
    std::vector<std::string> inhibit_rules; // 被哪些规则抑制
    std::string group_policy; // 分组策略
};

class AlertManager {
public:
    AlertManager(std::shared_ptr<IMessageSender> message_sender,
                 std::shared_ptr<IStorageService> storage_service);

    void initialize(const nlohmann::json& config);
    void handleAlert(const std::string& camera_id,
                    const std::string& alert_type,
                    const nlohmann::json& details);

    void enable() { enabled_ = true; }
    void disable() { enabled_ = false; }
    bool isEnabled() const { return enabled_; }

    std::map<std::string, int> getAlertStatistics() const;
    std::string getStatus() const;

private:
    void executeActions(const std::string& alert_type, const nlohmann::json& alert_message);
    void sendMQTTAlert(const nlohmann::json& alert_message);
    void logAlert(const nlohmann::json& alert_message);
    void sendEmailAlert(const nlohmann::json& alert_message);
    void saveEvidence(const nlohmann::json& alert_message);

    bool isAlertInhibited(const std::string& alert_type, const nlohmann::json& details);
    void checkAndTriggerGroupedAlert(const std::string& alert_type,
                                    const nlohmann::json& alert_message);

    std::shared_ptr<IMessageSender> message_sender_;
    std::shared_ptr<IStorageService> storage_service_;

    mutable std::mutex config_mutex_;
    nlohmann::json config_;
    std::map<std::string, AlertRule> alert_rules_;

    mutable std::mutex alert_mutex_;
    std::atomic<int> alert_count_{0};
    std::map<std::string, int> alert_counts_;
    std::map<std::string, std::chrono::steady_clock::time_point> last_alert_times_;

    std::atomic<bool> enabled_{true};
    std::atomic<bool> initialized_{false};

    // 增强功能：分组和抑制
    std::map<std::string, std::vector<nlohmann::json>> alert_groups_;
    std::set<std::string> active_critical_alerts_;
};