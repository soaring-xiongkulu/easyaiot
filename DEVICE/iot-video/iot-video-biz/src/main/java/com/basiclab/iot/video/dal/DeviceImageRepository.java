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
public class DeviceImageRepository {

    private final JdbcTemplate jdbc;

    public Optional<Map<String, Object>> findLatestByDevice(String deviceId) {
        List<Map<String, Object>> rows = jdbc.query(
                """
                SELECT id, filename, original_filename, path, width, height, created_at, device_id
                FROM image
                WHERE device_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (rs, rowNum) -> {
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("id", rs.getInt("id"));
                    row.put("filename", rs.getString("filename"));
                    row.put("original_filename", rs.getString("original_filename"));
                    row.put("path", rs.getString("path"));
                    row.put("width", rs.getInt("width"));
                    row.put("height", rs.getInt("height"));
                    row.put("device_id", rs.getString("device_id"));
                    if (rs.getTimestamp("created_at") != null) {
                        row.put("created_at", rs.getTimestamp("created_at").toInstant().toString());
                    }
                    return row;
                },
                deviceId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public boolean exists(int imageId) {
        Long count = jdbc.queryForObject("SELECT COUNT(*) FROM image WHERE id = ?", Long.class, imageId);
        return count != null && count > 0;
    }
}
