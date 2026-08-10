package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class AlgorithmTaskRepository {

    private final JdbcTemplate jdbc;

    private static final RowMapper<AlgorithmTaskRow> ROW_MAPPER = new RowMapper<>() {
        @Override
        public AlgorithmTaskRow mapRow(ResultSet rs, int rowNum) throws SQLException {
            AlgorithmTaskRow row = new AlgorithmTaskRow();
            row.setId(rs.getLong("id"));
            row.setTaskName(rs.getString("task_name"));
            row.setTaskCode(rs.getString("task_code"));
            row.setTaskType(rs.getString("task_type"));
            row.setExecutor(rs.getString("executor"));
            row.setIsEnabled(rs.getBoolean("is_enabled"));
            row.setRunStatus(rs.getString("run_status"));
            row.setAlertEventEnabled(rs.getBoolean("alert_event_enabled"));
            row.setAlertEventSuppressTime(rs.getInt("alert_event_suppress_time"));
            row.setDetectConf(rs.getFloat("detect_conf"));
            row.setModelNames(rs.getString("model_names"));
            row.setModelIds(rs.getString("model_ids"));
            int cp = rs.getInt("runtime_control_port");
            row.setRuntimeControlPort(rs.wasNull() ? null : cp);
            row.setRuntimeBinPath(rs.getString("runtime_bin_path"));
            row.setSchedulePolicy(rs.getString("schedule_policy"));
            row.setPreferGpu(rs.getBoolean("prefer_gpu"));
            int ei = rs.getInt("extract_interval");
            row.setExtractInterval(rs.wasNull() ? null : ei);
            row.setFrameSkip(rs.getInt("frame_skip"));
            row.setServiceServerIp(rs.getString("service_server_ip"));
            int sp = rs.getInt("service_port");
            row.setServicePort(rs.wasNull() ? null : sp);
            int pid = rs.getInt("service_process_id");
            row.setServiceProcessId(rs.wasNull() ? null : pid);
            Timestamp hb = rs.getTimestamp("service_last_heartbeat");
            row.setServiceLastHeartbeat(hb != null ? hb.toInstant() : null);
            row.setServiceLogPath(rs.getString("service_log_path"));
            return row;
        }
    };

    public Optional<AlgorithmTaskRow> findById(long id) {
        List<AlgorithmTaskRow> rows = jdbc.query(
                "SELECT * FROM algorithm_task WHERE id = ?",
                ROW_MAPPER,
                id
        );
        if (rows.isEmpty()) {
            return Optional.empty();
        }
        AlgorithmTaskRow row = rows.get(0);
        attachDevices(row);
        return Optional.of(row);
    }

    public List<AlgorithmTaskRow> list(int pageNo, int pageSize, String search) {
        int offset = Math.max(0, (pageNo - 1) * pageSize);
        String like = search != null && !search.isBlank() ? "%" + search.trim() + "%" : null;
        List<AlgorithmTaskRow> rows;
        if (like != null) {
            rows = jdbc.query(
                    "SELECT * FROM algorithm_task WHERE task_name ILIKE ? OR task_code ILIKE ? ORDER BY id DESC LIMIT ? OFFSET ?",
                    ROW_MAPPER,
                    like, like, pageSize, offset
            );
        } else {
            rows = jdbc.query(
                    "SELECT * FROM algorithm_task ORDER BY id DESC LIMIT ? OFFSET ?",
                    ROW_MAPPER,
                    pageSize,
                    offset
            );
        }
        rows.forEach(this::attachDevices);
        return rows;
    }

    public void updateRunState(long id, boolean enabled, String runStatus, String logPath, Integer port, Integer pid) {
        jdbc.update(
                """
                UPDATE algorithm_task
                SET is_enabled = ?, run_status = ?, service_log_path = COALESCE(?, service_log_path),
                    service_port = COALESCE(?, service_port), service_process_id = COALESCE(?, service_process_id),
                    updated_at = NOW()
                WHERE id = ?
                """,
                enabled,
                runStatus,
                logPath,
                port,
                pid,
                id
        );
    }

    public void updateHeartbeat(long id, String serverIp, Integer port, Integer processId, String logPath, String runStatus) {
        jdbc.update(
                """
                UPDATE algorithm_task
                SET service_last_heartbeat = NOW(),
                    service_server_ip = COALESCE(?, service_server_ip),
                    service_port = COALESCE(?, service_port),
                    service_process_id = COALESCE(?, service_process_id),
                    service_log_path = COALESCE(?, service_log_path),
                    run_status = COALESCE(?, run_status),
                    updated_at = NOW()
                WHERE id = ?
                """,
                serverIp,
                port,
                processId,
                logPath,
                runStatus,
                id
        );
    }

    public Optional<Map<String, Object>> findAlertEventTask(String deviceId, String taskType) {
        String tt = taskType != null ? taskType : "realtime";
        if ("snapshot".equals(tt)) {
            tt = "snap";
        }
        List<Map<String, Object>> rows = jdbc.queryForList(
                """
                SELECT t.id AS task_id, t.task_name, t.task_type,
                       t.face_detection_enabled, t.plate_detection_enabled,
                       t.alert_event_suppress_time
                FROM algorithm_task t
                JOIN algorithm_task_device atd ON atd.task_id = t.id
                WHERE atd.device_id = ?
                  AND t.alert_event_enabled = true
                  AND t.is_enabled = true
                  AND t.task_type = ?
                ORDER BY t.id ASC
                LIMIT 1
                """,
                deviceId,
                tt
        );
        return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
    }

    private void attachDevices(AlgorithmTaskRow row) {
        List<Map<String, Object>> devices = jdbc.queryForList(
                """
                SELECT d.id, COALESCE(d.name, d.id) AS name
                FROM algorithm_task_device atd
                JOIN device d ON d.id = atd.device_id
                WHERE atd.task_id = ?
                """,
                row.getId()
        );
        List<String> ids = new ArrayList<>();
        List<String> names = new ArrayList<>();
        for (Map<String, Object> d : devices) {
            ids.add(String.valueOf(d.get("id")));
            names.add(String.valueOf(d.get("name")));
        }
        row.setDeviceIds(ids);
        row.setDeviceNames(names);
    }

    public Optional<Map<String, String>> findDevice(String deviceId) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "SELECT id, name, source, ai_rtmp_stream, rtmp_stream FROM device WHERE id = ?",
                deviceId
        );
        if (rows.isEmpty()) {
            return Optional.empty();
        }
        Map<String, Object> r = rows.get(0);
        Map<String, String> out = new HashMap<>();
        out.put("id", String.valueOf(r.get("id")));
        out.put("name", r.get("name") != null ? String.valueOf(r.get("name")) : String.valueOf(r.get("id")));
        out.put("source", r.get("source") != null ? String.valueOf(r.get("source")) : "");
        out.put("ai_rtmp_stream", r.get("ai_rtmp_stream") != null ? String.valueOf(r.get("ai_rtmp_stream")) : "");
        out.put("rtmp_stream", r.get("rtmp_stream") != null ? String.valueOf(r.get("rtmp_stream")) : "");
        return Optional.of(out);
    }
}
