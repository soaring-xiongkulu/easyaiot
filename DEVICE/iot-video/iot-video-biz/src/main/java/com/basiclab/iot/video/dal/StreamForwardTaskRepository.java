package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.domain.StreamForwardTaskRow;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class StreamForwardTaskRepository {

    private static final String SELECT_COLUMNS = """
            id, task_name, task_code, output_format, output_quality, output_bitrate,
            status, is_enabled, exception_reason, service_server_ip, service_port,
            service_process_id, service_last_heartbeat, service_log_path,
            schedule_policy, prefer_gpu, target_node_id, node_id, device_deployments,
            total_streams, last_process_time, last_success_time, description,
            created_at, updated_at
            """;

    private final JdbcTemplate jdbc;

    private static final RowMapper<StreamForwardTaskRow> ROW_MAPPER = new RowMapper<>() {
        @Override
        public StreamForwardTaskRow mapRow(ResultSet rs, int rowNum) throws SQLException {
            StreamForwardTaskRow row = new StreamForwardTaskRow();
            row.setId(rs.getLong("id"));
            row.setTaskName(rs.getString("task_name"));
            row.setTaskCode(rs.getString("task_code"));
            row.setOutputFormat(rs.getString("output_format"));
            row.setOutputQuality(rs.getString("output_quality"));
            row.setOutputBitrate(rs.getString("output_bitrate"));
            row.setStatus(rs.getInt("status"));
            row.setIsEnabled(rs.getBoolean("is_enabled"));
            row.setExceptionReason(rs.getString("exception_reason"));
            row.setServiceServerIp(rs.getString("service_server_ip"));
            int sp = rs.getInt("service_port");
            row.setServicePort(rs.wasNull() ? null : sp);
            int pid = rs.getInt("service_process_id");
            row.setServiceProcessId(rs.wasNull() ? null : pid);
            Timestamp hb = rs.getTimestamp("service_last_heartbeat");
            row.setServiceLastHeartbeat(hb != null ? hb.toInstant() : null);
            row.setServiceLogPath(rs.getString("service_log_path"));
            row.setSchedulePolicy(rs.getString("schedule_policy"));
            row.setPreferGpu(rs.getBoolean("prefer_gpu"));
            long tni = rs.getLong("target_node_id");
            row.setTargetNodeId(rs.wasNull() ? null : tni);
            long ni = rs.getLong("node_id");
            row.setNodeId(rs.wasNull() ? null : ni);
            row.setDeviceDeployments(rs.getString("device_deployments"));
            row.setTotalStreams(rs.getInt("total_streams"));
            Timestamp lpt = rs.getTimestamp("last_process_time");
            row.setLastProcessTime(lpt != null ? lpt.toInstant() : null);
            Timestamp lst = rs.getTimestamp("last_success_time");
            row.setLastSuccessTime(lst != null ? lst.toInstant() : null);
            row.setDescription(rs.getString("description"));
            Timestamp ca = rs.getTimestamp("created_at");
            row.setCreatedAt(ca != null ? ca.toInstant() : null);
            Timestamp ua = rs.getTimestamp("updated_at");
            row.setUpdatedAt(ua != null ? ua.toInstant() : null);
            return row;
        }
    };

    public List<StreamForwardTaskRow> findEnabledLocal() {
        List<StreamForwardTaskRow> rows = jdbc.query(
                "SELECT " + SELECT_COLUMNS + """
                 FROM stream_forward_task
                 WHERE is_enabled = true
                   AND COALESCE(schedule_policy, 'local') = 'local'
                 ORDER BY id ASC
                """,
                ROW_MAPPER
        );
        rows.forEach(this::attachDevices);
        return rows;
    }

    /** Enabled tasks with auto/node schedule (cluster health migration scan set). */
    public List<StreamForwardTaskRow> findEnabledRemoteCapable() {
        List<StreamForwardTaskRow> rows = jdbc.query(
                "SELECT " + SELECT_COLUMNS + """
                 FROM stream_forward_task
                 WHERE is_enabled = true
                   AND COALESCE(schedule_policy, 'local') IN ('auto', 'node')
                 ORDER BY id ASC
                """,
                ROW_MAPPER
        );
        rows.forEach(this::attachDevices);
        return rows;
    }

    public Optional<StreamForwardTaskRow> findById(long id) {
        List<StreamForwardTaskRow> rows = jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM stream_forward_task WHERE id = ?",
                ROW_MAPPER,
                id
        );
        if (rows.isEmpty()) {
            return Optional.empty();
        }
        StreamForwardTaskRow row = rows.get(0);
        attachDevices(row);
        return Optional.of(row);
    }

    private void attachDevices(StreamForwardTaskRow row) {
        List<String> ids = new ArrayList<>();
        List<String> names = new ArrayList<>();
        jdbc.query(
                """
                SELECT d.id, d.name
                FROM stream_forward_task_device sftd
                JOIN device d ON d.id = sftd.device_id
                WHERE sftd.stream_forward_task_id = ?
                ORDER BY d.id
                """,
                rs -> {
                    ids.add(rs.getString("id"));
                    names.add(rs.getString("name"));
                },
                row.getId()
        );
        row.setDeviceIds(ids);
        row.setDeviceNames(names);
    }

    public void updateEnabled(long id, boolean enabled, Instant lastSuccessTime) {
        jdbc.update(
                """
                UPDATE stream_forward_task
                SET is_enabled = ?, last_success_time = ?, updated_at = NOW()
                WHERE id = ?
                """,
                enabled,
                lastSuccessTime != null ? Timestamp.from(lastSuccessTime) : null,
                id
        );
    }

    public void updateServiceState(long id, boolean enabled, String logPath, Integer pid) {
        jdbc.update(
                """
                UPDATE stream_forward_task
                SET is_enabled = ?, service_log_path = ?, service_process_id = ?,
                    last_success_time = CASE WHEN ? THEN NOW() ELSE last_success_time END,
                    updated_at = NOW()
                WHERE id = ?
                """,
                enabled,
                logPath,
                pid,
                enabled,
                id
        );
    }

    public void updateRemoteDeployState(
            long id,
            boolean enabled,
            String logPath,
            Integer pid,
            Long nodeId,
            String serverIp,
            String deviceDeployments
    ) {
        jdbc.update(
                """
                UPDATE stream_forward_task
                SET is_enabled = ?, service_log_path = ?, service_process_id = ?,
                    node_id = ?, service_server_ip = ?, device_deployments = ?,
                    last_success_time = CASE WHEN ? THEN NOW() ELSE last_success_time END,
                    updated_at = NOW()
                WHERE id = ?
                """,
                enabled,
                logPath,
                pid,
                nodeId,
                serverIp,
                deviceDeployments,
                enabled,
                id
        );
    }

    public void clearRemoteBinding(long id) {
        jdbc.update(
                """
                UPDATE stream_forward_task
                SET node_id = NULL, service_process_id = NULL, service_server_ip = NULL,
                    device_deployments = NULL, updated_at = NOW()
                WHERE id = ?
                """,
                id
        );
    }

    public List<StreamForwardTaskRow> list(
            int pageNo, int pageSize, String search, String deviceId, Boolean isEnabled
    ) {
        int offset = Math.max(0, (pageNo - 1) * pageSize);
        String like = search != null && !search.isBlank() ? "%" + search.trim() + "%" : null;
        StringBuilder sql = new StringBuilder("SELECT " + SELECT_COLUMNS + " FROM stream_forward_task WHERE 1=1");
        List<Object> args = new ArrayList<>();
        if (deviceId != null && !deviceId.isBlank()) {
            sql.append("""
                     AND EXISTS (
                       SELECT 1 FROM stream_forward_task_device sftd
                       WHERE sftd.stream_forward_task_id = stream_forward_task.id
                         AND sftd.device_id = ?
                     )
                    """);
            args.add(deviceId.trim());
        }
        if (isEnabled != null) {
            sql.append(" AND is_enabled = ?");
            args.add(isEnabled);
        }
        if (like != null) {
            sql.append(" AND (task_name ILIKE ? OR task_code ILIKE ?)");
            args.add(like);
            args.add(like);
        }
        sql.append(" ORDER BY created_at DESC LIMIT ? OFFSET ?");
        args.add(pageSize);
        args.add(offset);
        List<StreamForwardTaskRow> rows = jdbc.query(sql.toString(), ROW_MAPPER, args.toArray());
        rows.forEach(this::attachDevices);
        return rows;
    }

    public long count(String search, String deviceId, Boolean isEnabled) {
        String like = search != null && !search.isBlank() ? "%" + search.trim() + "%" : null;
        StringBuilder sql = new StringBuilder("SELECT COUNT(*) FROM stream_forward_task WHERE 1=1");
        List<Object> args = new ArrayList<>();
        if (deviceId != null && !deviceId.isBlank()) {
            sql.append("""
                     AND EXISTS (
                       SELECT 1 FROM stream_forward_task_device sftd
                       WHERE sftd.stream_forward_task_id = stream_forward_task.id
                         AND sftd.device_id = ?
                     )
                    """);
            args.add(deviceId.trim());
        }
        if (isEnabled != null) {
            sql.append(" AND is_enabled = ?");
            args.add(isEnabled);
        }
        if (like != null) {
            sql.append(" AND (task_name ILIKE ? OR task_code ILIKE ?)");
            args.add(like);
            args.add(like);
        }
        Long total = jdbc.queryForObject(sql.toString(), Long.class, args.toArray());
        return total != null ? total : 0L;
    }

    public long insert(Map<String, Object> fields) {
        Long id = jdbc.queryForObject(
                """
                INSERT INTO stream_forward_task (
                    task_name, task_code, output_format, output_quality, output_bitrate,
                    description, is_enabled, total_streams, schedule_policy, prefer_gpu,
                    target_node_id, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NOW(), NOW())
                RETURNING id
                """,
                Long.class,
                fields.get("task_name"),
                fields.get("task_code"),
                fields.get("output_format"),
                fields.get("output_quality"),
                fields.get("output_bitrate"),
                fields.get("description"),
                fields.get("is_enabled"),
                fields.get("total_streams"),
                fields.get("schedule_policy"),
                fields.get("prefer_gpu"),
                fields.get("target_node_id")
        );
        return id != null ? id : 0L;
    }

    public void updateFields(long id, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE stream_forward_task SET updated_at = NOW()");
        List<Object> args = new ArrayList<>();
        for (Map.Entry<String, Object> entry : fields.entrySet()) {
            sql.append(", ").append(entry.getKey()).append(" = ?");
            args.add(entry.getValue());
        }
        sql.append(" WHERE id = ?");
        args.add(id);
        jdbc.update(sql.toString(), args.toArray());
    }

    public void delete(long id) {
        jdbc.update("DELETE FROM stream_forward_task_device WHERE stream_forward_task_id = ?", id);
        jdbc.update("DELETE FROM stream_forward_task WHERE id = ?", id);
    }

    public void replaceDevices(long taskId, List<String> deviceIds) {
        jdbc.update("DELETE FROM stream_forward_task_device WHERE stream_forward_task_id = ?", taskId);
        if (deviceIds == null) {
            return;
        }
        for (String deviceId : deviceIds) {
            jdbc.update(
                    """
                    INSERT INTO stream_forward_task_device (stream_forward_task_id, device_id, created_at)
                    VALUES (?, ?, NOW())
                    """,
                    taskId,
                    deviceId
            );
        }
    }

    public Optional<Long> findTaskIdByDeviceId(String deviceId) {
        List<Long> ids = jdbc.query(
                """
                SELECT sft.id
                FROM stream_forward_task sft
                JOIN stream_forward_task_device sftd ON sftd.stream_forward_task_id = sft.id
                WHERE sftd.device_id = ?
                ORDER BY sft.id ASC
                LIMIT 1
                """,
                (rs, rowNum) -> rs.getLong("id"),
                deviceId
        );
        return ids.isEmpty() ? Optional.empty() : Optional.of(ids.get(0));
    }

    public void updateHeartbeat(
            long id, String serverIp, Integer port, Integer processId, String logPath
    ) {
        jdbc.update(
                """
                UPDATE stream_forward_task
                SET service_last_heartbeat = NOW(),
                    service_server_ip = COALESCE(?, service_server_ip),
                    service_port = COALESCE(?, service_port),
                    service_process_id = COALESCE(?, service_process_id),
                    service_log_path = COALESCE(?, service_log_path),
                    updated_at = NOW()
                WHERE id = ?
                """,
                serverIp,
                port,
                processId,
                logPath,
                id
        );
    }

    public List<Map<String, Object>> listStreamDevices(long taskId) {
        return jdbc.query(
                """
                SELECT d.id AS device_id,
                       COALESCE(d.name, d.id) AS device_name,
                       d.rtmp_stream,
                       d.http_stream,
                       d.source,
                       d.cover_image_path
                FROM stream_forward_task_device sftd
                JOIN device d ON d.id = sftd.device_id
                WHERE sftd.stream_forward_task_id = ?
                ORDER BY d.id
                """,
                (rs, rowNum) -> {
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("device_id", rs.getString("device_id"));
                    row.put("device_name", rs.getString("device_name"));
                    row.put("rtmp_stream", rs.getString("rtmp_stream"));
                    row.put("http_stream", rs.getString("http_stream"));
                    row.put("source", rs.getString("source"));
                    row.put("cover_image_path", rs.getString("cover_image_path"));
                    return row;
                },
                taskId
        );
    }
}
