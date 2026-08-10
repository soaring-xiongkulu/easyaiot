package com.basiclab.iot.video.dal;

import com.basiclab.iot.video.domain.AlgorithmTaskRow;
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
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class AlgorithmTaskRepository {

    private final JdbcTemplate jdbc;

    private static final String SELECT_TASK = """
            SELECT t.*, ss.space_name AS snap_space_name
            FROM algorithm_task t
            LEFT JOIN snap_space ss ON ss.id = t.space_id
            """;

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
            row.setAlertEventSuppressTime(JdbcValues.getInteger(rs, "alert_event_suppress_time"));
            row.setDetectConf(JdbcValues.getFloat(rs, "detect_conf"));
            row.setModelNames(rs.getString("model_names"));
            row.setModelIds(rs.getString("model_ids"));
            row.setRuntimeControlPort(JdbcValues.getInteger(rs, "runtime_control_port"));
            row.setRuntimeBinPath(rs.getString("runtime_bin_path"));
            row.setSchedulePolicy(rs.getString("schedule_policy"));
            row.setPreferGpu((Boolean) rs.getObject("prefer_gpu"));
            row.setExtractInterval(JdbcValues.getInteger(rs, "extract_interval"));
            row.setFrameSkip(JdbcValues.getInteger(rs, "frame_skip"));
            row.setServiceServerIp(rs.getString("service_server_ip"));
            row.setServicePort(JdbcValues.getInteger(rs, "service_port"));
            row.setServiceProcessId(JdbcValues.getInteger(rs, "service_process_id"));
            row.setServiceLastHeartbeat(getInstant(rs, "service_last_heartbeat"));
            row.setServiceLogPath(rs.getString("service_log_path"));
            row.setRtmpInputUrl(rs.getString("rtmp_input_url"));
            row.setRtmpOutputUrl(rs.getString("rtmp_output_url"));
            row.setTrackingEnabled(JdbcValues.getBoolean(rs, "tracking_enabled"));
            row.setTrackingSimilarityThreshold(JdbcValues.getFloat(rs, "tracking_similarity_threshold"));
            row.setTrackingMaxAge(JdbcValues.getInteger(rs, "tracking_max_age"));
            row.setTrackingSmoothAlpha(JdbcValues.getFloat(rs, "tracking_smooth_alpha"));
            row.setAlertClassNames(rs.getString("alert_class_names"));
            row.setFaceDetectionEnabled(JdbcValues.getBoolean(rs, "face_detection_enabled"));
            row.setPlateDetectionEnabled(JdbcValues.getBoolean(rs, "plate_detection_enabled"));
            row.setFaceMatchingEnabled(JdbcValues.getBoolean(rs, "face_matching_enabled"));
            row.setFaceLibraryIds(rs.getString("face_library_ids"));
            row.setFaceMatchingThreshold(JdbcValues.getFloat(rs, "face_matching_threshold"));
            row.setPlateMatchingEnabled(JdbcValues.getBoolean(rs, "plate_matching_enabled"));
            row.setPlateLibraryIds(rs.getString("plate_library_ids"));
            row.setMatchingBusinessTags(rs.getString("matching_business_tags"));
            row.setAlertNotificationEnabled(JdbcValues.getBoolean(rs, "alert_notification_enabled"));
            row.setAlertNotificationConfig(rs.getString("alert_notification_config"));
            row.setAlarmSuppressTime(JdbcValues.getInteger(rs, "alarm_suppress_time"));
            row.setLastNotifyTime(getInstant(rs, "last_notify_time"));
            row.setSpaceId(JdbcValues.getInteger(rs, "space_id"));
            row.setSpaceName(rs.getString("snap_space_name"));
            row.setCronExpression(rs.getString("cron_expression"));
            row.setPatrolMode(rs.getString("patrol_mode"));
            row.setPatrolIntervalSec(JdbcValues.getInteger(rs, "patrol_interval_sec"));
            row.setPatrolPoolSize(JdbcValues.getInteger(rs, "patrol_pool_size"));
            row.setFocusDeviceId(rs.getString("focus_device_id"));
            row.setStatus(JdbcValues.getInteger(rs, "status"));
            row.setExceptionReason(rs.getString("exception_reason"));
            row.setTotalFrames(JdbcValues.getInteger(rs, "total_frames"));
            row.setTotalDetections(JdbcValues.getInteger(rs, "total_detections"));
            row.setTotalCaptures(JdbcValues.getInteger(rs, "total_captures"));
            row.setLastProcessTime(getInstant(rs, "last_process_time"));
            row.setLastSuccessTime(getInstant(rs, "last_success_time"));
            row.setLastCaptureTime(getInstant(rs, "last_capture_time"));
            row.setDefenseMode(rs.getString("defense_mode"));
            row.setDefenseSchedule(rs.getString("defense_schedule"));
            row.setTargetNodeId(JdbcValues.getLong(rs, "target_node_id"));
            row.setNodeId(JdbcValues.getLong(rs, "node_id"));
            row.setSamSupplementEnabled(JdbcValues.getBoolean(rs, "sam_supplement_enabled"));
            row.setSamSupplementConfig(rs.getString("sam_supplement_config"));
            row.setMotionGateEnabled(JdbcValues.getBoolean(rs, "motion_gate_enabled"));
            row.setMotionGateConfig(rs.getString("motion_gate_config"));
            row.setPoseAnalysisEnabled(JdbcValues.getBoolean(rs, "pose_analysis_enabled"));
            row.setPoseAnalysisConfig(rs.getString("pose_analysis_config"));
            row.setPoseIntentEnabled(JdbcValues.getBoolean(rs, "pose_intent_enabled"));
            row.setPoseLibraryIds(rs.getString("pose_library_ids"));
            row.setPoseIntentThreshold(JdbcValues.getFloat(rs, "pose_intent_threshold"));
            row.setPoseIntentConfig(rs.getString("pose_intent_config"));
            row.setPostProcessEnabled(JdbcValues.getBoolean(rs, "post_process_enabled"));
            row.setPostProcessScript(rs.getString("post_process_script"));
            row.setPostProcessReplicas(JdbcValues.getInteger(rs, "post_process_replicas"));
            row.setCreatedAt(getInstant(rs, "created_at"));
            row.setUpdatedAt(getInstant(rs, "updated_at"));
            return row;
        }
    };

    public Optional<AlgorithmTaskRow> findById(long id) {
        List<AlgorithmTaskRow> rows = jdbc.query(
                SELECT_TASK + " WHERE t.id = ?",
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

    public List<AlgorithmTaskRow> findEnabledLocal() {
        List<AlgorithmTaskRow> rows = jdbc.query(
                SELECT_TASK + """
                 WHERE t.is_enabled = true
                   AND COALESCE(t.schedule_policy, 'local') = 'local'
                 ORDER BY t.id ASC
                """,
                ROW_MAPPER
        );
        rows.forEach(this::attachDevices);
        return rows;
    }

    public List<AlgorithmTaskRow> list(int pageNo, int pageSize, String search, String taskType) {
        return list(pageNo, pageSize, search, taskType, null, null);
    }

    public List<AlgorithmTaskRow> list(
            int pageNo, int pageSize, String search, String taskType, String deviceId, Boolean isEnabled
    ) {
        int offset = Math.max(0, (pageNo - 1) * pageSize);
        String like = search != null && !search.isBlank() ? "%" + search.trim() + "%" : null;
        StringBuilder sql = new StringBuilder(SELECT_TASK + " WHERE 1=1");
        List<Object> args = new ArrayList<>();
        if (taskType != null && !taskType.isBlank()) {
            sql.append(" AND t.task_type = ?");
            args.add(taskType.trim());
        }
        if (deviceId != null && !deviceId.isBlank()) {
            sql.append(" AND EXISTS (SELECT 1 FROM algorithm_task_device atd WHERE atd.task_id = t.id AND atd.device_id = ?)");
            args.add(deviceId.trim());
        }
        if (isEnabled != null) {
            sql.append(" AND t.is_enabled = ?");
            args.add(isEnabled);
        }
        if (like != null) {
            sql.append(" AND (t.task_name ILIKE ? OR t.task_code ILIKE ?)");
            args.add(like);
            args.add(like);
        }
        sql.append(" ORDER BY t.is_enabled DESC, t.updated_at DESC LIMIT ? OFFSET ?");
        args.add(pageSize);
        args.add(offset);
        List<AlgorithmTaskRow> rows = jdbc.query(sql.toString(), ROW_MAPPER, args.toArray());
        rows.forEach(this::attachDevices);
        return rows;
    }

    public long count(String search, String taskType) {
        return count(search, taskType, null, null);
    }

    public long count(String search, String taskType, String deviceId, Boolean isEnabled) {
        String like = search != null && !search.isBlank() ? "%" + search.trim() + "%" : null;
        StringBuilder sql = new StringBuilder("SELECT COUNT(*) FROM algorithm_task t WHERE 1=1");
        List<Object> args = new ArrayList<>();
        if (taskType != null && !taskType.isBlank()) {
            sql.append(" AND t.task_type = ?");
            args.add(taskType.trim());
        }
        if (deviceId != null && !deviceId.isBlank()) {
            sql.append(" AND EXISTS (SELECT 1 FROM algorithm_task_device atd WHERE atd.task_id = t.id AND atd.device_id = ?)");
            args.add(deviceId.trim());
        }
        if (isEnabled != null) {
            sql.append(" AND t.is_enabled = ?");
            args.add(isEnabled);
        }
        if (like != null) {
            sql.append(" AND (t.task_name ILIKE ? OR t.task_code ILIKE ?)");
            args.add(like);
            args.add(like);
        }
        Long total = jdbc.queryForObject(sql.toString(), Long.class, args.toArray());
        return total != null ? total : 0L;
    }

    public long insert(Map<String, Object> fields) {
        Long id = jdbc.queryForObject(
                """
                INSERT INTO algorithm_task (
                    task_name, task_code, task_type, executor, schedule_policy, is_enabled,
                    extract_interval, frame_skip, detect_conf,
                    tracking_enabled, tracking_similarity_threshold, tracking_max_age, tracking_smooth_alpha,
                    alert_event_enabled, alert_event_suppress_time, alarm_suppress_time,
                    face_detection_enabled, plate_detection_enabled,
                    face_matching_enabled, plate_matching_enabled, alert_notification_enabled,
                    post_process_enabled, post_process_replicas, prefer_gpu,
                    defense_mode, patrol_mode, patrol_interval_sec, patrol_pool_size,
                    model_ids, alert_class_names, face_library_ids, plate_library_ids,
                    matching_business_tags, alert_notification_config, defense_schedule,
                    sam_supplement_enabled, sam_supplement_config,
                    motion_gate_enabled, motion_gate_config,
                    pose_analysis_enabled, pose_analysis_config,
                    pose_intent_enabled, pose_library_ids, pose_intent_config,
                    cron_expression, target_node_id, runtime_bin_path, runtime_control_port,
                    total_frames, total_detections, total_captures,
                    run_status, status, created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    0, 0, 0,
                    'stopped', 0, NOW(), NOW()
                ) RETURNING id
                """,
                Long.class,
                fields.get("task_name"),
                fields.get("task_code"),
                fields.get("task_type"),
                fields.get("executor"),
                fields.get("schedule_policy"),
                fields.get("is_enabled"),
                fields.get("extract_interval"),
                fields.get("frame_skip"),
                fields.get("detect_conf"),
                fields.get("tracking_enabled"),
                fields.get("tracking_similarity_threshold"),
                fields.get("tracking_max_age"),
                fields.get("tracking_smooth_alpha"),
                fields.get("alert_event_enabled"),
                fields.get("alert_event_suppress_time"),
                fields.get("alarm_suppress_time"),
                fields.get("face_detection_enabled"),
                fields.get("plate_detection_enabled"),
                fields.get("face_matching_enabled"),
                fields.get("plate_matching_enabled"),
                fields.get("alert_notification_enabled"),
                fields.get("post_process_enabled"),
                fields.get("post_process_replicas"),
                fields.get("prefer_gpu"),
                fields.get("defense_mode"),
                fields.get("patrol_mode"),
                fields.get("patrol_interval_sec"),
                fields.get("patrol_pool_size"),
                fields.get("model_ids"),
                fields.get("alert_class_names"),
                fields.get("face_library_ids"),
                fields.get("plate_library_ids"),
                fields.get("matching_business_tags"),
                fields.get("alert_notification_config"),
                fields.get("defense_schedule"),
                fields.get("sam_supplement_enabled"),
                fields.get("sam_supplement_config"),
                fields.get("motion_gate_enabled"),
                fields.get("motion_gate_config"),
                fields.get("pose_analysis_enabled"),
                fields.get("pose_analysis_config"),
                fields.get("pose_intent_enabled"),
                fields.get("pose_library_ids"),
                fields.get("pose_intent_config"),
                fields.get("cron_expression"),
                fields.get("target_node_id"),
                fields.get("runtime_bin_path"),
                fields.get("runtime_control_port")
        );
        return id != null ? id : 0L;
    }

    public void updateFields(long id, Map<String, Object> fields) {
        if (fields.isEmpty()) {
            return;
        }
        StringBuilder sql = new StringBuilder("UPDATE algorithm_task SET updated_at = NOW()");
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
        jdbc.update("DELETE FROM algorithm_task_device WHERE task_id = ?", id);
        jdbc.update("DELETE FROM algorithm_task WHERE id = ?", id);
    }

    public void replaceDevices(long taskId, List<String> deviceIds) {
        jdbc.update("DELETE FROM algorithm_task_device WHERE task_id = ?", taskId);
        if (deviceIds == null) {
            return;
        }
        for (String deviceId : deviceIds) {
            jdbc.update(
                    "INSERT INTO algorithm_task_device (task_id, device_id, created_at) VALUES (?, ?, NOW())",
                    taskId,
                    deviceId
            );
        }
    }

    public List<Map<String, Object>> listStreamDevices(long taskId) {
        return jdbc.queryForList(
                """
                SELECT d.id AS device_id,
                       COALESCE(d.name, d.id) AS device_name,
                       d.http_stream,
                       d.rtmp_stream,
                       d.ai_http_stream,
                       d.ai_rtmp_stream,
                       d.source,
                       d.cover_image_path
                FROM algorithm_task_device atd
                JOIN device d ON d.id = atd.device_id
                WHERE atd.task_id = ?
                ORDER BY d.id
                """,
                taskId
        );
    }

    public void updatePatrolHeartbeat(
            long taskId,
            String serverIp,
            Integer processId,
            String logPath,
            Integer totalPatrols,
            Integer totalDetections
    ) {
        jdbc.update(
                """
                UPDATE algorithm_task
                SET service_last_heartbeat = NOW(),
                    service_server_ip = COALESCE(?, service_server_ip),
                    service_process_id = COALESCE(?, service_process_id),
                    service_log_path = COALESCE(?, service_log_path),
                    total_captures = COALESCE(?, total_captures),
                    total_detections = COALESCE(?, total_detections),
                    last_process_time = NOW(),
                    run_status = CASE WHEN run_status = 'stopped' THEN run_status ELSE 'running' END,
                    updated_at = NOW()
                WHERE id = ?
                """,
                serverIp,
                processId,
                logPath,
                totalPatrols,
                totalDetections,
                taskId
        );
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

    private static Instant getInstant(ResultSet rs, String column) throws SQLException {
        Timestamp ts = rs.getTimestamp(column);
        return ts != null ? ts.toInstant() : null;
    }
}
