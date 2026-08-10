package com.basiclab.iot.video.dal;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class DeviceSpaceRepository {

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
        jdbc.update(
                """
                INSERT INTO snap_space (space_name, device_id, save_time, is_custom_save_time, status)
                VALUES (?, ?, 1, false, 1)
                ON CONFLICT DO NOTHING
                """,
                deviceName != null ? deviceName : deviceId,
                deviceId
        );
    }

    public void createRecordSpace(String deviceId, String deviceName) {
        jdbc.update(
                """
                INSERT INTO record_space (space_name, device_id, save_time, is_custom_save_time, status)
                VALUES (?, ?, 1, false, 1)
                ON CONFLICT DO NOTHING
                """,
                deviceName != null ? deviceName : deviceId,
                deviceId
        );
    }

    private static Map<String, Object> spaceRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("space_name", rs.getString("space_name"));
        row.put("device_id", rs.getString("device_id"));
        row.put("save_time", rs.getInt("save_time"));
        row.put("is_custom_save_time", rs.getBoolean("is_custom_save_time"));
        row.put("status", rs.getInt("status"));
        return row;
    }
}
