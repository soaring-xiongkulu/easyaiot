#pragma once
#include "IMessageSender.h"
#include "MQTTClient.h"

class MQTTMessageSender : public IMessageSender {
public:
    MQTTMessageSender(std::shared_ptr<MQTTClient> mqtt_client) 
        : mqtt_client_(mqtt_client) {}

    bool send(const std::string& topic, const std::string& message) override {
        if (mqtt_client_ && mqtt_client_->isConnected()) {
            return mqtt_client_->publish(topic, message);
        }
        return false;
    }

    bool isConnected() const override {
        return mqtt_client_ ? mqtt_client_->isConnected() : false;
    }

private:
    std::shared_ptr<MQTTClient> mqtt_client_;
};