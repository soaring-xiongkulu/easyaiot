package com.basiclab.iot.video.service;

import org.springframework.stereotype.Component;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

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

    /**
     * Full notification payload aligned with Python {@code _build_notification_message_for_kafka}.
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> buildNotificationMessage(
            Map<String, Object> alertData,
            Map<String, Object> notificationConfig,
            Map<String, Boolean> detectionSwitches
    ) {
        if (notificationConfig == null) {
            return null;
        }
        Map<String, Boolean> switches = detectionSwitches != null ? detectionSwitches : Map.of();
        String deviceId = String.valueOf(alertData.get("device_id"));
        Object taskId = notificationConfig.get("task_id");
        String taskName = notificationConfig.get("task_name") != null
                ? String.valueOf(notificationConfig.get("task_name")) : null;

        Map<String, Object> alertNotificationConfig = notificationConfig.get("alert_notification_config") instanceof Map<?, ?> map
                ? castMap(map) : Map.of();
        List<Map<String, Object>> channels = extractChannels(alertNotificationConfig, notificationConfig);
        channels = enrichChannelsUserlessFlags(channels);

        List<String> notifyMethods = new ArrayList<>();
        for (Map<String, Object> ch : channels) {
            Object method = ch.get("method");
            if (method != null && !String.valueOf(method).isBlank()) {
                notifyMethods.add(String.valueOf(method));
            }
        }

        List<Map<String, Object>> notifyUsers = extractNotifyUsers(notificationConfig, alertNotificationConfig);
        boolean hasChannels = !channels.isEmpty() || !notifyMethods.isEmpty();
        boolean hasUsers = !notifyUsers.isEmpty();
        boolean hasUserless = hasUserlessChannel(channels);
        boolean shouldNotify = hasChannels && (hasUsers || hasUserless);

        if (!shouldNotify && hasChannels && !hasUsers && !hasUserless) {
            List<Map<String, Object>> robotChannels = channels.stream().filter(this::isRobotFallbackChannel).toList();
            if (!robotChannels.isEmpty()) {
                shouldNotify = true;
                for (Map<String, Object> ch : robotChannels) {
                    ch.put("userless", true);
                }
                hasUserless = true;
            }
        }
        if (Boolean.TRUE.equals(notificationConfig.get("notification_suppressed"))) {
            shouldNotify = false;
        }
        if (!shouldNotify) {
            return null;
        }

        boolean faceEnabled = switches.getOrDefault("face_detection_enabled", false);
        if (!faceEnabled) {
            faceEnabled = toBool(notificationConfig.get("face_detection_enabled"));
        }
        boolean plateEnabled = switches.getOrDefault("plate_detection_enabled", false);
        if (!plateEnabled) {
            plateEnabled = toBool(notificationConfig.get("plate_detection_enabled"));
        }

        Map<String, Object> alert = new LinkedHashMap<>();
        alert.put("object", alertData.get("object"));
        alert.put("event", alertData.get("event"));
        alert.put("region", alertData.get("region"));
        alert.put("information", alertData.get("information"));
        alert.put("imagePath", firstNonBlank(alertData, "image_path", "imagePath"));
        alert.put("recordPath", firstNonBlank(alertData, "record_path", "recordPath"));
        alert.put("time", normalizeAlertWallTime(alertData.get("time")));
        alert.put("taskType", notificationTaskTypeFrom(alertData, notificationConfig));

        Map<String, Object> message = new LinkedHashMap<>();
        message.put("taskId", taskId);
        message.put("taskName", taskName);
        message.put("deviceId", deviceId);
        message.put("deviceName", alertData.get("device_name"));
        message.put("alert", alert);
        message.put("channels", channels);
        message.put("notifyMethods", notifyMethods);
        message.put("notifyUsers", notifyUsers);
        message.put("faceDetectionEnabled", faceEnabled);
        message.put("plateDetectionEnabled", plateEnabled);
        message.put("shouldNotify", shouldNotify);
        message.put("timestamp", shanghaiIsoNow());

        String correlationId = firstNonBlank(alertData, "correlation_id", "correlationId");
        if (correlationId != null) {
            message.put("correlationId", correlationId);
        }
        return message;
    }

    private static final Set<String> USERLESS_NOTIFY_METHODS = Set.of("http", "webhook");

    @SuppressWarnings("unchecked")
    private static List<Map<String, Object>> extractChannels(
            Map<String, Object> alertNotificationConfig,
            Map<String, Object> notificationConfig
    ) {
        Object channelsObj = alertNotificationConfig.get("channels");
        if (channelsObj instanceof List<?> list && !list.isEmpty()) {
            List<Map<String, Object>> out = new ArrayList<>();
            for (Object item : list) {
                if (item instanceof Map<?, ?> map) {
                    out.add(castMap(map));
                }
            }
            return out;
        }
        Object notifyMethodsRaw = notificationConfig.get("notify_methods");
        if (notifyMethodsRaw == null) {
            return List.of();
        }
        List<String> methods;
        if (notifyMethodsRaw instanceof String text) {
            methods = List.of(text.split(",")).stream().map(String::trim).filter(s -> !s.isEmpty()).toList();
        } else if (notifyMethodsRaw instanceof List<?> list) {
            methods = list.stream().map(String::valueOf).map(String::trim).filter(s -> !s.isEmpty()).toList();
        } else {
            methods = List.of();
        }
        List<Map<String, Object>> channels = new ArrayList<>();
        for (String method : methods) {
            channels.add(Map.of("method", method));
        }
        return channels;
    }

    @SuppressWarnings("unchecked")
    private static List<Map<String, Object>> extractNotifyUsers(
            Map<String, Object> notificationConfig,
            Map<String, Object> alertNotificationConfig
    ) {
        Object raw = notificationConfig.get("notify_users");
        if (raw instanceof List<?> list && !list.isEmpty()) {
            return (List<Map<String, Object>>) (List<?>) list;
        }
        Object fromConfig = alertNotificationConfig.get("notify_users");
        if (fromConfig instanceof List<?> list && !list.isEmpty()) {
            return (List<Map<String, Object>>) (List<?>) list;
        }
        return List.of();
    }

    private static List<Map<String, Object>> enrichChannelsUserlessFlags(List<Map<String, Object>> channels) {
        if (channels == null || channels.isEmpty()) {
            return List.of();
        }
        List<Map<String, Object>> out = new ArrayList<>();
        for (Map<String, Object> ch : channels) {
            Map<String, Object> copy = new LinkedHashMap<>(ch);
            if (!Boolean.TRUE.equals(copy.get("userless"))) {
                String method = copy.get("method") != null ? String.valueOf(copy.get("method")).toLowerCase() : "";
                if (USERLESS_NOTIFY_METHODS.contains(method)) {
                    copy.put("userless", true);
                }
            }
            out.add(copy);
        }
        return out;
    }

    private static boolean hasUserlessChannel(List<Map<String, Object>> channels) {
        for (Map<String, Object> ch : channels) {
            if (Boolean.TRUE.equals(ch.get("userless"))) {
                return true;
            }
            String method = ch.get("method") != null ? String.valueOf(ch.get("method")).toLowerCase() : "";
            if (USERLESS_NOTIFY_METHODS.contains(method)) {
                return true;
            }
        }
        return false;
    }

    private boolean isRobotFallbackChannel(Map<String, Object> channel) {
        if (channel == null) {
            return false;
        }
        String method = channel.get("method") != null ? String.valueOf(channel.get("method")).toLowerCase() : "";
        return "ding".equals(method) || "feishu".equals(method) || "webhook".equals(method) || "http".equals(method);
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> castMap(Map<?, ?> map) {
        Map<String, Object> out = new LinkedHashMap<>();
        for (Map.Entry<?, ?> entry : map.entrySet()) {
            out.put(String.valueOf(entry.getKey()), entry.getValue());
        }
        return out;
    }

    private static String notificationTaskTypeFrom(Map<String, Object> alertData, Map<String, Object> notificationConfig) {
        String raw = firstNonBlank(alertData, "task_type", "taskType");
        if (raw == null && notificationConfig.get("task_type") != null) {
            raw = String.valueOf(notificationConfig.get("task_type"));
        }
        if (raw == null || raw.isBlank()) {
            return "realtime";
        }
        return "snapshot".equals(raw) ? "snap" : raw;
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
