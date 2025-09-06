#include "AlertManager.h"
#include "Logger.h"
#include "TimeUtils.h"
#include <iostream>

AlertManager::AlertManager(std::shared_ptr<IMessageSender> message_sender,
                           std::shared_ptr<IStorageService> storage_service)
    : message_sender_(std::move(message_sender)),
      storage_service_(std::move(storage_service)),
      enabled_(true),
      initialized_(false) {}

void AlertManager::initialize(const nlohmann::json& config) {
    std::lock_guard<std::mutex> lock(config_mutex_);
    config_ = config;

    // Initialize alert rules
    if (config.contains("alert_rules")) {
        for (const auto& rule : config["alert_rules"]) {
            AlertRule alert_rule;
            alert_rule.type = rule.value("type", "");
            alert_rule.enabled = rule.value("enabled", true);
            alert_rule.severity = rule.value("severity", "P2");
            alert_rule.threshold = rule.value("threshold", 0.0f);
            alert_rule.cooldown = rule.value("cooldown", 0);
            alert_rule.actions = rule.value("actions", std::vector<std::string>());
            alert_rule.inhibit_rules = rule.value("inhibit_rules", std::vector<std::string>());
            alert_rule.group_policy = rule.value("group_policy", "");

            alert_rules_[alert_rule.type] = alert_rule;
        }
    }

    initialized_ = true;
}

void AlertManager::handleAlert(const std::string& camera_id,
                             const std::string& alert_type,
                             const nlohmann::json& details) {
    if (!enabled_ || !initialized_) {
        return;
    }

    std::lock_guard<std::mutex> lock(alert_mutex_);

    // Check if alert type is enabled
    auto rule_it = alert_rules_.find(alert_type);
    if (rule_it == alert_rules_.end() || !rule_it->second.enabled) {
        return;
    }

    // 检查抑制规则
    if (isAlertInhibited(alert_type, details)) {
        Logger::debug("Alert " + alert_type + " is inhibited by other active critical alert.");
        return;
    }

    // Check cooldown period
    auto last_alert_it = last_alert_times_.find(alert_type);
    if (last_alert_it != last_alert_times_.end()) {
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
            now - last_alert_it->second).count();

        if (elapsed < rule_it->second.cooldown) {
            return; // Still in cooldown period
        }
    }

    // Create alert message
    nlohmann::json alert_message = {
        {"camera_id", camera_id},
        {"alert_type", alert_type},
        {"severity", rule_it->second.severity},
        {"timestamp", TimeUtils::getCurrentMillis()},
        {"details", details}
    };

    // 处理分组逻辑
    if (!rule_it->second.group_policy.empty()) {
        checkAndTriggerGroupedAlert(alert_type, alert_message);
    } else {
        executeActions(alert_type, alert_message);
    }

    // Update last alert time
    last_alert_times_[alert_type] = std::chrono::steady_clock::now();
    alert_count_++;
    alert_counts_[alert_type]++;

    // 如果是高优先级告警，添加到活跃集合以抑制其他告警
    if (rule_it->second.severity == "P0" || rule_it->second.severity == "P1") {
        active_critical_alerts_.insert(alert_type);
    }
}

bool AlertManager::isAlertInhibited(const std::string& alert_type, const nlohmann::json& details) {
    auto rule_it = alert_rules_.find(alert_type);
    if (rule_it == alert_rules_.end()) return false;

    for (const auto& inhibit_rule_type : rule_it->second.inhibit_rules) {
        if (active_critical_alerts_.find(inhibit_rule_type) != active_critical_alerts_.end()) {
            return true;
        }
    }
    return false;
}

void AlertManager::checkAndTriggerGroupedAlert(const std::string& alert_type,
                                              const nlohmann::json& alert_message) {
    // 简单的按类型分组示例
    alert_groups_[alert_type].push_back(alert_message);

    if (alert_groups_[alert_type].size() >= 5) { // 每5条同类型告警发送一次
        nlohmann::json grouped_alert = {
            {"grouped", true},
            {"alert_type", alert_type},
            {"alerts", alert_groups_[alert_type]}
        };
        executeActions(alert_type, grouped_alert);
        alert_groups_[alert_type].clear();
    }
}

void AlertManager::executeActions(const std::string& alert_type,
                                const nlohmann::json& alert_message) {
    auto rule_it = alert_rules_.find(alert_type);
    if (rule_it == alert_rules_.end()) {
        return;
    }

    for (const auto& action : rule_it->second.actions) {
        if (action == "mqtt") {
            sendMQTTAlert(alert_message);
        } else if (action == "log") {
            logAlert(alert_message);
        } else if (action == "email") {
            sendEmailAlert(alert_message);
        } else if (action == "save_evidence") {
            saveEvidence(alert_message);
        }
    }
}

void AlertManager::sendMQTTAlert(const nlohmann::json& alert_message) {
    if (message_sender_) {
        std::string topic = "surveillance/alerts/" +
                           alert_message["camera_id"].get<std::string>();
        message_sender_->send(topic, alert_message.dump());
    } else {
        Logger::warning("Message sender unavailable, alert not sent: " + alert_message.dump());
    }
}

void AlertManager::logAlert(const nlohmann::json& alert_message) {
    std::string log_message = "ALERT: " +
                             alert_message["camera_id"].get<std::string>() + " - " +
                             alert_message["alert_type"].get<std::string>() + " - " +
                             alert_message["severity"].get<std::string>();

    Logger::info(log_message);
}

void AlertManager::sendEmailAlert(const nlohmann::json& alert_message) {
    // 实现邮件发送逻辑（可参考搜索结果中的Python实现）
    Logger::info("Email alert would be sent: " + alert_message.dump());
}

void AlertManager::saveEvidence(const nlohmann::json& alert_message) {
    if (storage_service_) {
        std::string evidence_data = alert_message.dump();
        bool success = storage_service_->saveEvidence(
            alert_message["camera_id"].get<std::string>(),
            alert_message["alert_type"].get<std::string>(),
            evidence_data
        );

        if (!success) {
            Logger::error("Failed to save evidence for alert: " +
                         alert_message["alert_type"].get<std::string>());
        }
    }
}

std::map<std::string, int> AlertManager::getAlertStatistics() const {
    std::lock_guard<std::mutex> lock(alert_mutex_);

    std::map<std::string, int> stats;
    for (const auto& [alert_type, rule] : alert_rules_) {
        stats[alert_type] = alert_counts_.count(alert_type) ? alert_counts_.at(alert_type) : 0;
    }

    stats["total"] = alert_count_;
    return stats;
}

std::string AlertManager::getStatus() const {
    std::lock_guard<std::mutex> lock(alert_mutex_);

    std::string status = "AlertManager Status:\n";
    status += "Enabled: " + std::string(enabled_ ? "Yes" : "No") + "\n";
    status += "Initialized: " + std::string(initialized_ ? "Yes" : "No") + "\n";
    status += "Total Alerts Processed: " + std::to_string(alert_count_) + "\n";
    status += "Active Critical Alerts: " + std::to_string(active_critical_alerts_.size()) + "\n";
    status += "Configured Rules: " + std::to_string(alert_rules_.size()) + "\n";

    return status;
}