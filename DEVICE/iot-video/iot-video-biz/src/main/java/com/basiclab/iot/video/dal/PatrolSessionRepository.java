package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.domain.PatrolSessionRow;
import com.basiclab.iot.video.support.JdbcValues;
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
import java.util.Map;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class PatrolSessionRepository {

    private static final String SELECT_COLUMNS = """
            id, session_name, patrol_mode, interval_sec, pool_size,
            device_ids, model_ids, focus_device_id, algorithm_task_id,
            alert_event_enabled, alert_event_suppress_time,
            face_detection_enabled, plate_detection_enabled,
            status, exception_reason, service_server_ip, service_process_id,
            service_last_heartbeat, service_log_path, progress_json,
            total_patrols, total_detections, last_patrol_time,
            created_at, updated_at
            """;

    private final JdbcTemplate jdbc;

    private static final RowMapper<PatrolSessionRow> ROW_MAPPER = new RowMapper<>() {
        @Override
        public PatrolSessionRow mapRow(ResultSet rs, int rowNum) throws SQLException {
            PatrolSessionRow row = new PatrolSessionRow();
            row.setId(rs.getLong("id"));
            row.setSessionName(rs.getString("session_name"));
            row.setPatrolMode(rs.getString("patrol_mode"));
            row.setIntervalSec(JdbcValues.getInteger(rs, "interval_sec"));
            row.setPoolSize(JdbcValues.getInteger(rs, "pool_size"));
            row.setDeviceIdsJson(rs.getString("device_ids"));
            row.setModelIdsJson(rs.getString("model_ids"));
            row.setFocusDeviceId(rs.getString("focus_device_id"));
            row.setAlgorithmTaskId(JdbcValues.getLong(rs, "algorithm_task_id"));
            row.setAlertEventEnabled(JdbcValues.getBoolean(rs, "alert_event_enabled"));
            row.setAlertEventSuppressTime(JdbcValues.getInteger(rs, "alert_event_suppress_time"));
            row.setFaceDetectionEnabled(JdbcValues.getBoolean(rs, "face_detection_enabled"));
            row.setPlateDetectionEnabled(JdbcValues.getBoolean(rs, "plate_detection_enabled"));
            row.setStatus(rs.getString("status"));
            row.setExceptionReason(rs.getString("exception_reason"));
            row.setServiceServerIp(rs.getString("service_server_ip"));
            row.setServiceProcessId(JdbcValues.getInteger(rs, "service_process_id"));
            row.setServiceLastHeartbeat(getInstant(rs, "service_last_heartbeat"));
            row.setServiceLogPath(rs.getString("service_log_path"));
            row.setProgressJson(rs.getString("progress_json"));
            row.setTotalPatrols(JdbcValues.getInteger(rs, "total_patrols"));
            row.setTotalDetections(JdbcValues.getInteger(rs, "total_detections"));
            row.setLastPatrolTime(getInstant(rs, "last_patrol_time"));
            row.setCreatedAt(getInstant(rs, "created_at"));
            row.setUpdatedAt(getInstant(rs, "updated_at"));
            return row;
        }
    };

    public Optional<PatrolSessionRow> findById(long id) {
        List<PatrolSessionRow> rows = jdbc.query(
                "SELECT " + SELECT_COLUMNS + " FROM patrol_session WHERE id = ?",
                ROW_MAPPER,
                id
        );
        if (rows.isEmpty()) {
            return Optional.empty();
        }
        PatrolSessionRow row = rows.get(0);
        attachDeviceNames(row);
        return Optional.of(row);
    }

    public long insert(PatrolSessionRow row) {
        Long id = jdbc.queryForObject(
                """
                INSERT INTO patrol_session (
                    session_name, patrol_mode, interval_sec, pool_size,
                    device_ids, model_ids, focus_device_id, algorithm_task_id,
                    alert_event_enabled, alert_event_suppress_time,
                    face_detection_enabled, plate_detection_enabled,
                    status, progress_json, total_patrols, total_detections,
                    created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, 0, 0,
                    NOW(), NOW()
                ) RETURNING id
                """,
                Long.class,
                row.getSessionName(),
                row.getPatrolMode() != null ? row.getPatrolMode() : "pool",
                row.getIntervalSec() != null ? row.getIntervalSec() : 10,
                row.getPoolSize() != null ? row.getPoolSize() : 4,
                row.getDeviceIdsJson(),
                row.getModelIdsJson(),
                row.getFocusDeviceId(),
                row.getAlgorithmTaskId(),
                row.getAlertEventEnabled() != null ? row.getAlertEventEnabled() : true,
                row.getAlertEventSuppressTime() != null ? row.getAlertEventSuppressTime() : 5,
                row.getFaceDetectionEnabled() != null ? row.getFaceDetectionEnabled() : true,
                row.getPlateDetectionEnabled() != null ? row.getPlateDetectionEnabled() : true,
                row.getStatus() != null ? row.getStatus() : "stopped",
                row.getProgressJson()
        );
        return id != null ? id : 0L;
    }

    public void updatePatch(long id, Map<String, Object> fields) {
        if (fields.containsKey("focus_device_id")) {
            Object raw = fields.get("focus_device_id");
            String focus = raw != null && !String.valueOf(raw).isBlank() ? String.valueOf(raw) : null;
            jdbc.update("UPDATE patrol_session SET focus_device_id = ?, updated_at = NOW() WHERE id = ?", focus, id);
        }
        if (fields.containsKey("interval_sec") && fields.get("interval_sec") != null) {
            int interval = Math.max(3, Integer.parseInt(String.valueOf(fields.get("interval_sec"))));
            jdbc.update("UPDATE patrol_session SET interval_sec = ?, updated_at = NOW() WHERE id = ?", interval, id);
        }
        if (fields.containsKey("pool_size") && fields.get("pool_size") != null) {
            int pool = Math.max(1, Math.min(Integer.parseInt(String.valueOf(fields.get("pool_size"))), 16));
            jdbc.update("UPDATE patrol_session SET pool_size = ?, updated_at = NOW() WHERE id = ?", pool, id);
        }
    }

    public void updateRunning(long id, String logPath) {
        jdbc.update(
                """
                UPDATE patrol_session
                SET status = 'running', exception_reason = NULL, service_log_path = ?,
                    updated_at = NOW()
                WHERE id = ?
                """,
                logPath,
                id
        );
    }

    public void updateStopped(long id) {
        jdbc.update(
                """
                UPDATE patrol_session
                SET status = 'stopped', service_process_id = NULL, updated_at = NOW()
                WHERE id = ?
                """,
                id
        );
    }

    public void updateError(long id, String reason) {
        jdbc.update(
                """
                UPDATE patrol_session
                SET status = 'error', exception_reason = ?, updated_at = NOW()
                WHERE id = ?
                """,
                reason,
                id
        );
    }

    public void updateHeartbeat(
            long id,
            String serverIp,
            Integer processId,
            String progressJson,
            Integer totalPatrols,
            Integer totalDetections,
            String status
    ) {
        jdbc.update(
                """
                UPDATE patrol_session
                SET service_last_heartbeat = NOW(),
                    service_server_ip = COALESCE(?, service_server_ip),
                    service_process_id = COALESCE(?, service_process_id),
                    progress_json = COALESCE(?, progress_json),
                    total_patrols = COALESCE(?, total_patrols),
                    total_detections = COALESCE(?, total_detections),
                    last_patrol_time = NOW(),
                    status = COALESCE(?, status),
                    updated_at = NOW()
                WHERE id = ?
                """,
                serverIp,
                processId,
                progressJson,
                totalPatrols,
                totalDetections,
                status,
                id
        );
    }

    public long countRunning() {
        Long count = jdbc.queryForObject(
                "SELECT COUNT(*) FROM patrol_session WHERE status = 'running'",
                Long.class
        );
        return count != null ? count : 0L;
    }

    private void attachDeviceNames(PatrolSessionRow row) {
        List<Object> deviceIds = com.basiclab.iot.video.support.JsonFields.parseJsonList(row.getDeviceIdsJson());
        if (deviceIds.isEmpty()) {
            row.setDeviceNames(List.of());
            return;
        }
        List<String> ids = deviceIds.stream().map(String::valueOf).toList();
        String placeholders = String.join(",", ids.stream().map(id -> "?").toList());
        Map<String, String> nameMap = new java.util.LinkedHashMap<>();
        jdbc.query(
                "SELECT id, name FROM device WHERE id IN (" + placeholders + ")",
                rs -> nameMap.put(rs.getString("id"), rs.getString("name")),
                ids.toArray()
        );
        List<String> ordered = new ArrayList<>();
        for (String did : ids) {
            String name = nameMap.get(did);
            ordered.add(name != null && !name.isBlank() ? name : did);
        }
        row.setDeviceNames(ordered);
    }

    private static Instant getInstant(ResultSet rs, String column) throws SQLException {
        Timestamp ts = rs.getTimestamp(column);
        return ts != null ? ts.toInstant() : null;
    }
}
