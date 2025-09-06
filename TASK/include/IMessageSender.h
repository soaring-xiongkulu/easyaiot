#pragma once
#include <string>

class IMessageSender {
public:
    virtual ~IMessageSender() = default;
    virtual bool send(const std::string& topic, const std::string& message) = 0;
    virtual bool isConnected() const = 0;
};