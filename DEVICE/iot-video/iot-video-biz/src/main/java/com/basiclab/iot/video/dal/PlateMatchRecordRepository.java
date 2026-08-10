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

public class PlateMatchRecordRepository {



    private final JdbcTemplate jdbc;



    public Map<String, Object> insert(

            Long taskId,

            String taskName,

            String deviceId,

            String deviceName,

            Integer libraryId,

            String libraryName,

            String plateNo,

            String plateColor,

            String plateImagePath,

            boolean matched,

            String correlationId,

            String taskType,

            Float detectConf

    ) {

        Timestamp now = Timestamp.from(Instant.now());

        Long id = jdbc.queryForObject(

                """

                INSERT INTO plate_match_record (

                  task_id, task_name, device_id, device_name, library_id, library_name,

                  plate_no, plate_color, plate_image_path, matched, detect_conf,

                  correlation_id, task_type, status, created_at

                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'success', ?)

                RETURNING id

                """,

                Long.class,

                taskId,

                taskName,

                deviceId,

                deviceName,

                libraryId,

                libraryName,

                plateNo,

                plateColor,

                plateImagePath,

                matched,

                detectConf,

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

        row.put("plate_no", plateNo);

        row.put("plate_color", plateColor);

        row.put("plate_image_path", plateImagePath);

        row.put("matched", matched);

        row.put("matched_plate_entry_id", null);

        row.put("matched_owner_name", null);

        row.put("detect_conf", detectConf);

        row.put("alert_id", null);

        row.put("correlation_id", correlationId);

        row.put("task_type", taskType);

        row.put("status", "success");

        row.put("error_message", null);

        row.put("created_at", now.toInstant().toString());

        return row;

    }

    public java.util.List<Map<String, Object>> listByCorrelationId(String correlationId) {
        return jdbc.queryForList(
                "SELECT * FROM plate_match_record WHERE correlation_id = ? ORDER BY id ASC",
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
        out.put("plate_no", row.get("plate_no"));
        out.put("plate_color", row.get("plate_color"));
        out.put("plate_image_path", row.get("plate_image_path"));
        out.put("matched", row.get("matched"));
        out.put("matched_plate_entry_id", row.get("matched_plate_entry_id"));
        out.put("matched_owner_name", row.get("matched_owner_name"));
        out.put("detect_conf", row.get("detect_conf"));
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

}

