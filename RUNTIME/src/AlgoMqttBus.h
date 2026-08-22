/*
 * Algorithm event bus — MQTT publish (alert / post-process) to iot-sink.
 * Heartbeat remains HTTP to VIDEO.
 */

#ifndef ALGO_MQTT_BUS_H
#define ALGO_MQTT_BUS_H

#include <string>
#include <vector>
#include <utility>
#include "Config.h"

class AlgoMqttBus {
public:
    /** True when ALGO_BUS_TRANSPORT is not explicitly http/off/0/false. */
    static bool busEnabled(const Config& config);

    /** Publish flat VIDEO-hook-style alert JSON via mqtt/iot-alert-notification|snapshot. */
    static bool publishAlert(const Config& config, const std::string& flatAlertJson, bool snapshot);

    /** Publish post-process request JSON via mqtt/iot-post-process-request. */
    static bool publishPostProcess(const Config& config, const std::string& payloadJson);

    /** POST_ENABLED=true → InferEvent path instead of final alert. */
    static bool postEnabled();

    /** POST_FAILOVER_OPEN (default true). */
    static bool postFailoverOpen();

    /** Probe cluster: Nacos healthy instances, else GET {POST_BASE_URL}/readyz. */
    static bool probePostReady();

    /** Cached readiness (background probe). Call ensureHealthProbe() first. */
    static bool postIsReady();

    /** Fail-open bypass: POST enabled, failover open, not ready. */
    static bool postInBypass();

    /** Should publish InferEvent (not direct alert). */
    static bool shouldPublishInferEvent();

    /** Start background health probe (idempotent). */
    static void ensureHealthProbe();

    /** Publish raw InferEvent JSON to mqtt/iot-infer-event (no algo envelope). */
    static bool publishInferEvent(const Config& config, const std::string& inferEventJson);

private:
    static std::vector<std::pair<std::string, int>> resolveBrokers(const Config& config);
    static bool publishRaw(const Config& config,
                           const std::string& topic,
                           const std::string& msgType,
                           const std::string& payloadJson);
    static bool publishBytes(const Config& config, const std::string& topic, const std::string& body, int qos);
    static std::string normalizeAlertPayload(const std::string& flatAlertJson, bool snapshot, const Config& config);
    static std::string makeUuid();
    static std::string utcNowIso();
    static std::string postBaseUrl();
    static int healthIntervalSec();
    static int healthFailThreshold();
};

#endif // ALGO_MQTT_BUS_H
