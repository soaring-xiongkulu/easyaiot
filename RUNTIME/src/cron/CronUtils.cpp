#include "cron/CronUtils.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <sstream>
#include <vector>

namespace runtime {
namespace cron {
namespace {

std::string trim(const std::string& s) {
    size_t b = 0;
    while (b < s.size() && (s[b] == ' ' || s[b] == '\t')) {
        ++b;
    }
    size_t e = s.size();
    while (e > b && (s[e - 1] == ' ' || s[e - 1] == '\t')) {
        --e;
    }
    return s.substr(b, e - b);
}

std::vector<std::string> splitWs(const std::string& expr) {
    std::istringstream iss(expr);
    std::vector<std::string> parts;
    std::string tok;
    while (iss >> tok) {
        if (tok == "?") {
            tok = "*";
        }
        parts.push_back(tok);
    }
    return parts;
}

bool matchToken(const std::string& token, int value, int minValue, int maxValue) {
    if (token.empty() || token == "*") {
        return true;
    }
    if (token.size() >= 3 && token[0] == '*' && token[1] == '/') {
        int step = std::atoi(token.c_str() + 2);
        return step > 0 && ((value - minValue) % step) == 0;
    }
    const size_t slash = token.find('/');
    if (slash != std::string::npos) {
        std::string rangePart = token.substr(0, slash);
        int step = std::atoi(token.c_str() + slash + 1);
        if (step <= 0) {
            return false;
        }
        int lo = minValue;
        int hi = maxValue;
        const size_t dash = rangePart.find('-');
        if (dash != std::string::npos) {
            lo = std::atoi(rangePart.c_str());
            hi = std::atoi(rangePart.c_str() + dash + 1);
        } else if (rangePart != "*") {
            lo = std::atoi(rangePart.c_str());
            hi = maxValue;
        }
        if (value < lo || value > hi) {
            return false;
        }
        return ((value - lo) % step) == 0;
    }
    const size_t dash = token.find('-');
    if (dash != std::string::npos) {
        int lo = std::atoi(token.c_str());
        int hi = std::atoi(token.c_str() + dash + 1);
        return value >= lo && value <= hi;
    }
    return std::atoi(token.c_str()) == value;
}

std::tm epochToUtcTm(std::time_t epoch) {
    std::tm tm{};
#if defined(_WIN32)
    gmtime_s(&tm, &epoch);
#else
    gmtime_r(&epoch, &tm);
#endif
    return tm;
}

int fieldMin(size_t idx, bool hasSeconds) {
    (void)idx;
    (void)hasSeconds;
    return 0;
}

int fieldMax(size_t idx, bool hasSeconds) {
    // idx into parts.fields
    if (hasSeconds) {
        static const int kMax[] = {59, 59, 23, 31, 12, 6};
        return kMax[idx];
    }
    static const int kMax5[] = {59, 23, 31, 12, 6};
    return kMax5[idx];
}

int tmValue(const std::tm& tm, size_t idx, bool hasSeconds) {
    if (hasSeconds) {
        switch (idx) {
            case 0: return tm.tm_sec;
            case 1: return tm.tm_min;
            case 2: return tm.tm_hour;
            case 3: return tm.tm_mday;
            case 4: return tm.tm_mon + 1;
            case 5: return tm.tm_wday;  // 0=Sun
            default: return 0;
        }
    }
    switch (idx) {
        case 0: return tm.tm_min;
        case 1: return tm.tm_hour;
        case 2: return tm.tm_mday;
        case 3: return tm.tm_mon + 1;
        case 4: return tm.tm_wday;
        default: return 0;
    }
}

double estimateFromParts(const CronParts& parts) {
    // Prefer second/minute/hour step patterns used by snap tasks.
    auto stepOf = [](const std::string& f) -> int {
        if (f.size() >= 3 && f[0] == '*' && f[1] == '/') {
            return std::atoi(f.c_str() + 2);
        }
        return 0;
    };
    if (parts.hasSeconds) {
        int secStep = stepOf(parts.fields[0]);
        if (secStep > 0) {
            return static_cast<double>(secStep);
        }
        if (parts.fields[0] != "*" && parts.fields[0].find(',') == std::string::npos
            && parts.fields[0].find('-') == std::string::npos) {
            int minStep = stepOf(parts.fields[1]);
            if (minStep > 0) {
                return static_cast<double>(minStep) * 60.0;
            }
        }
        int minStep = stepOf(parts.fields[1]);
        if (minStep > 0) {
            return static_cast<double>(minStep) * 60.0;
        }
        int hourStep = stepOf(parts.fields[2]);
        if (hourStep > 0) {
            return static_cast<double>(hourStep) * 3600.0;
        }
    } else {
        int minStep = stepOf(parts.fields[0]);
        if (minStep > 0) {
            return static_cast<double>(minStep) * 60.0;
        }
        int hourStep = stepOf(parts.fields[1]);
        if (hourStep > 0) {
            return static_cast<double>(hourStep) * 3600.0;
        }
    }
    return 3600.0;
}

}  // namespace

bool parseExpression(const std::string& expression, CronParts& out) {
    out = CronParts{};
    auto parts = splitWs(trim(expression));
    if (parts.size() == 7) {
        parts.resize(6);
    }
    if (parts.size() != 5 && parts.size() != 6) {
        return false;
    }
    out.fields = std::move(parts);
    out.hasSeconds = out.fields.size() == 6;
    return true;
}

std::tm toShanghaiTm(std::time_t epoch) {
    // Asia/Shanghai = UTC+8 year-round (no DST).
    return epochToUtcTm(epoch + 8 * 3600);
}

std::string formatSlotKey(const std::tm& shanghai) {
    char buf[32];
    std::snprintf(buf, sizeof(buf), "%04d%02d%02d%02d%02d%02d",
                  shanghai.tm_year + 1900, shanghai.tm_mon + 1, shanghai.tm_mday,
                  shanghai.tm_hour, shanghai.tm_min, shanghai.tm_sec);
    return buf;
}

bool matchField(const std::string& field, int value, int minValue, int maxValue) {
    // Support comma lists: "0,15,30"
    size_t start = 0;
    while (start <= field.size()) {
        size_t comma = field.find(',', start);
        std::string token = (comma == std::string::npos)
            ? field.substr(start)
            : field.substr(start, comma - start);
        if (matchToken(token, value, minValue, maxValue)) {
            return true;
        }
        if (comma == std::string::npos) {
            break;
        }
        start = comma + 1;
    }
    return false;
}

bool matchesAt(const CronParts& parts, const std::tm& shanghai) {
    for (size_t i = 0; i < parts.fields.size(); ++i) {
        const int v = tmValue(shanghai, i, parts.hasSeconds);
        const int lo = fieldMin(i, parts.hasSeconds);
        const int hi = fieldMax(i, parts.hasSeconds);
        if (!matchField(parts.fields[i], v, lo, hi)) {
            return false;
        }
    }
    return true;
}

double estimateIntervalSeconds(const CronParts& parts) {
    return std::max(1.0, estimateFromParts(parts));
}

double matchWindowSeconds(const CronParts& parts, double floorSec) {
    // Mirror VIDEO cron_utils.snap_cron_match_window_seconds
    const double interval = estimateIntervalSeconds(parts);
    floorSec = std::max(0.0, floorSec);
    if (interval <= 120.0) {
        return std::min({std::max(floorSec, 10.0), interval * 0.45, interval - 1.0});
    }
    if (interval <= 3600.0) {
        return std::min({std::max(floorSec, 15.0), interval * 0.15, 120.0});
    }
    return std::min({std::max(floorSec, 30.0), interval * 0.05, 300.0});
}

bool slotForTime(const std::string& expression,
                 std::time_t epoch,
                 bool& inWindow,
                 std::string& slotKey,
                 double& offsetSec,
                 std::time_t& fireEpoch) {
    inWindow = false;
    slotKey.clear();
    offsetSec = 0.0;
    fireEpoch = 0;

    CronParts parts;
    if (!parseExpression(expression, parts)) {
        return false;
    }

    const double interval = estimateIntervalSeconds(parts);
    const double window = matchWindowSeconds(parts);
    // Scan back up to ~1.5 intervals (capped) for previous fire second.
    const int maxScan = static_cast<int>(std::min(std::max(interval * 1.5, window + 2.0), 7200.0));

    std::time_t prevFire = 0;
    bool foundPrev = false;
    for (int back = 0; back <= maxScan; ++back) {
        std::time_t cand = epoch - back;
        std::tm sh = toShanghaiTm(cand);
        if (matchesAt(parts, sh)) {
            prevFire = cand;
            foundPrev = true;
            break;
        }
    }
    if (!foundPrev) {
        return true;  // parsed ok but not in any slot
    }

    // Optional next fire for "closer to next" guard (Python cron_slot_for_time).
    std::time_t nextFire = 0;
    bool foundNext = false;
    const int fwdScan = static_cast<int>(std::min(std::max(interval * 1.5, 2.0), 7200.0));
    for (int fwd = 1; fwd <= fwdScan; ++fwd) {
        std::time_t cand = epoch + fwd;
        std::tm sh = toShanghaiTm(cand);
        if (matchesAt(parts, sh)) {
            nextFire = cand;
            foundNext = true;
            break;
        }
    }

    const double sincePrev = static_cast<double>(epoch - prevFire);
    double toNext = foundNext ? static_cast<double>(nextFire - epoch) : interval;
    std::time_t fire = prevFire;
    double offset = sincePrev;
    if (foundNext && sincePrev > toNext) {
        fire = nextFire;
        offset = toNext;
        if (offset > 0.05) {
            inWindow = false;
            fireEpoch = fire;
            slotKey = formatSlotKey(toShanghaiTm(fire));
            offsetSec = offset;
            return true;
        }
    }

    fireEpoch = fire;
    slotKey = formatSlotKey(toShanghaiTm(fire));
    offsetSec = offset;
    inWindow = (offset >= 0.0 && offset < window);
    return true;
}

}  // namespace cron
}  // namespace runtime
