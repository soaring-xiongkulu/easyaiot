#pragma once
#include <string>
#include <functional>
#include <memory>
#include <mqtt/async_client.h>
#include <mqtt/callback.h>

class MQTTClient : public mqtt::callback
{
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
    // 使用正确的类型，而不是 std::shared_ptr<void>
    std::shared_ptr<mqtt::async_client> mqtt_client_;

    // 重写 mqtt::callback 接口中的虚函数
    void connected(const mqtt::string& cause) override;
    void connection_lost(const std::string& cause) override;
    void message_arrived(mqtt::const_message_ptr msg) override; // 修正函数签名
    void delivery_complete(mqtt::delivery_token_ptr token) override; // 修正函数签名
};