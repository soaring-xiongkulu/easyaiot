#pragma once
#include "MQTTClient.h"
#include "MinIOClient.h"
#include <memory>
#include <mutex>

class ServiceLocator {
public:
    static ServiceLocator& getInstance();

    void initializeServices();
    void shutdownServices();

    std::shared_ptr<MQTTClient> getMQTTClient();
    std::shared_ptr<MinIOClient> getMinIOClient();

    bool areServicesReady() const;
    std::string getServiceStatus() const;

private:
    ServiceLocator() = default;
    ~ServiceLocator() = default;

    std::shared_ptr<MQTTClient> mqtt_client_;
    std::shared_ptr<MinIOClient> minio_client_;

    mutable std::mutex services_mutex_;
    bool services_ready_{false};
    bool mqtt_initialized_{false};
    bool minio_initialized_{false};
};