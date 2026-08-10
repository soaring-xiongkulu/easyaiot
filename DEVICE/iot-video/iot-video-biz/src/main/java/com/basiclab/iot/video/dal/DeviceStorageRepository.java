package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.support.JdbcValues;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class DeviceStorageRepository {

    private final JdbcTemplate jdbc;

    public Optional<Map<String, Object>> findByDeviceId(String deviceId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM device_storage_config WHERE device_id = ? LIMIT 1",
                (rs, rowNum) -> configRow(rs),
                deviceId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public void insertDefault(String deviceId) {
        // Python models.DeviceStorageConfig defaults (storage_service.get_or_create_device_storage_config)
        jdbc.update(
                """
                INSERT INTO device_storage_config (
                    device_id,
                    snap_storage_cleanup_enabled, snap_storage_cleanup_threshold, snap_storage_cleanup_ratio,
                    video_storage_cleanup_enabled, video_storage_cleanup_threshold, video_storage_cleanup_ratio
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (device_id) DO NOTHING
                """,
                deviceId, true, 0.8, 0.3, true, 0.8, 0.3
        );
    }

    public void updateFields(String deviceId, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE device_storage_config SET updated_at = NOW()");
        java.util.List<Object> args = new java.util.ArrayList<>();
        for (Map.Entry<String, Object> entry : fields.entrySet()) {
            sql.append(", ").append(entry.getKey()).append(" = ?");
            args.add(entry.getValue());
        }
        sql.append(" WHERE device_id = ?");
        args.add(deviceId);
        jdbc.update(sql.toString(), args.toArray());
    }

    public void touchLastSnapCleanupTime(String deviceId) {
        jdbc.update(
                "UPDATE device_storage_config SET last_snap_cleanup_time = NOW(), updated_at = NOW() WHERE device_id = ?",
                deviceId
        );
    }

    public void touchLastVideoCleanupTime(String deviceId) {
        jdbc.update(
                "UPDATE device_storage_config SET last_video_cleanup_time = NOW(), updated_at = NOW() WHERE device_id = ?",
                deviceId
        );
    }

    public boolean deviceExists(String deviceId) {
        Long count = jdbc.queryForObject("SELECT COUNT(*) FROM device WHERE id = ?", Long.class, deviceId);
        return count != null && count > 0;
    }

    private static Map<String, Object> configRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("device_id", rs.getString("device_id"));
        row.put("snap_storage_bucket", rs.getString("snap_storage_bucket"));
        row.put("snap_storage_max_size", JdbcValues.getLong(rs, "snap_storage_max_size"));
        row.put("snap_storage_cleanup_enabled", Boolean.TRUE.equals(JdbcValues.getBoolean(rs, "snap_storage_cleanup_enabled")));
        row.put("snap_storage_cleanup_threshold", JdbcValues.getDouble(rs, "snap_storage_cleanup_threshold"));
        row.put("snap_storage_cleanup_ratio", JdbcValues.getDouble(rs, "snap_storage_cleanup_ratio"));
        row.put("video_storage_bucket", rs.getString("video_storage_bucket"));
        row.put("video_storage_max_size", JdbcValues.getLong(rs, "video_storage_max_size"));
        row.put("video_storage_cleanup_enabled", Boolean.TRUE.equals(JdbcValues.getBoolean(rs, "video_storage_cleanup_enabled")));
        row.put("video_storage_cleanup_threshold", JdbcValues.getDouble(rs, "video_storage_cleanup_threshold"));
        row.put("video_storage_cleanup_ratio", JdbcValues.getDouble(rs, "video_storage_cleanup_ratio"));
        row.put("last_snap_cleanup_time", rs.getTimestamp("last_snap_cleanup_time") != null
                ? rs.getTimestamp("last_snap_cleanup_time").toInstant().toString() : null);
        row.put("last_video_cleanup_time", rs.getTimestamp("last_video_cleanup_time") != null
                ? rs.getTimestamp("last_video_cleanup_time").toInstant().toString() : null);
        return row;
    }
}
