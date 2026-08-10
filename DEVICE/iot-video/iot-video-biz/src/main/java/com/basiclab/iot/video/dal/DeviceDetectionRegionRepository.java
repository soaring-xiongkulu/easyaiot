package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.support.JdbcValues;
import com.basiclab.iot.video.support.JsonFields;
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
