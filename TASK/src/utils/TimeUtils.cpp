#include "TimeUtils.h"
#include <chrono>
#include <sstream>
#include <iomanip>

namespace TimeUtils {

    uint64_t getCurrentMillis() {
        auto now = std::chrono::system_clock::now();
        auto duration = now.time_since_epoch();
        return std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
    }

    std::string getCurrentTimeString(const std::string& format) {
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        std::tm tm = *std::localtime(&time_t);

        std::ostringstream oss;
        oss << std::put_time(&tm, format.c_str());
        return oss.str();
    }

    std::string formatTime(uint64_t millis, const std::string& format) {
        std::time_t time = millis / 1000;
        std::tm tm = *std::localtime(&time);

        std::ostringstream oss;
        oss << std::put_time(&tm, format.c_str());
        return oss.str();
    }

    uint64_t parseTimeString(const std::string& time_str, const std::string& format) {
        std::tm tm = {};
        std::istringstream iss(time_str);
        iss >> std::get_time(&tm, format.c_str());

        if (iss.fail()) {
            return 0;
        }

        auto time = std::mktime(&tm);
        return static_cast<uint64_t>(time) * 1000;
    }

    std::string formatDuration(uint64_t millis) {
        uint64_t seconds = millis / 1000;
        uint64_t minutes = seconds / 60;
        uint64_t hours = minutes / 60;
        uint64_t days = hours / 24;

        seconds %= 60;
        minutes %= 60;
        hours %= 24;

        std::ostringstream oss;
        if (days > 0) {
            oss << days << "d ";
        }
        if (hours > 0 || days > 0) {
            oss << hours << "h ";
        }
        if (minutes > 0 || hours > 0 || days > 0) {
            oss << minutes << "m ";
        }
        oss << seconds << "s";

        return oss.str();
    }

} // namespace TimeUtils