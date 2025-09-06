#include "AlertManager.h"
#include "ServiceLocator.h"

AlertManager::AlertManager() : enabled_(true) {}

void AlertManager::initialize(const nlohmann::json& config) {
    std::lock_guard<std::mutex> lock(config_mutex_);
    config_ = config;
    
    // Initialize alert rules
    if (config.contains("alert_rules")) {
        for (const auto& rule : config["alert_rules"]) {
            AlertRule alert_rule;
            alert_rule.type = rule.value("type", "");
            alert_rule.enabled = rule.value("enabled", true);
            alert_rule.threshold = rule.value("threshold", 0.0f);
            alert_rule.cooldown = rule.value("cooldown", 0);
            alert_rule.actions = rule.value("actions", std::vector<std::string>());
            
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
        {"timestamp", TimeUtils::getCurrentMillis()},
        {"details", details}
    };
    
    // Execute alert actions
    executeActions(alert_type, alert_message);
    
    // Update last alert time
    last_alert_times_[alert_type] = std::chrono::steady_clock::now();
    alert_count_++;
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
    auto service_locator = ServiceLocator::getInstance();
    auto mqtt_client = service_locator.getMQTTClient();
    
    if (mqtt_client) {
        std::string topic = "surveillance/alerts/" + 
                           alert_message["camera_id"].get<std::string>();
        
        mqtt_client->publish(topic, alert_message.dump());
    }
}

void AlertManager::logAlert(const nlohmann::json& alert_message) {
    std::string log_message = "ALERT: " + 
                             alert_message["camera_id"].get<std::string>() + " - " +
                             alert_message["alert_type"].get<std::string>();
    
    Logger::info(log_message);
}

void AlertManager::saveEvidence(const nlohmann::json& alert_message) {
    // This would typically save images or video evidence
    // Implementation depends on storage system
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