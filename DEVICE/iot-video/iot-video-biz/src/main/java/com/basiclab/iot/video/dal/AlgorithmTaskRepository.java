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
        int offset = Math.max(0, (pageNo - 1) * pageSize);
        String like = search != null && !search.isBlank() ? "%" + search.trim() + "%" : null;
        StringBuilder sql = new StringBuilder(SELECT_TASK + " WHERE 1=1");
        List<Object> args = new ArrayList<>();
        if (taskType != null && !taskType.isBlank()) {
            sql.append(" AND t.task_type = ?");
            args.add(taskType.trim());
        }
        if (like != null) {
            sql.append(" AND (t.task_name ILIKE ? OR t.task_code ILIKE ?)");
            args.add(like);
            args.add(like);
        }
        sql.append(" ORDER BY t.id DESC LIMIT ? OFFSET ?");
        args.add(pageSize);
        args.add(offset);
        List<AlgorithmTaskRow> rows = jdbc.query(sql.toString(), ROW_MAPPER, args.toArray());
        rows.forEach(this::attachDevices);
        return rows;
    }

    public long count(String search, String taskType) {
        String like = search != null && !search.isBlank() ? "%" + search.trim() + "%" : null;
        StringBuilder sql = new StringBuilder("SELECT COUNT(*) FROM algorithm_task t WHERE 1=1");
        List<Object> args = new ArrayList<>();
        if (taskType != null && !taskType.isBlank()) {
            sql.append(" AND t.task_type = ?");
            args.add(taskType.trim());
        }
        if (like != null) {
            sql.append(" AND (t.task_name ILIKE ? OR t.task_code ILIKE ?)");
            args.add(like);
            args.add(like);
        }
        Long total = jdbc.queryForObject(sql.toString(), Long.class, args.toArray());
        return total != null ? total : 0L;
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
