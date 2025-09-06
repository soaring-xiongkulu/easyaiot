#include "Logger.h"
#include <iostream>
#include <iomanip>
#include <sstream>

std::shared_ptr<Logger> Logger::instance_ = nullptr;
std::mutex Logger::instance_mutex_;

Logger::Logger(const std::string& log_file, Level level)
    : log_level_(level), running_(true) {

    if (!log_file.empty()) {
        log_file_.open(log_file, std::ios::out | std::ios::app);
    }

    // Start logging thread
    logging_thread_ = std::thread(&Logger::processLogs, this);
}

Logger::~Logger() {
    running_ = false;
    queue_cv_.notify_all();

    if (logging_thread_.joinable()) {
        logging_thread_.join();
    }

    if (log_file_.is_open()) {
        log_file_.close();
    }
}

std::shared_ptr<Logger> Logger::getInstance() {
    std::lock_guard<std::mutex> lock(instance_mutex_);
    if (!instance_) {
        instance_ = std::shared_ptr<Logger>(new Logger());
    }
    return instance_;
}

void Logger::initialize(const std::string& log_file, Level level) {
    std::lock_guard<std::mutex> lock(instance_mutex_);
    if (!instance_) {
        instance_ = std::shared_ptr<Logger>(new Logger(log_file, level));
    }
}

void Logger::log(Level level, const std::string& message) {
    if (level < log_level_) {
        return;
    }

    LogEntry entry;
    entry.timestamp = std::chrono::system_clock::now();
    entry.level = level;
    entry.message = message;

    {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        log_queue_.push(entry);
    }

    queue_cv_.notify_one();
}

void Logger::processLogs() {
    while (running_ || !log_queue_.empty()) {
        std::unique_lock<std::mutex> lock(queue_mutex_);
        queue_cv_.wait(lock, [this] {
            return !log_queue_.empty() || !running_;
        });

        if (log_queue_.empty()) {
            continue;
        }

        LogEntry entry = log_queue_.front();
        log_queue_.pop();
        lock.unlock();

        // Format log message
        std::string formatted = formatLogEntry(entry);

        // Output to console
        std::cout << formatted << std::endl;

        // Output to file
        if (log_file_.is_open()) {
            log_file_ << formatted << std::endl;
            log_file_.flush();
        }
    }
}

std::string Logger::formatLogEntry(const LogEntry& entry) {
    auto time_t = std::chrono::system_clock::to_time_t(entry.timestamp);
    std::tm tm = *std::localtime(&time_t);

    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S") << " [";

    switch (entry.level) {
        case Level::DEBUG: oss << "DEBUG"; break;
        case Level::INFO: oss << "INFO"; break;
        case Level::WARNING: oss << "WARNING"; break;
        case Level::ERROR: oss << "ERROR"; break;
        case Level::FATAL: oss << "FATAL"; break;
    }

    oss << "] " << entry.message;
    return oss.str();
}

void Logger::debug(const std::string& message) {
    log(Level::DEBUG, message);
}

void Logger::info(const std::string& message) {
    log(Level::INFO, message);
}

void Logger::warning(const std::string& message) {
    log(Level::WARNING, message);
}

void Logger::error(const std::string& message) {
    log(Level::ERROR, message);
}

void Logger::fatal(const std::string& message) {
    log(Level::FATAL, message);
}