package com.basiclab.iot.video.dal;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

import java.sql.PreparedStatement;
import java.sql.Statement;
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
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbc.update(con -> {
            PreparedStatement ps = con.prepareStatement(
                    """
                    INSERT INTO alert (
                      object, event, region, device_id, device_name, information, time,
                      image_path, record_path, task_id, task_name, task_type, correlation_id,
                      notification_sent
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    Statement.RETURN_GENERATED_KEYS
            );
            ps.setString(1, String.valueOf(alertData.get("object")));
            ps.setString(2, String.valueOf(alertData.get("event")));
            ps.setString(3, alertData.get("region") != null ? String.valueOf(alertData.get("region")) : null);
            ps.setString(4, String.valueOf(alertData.get("device_id")));
            ps.setString(5, String.valueOf(alertData.get("device_name")));
            ps.setString(6, information);
            ps.setTimestamp(7, Timestamp.valueOf(alertTime));
            ps.setString(8, alertData.get("image_path") != null ? String.valueOf(alertData.get("image_path")) : null);
            ps.setString(9, alertData.get("record_path") != null ? String.valueOf(alertData.get("record_path")) : null);
            if (taskId != null) {
                ps.setLong(10, taskId);
            } else {
                ps.setObject(10, null);
            }
            ps.setString(11, taskName);
            ps.setString(12, alertData.get("task_type") != null ? String.valueOf(alertData.get("task_type")) : "realtime");
            ps.setString(13, alertData.get("correlation_id") != null ? String.valueOf(alertData.get("correlation_id")) : null);
            ps.setBoolean(14, false);
            return ps;
        }, keyHolder);
        Number key = keyHolder.getKey();
        return key != null ? key.longValue() : 0L;
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
