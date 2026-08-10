package com.basiclab.iot.video.dal;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Map;

@Repository
@RequiredArgsConstructor
public class AlertRepository {

    private static final ZoneId SHANGHAI = ZoneId.of("Asia/Shanghai");

    private final JdbcTemplate jdbc;

    public long insertAlert(Map<String, Object> alertData, Long taskId, String taskName) {
        LocalDateTime alertTime = parseTime(alertData.get("time"));
        String information = alertData.get("information") != null ? String.valueOf(alertData.get("information")) : null;
        Long id = jdbc.queryForObject(
                """
                INSERT INTO alert (
                  object, event, region, device_id, device_name, information, time,
                  image_path, record_path, task_id, task_name, task_type, correlation_id,
                  notification_sent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                Long.class,
                String.valueOf(alertData.get("object")),
                String.valueOf(alertData.get("event")),
                alertData.get("region") != null ? String.valueOf(alertData.get("region")) : null,
                String.valueOf(alertData.get("device_id")),
                String.valueOf(alertData.get("device_name")),
                information,
                Timestamp.valueOf(alertTime),
                alertData.get("image_path") != null ? String.valueOf(alertData.get("image_path")) : null,
                alertData.get("record_path") != null ? String.valueOf(alertData.get("record_path")) : null,
                taskId,
                taskName,
                alertData.get("task_type") != null ? String.valueOf(alertData.get("task_type")) : "realtime",
                alertData.get("correlation_id") != null ? String.valueOf(alertData.get("correlation_id")) : null,
                false
        );
        return id != null ? id : 0L;
    }

    private LocalDateTime parseTime(Object raw) {
        if (raw == null) {
            return LocalDateTime.now(SHANGHAI);
        }
        if (raw instanceof LocalDateTime ldt) {
            return ldt;
        }
        String s = String.valueOf(raw).trim();
        if (s.isEmpty()) {
            return LocalDateTime.now(SHANGHAI);
        }
        try {
            return LocalDateTime.parse(s.replace(" ", "T"));
        } catch (Exception ignored) {
            return LocalDateTime.now(SHANGHAI);
        }
    }
}
