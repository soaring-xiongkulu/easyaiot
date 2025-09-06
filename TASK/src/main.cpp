#include "core/SystemSupervisor.h"
#include "utils/Logger.h"
#include <iostream>
#include <csignal>
#include <atomic>

std::atomic<bool> running{true};

void signalHandler(int signal) {
    Logger::info("Received signal: " + std::to_string(signal) + ", shutting down...");
    running = false;
}

void printSystemInfo() {
    std::cout << "==================================================" << std::endl;
    std::cout << "       Smart Surveillance System" << std::endl;
    std::cout << "       Version: 2.0.0" << std::endl;
    std::cout << "       Build Date: " << __DATE__ << " " << __TIME__ << std::endl;
    std::cout << "==================================================" << std::endl;
}

int main(int argc, char** argv) {
    // Set up signal handlers
    std::signal(SIGINT, signalHandler);
    std::signal(SIGTERM, signalHandler);
    std::signal(SIGUSR1, signalHandler);  // For configuration reload

    printSystemInfo();

    // Initialize logging system
    Logger::initialize("logs/system.log", Logger::Level::INFO);
    Logger::info("Starting Smart Surveillance System...");

    try {
        // Initialize system supervisor
        SystemSupervisor supervisor;

        Logger::info("Initializing system components...");
        if (!supervisor.initialize()) {
            Logger::error("Failed to initialize system supervisor");
            return 1;
        }

        Logger::info("Starting all cameras and processing pipelines...");
        supervisor.start();

        Logger::info("System started successfully. Press Ctrl+C to stop.");
        std::cout << "System is running. Press Ctrl+C to stop." << std::endl;
        std::cout << "Send SIGUSR1 to reload configurations" << std::endl;

        // Main loop
        auto last_status_time = std::chrono::steady_clock::now();
        while (running) {
            // Check system status periodically
            if (std::chrono::steady_clock::now() - last_status_time > std::chrono::minutes(1)) {
                auto status = supervisor.getStatus();
                Logger::info("System status check:");
                for (const auto& [key, value] : status) {
                    Logger::info("  " + key + ": " + value);
                }
                last_status_time = std::chrono::steady_clock::now();
            }

            std::this_thread::sleep_for(std::chrono::seconds(1));
        }

        // Stop the system
        Logger::info("Stopping system components...");
        supervisor.stop();
        supervisor.shutdown();
        
        Logger::info("System stopped gracefully");
    }
    catch (const std::exception& e) {
        Logger::error("Fatal error: " + std::string(e.what()));
        return 1;
    }
    
    return 0;
}