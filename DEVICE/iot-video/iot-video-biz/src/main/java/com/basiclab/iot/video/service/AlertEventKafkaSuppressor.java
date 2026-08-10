package com.basiclab.iot.video.service;

import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * In-memory Kafka alert-event suppress (mirrors Python {@code _should_suppress_alert_event_kafka}).
 */
@Component
public class AlertEventKafkaSuppressor {

    private final Map<String, Long> lastSentEpochMs = new ConcurrentHashMap<>();

    public boolean shouldSuppress(String deviceId, String taskType, int suppressSeconds) {
        if (deviceId == null || deviceId.isBlank() || suppressSeconds <= 0) {
            return false;
        }
        String normalizedType = normalizeTaskType(taskType);
        String key = deviceId + "|" + normalizedType;
        long now = System.currentTimeMillis();
        Long last = lastSentEpochMs.get(key);
        if (last != null && now - last < suppressSeconds * 1000L) {
            return true;
        }
        lastSentEpochMs.put(key, now);
        return false;
    }

    private static String normalizeTaskType(String taskType) {
        String tt = taskType != null && !taskType.isBlank() ? taskType : "realtime";
        return "snapshot".equals(tt) ? "snap" : tt;
    }
}
