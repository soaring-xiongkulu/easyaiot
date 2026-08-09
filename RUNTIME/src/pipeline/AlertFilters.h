#pragma once

#include <string>
#include <vector>

#include "Datatype.h"
#include "Config.h"

namespace runtime {

/** Normalize class labels for whitelist / face-plate keyword matching. */
std::string normalizeClassName(const std::string& name);

/** Parse alert_class_names JSON array (or comma / single token). */
std::vector<std::string> parseAlertClassNames(const std::string& jsonOrList);

bool isFaceClass(const std::string& className);
bool isPlateClass(const std::string& className);

/**
 * CAP-ALERT-CLASS-FILTER + CAP-FACE-FILTER + CAP-PLATE-FILTER.
 * Empty alert_class whitelist → keep all (compat). face/plate flags drop
 * incidental face/plate classes when disabled (matches Python run_deploy).
 */
std::vector<DetectObject> filterDetectionsForAlert(
    const std::vector<DetectObject>& detections,
    const Config& config);

/**
 * CAP-DEFENSE: schedule_json supports:
 *   {"active": false}                         → always skip
 *   {"active": true}                          → always allow
 *   {"windows":[{"start":"HH:MM","end":"HH:MM","days":[0-6]}]}
 * Empty / {} → allow (compat). mode=full|half is logged; half still arms on windows.
 */
bool isDefenseArmed(const Config& config);

}  // namespace runtime
