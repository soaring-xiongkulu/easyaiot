#pragma once
#include <atomic>
#include <string>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <thread>
#include <memory>
#include <fstream>

class Logger {
public:
    enum class Level {
        DEBUG,
        INFO,
        WARNING,
        ERROR,
        FATAL
    };

    static std::shared_ptr<Logger> getInstance();
    static void initialize(const std::string& log_file = "", Level level = Level::INFO);

    void log(Level level, const std::string& message);

    static void debug(const std::string& message);
    static void info(const std::string& message);
    static void warning(const std::string& message);
    static void error(const std::string& message);
    static void fatal(const std::string& message);

private:
    struct LogEntry {
        std::chrono::system_clock::time_point timestamp;
        Level level;
        std::string message;
    };

    Logger(const std::string& log_file = "", Level level = Level::INFO);
    ~Logger();

    void processLogs();
    std::string formatLogEntry(const LogEntry& entry);

    static std::shared_ptr<Logger> instance_;
    static std::mutex instance_mutex_;

    Level log_level_;
    std::queue<LogEntry> log_queue_;
    mutable std::mutex queue_mutex_;
    std::condition_variable queue_cv_;
    std::thread logging_thread_;
    std::ofstream log_file_;
    std::atomic<bool> running_{false};
};