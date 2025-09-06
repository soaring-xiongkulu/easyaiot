#pragma once
#include <string>
#include <functional>
#include <memory>

class MQTTClient {
public:
    using MessageCallback = std::function<void(const std::string& topic, const std::string& payload)>;

    MQTTClient(const std::string& broker_url,
              const std::string& client_id,
              const std::string& username = "",
              const std::string& password = "");
    ~MQTTClient();

    bool connect();
    void disconnect();
    bool publish(const std::string& topic, const std::string& payload, int qos = 1);
    bool subscribe(const std::string& topic, int qos = 1);

    void setMessageCallback(MessageCallback callback);
    void setAutoReconnect(bool auto_reconnect) { auto_reconnect_ = auto_reconnect; }

private:
    std::string broker_url_;
    std::string client_id_;
    std::string username_;
    std::string password_;
    bool connected_{false};
    bool auto_reconnect_{true};

    MessageCallback message_callback_;
    std::shared_ptr<void> mqtt_client_; // Using void* to avoid including MQTT headers here

    // MQTT callback methods
    void connected(const std::string& cause);
    void connection_lost(const std::string& cause);
    void message_arrived(void* message);
    void delivery_complete(void* token);
};