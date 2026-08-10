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
import java.util.List;
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
}
