#pragma once
#include <memory>
#include <mutex>
#include <atomic>
#include "MQTTClient.h"
#include "MinIOClient.h"
#include "IMessageSender.h"
#include "IStorageService.h"

class ServiceLocator {
public:
    static ServiceLocator& getInstance();

    void initializeServices();
    void shutdownServices();

    std::shared_ptr<MQTTClient> getMQTTClient();
    std::shared_ptr<MinIOClient> getMinIOClient();

    std::shared_ptr<IMessageSender> getMessageSender();
    std::shared_ptr<IStorageService> getStorageService();

    bool areServicesReady() const;
    std::string getServiceStatus() const;

private:
    ServiceLocator() = default;
    ~ServiceLocator() = default;

    mutable std::mutex services_mutex_;
    std::shared_ptr<MQTTClient> mqtt_client_;
    std::shared_ptr<MinIOClient> minio_client_;

    std::shared_ptr<IMessageSender> message_sender_;
    std::shared_ptr<IStorageService> storage_service_;

    std::atomic<bool> services_ready_{false};
    std::atomic<bool> mqtt_initialized_{false};
    std::atomic<bool> minio_initialized_{false};
};