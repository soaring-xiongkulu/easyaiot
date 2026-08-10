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

        return insert(

                taskId, taskName, deviceId, deviceName, libraryId, libraryName,

                plateNo, plateColor, plateImagePath, matched, null, null,

                correlationId, taskType, detectConf, "success", null, null

        );

    }



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

            Integer matchedPlateEntryId,

            String matchedOwnerName,

            String correlationId,

            String taskType,

            Float detectConf,

            String status,

            String errorMessage,

            Long alertId

    ) {

        Timestamp now = Timestamp.from(Instant.now());

        Long id = jdbc.queryForObject(

                """

                INSERT INTO plate_match_record (

                  task_id, task_name, device_id, device_name, library_id, library_name,

                  plate_no, plate_color, plate_image_path, matched, matched_plate_entry_id,

                  matched_owner_name, detect_conf, correlation_id, task_type, status, error_message, alert_id, created_at

                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

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

                matchedPlateEntryId,

                matchedOwnerName,

                detectConf,

                correlationId,

                taskType,

                status != null ? status : "success",

                errorMessage,

                alertId,

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

        row.put("matched_plate_entry_id", matchedPlateEntryId);

        row.put("matched_owner_name", matchedOwnerName);

        row.put("detect_conf", detectConf);

        row.put("alert_id", alertId);

        row.put("correlation_id", correlationId);

        row.put("task_type", taskType);

        row.put("status", status != null ? status : "success");

        row.put("error_message", errorMessage);

        row.put("created_at", now.toInstant().toString());

        return row;

    }

    public Map<String, Object> listRecords(int page, int pageSize, Integer libraryId, String deviceId,
                                           Boolean matched, String correlationId) {
        int offset = Math.max(0, (page - 1) * pageSize);
        StringBuilder sql = new StringBuilder("SELECT * FROM plate_match_record WHERE 1=1");
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
        result.put("list", items);
        result.put("total", total != null ? total : 0L);
        result.put("page", page);
        result.put("page_size", pageSize);
        return result;
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

