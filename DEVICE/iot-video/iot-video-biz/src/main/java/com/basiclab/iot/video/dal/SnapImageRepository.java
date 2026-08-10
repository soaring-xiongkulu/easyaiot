package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.support.JdbcValues;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class SnapImageRepository {

    private final JdbcTemplate jdbc;

    public long countBySpace(int spaceId, String deviceId, String search, String source) {
        StringBuilder sql = new StringBuilder("SELECT COUNT(*) FROM snap_image WHERE space_id = ?");
        List<Object> args = new ArrayList<>();
        args.add(spaceId);
        imageFilters(sql, args, deviceId, search, source, null, null);
        Long total = jdbc.queryForObject(sql.toString(), Long.class, args.toArray());
        return total != null ? total : 0L;
    }

    public List<Map<String, Object>> list(int spaceId, String deviceId, int pageNo, int pageSize,
                                          String search, String source, Timestamp start, Timestamp end) {
        int offset = Math.max(0, (pageNo - 1) * pageSize);
        StringBuilder sql = new StringBuilder(
                "SELECT * FROM snap_image WHERE space_id = ?"
        );
        List<Object> args = new ArrayList<>();
        args.add(spaceId);
        imageFilters(sql, args, deviceId, search, source, start, end);
        sql.append(" ORDER BY captured_at DESC LIMIT ? OFFSET ?");
        args.add(pageSize);
        args.add(offset);
        return jdbc.query(sql.toString(), (rs, rowNum) -> imageRow(rs), args.toArray());
    }

    public Optional<Map<String, Object>> findByObjectName(int spaceId, String objectName) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM snap_image WHERE space_id = ? AND object_name = ? LIMIT 1",
                (rs, rowNum) -> imageRow(rs),
                spaceId, objectName
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public void deleteByObjectNames(int spaceId, List<String> objectNames) {
        if (objectNames == null || objectNames.isEmpty()) {
            return;
        }
        for (String name : objectNames) {
            jdbc.update("DELETE FROM snap_image WHERE space_id = ? AND object_name = ?", spaceId, name);
        }
    }

    public long countBySpaceId(int spaceId) {
        Long total = jdbc.queryForObject("SELECT COUNT(*) FROM snap_image WHERE space_id = ?", Long.class, spaceId);
        return total != null ? total : 0L;
    }

    public boolean existsByDeviceAndObjectName(String deviceId, String objectName) {
        Long total = jdbc.queryForObject(
                "SELECT COUNT(*) FROM snap_image WHERE device_id = ? AND object_name = ?",
                Long.class,
                deviceId,
                objectName
        );
        return total != null && total > 0;
    }

    public int deleteExpiredBefore(int spaceId, String deviceId, Timestamp cutoff) {
        if (cutoff == null) {
            return 0;
        }
        if (deviceId != null && !deviceId.isBlank()) {
            return jdbc.update(
                    "DELETE FROM snap_image WHERE space_id = ? AND device_id = ? AND captured_at < ?",
                    spaceId,
                    deviceId,
                    cutoff
            );
        }
        return jdbc.update(
                "DELETE FROM snap_image WHERE space_id = ? AND captured_at < ?",
                spaceId,
                cutoff
        );
    }

    private static void imageFilters(StringBuilder sql, List<Object> args, String deviceId, String search,
                                     String source, Timestamp start, Timestamp end) {
        if (deviceId != null && !deviceId.isBlank()) {
            sql.append(" AND device_id = ?");
            args.add(deviceId.trim());
        }
        if (search != null && !search.isBlank()) {
            sql.append(" AND filename ILIKE ?");
            args.add("%" + search.trim() + "%");
        }
        if (source != null && !source.isBlank()) {
            sql.append(" AND source = ?");
            args.add(source.trim());
        }
        if (start != null) {
            sql.append(" AND captured_at >= ?");
            args.add(start);
        }
        if (end != null) {
            sql.append(" AND captured_at <= ?");
            args.add(end);
        }
    }

    private static Map<String, Object> imageRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("space_id", rs.getInt("space_id"));
        row.put("device_id", rs.getString("device_id"));
        row.put("object_name", rs.getString("object_name"));
        row.put("bucket_name", rs.getString("bucket_name"));
        row.put("filename", rs.getString("filename"));
        row.put("file_size", JdbcValues.getLong(rs, "file_size"));
        row.put("content_type", rs.getString("content_type"));
        row.put("url", rs.getString("url"));
        row.put("captured_at", rs.getTimestamp("captured_at") != null ? rs.getTimestamp("captured_at").toInstant().toString() : null);
        row.put("task_id", JdbcValues.getInteger(rs, "task_id"));
        row.put("source", rs.getString("source"));
        return row;
    }
}
