#ifndef ALERT_CLASS_FILTER_H
#define ALERT_CLASS_FILTER_H

#include <string>
#include <vector>

#include "Datatype.h"

namespace AlertClassFilter {

std::string normalizeClassName(const std::string& className);

std::vector<std::string> parseAlertClassNames(const std::string& raw);

std::vector<DetectObject> filterDetectionsForAlert(
    const std::vector<DetectObject>& detections,
    const std::vector<std::string>& alertClassNames);

}  // namespace AlertClassFilter

#endif  // ALERT_CLASS_FILTER_H
