package com.basiclab.iot.video.service;

import org.springframework.stereotype.Component;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Builds minimal alert Kafka payloads aligned with Python {@code _build_minimal_alert_kafka_message}
 * and iot-sink {@code AlertNotificationMessage}.
 */
@Component
public class AlertKafkaMessageBuilder {

    private static final ZoneId SHANGHAI = ZoneId.of("Asia/Shanghai");
    private static final DateTimeFormatter WALL = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final DateTimeFormatter ISO = DateTimeFormatter.ISO_OFFSET_DATE_TIME;

    public Map<String, Object> buildMinimal(
            Map<String, Object> alertData,
            Map<String, Object> alertEventTask,
            Map<String, Boolean> detectionSwitches
    ) {
        Map<String, Boolean> switches = detectionSwitches != null ? detectionSwitches : Map.of();
        Long taskId = taskIdFrom(alertData, alertEventTask);
        String taskName = taskNameFrom(alertData, alertEventTask);
        String taskType = taskTypeFrom(alertData, alertEventTask);

        Map<String, Object> alert = new LinkedHashMap<>();
        alert.put("object", alertData.get("object"));
        alert.put("event", alertData.get("event"));
        alert.put("region", alertData.get("region"));
        alert.put("information", alertData.get("information"));
        alert.put("imagePath", firstNonBlank(alertData, "image_path", "imagePath"));
        alert.put("recordPath", firstNonBlank(alertData, "record_path", "recordPath"));
        alert.put("time", normalizeAlertWallTime(alertData.get("time")));
        alert.put("taskType", taskType);

        Map<String, Object> message = new LinkedHashMap<>();
        message.put("deviceId", String.valueOf(alertData.get("device_id")));
        message.put("deviceName", alertData.get("device_name"));
        message.put("taskId", taskId);
        message.put("taskName", taskName);
        message.put("alert", alert);
        message.put("notifyUsers", null);
        message.put("notifyMethods", null);
        message.put("channels", null);
        message.put("faceDetectionEnabled", switches.getOrDefault("face_detection_enabled", false));
        message.put("plateDetectionEnabled", switches.getOrDefault("plate_detection_enabled", false));
        message.put("shouldNotify", false);
        message.put("timestamp", shanghaiIsoNow());

        String correlationId = firstNonBlank(alertData, "correlation_id", "correlationId");
        if (correlationId != null) {
            message.put("correlationId", correlationId);
        }
        return message;
    }

    public Map<String, Boolean> resolveDetectionSwitches(
            Map<String, Object> alertData,
            Map<String, Object> alertEventTask
    ) {
        boolean face = toBool(firstNonNull(alertData, "face_detection_enabled", "faceDetectionEnabled"));
        if (!face && alertEventTask != null) {
            face = toBool(alertEventTask.get("face_detection_enabled"));
        }
        boolean plate = toBool(firstNonNull(alertData, "plate_detection_enabled", "plateDetectionEnabled"));
        if (!plate && alertEventTask != null) {
            plate = toBool(alertEventTask.get("plate_detection_enabled"));
        }
        Map<String, Boolean> out = new LinkedHashMap<>();
        out.put("face_detection_enabled", face);
        out.put("plate_detection_enabled", plate);
        return out;
    }

    private static Long taskIdFrom(Map<String, Object> alertData, Map<String, Object> alertEventTask) {
        Object raw = firstNonNull(alertData, "task_id", "taskId");
        if (raw == null && alertEventTask != null) {
            raw = alertEventTask.get("task_id");
        }
        if (raw == null || String.valueOf(raw).isBlank()) {
            return null;
        }
        return Long.parseLong(String.valueOf(raw));
    }

    private static String taskNameFrom(Map<String, Object> alertData, Map<String, Object> alertEventTask) {
        String fromData = firstNonBlank(alertData, "task_name", "taskName");
        if (fromData != null) {
            return fromData;
        }
        if (alertEventTask != null && alertEventTask.get("task_name") != null) {
            return String.valueOf(alertEventTask.get("task_name"));
        }
        return null;
    }

    private static String taskTypeFrom(Map<String, Object> alertData, Map<String, Object> alertEventTask) {
        String raw = firstNonBlank(alertData, "task_type", "taskType");
        if (raw == null && alertEventTask != null && alertEventTask.get("task_type") != null) {
            raw = String.valueOf(alertEventTask.get("task_type"));
        }
        if (raw == null || raw.isBlank()) {
            return "realtime";
        }
        return "snapshot".equals(raw) ? "snap" : raw;
    }

    private static String normalizeAlertWallTime(Object rawTime) {
        if (rawTime == null || String.valueOf(rawTime).isBlank()) {
            return LocalDateTime.now(SHANGHAI).format(WALL);
        }
        if (rawTime instanceof Number number) {
            return LocalDateTime.ofInstant(Instant.ofEpochMilli(number.longValue()), SHANGHAI).format(WALL);
        }
        String text = String.valueOf(rawTime).trim();
        try {
            if (text.contains("T")) {
                return ZonedDateTime.parse(text).withZoneSameInstant(SHANGHAI).format(WALL);
            }
            LocalDateTime parsed = LocalDateTime.parse(text, WALL);
            return parsed.format(WALL);
        } catch (Exception ignored) {
            return LocalDateTime.now(SHANGHAI).format(WALL);
        }
    }

    private static String shanghaiIsoNow() {
        return ZonedDateTime.now(SHANGHAI).format(ISO);
    }

    private static Object firstNonNull(Map<String, Object> data, String... keys) {
        for (String key : keys) {
            if (data.containsKey(key) && data.get(key) != null) {
                return data.get(key);
            }
        }
        return null;
    }

    private static String firstNonBlank(Map<String, Object> data, String... keys) {
        Object value = firstNonNull(data, keys);
        if (value == null) {
            return null;
        }
        String text = String.valueOf(value).trim();
        return text.isEmpty() ? null : text;
    }

    private static boolean toBool(Object value) {
        if (value == null) {
            return false;
        }
        if (value instanceof Boolean bool) {
            return bool;
        }
        if (value instanceof Number number) {
            return number.intValue() != 0;
        }
        String text = String.valueOf(value).trim().toLowerCase();
        return "1".equals(text) || "true".equals(text) || "yes".equals(text) || "on".equals(text);
    }
}
