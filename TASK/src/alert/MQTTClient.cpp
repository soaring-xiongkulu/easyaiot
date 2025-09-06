#include "MQTTClient.h"
#include <iostream>
#include <chrono>
#include <thread>
#include <mutex>

std::mutex connection_mutex_;

MQTTClient::MQTTClient(const std::string& broker_url,
                     const std::string& client_id,
                     const std::string& username,
                     const std::string& password)
    : broker_url_(broker_url), client_id_(client_id),
      username_(username), password_(password),
      connected_(false), auto_reconnect_(true) {}

MQTTClient::~MQTTClient() {
    disconnect();
}

bool MQTTClient::connect() {
    try {
        // Create MQTT client
        mqtt::connect_options connOpts;
        connOpts.set_clean_session(true);

        if (!username_.empty()) {
            connOpts.set_user_name(username_);
        }

        if (!password_.empty()) {
            connOpts.set_password(password_);
        }

        // Create client
        mqtt_client_ = std::make_shared<mqtt::async_client>(broker_url_, client_id_);

        // Set callbacks
        mqtt_client_->set_callback(*this);

        // Connect to the broker
        mqtt::token_ptr conntok = mqtt_client_->connect(connOpts);
        conntok->wait();

        {
            std::lock_guard<std::mutex> lock(connection_mutex_);
            connected_ = true;
        }

        std::cout << "Connected to MQTT broker: " << broker_url_ << std::endl;
        return true;

    } catch (const mqtt::exception& exc) {
        std::cerr << "MQTT connection failed: " << exc.what() << std::endl;
        return false;
    }
}

void MQTTClient::disconnect() {
    bool was_connected = false;
    {
        std::lock_guard<std::mutex> lock(connection_mutex_);
        was_connected = connected_;
        connected_ = false;
    }

    if (was_connected && mqtt_client_) {
        try {
            mqtt_client_->disconnect()->wait();
            std::cout << "Disconnected from MQTT broker" << std::endl;
        } catch (const mqtt::exception& exc) {
            std::cerr << "MQTT disconnect failed: " << exc.what() << std::endl;
        }
    }
}

bool MQTTClient::publish(const std::string& topic, const std::string& payload, int qos) {
    if (!isConnected()) {
        std::cerr << "Not connected to broker" << std::endl;
        return false;
    }

    try {
        mqtt::message_ptr pubmsg = mqtt::make_message(topic, payload);
        pubmsg->set_qos(qos);

        mqtt_client_->publish(pubmsg)->wait();
        std::cout << "Message published to topic: " << topic << std::endl;
        return true;

    } catch (const mqtt::exception& exc) {
        std::cerr << "MQTT publish failed: " << exc.what() << std::endl;
        return false;
    }
}

bool MQTTClient::subscribe(const std::string& topic, int qos) {
    if (!isConnected()) {
        std::cerr << "Not connected to broker" << std::endl;
        return false;
    }

    try {
        mqtt_client_->subscribe(topic, qos)->wait();
        std::cout << "Subscribed to topic: " << topic << std::endl;
        return true;

    } catch (const mqtt::exception& exc) {
        std::cerr << "MQTT subscribe failed: " << exc.what() << std::endl;
        return false;
    }
}

void MQTTClient::setMessageCallback(MessageCallback callback) {
    message_callback_ = callback;
}

// 修正的 isConnected 方法
bool MQTTClient::isConnected() const {
    std::lock_guard<std::mutex> lock(connection_mutex_);
    return connected_;
}

// MQTT callback methods
void MQTTClient::connected(const mqtt::string& cause) {
    {
        std::lock_guard<std::mutex> lock(connection_mutex_);
        connected_ = true;
    }
    std::cout << "MQTT connection established: " << cause << std::endl;
}

void MQTTClient::connection_lost(const std::string& cause) {
    {
        std::lock_guard<std::mutex> lock(connection_mutex_);
        connected_ = false;
    }

    std::cout << "Connection lost: " << cause << std::endl;

    // Attempt to reconnect
    if (auto_reconnect_) {
        std::cout << "Attempting to reconnect in 5 seconds..." << std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(5));
        try {
            connect();
        } catch (...) {
            std::cerr << "Reconnection attempt failed" << std::endl;
        }
    }
}

void MQTTClient::message_arrived(mqtt::const_message_ptr msg) {
    if (message_callback_) {
        message_callback_(msg->get_topic(), msg->to_string());
    }
}

void MQTTClient::delivery_complete(mqtt::delivery_token_ptr token) {
    // Delivery confirmation handling if needed
    // std::cout << "Message delivery complete for token: " << (token ? token->get_message_id() : -1) << std::endl;
}