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
public class RecordFileRepository {

    private final JdbcTemplate jdbc;

    public long count(int spaceId, String deviceId, String search, Timestamp start, Timestamp end) {
        StringBuilder sql = new StringBuilder("SELECT COUNT(*) FROM record_file WHERE space_id = ?");
        List<Object> args = new ArrayList<>();
        args.add(spaceId);
        filters(sql, args, deviceId, search, start, end);
        Long total = jdbc.queryForObject(sql.toString(), Long.class, args.toArray());
        return total != null ? total : 0L;
    }

    public List<Map<String, Object>> list(int spaceId, String deviceId, int pageNo, int pageSize,
                                          String search, Timestamp start, Timestamp end) {
        int offset = Math.max(0, (pageNo - 1) * pageSize);
        StringBuilder sql = new StringBuilder("SELECT * FROM record_file WHERE space_id = ?");
        List<Object> args = new ArrayList<>();
        args.add(spaceId);
        filters(sql, args, deviceId, search, start, end);
        sql.append(" ORDER BY event_time DESC LIMIT ? OFFSET ?");
        args.add(pageSize);
        args.add(offset);
        return jdbc.query(sql.toString(), (rs, rowNum) -> fileRow(rs), args.toArray());
    }

    public List<String> listDates(int spaceId, String deviceId) {
        StringBuilder sql = new StringBuilder(
                "SELECT DISTINCT to_char(event_time, 'YYYY-MM-DD') AS d FROM record_file WHERE space_id = ?"
        );
        List<Object> args = new ArrayList<>();
        args.add(spaceId);
        if (deviceId != null && !deviceId.isBlank()) {
            sql.append(" AND device_id = ?");
            args.add(deviceId.trim());
        }
        sql.append(" ORDER BY d DESC");
        return jdbc.query(sql.toString(), (rs, rowNum) -> rs.getString("d"), args.toArray());
    }

    public List<Map<String, Object>> listByDate(int spaceId, String date, String deviceId) {
        StringBuilder sql = new StringBuilder(
                "SELECT * FROM record_file WHERE space_id = ? AND event_time::date = ?::date"
        );
        List<Object> args = new ArrayList<>();
        args.add(spaceId);
        args.add(date);
        if (deviceId != null && !deviceId.isBlank()) {
            sql.append(" AND device_id = ?");
            args.add(deviceId.trim());
        }
        sql.append(" ORDER BY event_time ASC");
        return jdbc.query(sql.toString(), (rs, rowNum) -> fileRow(rs), args.toArray());
    }

    public Optional<Map<String, Object>> findByObjectName(int spaceId, String objectName) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM record_file WHERE space_id = ? AND object_name = ? LIMIT 1",
                (rs, rowNum) -> fileRow(rs),
                spaceId, objectName
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public void deleteByObjectNames(int spaceId, List<String> objectNames) {
        if (objectNames == null || objectNames.isEmpty()) {
            return;
        }
        for (String name : objectNames) {
            jdbc.update("DELETE FROM record_file WHERE space_id = ? AND object_name = ?", spaceId, name);
        }
    }

    public boolean existsByDeviceAndObjectName(String deviceId, String objectName) {
        Long total = jdbc.queryForObject(
                "SELECT COUNT(*) FROM record_file WHERE device_id = ? AND object_name = ?",
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
                    "DELETE FROM record_file WHERE space_id = ? AND device_id = ? AND event_time < ?",
                    spaceId,
                    deviceId,
                    cutoff
            );
        }
        return jdbc.update(
                "DELETE FROM record_file WHERE space_id = ? AND event_time < ?",
                spaceId,
                cutoff
        );
    }

    public Optional<Map<String, Object>> findAlertSegment(String deviceId, int alertId) {
        List<Map<String, Object>> rows = jdbc.query(
                """
                SELECT rf.*, rs.id AS space_id, a.id AS alert_id
                FROM alert a
                JOIN record_space rs ON rs.device_id = a.device_id
                JOIN record_file rf ON rf.space_id = rs.id AND rf.device_id = a.device_id
                WHERE a.device_id = ? AND a.id = ?
                  AND rf.event_time <= a.alert_time
                ORDER BY rf.event_time DESC
                LIMIT 1
                """,
                (rs, rowNum) -> {
                    Map<String, Object> row = fileRow(rs);
                    row.put("alert_id", rs.getInt("alert_id"));
                    return row;
                },
                deviceId, alertId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    private static void filters(StringBuilder sql, List<Object> args, String deviceId, String search,
                                Timestamp start, Timestamp end) {
        if (deviceId != null && !deviceId.isBlank()) {
            sql.append(" AND device_id = ?");
            args.add(deviceId.trim());
        }
        if (search != null && !search.isBlank()) {
            sql.append(" AND filename ILIKE ?");
            args.add("%" + search.trim() + "%");
        }
        if (start != null) {
            sql.append(" AND event_time >= ?");
            args.add(start);
        }
        if (end != null) {
            sql.append(" AND event_time <= ?");
            args.add(end);
        }
    }

    private static Map<String, Object> fileRow(java.sql.ResultSet rs) throws java.sql.SQLException {
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
        row.put("thumbnail_url", rs.getString("thumbnail_url"));
        row.put("duration", JdbcValues.getInteger(rs, "duration"));
        row.put("event_time", rs.getTimestamp("event_time") != null ? rs.getTimestamp("event_time").toInstant().toString() : null);
        row.put("source", rs.getString("source"));
        return row;
    }
}
