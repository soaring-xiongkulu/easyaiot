package com.basiclab.iot.video.dal;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Repository
@RequiredArgsConstructor
public class TrackRepository {

    private final JdbcTemplate jdbc;

    public List<Map<String, Object>> listSessions(String deviceId, String begin, String end, int limit) {
        StringBuilder sql = new StringBuilder("""
                SELECT id, device_id, title, started_at, ended_at, point_count, distance_m, source,
                       external_key, created_at, updated_at
                FROM device_track_session WHERE 1=1
                """);
        List<Object> args = new ArrayList<>();
        if (deviceId != null && !deviceId.isBlank()) {
            sql.append(" AND device_id = ?");
            args.add(deviceId.trim());
        }
        if (begin != null && !begin.isBlank()) {
            sql.append(" AND started_at >= ?::timestamp");
            args.add(begin.trim());
        }
        if (end != null && !end.isBlank()) {
            sql.append(" AND started_at <= ?::timestamp");
            args.add(end.trim());
        }
        sql.append(" ORDER BY started_at DESC LIMIT ?");
        args.add(Math.max(1, Math.min(limit, 500)));
        return jdbc.query(sql.toString(), (rs, rowNum) -> {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("id", rs.getLong("id"));
            row.put("device_id", rs.getString("device_id"));
            row.put("title", rs.getString("title"));
            var startedAt = rs.getTimestamp("started_at");
            row.put("started_at", startedAt != null ? startedAt.toInstant().toString() : null);
            var endedAt = rs.getTimestamp("ended_at");
            row.put("ended_at", endedAt != null ? endedAt.toInstant().toString() : null);
            row.put("point_count", rs.getInt("point_count"));
            row.put("distance_m", rs.getObject("distance_m"));
            row.put("source", rs.getString("source"));
            row.put("external_key", rs.getString("external_key"));
            var createdAt = rs.getTimestamp("created_at");
            row.put("created_at", createdAt != null ? createdAt.toInstant().toString() : null);
            var updatedAt = rs.getTimestamp("updated_at");
            row.put("updated_at", updatedAt != null ? updatedAt.toInstant().toString() : null);
            return row;
        }, args.toArray());
    }

    public List<Map<String, Object>> listPoints(Long sessionId, String deviceId, String begin, String end, int limit) {
        StringBuilder sql = new StringBuilder("""
                SELECT id, device_id, session_id, recorded_at, longitude, latitude, altitude, speed,
                       direction, accuracy_m, source, report_source, external_key, created_at
                FROM device_track_point WHERE 1=1
                """);
        List<Object> args = new ArrayList<>();
        if (sessionId != null) {
            sql.append(" AND session_id = ?");
            args.add(sessionId);
        }
        if (deviceId != null && !deviceId.isBlank()) {
            sql.append(" AND device_id = ?");
            args.add(deviceId.trim());
        }
        if (begin != null && !begin.isBlank()) {
            sql.append(" AND recorded_at >= ?::timestamp");
            args.add(begin.trim());
        }
        if (end != null && !end.isBlank()) {
            sql.append(" AND recorded_at <= ?::timestamp");
            args.add(end.trim());
        }
        sql.append(" ORDER BY recorded_at ASC LIMIT ?");
        args.add(Math.max(1, Math.min(limit, 10000)));
        return jdbc.query(sql.toString(), (rs, rowNum) -> {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("id", rs.getLong("id"));
            row.put("device_id", rs.getString("device_id"));
            long sid = rs.getLong("session_id");
            row.put("session_id", rs.wasNull() ? null : sid);
            var recordedAt = rs.getTimestamp("recorded_at");
            row.put("recorded_at", recordedAt != null ? recordedAt.toInstant().toString() : null);
            row.put("longitude", rs.getDouble("longitude"));
            row.put("latitude", rs.getDouble("latitude"));
            row.put("altitude", rs.getObject("altitude"));
            row.put("speed", rs.getObject("speed"));
            row.put("direction", rs.getObject("direction"));
            row.put("accuracy_m", rs.getObject("accuracy_m"));
            row.put("source", rs.getString("source"));
            row.put("report_source", rs.getString("report_source"));
            row.put("external_key", rs.getString("external_key"));
            var createdAt = rs.getTimestamp("created_at");
            row.put("created_at", createdAt != null ? createdAt.toInstant().toString() : null);
            return row;
        }, args.toArray());
    }
}
