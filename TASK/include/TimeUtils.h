#pragma once
#include <string>
#include <cstdint>

namespace TimeUtils {
    uint64_t getCurrentMillis();
    std::string getCurrentTimeString(const std::string& format = "%Y-%m-%d %H:%M:%S");
    std::string formatTime(uint64_t millis, const std::string& format = "%Y-%m-%d %H:%M:%S");
    uint64_t parseTimeString(const std::string& time_str, const std::string& format = "%Y-%m-%d %H:%M:%S");
    std::string formatDuration(uint64_t millis);
}