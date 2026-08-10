package com.basiclab.iot.video.dal;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Repository
@RequiredArgsConstructor
public class DeviceSpaceRepository {

    private static final String SNAP_BUCKET = "snap-space";
    private static final String RECORD_BUCKET = "record-space";

    private final JdbcTemplate jdbc;

    public Optional<Map<String, Object>> findSnapSpaceByDeviceId(String deviceId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM snap_space WHERE device_id = ? LIMIT 1",
                (rs, rowNum) -> spaceRow(rs),
                deviceId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public Optional<Map<String, Object>> findRecordSpaceByDeviceId(String deviceId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM record_space WHERE device_id = ? LIMIT 1",
                (rs, rowNum) -> spaceRow(rs),
                deviceId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public void createSnapSpace(String deviceId, String deviceName) {
        String spaceCode = "SPACE_" + UUID.randomUUID().toString().replace("-", "").substring(0, 8).toUpperCase();
        jdbc.update(
                """
                INSERT INTO snap_space (
                    space_name, space_code, bucket_name, save_mode, save_time, save_time_custom, device_id
                )
                VALUES (?, ?, ?, 0, 1, false, ?)
                ON CONFLICT (device_id) DO NOTHING
                """,
                deviceName != null ? deviceName : deviceId,
                spaceCode,
                SNAP_BUCKET,
                deviceId
        );
    }

    public void createRecordSpace(String deviceId, String deviceName) {
        String spaceCode = "RECORD_" + UUID.randomUUID().toString().replace("-", "").substring(0, 8).toUpperCase();
        jdbc.update(
                """
                INSERT INTO record_space (
                    space_name, space_code, bucket_name, save_mode, save_time, save_time_custom, device_id
                )
                VALUES (?, ?, ?, 0, 1, false, ?)
                ON CONFLICT (device_id) DO NOTHING
                """,
                deviceName != null ? deviceName : deviceId,
                spaceCode,
                RECORD_BUCKET,
                deviceId
        );
    }

    private static Map<String, Object> spaceRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("space_name", rs.getString("space_name"));
        row.put("space_code", rs.getString("space_code"));
        row.put("bucket_name", rs.getString("bucket_name"));
        row.put("save_mode", rs.getInt("save_mode"));
        row.put("device_id", rs.getString("device_id"));
        row.put("save_time", rs.getInt("save_time"));
        row.put("save_time_custom", rs.getBoolean("save_time_custom"));
        return row;
    }
}
