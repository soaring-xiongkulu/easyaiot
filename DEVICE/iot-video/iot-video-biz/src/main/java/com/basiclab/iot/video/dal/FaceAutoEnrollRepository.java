package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.support.JsonFields;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class FaceAutoEnrollRepository {

    private final JdbcTemplate jdbc;

    public Optional<Map<String, Object>> findByLibrary(int libraryId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM face_auto_enroll_task WHERE library_id = ?",
                this::mapTask,
                libraryId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public void upsert(int libraryId, String deviceIdsJson, int durationMinutes, int captureIntervalSec, String personNamePrefix) {
        Optional<Map<String, Object>> existing = findByLibrary(libraryId);
        if (existing.isPresent()) {
            jdbc.update(
                    """
                    UPDATE face_auto_enroll_task
                    SET device_ids = ?, duration_minutes = ?, capture_interval_sec = ?, person_name_prefix = ?, updated_at = NOW()
                    WHERE library_id = ?
                    """,
                    deviceIdsJson, durationMinutes, captureIntervalSec, personNamePrefix, libraryId
            );
        } else {
            jdbc.update(
                    """
                    INSERT INTO face_auto_enroll_task (library_id, device_ids, duration_minutes, capture_interval_sec, person_name_prefix, is_running, enrolled_count, skipped_count, last_device_index, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, false, 0, 0, 0, NOW(), NOW())
                    """,
                    libraryId, deviceIdsJson, durationMinutes, captureIntervalSec, personNamePrefix
            );
        }
    }

    public void updateRunning(int libraryId, boolean running) {
        if (running) {
            jdbc.update(
                    """
                    UPDATE face_auto_enroll_task
                    SET is_running = true, started_at = NOW(),
                        expires_at = NOW() + (duration_minutes || ' minutes')::interval,
                        updated_at = NOW()
                    WHERE library_id = ?
                    """,
                    libraryId
            );
        } else {
            jdbc.update(
                    "UPDATE face_auto_enroll_task SET is_running = false, updated_at = NOW() WHERE library_id = ?",
                    libraryId
            );
        }
    }

    public Map<String, Object> enrichDeviceNames(Map<String, Object> task) {
        Map<String, Object> data = new LinkedHashMap<>(task);
        @SuppressWarnings("unchecked")
        List<Object> deviceIds = (List<Object>) task.getOrDefault("device_ids", List.of());
        List<String> names = deviceIds.stream().map(String::valueOf).map(id -> {
            List<Map<String, Object>> rows = jdbc.queryForList("SELECT name FROM device WHERE id = ?", id);
            return rows.isEmpty() ? id : String.valueOf(rows.get(0).getOrDefault("name", id));
        }).toList();
        data.put("device_names", names);
        return data;
    }

    private Map<String, Object> mapTask(ResultSet rs, int rowNum) throws SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("library_id", rs.getInt("library_id"));
        row.put("device_ids", JsonFields.parseJsonList(rs.getString("device_ids")));
        row.put("duration_minutes", rs.getInt("duration_minutes"));
        row.put("capture_interval_sec", rs.getInt("capture_interval_sec"));
        row.put("person_name_prefix", rs.getString("person_name_prefix"));
        row.put("is_running", rs.getBoolean("is_running"));
        if (rs.getTimestamp("started_at") != null) {
            row.put("started_at", rs.getTimestamp("started_at").toInstant().toString());
        }
        if (rs.getTimestamp("expires_at") != null) {
            row.put("expires_at", rs.getTimestamp("expires_at").toInstant().toString());
        }
        row.put("enrolled_count", rs.getInt("enrolled_count"));
        row.put("skipped_count", rs.getInt("skipped_count"));
        row.put("last_device_index", rs.getInt("last_device_index"));
        if (rs.getTimestamp("last_tick_at") != null) {
            row.put("last_tick_at", rs.getTimestamp("last_tick_at").toInstant().toString());
        }
        if (rs.getTimestamp("created_at") != null) {
            row.put("created_at", rs.getTimestamp("created_at").toInstant().toString());
        }
        if (rs.getTimestamp("updated_at") != null) {
            row.put("updated_at", rs.getTimestamp("updated_at").toInstant().toString());
        }
        return row;
    }
}
