package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.support.JdbcValues;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

import java.sql.PreparedStatement;
import java.sql.Statement;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Repository
@RequiredArgsConstructor
public class SnapTaskRepository {

    private final JdbcTemplate jdbc;

    public Optional<Map<String, Object>> findById(int taskId) {
        List<Map<String, Object>> rows = jdbc.query(
                """
                SELECT t.*, d.name AS device_name, s.space_name, p.pusher_name AS pusher_name
                FROM snap_task t
                LEFT JOIN device d ON d.id = t.device_id
                LEFT JOIN snap_space s ON s.id = t.space_id
                LEFT JOIN pusher p ON p.id = t.pusher_id
                WHERE t.id = ?
                """,
                (rs, rowNum) -> taskRow(rs),
                taskId
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    public long count(Integer spaceId, String deviceId, String search, Integer status) {
        StringBuilder sql = new StringBuilder("SELECT COUNT(*) FROM snap_task t WHERE 1=1");
        List<Object> args = taskFilters(sql, spaceId, deviceId, search, status);
        Long total = jdbc.queryForObject(sql.toString(), Long.class, args.toArray());
        return total != null ? total : 0L;
    }

    public List<Map<String, Object>> list(int pageNo, int pageSize, Integer spaceId, String deviceId,
                                          String search, Integer status) {
        int offset = Math.max(0, (pageNo - 1) * pageSize);
        StringBuilder sql = new StringBuilder(
                """
                SELECT t.*, d.name AS device_name, s.space_name, p.pusher_name AS pusher_name
                FROM snap_task t
                LEFT JOIN device d ON d.id = t.device_id
                LEFT JOIN snap_space s ON s.id = t.space_id
                LEFT JOIN pusher p ON p.id = t.pusher_id
                WHERE 1=1
                """
        );
        List<Object> args = taskFilters(sql, spaceId, deviceId, search, status);
        sql.append(" ORDER BY t.created_at DESC LIMIT ? OFFSET ?");
        args.add(pageSize);
        args.add(offset);
        return jdbc.query(sql.toString(), (rs, rowNum) -> taskRow(rs), args.toArray());
    }

    public int insert(Map<String, Object> fields) {
        String taskCode = "TASK_" + UUID.randomUUID().toString().replace("-", "").substring(0, 8).toUpperCase();
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbc.update(con -> {
            PreparedStatement ps = con.prepareStatement(
                    """
                    INSERT INTO snap_task (
                        task_name, task_code, space_id, device_id, capture_type, cron_expression, frame_skip,
                        algorithm_enabled, algorithm_type, algorithm_model_id, algorithm_threshold, algorithm_night_mode,
                        alarm_enabled, alarm_type, phone_number, email, notify_users, notify_methods, alarm_suppress_time,
                        auto_filename, custom_filename_prefix, is_enabled, status, run_status, total_captures
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    new String[]{"id"}
            );
            int i = 1;
            ps.setString(i++, str(fields.get("task_name")));
            ps.setString(i++, taskCode);
            ps.setInt(i++, intVal(fields.get("space_id")));
            ps.setString(i++, str(fields.get("device_id")));
            ps.setInt(i++, intOr(fields.get("capture_type"), 0));
            ps.setString(i++, strOr(fields.get("cron_expression"), "0 */5 * * * *"));
            ps.setInt(i++, intOr(fields.get("frame_skip"), 1));
            ps.setBoolean(i++, boolOr(fields.get("algorithm_enabled"), false));
            ps.setString(i++, str(fields.get("algorithm_type")));
            setNullableInt(ps, i++, fields.get("algorithm_model_id"));
            setNullableDouble(ps, i++, fields.get("algorithm_threshold"));
            ps.setBoolean(i++, boolOr(fields.get("algorithm_night_mode"), false));
            ps.setBoolean(i++, boolOr(fields.get("alarm_enabled"), false));
            ps.setInt(i++, intOr(fields.get("alarm_type"), 0));
            ps.setString(i++, str(fields.get("phone_number")));
            ps.setString(i++, str(fields.get("email")));
            ps.setString(i++, str(fields.get("notify_users")));
            ps.setString(i++, str(fields.get("notify_methods")));
            ps.setInt(i++, intOr(fields.get("alarm_suppress_time"), 300));
            ps.setBoolean(i++, boolOr(fields.get("auto_filename"), true));
            ps.setString(i++, str(fields.get("custom_filename_prefix")));
            ps.setBoolean(i++, true);
            ps.setInt(i++, 0);
            ps.setString(i++, "stopped");
            ps.setInt(i++, 0);
            return ps;
        }, keyHolder);
        Number key = keyHolder.getKey();
        return key != null ? key.intValue() : 0;
    }

    public void updateFields(int taskId, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE snap_task SET updated_at = NOW()");
        List<Object> args = new ArrayList<>();
        for (Map.Entry<String, Object> entry : fields.entrySet()) {
            sql.append(", ").append(entry.getKey()).append(" = ?");
            args.add(entry.getValue());
        }
        sql.append(" WHERE id = ?");
        args.add(taskId);
        jdbc.update(sql.toString(), args.toArray());
    }

    public void delete(int taskId) {
        jdbc.update("DELETE FROM snap_task WHERE id = ?", taskId);
    }

    public void setRunState(int taskId, boolean enabled, String runStatus) {
        jdbc.update(
                "UPDATE snap_task SET is_enabled = ?, run_status = ?, updated_at = NOW() WHERE id = ?",
                enabled, runStatus, taskId
        );
    }

    public List<Map<String, Object>> listEnabled() {
        return jdbc.query(
                """
                SELECT t.*, d.name AS device_name, s.space_name
                FROM snap_task t
                LEFT JOIN device d ON d.id = t.device_id
                LEFT JOIN snap_space s ON s.id = t.space_id
                WHERE t.is_enabled = TRUE
                ORDER BY t.id
                """,
                (rs, rowNum) -> taskRow(rs)
        );
    }

    public void recordExecutionResult(int taskId, boolean success, String exceptionReason) {
        if (success) {
            jdbc.update(
                    """
                    UPDATE snap_task
                    SET total_captures = COALESCE(total_captures, 0) + 1,
                        last_capture_time = NOW(),
                        last_success_time = NOW(),
                        status = 0,
                        exception_reason = NULL,
                        updated_at = NOW()
                    WHERE id = ?
                    """,
                    taskId
            );
        } else {
            jdbc.update(
                    """
                    UPDATE snap_task
                    SET total_captures = COALESCE(total_captures, 0) + 1,
                        last_capture_time = NOW(),
                        status = 1,
                        exception_reason = ?,
                        updated_at = NOW()
                    WHERE id = ?
                    """,
                    exceptionReason != null ? exceptionReason : "抓拍失败",
                    taskId
            );
        }
    }

    public long countBySpaceId(int spaceId) {
        Long total = jdbc.queryForObject("SELECT COUNT(*) FROM snap_task WHERE space_id = ?", Long.class, spaceId);
        return total != null ? total : 0L;
    }

    private static List<Object> taskFilters(StringBuilder sql, Integer spaceId, String deviceId,
                                            String search, Integer status) {
        List<Object> args = new ArrayList<>();
        if (spaceId != null) {
            sql.append(" AND t.space_id = ?");
            args.add(spaceId);
        }
        if (deviceId != null && !deviceId.isBlank()) {
            sql.append(" AND t.device_id = ?");
            args.add(deviceId.trim());
        }
        if (search != null && !search.isBlank()) {
            sql.append(" AND t.task_name ILIKE ?");
            args.add("%" + search.trim() + "%");
        }
        if (status != null) {
            sql.append(" AND t.status = ?");
            args.add(status);
        }
        return args;
    }

    private static Map<String, Object> taskRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getInt("id"));
        row.put("task_name", rs.getString("task_name"));
        row.put("task_code", rs.getString("task_code"));
        row.put("space_id", rs.getInt("space_id"));
        row.put("space_name", rs.getString("space_name"));
        row.put("device_id", rs.getString("device_id"));
        row.put("device_name", rs.getString("device_name"));
        row.put("capture_type", JdbcValues.getInteger(rs, "capture_type"));
        row.put("cron_expression", rs.getString("cron_expression"));
        row.put("frame_skip", JdbcValues.getInteger(rs, "frame_skip"));
        row.put("algorithm_enabled", Boolean.TRUE.equals(JdbcValues.getBoolean(rs, "algorithm_enabled")));
        row.put("algorithm_type", rs.getString("algorithm_type"));
        row.put("algorithm_model_id", JdbcValues.getInteger(rs, "algorithm_model_id"));
        row.put("algorithm_threshold", JdbcValues.getDouble(rs, "algorithm_threshold"));
        row.put("algorithm_night_mode", Boolean.TRUE.equals(JdbcValues.getBoolean(rs, "algorithm_night_mode")));
        row.put("alarm_enabled", Boolean.TRUE.equals(JdbcValues.getBoolean(rs, "alarm_enabled")));
        row.put("alarm_type", JdbcValues.getInteger(rs, "alarm_type"));
        row.put("phone_number", rs.getString("phone_number"));
        row.put("email", rs.getString("email"));
        row.put("notify_users", rs.getString("notify_users"));
        row.put("notify_methods", rs.getString("notify_methods"));
        row.put("alarm_suppress_time", JdbcValues.getInteger(rs, "alarm_suppress_time"));
        row.put("auto_filename", Boolean.TRUE.equals(JdbcValues.getBoolean(rs, "auto_filename")));
        row.put("custom_filename_prefix", rs.getString("custom_filename_prefix"));
        row.put("status", JdbcValues.getInteger(rs, "status"));
        row.put("is_enabled", Boolean.TRUE.equals(JdbcValues.getBoolean(rs, "is_enabled")));
        row.put("run_status", rs.getString("run_status"));
        row.put("exception_reason", rs.getString("exception_reason"));
        row.put("total_captures", JdbcValues.getInteger(rs, "total_captures"));
        row.put("pusher_id", JdbcValues.getInteger(rs, "pusher_id"));
        row.put("pusher_name", rs.getString("pusher_name"));
        row.put("created_at", formatTs(rs.getTimestamp("created_at")));
        row.put("updated_at", formatTs(rs.getTimestamp("updated_at")));
        row.put("last_capture_time", formatTs(rs.getTimestamp("last_capture_time")));
        row.put("last_success_time", formatTs(rs.getTimestamp("last_success_time")));
        row.put("last_notify_time", formatTs(rs.getTimestamp("last_notify_time")));
        return row;
    }

    private static String formatTs(Timestamp ts) {
        return ts != null ? ts.toInstant().toString() : null;
    }

    private static String str(Object v) {
        return v == null ? null : String.valueOf(v).trim();
    }

    private static String strOr(Object v, String d) {
        String s = str(v);
        return s == null || s.isEmpty() ? d : s;
    }

    private static int intVal(Object v) {
        return v instanceof Number n ? n.intValue() : Integer.parseInt(String.valueOf(v));
    }

    private static int intOr(Object v, int d) {
        return v == null ? d : intVal(v);
    }

    private static boolean boolOr(Object v, boolean d) {
        if (v == null) {
            return d;
        }
        if (v instanceof Boolean b) {
            return b;
        }
        return Boolean.parseBoolean(String.valueOf(v));
    }

    private static void setNullableInt(PreparedStatement ps, int index, Object v) throws java.sql.SQLException {
        if (v == null) {
            ps.setObject(index, null);
        } else {
            ps.setInt(index, intVal(v));
        }
    }

    private static void setNullableDouble(PreparedStatement ps, int index, Object v) throws java.sql.SQLException {
        if (v == null) {
            ps.setObject(index, null);
        } else {
            ps.setDouble(index, v instanceof Number n ? n.doubleValue() : Double.parseDouble(String.valueOf(v)));
        }
    }
}
