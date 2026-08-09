#ifndef RUNTIME_CRON_CRON_UTILS_H
#define RUNTIME_CRON_CRON_UTILS_H

#include <ctime>
#include <string>
#include <vector>

namespace runtime {
namespace cron {

/**
 * Snap Cron helpers aligned with VIDEO `app/utils/cron_utils.py`:
 * - 5-field (min hour dom mon dow) or 6-field (sec min hour dom mon dow)
 * - Asia/Shanghai (UTC+8) wall clock, no DST
 * - Match window from interval (same formula as snap_cron_match_window_seconds)
 */

struct CronParts {
    std::vector<std::string> fields;  // 5 or 6
    bool hasSeconds{false};
};

bool parseExpression(const std::string& expression, CronParts& out);

/** Convert Unix epoch to Asia/Shanghai naive tm (UTC+8). */
std::tm toShanghaiTm(std::time_t epoch);

/** Format Shanghai fire time as slot key YYYYMMDDHHMMSS. */
std::string formatSlotKey(const std::tm& shanghai);

/**
 * Whether value matches a single cron field (star, star/step, N, A-B, lists).
 * maxValue is inclusive upper bound used for range expansion (e.g. 59 for sec/min).
 */
bool matchField(const std::string& field, int value, int minValue, int maxValue);

bool matchesAt(const CronParts& parts, const std::tm& shanghai);

/** Estimate nominal interval seconds between fires (for window sizing). */
double estimateIntervalSeconds(const CronParts& parts);

/** Window seconds after a fire during which capture is allowed (Python-aligned). */
double matchWindowSeconds(const CronParts& parts, double floorSec = 5.0);

/**
 * Python `cron_slot_for_time` equivalent.
 * Returns true when `epoch` is inside the post-fire match window of the nearest past fire.
 */
bool slotForTime(const std::string& expression,
                 std::time_t epoch,
                 bool& inWindow,
                 std::string& slotKey,
                 double& offsetSec,
                 std::time_t& fireEpoch);

}  // namespace cron
}  // namespace runtime

#endif
