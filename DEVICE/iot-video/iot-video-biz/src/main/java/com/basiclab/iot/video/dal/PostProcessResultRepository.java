package com.basiclab.iot.video.dal;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Repository
@RequiredArgsConstructor
public class PostProcessResultRepository {

    private final JdbcTemplate jdbc;

    public Map<String, Object> list(
            long taskId,
            int pageNo,
            int pageSize,
            String deviceId,
            LocalDateTime beginDatetime,
            LocalDateTime endDatetime
    ) {
        StringBuilder where = new StringBuilder(" WHERE task_id = ?");
        List<Object> args = new ArrayList<>();
        args.add(taskId);
        if (deviceId != null && !deviceId.isBlank()) {
            where.append(" AND device_id = ?");
            args.add(deviceId.trim());
        }
        if (beginDatetime != null) {
            where.append(" AND event_time >= ?");
            args.add(beginDatetime);
        }
        if (endDatetime != null) {
            where.append(" AND event_time <= ?");
            args.add(endDatetime);
        }
        Long total = jdbc.queryForObject(
                "SELECT COUNT(*) FROM algorithm_post_process_result" + where,
                Long.class,
                args.toArray()
        );
        int offset = Math.max(0, (pageNo - 1) * pageSize);
        List<Object> pageArgs = new ArrayList<>(args);
        pageArgs.add(pageSize);
        pageArgs.add(offset);
        List<Map<String, Object>> items = jdbc.queryForList(
                """
                SELECT id, task_id, task_name, task_code, task_type, device_id, device_name,
                       frame_number, event_time, counts, events, alerts, payload, correlation_id, created_at
                FROM algorithm_post_process_result
                """ + where + " ORDER BY id DESC LIMIT ? OFFSET ?",
                pageArgs.toArray()
        );
        List<Map<String, Object>> normalized = new ArrayList<>();
        for (Map<String, Object> row : items) {
            Map<String, Object> item = new LinkedHashMap<>(row);
            normalized.add(item);
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("items", normalized);
        result.put("total", total != null ? total : 0L);
        result.put("page_no", pageNo);
        result.put("page_size", pageSize);
        return result;
    }

    /** Best-effort persist for Java YAML rule evaluations (Part2 W3). */
    public void insertIfSupported(Map<String, Object> row) {
        if (row == null || row.isEmpty()) {
            return;
        }
        try {
            jdbc.update(
                    """
                    INSERT INTO algorithm_post_process_result
                      (task_id, device_id, frame_number, correlation_id, payload, event_time, created_at)
                    VALUES (?, ?, ?, ?, ?::jsonb, NOW(), NOW())
                    """,
                    row.get("task_id"),
                    row.get("device_id"),
                    row.get("frame_number"),
                    row.get("correlation_id"),
                    new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(row.get("result"))
            );
        } catch (Exception ex) {
            // Schema variants across envs — evaluation still counted in logs/evidence.
            throw new IllegalStateException(ex.getMessage(), ex);
        }
    }
}
