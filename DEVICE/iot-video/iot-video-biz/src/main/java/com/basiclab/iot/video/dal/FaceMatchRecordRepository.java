package com.basiclab.iot.video.dal;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.sql.Timestamp;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

@Repository
@RequiredArgsConstructor
public class FaceMatchRecordRepository {

    private final JdbcTemplate jdbc;

    public Map<String, Object> insert(
            Long taskId,
            String taskName,
            String deviceId,
            String deviceName,
            Integer libraryId,
            String libraryName,
            String faceImagePath,
            boolean matched,
            String correlationId,
            String taskType,
            Float threshold
    ) {
        Timestamp now = Timestamp.from(Instant.now());
        Long id = jdbc.queryForObject(
                """
                INSERT INTO face_match_record (
                  task_id, task_name, device_id, device_name, library_id, library_name,
                  face_image_path, matched, threshold, correlation_id, task_type, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'success', ?)
                RETURNING id
                """,
                Long.class,
                taskId,
                taskName,
                deviceId,
                deviceName,
                libraryId,
                libraryName,
                faceImagePath,
                matched,
                threshold,
                correlationId,
                taskType,
                now
        );
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", id != null ? id : 0L);
        row.put("task_id", taskId);
        row.put("task_name", taskName);
        row.put("device_id", deviceId);
        row.put("device_name", deviceName);
        row.put("library_id", libraryId);
        row.put("library_name", libraryName);
        row.put("face_image_path", faceImagePath);
        row.put("matched", matched);
        row.put("matched_person_name", null);
        row.put("matched_person_code", null);
        row.put("matched_face_entry_id", null);
        row.put("similarity", null);
        row.put("threshold", threshold);
        row.put("candidates", null);
        row.put("alert_id", null);
        row.put("correlation_id", correlationId);
        row.put("task_type", taskType);
        row.put("status", "success");
        row.put("error_message", null);
        row.put("created_at", now.toInstant().toString());
        return row;
    }

    public Map<String, Object> listRecords(int page, int pageSize, Integer libraryId, String deviceId,
                                          Boolean matched, String correlationId) {
        int offset = Math.max(0, (page - 1) * pageSize);
        StringBuilder sql = new StringBuilder("SELECT * FROM face_match_record WHERE 1=1");
        java.util.List<Object> args = new java.util.ArrayList<>();
        if (libraryId != null) {
            sql.append(" AND library_id = ?");
            args.add(libraryId);
        }
        if (deviceId != null && !deviceId.isBlank()) {
            sql.append(" AND device_id = ?");
            args.add(deviceId);
        }
        if (matched != null) {
            sql.append(" AND matched = ?");
            args.add(matched);
        }
        if (correlationId != null && !correlationId.isBlank()) {
            sql.append(" AND correlation_id = ?");
            args.add(correlationId);
        }
        String countSql = sql.toString().replace("SELECT *", "SELECT COUNT(*)");
        Long total = jdbc.queryForObject(countSql, Long.class, args.toArray());
        sql.append(" ORDER BY id DESC LIMIT ? OFFSET ?");
        args.add(pageSize);
        args.add(offset);
        java.util.List<Map<String, Object>> items = jdbc.queryForList(sql.toString(), args.toArray()).stream()
                .map(this::toApiMap)
                .toList();
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("data", items);
        result.put("total", total != null ? total : 0L);
        result.put("page", page);
        result.put("page_size", pageSize);
        return result;
    }

    public java.util.List<Map<String, Object>> listByCorrelationId(String correlationId) {
        return jdbc.queryForList(
                "SELECT * FROM face_match_record WHERE correlation_id = ? ORDER BY id ASC",
                correlationId
        ).stream().map(this::toApiMap).toList();
    }

    private Map<String, Object> toApiMap(Map<String, Object> row) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", row.get("id"));
        out.put("task_id", row.get("task_id"));
        out.put("task_name", row.get("task_name"));
        out.put("device_id", row.get("device_id"));
        out.put("device_name", row.get("device_name"));
        out.put("library_id", row.get("library_id"));
        out.put("library_name", row.get("library_name"));
        out.put("face_image_path", row.get("face_image_path"));
        out.put("matched", row.get("matched"));
        out.put("matched_person_name", row.get("matched_person_name"));
        out.put("matched_person_code", row.get("matched_person_code"));
        out.put("matched_face_entry_id", row.get("matched_face_entry_id"));
        out.put("similarity", row.get("similarity"));
        out.put("threshold", row.get("threshold"));
        out.put("candidates", parseJsonMaybe(row.get("candidates")));
        out.put("alert_id", row.get("alert_id"));
        out.put("correlation_id", row.get("correlation_id"));
        out.put("task_type", row.get("task_type"));
        out.put("status", row.get("status"));
        out.put("error_message", row.get("error_message"));
        Object createdAt = row.get("created_at");
        if (createdAt instanceof java.sql.Timestamp ts) {
            out.put("created_at", ts.toInstant().toString());
        } else {
            out.put("created_at", createdAt);
        }
        return out;
    }

    private Object parseJsonMaybe(Object raw) {
        if (raw == null) {
            return null;
        }
        if (!(raw instanceof String s)) {
            return raw;
        }
        String trimmed = s.trim();
        if (trimmed.isEmpty()) {
            return null;
        }
        try {
            return new com.fasterxml.jackson.databind.ObjectMapper().readValue(trimmed, Object.class);
        } catch (Exception ignored) {
            return raw;
        }
    }
}
