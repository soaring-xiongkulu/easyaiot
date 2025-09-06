#pragma once

#include <string>
#include <functional>
#include <memory>
#include <mutex>
#include <mqtt/async_client.h>
#include <mqtt/callback.h>
#include <mqtt/types.h>

class MQTTClient : public mqtt::callback
{
public:
    using MessageCallback = std::function<void(const std::string& topic, const std::string& payload)>;

    MQTTClient(const std::string& broker_url,
              const std::string& client_id,
              const std::string& username = "",
              const std::string& password = "");

    // 禁止拷贝构造和赋值操作
    MQTTClient(const MQTTClient&) = delete;
    MQTTClient& operator=(const MQTTClient&) = delete;

    ~MQTTClient();

    bool connect();
    void disconnect();
    bool publish(const std::string& topic, const std::string& payload, int qos = 1);
    bool subscribe(const std::string& topic, int qos = 1);
    bool unsubscribe(const std::string& topic);

    bool isConnected() const;
    void setMessageCallback(MessageCallback callback);
    void setAutoReconnect(bool auto_reconnect) { auto_reconnect_ = auto_reconnect; }

    // 新增方法：获取客户端ID
    std::string getClientId() const { return client_id_; }

    // 新增方法：获取Broker URL
    std::string getBrokerUrl() const { return broker_url_; }

private:
    std::string broker_url_;
    std::string client_id_;
    std::string username_;
    std::string password_;
    mutable std::mutex connection_mutex_; // 添加mutable修饰符，用于const方法
    bool connected_{false};
    bool auto_reconnect_{true};

    MessageCallback message_callback_;
    std::shared_ptr<mqtt::async_client> mqtt_client_;

    // MQTT callback methods
    void connected(const mqtt::string& cause) override;
    void connection_lost(const std::string& cause) override;
    void message_arrived(mqtt::const_message_ptr msg) override;
    void delivery_complete(mqtt::delivery_token_ptr token) override;

    // 新增私有方法：尝试重新连接
    bool tryReconnect();
};