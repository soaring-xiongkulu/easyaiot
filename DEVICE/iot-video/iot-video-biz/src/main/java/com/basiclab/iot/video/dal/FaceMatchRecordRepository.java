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
}
