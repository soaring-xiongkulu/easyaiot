package com.basiclab.iot.video.dal;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

import java.sql.PreparedStatement;
import java.sql.Statement;
import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class PlaybackRepository {

    private final JdbcTemplate jdbc;

    public long count(String deviceId, String search, Timestamp start, Timestamp end) {
        StringBuilder sql = new StringBuilder("SELECT COUNT(*) FROM playback WHERE 1=1");
        List<Object> args = buildFilters(sql, deviceId, search, start, end);
        Long total = jdbc.queryForObject(sql.toString(), Long.class, args.toArray());
        return total != null ? total : 0L;
    }

    public List<Map<String, Object>> list(int pageNo, int pageSize, String deviceId, String search,
                                          Timestamp start, Timestamp end) {
        int offset = Math.max(0, (pageNo - 1) * pageSize);
        StringBuilder sql = new StringBuilder(
                "SELECT id, file_path, event_time, device_id, device_name, duration, "
                        + "thumbnail_path, file_size, created_at, updated_at FROM playback WHERE 1=1"
        );
        List<Object> args = buildFilters(sql, deviceId, search, start, end);
        sql.append(" ORDER BY event_time DESC LIMIT ? OFFSET ?");
        args.add(pageSize);
        args.add(offset);
        return jdbc.query(sql.toString(), (rs, rowNum) -> playbackRow(rs), args.toArray());
    }

    public Optional<Map<String, Object>> findById(int playbackId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM playback WHERE id = ?",
                (rs, rowNum) -> playbackRow(rs),
                playbackId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public int insert(Map<String, Object> fields) {
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbc.update(con -> {
            PreparedStatement ps = con.prepareStatement(
                    """
                    INSERT INTO playback (file_path, event_time, device_id, device_name, duration,
                        thumbnail_path, file_size, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,NOW(),NOW())
                    """,
                    Statement.RETURN_GENERATED_KEYS
            );
            int i = 1;
            ps.setString(i++, str(fields.get("file_path")));
            ps.setTimestamp(i++, (Timestamp) fields.get("event_time"));
            ps.setString(i++, str(fields.get("device_id")));
            ps.setString(i++, str(fields.get("device_name")));
            ps.setInt(i++, intVal(fields.get("duration")));
            ps.setString(i++, str(fields.get("thumbnail_path")));
            if (fields.get("file_size") == null) {
                ps.setObject(i++, null);
            } else {
                ps.setLong(i++, longVal(fields.get("file_size")));
            }
            return ps;
        }, keyHolder);
        Number key = keyHolder.getKey();
        return key != null ? key.intValue() : 0;
    }

    public void updateFields(int playbackId, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE playback SET updated_at = NOW()");
        List<Object> args = new ArrayList<>();
        for (Map.Entry<String, Object> entry : fields.entrySet()) {
            sql.append(", ").append(entry.getKey()).append(" = ?");
            args.add(entry.getValue());
        }
        sql.append(" WHERE id = ?");
        args.add(playbackId);
        jdbc.update(sql.toString(), args.toArray());
    }

    public void delete(int playbackId) {
        jdbc.update("DELETE FROM playback WHERE id = ?", playbackId);
    }

    public Map<String, Object> statistics(String deviceId, Timestamp start, Timestamp end) {
        StringBuilder sql = new StringBuilder(
                "SELECT COUNT(*) AS total_count, COALESCE(SUM(duration),0) AS total_duration, "
                        + "COALESCE(SUM(file_size),0) AS total_size FROM playback WHERE 1=1"
        );
        List<Object> args = buildFilters(sql, deviceId, null, start, end);
        return jdbc.queryForObject(sql.toString(), (rs, rowNum) -> {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("total_count", rs.getLong("total_count"));
            row.put("total_duration", rs.getLong("total_duration"));
            row.put("total_size", rs.getLong("total_size"));
            return row;
        }, args.toArray());
    }

    private List<Object> buildFilters(StringBuilder sql, String deviceId, String search,
                                      Timestamp start, Timestamp end) {
        List<Object> args = new ArrayList<>();
        if (deviceId != null && !deviceId.isBlank()) {
            sql.append(" AND device_id = ?");
            args.add(deviceId.trim());
        }
        if (search != null && !search.isBlank()) {
            String like = "%" + search.trim() + "%";
            sql.append(" AND (device_name ILIKE ? OR device_id ILIKE ? OR file_path ILIKE ?)");
            args.add(like);
            args.add(like);
            args.add(like);
        }
        if (start != null) {
            sql.append(" AND event_time >= ?");
            args.add(start);
        }
        if (end != null) {
            sql.append(" AND event_time <= ?");
            args.add(end);
        }
        return args;
    }

    private static Map<String, Object> playbackRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("file_path", rs.getString("file_path"));
        row.put("video_url", rs.getString("file_path"));
        row.put("event_time", rs.getTimestamp("event_time") != null ? rs.getTimestamp("event_time").toInstant().toString() : null);
        row.put("device_id", rs.getString("device_id"));
        row.put("device_name", rs.getString("device_name"));
        row.put("duration", rs.getInt("duration"));
        row.put("thumbnail_path", rs.getString("thumbnail_path"));
        Object fileSize = rs.getObject("file_size");
        row.put("file_size", fileSize);
        row.put("created_at", rs.getTimestamp("created_at") != null ? rs.getTimestamp("created_at").toInstant().toString() : null);
        row.put("updated_at", rs.getTimestamp("updated_at") != null ? rs.getTimestamp("updated_at").toInstant().toString() : null);
        return row;
    }

    private static String str(Object v) {
        return v == null ? null : String.valueOf(v).trim();
    }

    private static int intVal(Object v) {
        return v instanceof Number n ? n.intValue() : Integer.parseInt(String.valueOf(v));
    }

    private static long longVal(Object v) {
        return v instanceof Number n ? n.longValue() : Long.parseLong(String.valueOf(v));
    }
}
