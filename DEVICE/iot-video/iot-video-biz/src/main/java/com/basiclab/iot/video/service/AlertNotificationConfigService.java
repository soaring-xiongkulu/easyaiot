package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.support.JsonFields;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Mirrors Python {@code _query_alert_notification_config} for alert hook Kafka payloads.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AlertNotificationConfigService {

    private final AlgorithmTaskRepository taskRepository;

    public Optional<Map<String, Object>> queryConfig(String deviceId, String taskType) {
        if (deviceId == null || deviceId.isBlank()) {
            return Optional.empty();
        }
        Optional<Map<String, Object>> rowOpt = taskRepository.findAlertNotificationConfig(deviceId, taskType);
        if (rowOpt.isEmpty()) {
            return Optional.empty();
        }
        Map<String, Object> row = rowOpt.get();
        Object configRaw = row.get("alert_notification_config");
        if (configRaw == null || String.valueOf(configRaw).isBlank()) {
            log.warn("告警通知已开启但未配置渠道: deviceId={}, taskId={}", deviceId, row.get("task_id"));
            return Optional.empty();
        }

        Map<String, Object> notificationConfigData = parseConfigMap(configRaw);
        List<Map<String, Object>> notifyUsers = extractNotifyUsers(notificationConfigData, row);

        Map<String, Object> config = new LinkedHashMap<>();
        config.put("task_id", row.get("task_id"));
        config.put("task_name", row.get("task_name"));
        config.put("task_type", row.getOrDefault("task_type", taskType != null ? taskType : "realtime"));
        config.put("alert_notification_config", notificationConfigData);
        config.put("notify_users", notifyUsers);
        config.put("alarm_suppress_time", row.get("alarm_suppress_time"));
        config.put("face_detection_enabled", toBool(row.get("face_detection_enabled")));
        config.put("plate_detection_enabled", toBool(row.get("plate_detection_enabled")));

        if (isSuppressed(row)) {
            config.put("notification_suppressed", true);
        }
        return Optional.of(config);
    }

    public void markNotificationSent(Map<String, Object> config) {
        Object taskId = config != null ? config.get("task_id") : null;
        if (taskId == null) {
            return;
        }
        try {
            taskRepository.updateLastNotifyTime(Long.parseLong(String.valueOf(taskId)));
        } catch (Exception ex) {
            log.warn("更新告警通知抑制时间失败 taskId={}: {}", taskId, ex.getMessage());
        }
    }

    private static boolean isSuppressed(Map<String, Object> row) {
        Object lastNotify = row.get("last_notify_time");
        Object suppressRaw = row.get("alarm_suppress_time");
        if (lastNotify == null || suppressRaw == null) {
            return false;
        }
        int suppressSeconds;
        try {
            suppressSeconds = Integer.parseInt(String.valueOf(suppressRaw));
        } catch (NumberFormatException ex) {
            return false;
        }
        if (suppressSeconds <= 0) {
            return false;
        }
        Instant last = lastNotify instanceof Instant instant ? instant : Instant.parse(String.valueOf(lastNotify));
        return Duration.between(last, Instant.now()).getSeconds() < suppressSeconds;
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> parseConfigMap(Object raw) {
        if (raw instanceof Map<?, ?> map) {
            Map<String, Object> out = new LinkedHashMap<>();
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                out.put(String.valueOf(entry.getKey()), entry.getValue());
            }
            return out;
        }
        Object parsed = JsonFields.parseJsonObject(String.valueOf(raw));
        if (parsed instanceof Map<?, ?> map) {
            Map<String, Object> out = new LinkedHashMap<>();
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                out.put(String.valueOf(entry.getKey()), entry.getValue());
            }
            return out;
        }
        return Map.of();
    }

    @SuppressWarnings("unchecked")
    private static List<Map<String, Object>> extractNotifyUsers(
            Map<String, Object> notificationConfigData,
            Map<String, Object> row
    ) {
        Object fromConfig = notificationConfigData.get("notify_users");
        if (fromConfig instanceof List<?> list && !list.isEmpty()) {
            return (List<Map<String, Object>>) (List<?>) list;
        }
        Object raw = row.get("notify_users");
        if (raw instanceof List<?> list && !list.isEmpty()) {
            return (List<Map<String, Object>>) (List<?>) list;
        }
        if (raw instanceof String text && !text.isBlank()) {
            Object parsed = JsonFields.parseJsonObject(text);
            if (parsed instanceof List<?> list) {
                return (List<Map<String, Object>>) (List<?>) list;
            }
        }
        return List.of();
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
