package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.support.JdbcValues;
import com.basiclab.iot.video.support.JsonFields;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class DeviceDetectionRegionRepository {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final JdbcTemplate jdbc;

    public boolean deviceExists(String deviceId) {
        Long count = jdbc.queryForObject(
                "SELECT COUNT(*) FROM device WHERE id = ?",
                Long.class,
                deviceId
        );
        return count != null && count > 0;
    }

    public List<Map<String, Object>> listByDevice(String deviceId) {
        return jdbc.query(
                """
                SELECT r.*, i.path AS image_path
                FROM device_detection_region r
                LEFT JOIN image i ON i.id = r.image_id
                WHERE r.device_id = ?
                ORDER BY r.sort_order, r.id
                """,
                this::mapRow,
                deviceId
        );
    }

    public Optional<Map<String, Object>> findById(int regionId) {
        List<Map<String, Object>> rows = jdbc.query(
                """
                SELECT r.*, i.path AS image_path
                FROM device_detection_region r
                LEFT JOIN image i ON i.id = r.image_id
                WHERE r.id = ?
                """,
                this::mapRow,
                regionId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public int insert(String deviceId, String regionName, String regionType, String pointsJson,
                      Integer imageId, String color, double opacity, boolean isEnabled, int sortOrder, String modelIdsJson) {
        Integer id = jdbc.queryForObject(
                """
                INSERT INTO device_detection_region (device_id, region_name, region_type, points, image_id, color, opacity, is_enabled, sort_order, model_ids, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
                RETURNING id
                """,
                Integer.class,
                deviceId, regionName, regionType, pointsJson, imageId, color, opacity, isEnabled, sortOrder, modelIdsJson
        );
        return id != null ? id : 0;
    }

    public void update(int regionId, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE device_detection_region SET ");
        List<Object> args = new ArrayList<>();
        int i = 0;
        for (Map.Entry<String, Object> entry : fields.entrySet()) {
            if (i++ > 0) {
                sql.append(", ");
            }
            sql.append(entry.getKey()).append(" = ?");
            args.add(entry.getValue());
        }
        sql.append(", updated_at = NOW() WHERE id = ?");
        args.add(regionId);
        jdbc.update(sql.toString(), args.toArray());
    }

    public void delete(int regionId) {
        jdbc.update("DELETE FROM device_detection_region WHERE id = ?", regionId);
    }

    public boolean hasRealtimeTasks(String deviceId) {
        Long count = jdbc.queryForObject(
                """
                SELECT COUNT(*)
                FROM algorithm_task t
                JOIN algorithm_task_device atd ON atd.task_id = t.id
                WHERE atd.device_id = ? AND t.task_type = 'realtime'
                """,
                Long.class,
                deviceId
        );
        return count != null && count > 0;
    }

    public boolean deviceHasRealtimeModelConfig(String deviceId) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                """
                SELECT t.model_ids
                FROM algorithm_task t
                JOIN algorithm_task_device atd ON atd.task_id = t.id
                WHERE atd.device_id = ? AND t.task_type = 'realtime'
                """,
                deviceId
        );
        for (Map<String, Object> row : rows) {
            Object raw = row.get("model_ids");
            if (raw == null) {
                continue;
            }
            List<Object> ids = JsonFields.parseJsonList(String.valueOf(raw));
            if (!ids.isEmpty()) {
                return true;
            }
        }
        return false;
    }

    public void updateDeviceCoverImage(String deviceId, String imagePath) {
        jdbc.update("UPDATE device SET cover_image_path = ?, updated_at = NOW() WHERE id = ?", imagePath, deviceId);
    }

    public String deviceCoverImage(String deviceId) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "SELECT cover_image_path FROM device WHERE id = ?",
                deviceId
        );
        if (rows.isEmpty()) {
            return null;
        }
        Object path = rows.get(0).get("cover_image_path");
        return path != null ? String.valueOf(path) : null;
    }

    public static String toJson(Object value) {
        if (value == null) {
            return null;
        }
        try {
            return MAPPER.writeValueAsString(value);
        } catch (Exception ex) {
            return null;
        }
    }

    private Map<String, Object> mapRow(ResultSet rs, int rowNum) throws SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("device_id", rs.getString("device_id"));
        row.put("region_name", rs.getString("region_name"));
        row.put("region_type", rs.getString("region_type"));
        row.put("points", JsonFields.parseJsonList(rs.getString("points")));
        row.put("image_id", (Integer) rs.getObject("image_id"));
        row.put("image_path", rs.getString("image_path"));
        row.put("color", rs.getString("color"));
        row.put("opacity", JdbcValues.getDouble(rs, "opacity"));
        row.put("is_enabled", rs.getBoolean("is_enabled"));
        row.put("sort_order", rs.getInt("sort_order"));
        row.put("model_ids", JsonFields.parseJsonList(rs.getString("model_ids")));
        row.put("created_at", rs.getTimestamp("created_at") != null
                ? rs.getTimestamp("created_at").toInstant().toString() : null);
        row.put("updated_at", rs.getTimestamp("updated_at") != null
                ? rs.getTimestamp("updated_at").toInstant().toString() : null);
        return row;
    }
}
