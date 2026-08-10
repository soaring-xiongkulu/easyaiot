package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class AlgorithmTaskAdminService {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final AlgorithmTaskRepository taskRepository;
    private final AlgorithmTaskLifecycleService lifecycleService;

    public AlgorithmTaskRow create(Map<String, Object> body) {
        if (body == null || body.isEmpty()) {
            throw new VideoBusinessException(400, "请求数据不能为空");
        }
        String taskName = asString(body.get("task_name"));
        if (taskName == null || taskName.isBlank()) {
            throw new VideoBusinessException(400, "任务名称不能为空");
        }
        String taskType = asString(body.getOrDefault("task_type", "realtime"));
        if (!List.of("realtime", "snap", "patrol").contains(taskType)) {
            throw new VideoBusinessException(400, "任务类型必须是 realtime、snap 或 patrol");
        }
        String schedulePolicy = asString(body.getOrDefault("schedule_policy", "local"));
        String executor = asString(body.getOrDefault("executor", "cpp"));
        lifecycleService.normalizeExecutor(executor);
        if ("cpp".equalsIgnoreCase(executor) && !"local".equalsIgnoreCase(schedulePolicy)) {
            // remote node: skip local runtime bin check (EX-REMOTE-NODE)
        }
        List<String> deviceIds = parseStringList(body.get("device_ids"));
        for (String deviceId : deviceIds) {
            taskRepository.findDevice(deviceId)
                    .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: " + deviceId));
        }
        String prefix = switch (taskType) {
            case "snap" -> "SNAP_TASK";
            case "patrol" -> "PATROL_TASK";
            default -> "REALTIME_TASK";
        };
        String taskCode = prefix + "_" + UUID.randomUUID().toString().replace("-", "").substring(0, 8).toUpperCase();
        Map<String, Object> fields = new LinkedHashMap<>();
        fields.put("task_name", taskName.trim());
        fields.put("task_code", taskCode);
        fields.put("task_type", taskType);
        fields.put("executor", executor);
        fields.put("schedule_policy", schedulePolicy);
        fields.put("is_enabled", asBoolean(body.get("is_enabled"), false));
        fields.put("extract_interval", asInt(body.get("extract_interval"), 12));
        fields.put("frame_skip", asInt(body.get("frame_skip"), 25));
        fields.put("detect_conf", asFloat(body.get("detect_conf"), 0.5f));
        fields.put("tracking_enabled", asBoolean(body.get("tracking_enabled"), false));
        fields.put("tracking_similarity_threshold", asFloat(body.get("tracking_similarity_threshold"), 0.2f));
        fields.put("tracking_max_age", asInt(body.get("tracking_max_age"), 25));
        fields.put("tracking_smooth_alpha", asFloat(body.get("tracking_smooth_alpha"), 0.25f));
        fields.put("alert_event_enabled", asBoolean(body.get("alert_event_enabled"), false));
        fields.put("alert_event_suppress_time", asInt(body.get("alert_event_suppress_time"), 5));
        fields.put("alarm_suppress_time", asInt(body.get("alarm_suppress_time"), 300));
        fields.put("face_detection_enabled", asBoolean(body.get("face_detection_enabled"),
                asBoolean(body.get("face_matching_enabled"), true)));
        fields.put("plate_detection_enabled", asBoolean(body.get("plate_detection_enabled"),
                asBoolean(body.get("plate_matching_enabled"), false)));
        fields.put("face_matching_enabled", asBoolean(body.get("face_matching_enabled"), false));
        fields.put("plate_matching_enabled", asBoolean(body.get("plate_matching_enabled"), false));
        fields.put("alert_notification_enabled", asBoolean(body.get("alert_notification_enabled"), false));
        fields.put("post_process_enabled", asBoolean(body.get("post_process_enabled"), false));
        fields.put("post_process_replicas", Math.max(1, asInt(body.get("post_process_replicas"), 1)));
        fields.put("prefer_gpu", asBoolean(body.get("prefer_gpu"), true));
        fields.put("defense_mode", asString(body.getOrDefault("defense_mode", "full")));
        fields.put("patrol_mode", asString(body.getOrDefault("patrol_mode", "pool")));
        fields.put("patrol_interval_sec", Math.max(3, asInt(body.get("patrol_interval_sec"), 10)));
        fields.put("patrol_pool_size", Math.max(1, Math.min(asInt(body.get("patrol_pool_size"), 4), 16)));
        fields.put("model_ids", toJson(body.get("model_ids")));
        fields.put("alert_class_names", toJson(body.get("alert_class_names")));
        fields.put("face_library_ids", toJson(body.get("face_library_ids")));
        fields.put("plate_library_ids", toJson(body.get("plate_library_ids")));
        fields.put("matching_business_tags", toJson(body.get("matching_business_tags")));
        fields.put("alert_notification_config", toJson(body.get("alert_notification_config")));
        fields.put("defense_schedule", toJson(body.get("defense_schedule")));
        fields.put("sam_supplement_enabled", asBoolean(body.get("sam_supplement_enabled"), false));
        fields.put("sam_supplement_config", toJson(body.get("sam_supplement_config")));
        fields.put("motion_gate_enabled", asBoolean(body.get("motion_gate_enabled"), false));
        fields.put("motion_gate_config", toJson(body.get("motion_gate_config")));
        fields.put("pose_analysis_enabled", asBoolean(body.get("pose_analysis_enabled"), false));
        fields.put("pose_analysis_config", toJson(body.get("pose_analysis_config")));
        fields.put("pose_intent_enabled", asBoolean(body.get("pose_intent_enabled"), false));
        fields.put("pose_library_ids", toJson(body.get("pose_library_ids")));
        fields.put("pose_intent_config", toJson(body.get("pose_intent_config")));
        fields.put("cron_expression", asString(body.get("cron_expression")));
        fields.put("target_node_id", body.get("target_node_id"));
        fields.put("runtime_bin_path", asString(body.get("runtime_bin_path")));
        fields.put("runtime_control_port", body.get("runtime_control_port"));
        if ("snap".equals(taskType) && (fields.get("cron_expression") == null || String.valueOf(fields.get("cron_expression")).isBlank())) {
            throw new VideoBusinessException(400, "抓拍算法任务必须指定Cron表达式");
        }
        long id = taskRepository.insert(fields);
        taskRepository.replaceDevices(id, deviceIds);
        return taskRepository.findById(id)
                .orElseThrow(() -> new VideoBusinessException(500, "创建算法任务失败"));
    }

    public AlgorithmTaskRow update(long id, Map<String, Object> body) {
        if (body == null || body.isEmpty()) {
            throw new VideoBusinessException(400, "请求数据不能为空");
        }
        AlgorithmTaskRow existing = taskRepository.findById(id)
                .orElseThrow(() -> new VideoBusinessException(404, "算法任务不存在"));
        if (Boolean.TRUE.equals(existing.getIsEnabled()) && !body.containsKey("is_enabled")) {
            throw new VideoBusinessException(400, "任务运行中，无法编辑，请先停止任务");
        }
        if (body.containsKey("device_ids")) {
            List<String> deviceIds = parseStringList(body.get("device_ids"));
            for (String deviceId : deviceIds) {
                taskRepository.findDevice(deviceId)
                        .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: " + deviceId));
            }
            taskRepository.replaceDevices(id, deviceIds);
        }
        Map<String, Object> fields = new LinkedHashMap<>();
        copyIfPresent(body, fields, "task_name");
        copyIfPresent(body, fields, "task_type");
        copyIfPresent(body, fields, "executor");
        copyIfPresent(body, fields, "schedule_policy");
        copyIfPresent(body, fields, "is_enabled");
        copyIfPresent(body, fields, "extract_interval");
        copyIfPresent(body, fields, "frame_skip");
        copyIfPresent(body, fields, "detect_conf");
        copyIfPresent(body, fields, "tracking_enabled");
        copyIfPresent(body, fields, "tracking_similarity_threshold");
        copyIfPresent(body, fields, "tracking_max_age");
        copyIfPresent(body, fields, "tracking_smooth_alpha");
        copyIfPresent(body, fields, "alert_event_enabled");
        copyIfPresent(body, fields, "alert_event_suppress_time");
        copyIfPresent(body, fields, "alarm_suppress_time");
        copyIfPresent(body, fields, "face_detection_enabled");
        copyIfPresent(body, fields, "plate_detection_enabled");
        copyIfPresent(body, fields, "face_matching_enabled");
        copyIfPresent(body, fields, "plate_matching_enabled");
        copyIfPresent(body, fields, "alert_notification_enabled");
        copyIfPresent(body, fields, "post_process_enabled");
        copyIfPresent(body, fields, "post_process_script");
        copyIfPresent(body, fields, "post_process_replicas");
        copyIfPresent(body, fields, "prefer_gpu");
        copyIfPresent(body, fields, "defense_mode");
        copyIfPresent(body, fields, "patrol_mode");
        copyIfPresent(body, fields, "patrol_interval_sec");
        copyIfPresent(body, fields, "patrol_pool_size");
        copyIfPresent(body, fields, "focus_device_id");
        copyIfPresent(body, fields, "cron_expression");
        copyIfPresent(body, fields, "target_node_id");
        copyIfPresent(body, fields, "runtime_bin_path");
        copyIfPresent(body, fields, "runtime_control_port");
        copyJsonIfPresent(body, fields, "model_ids");
        copyJsonIfPresent(body, fields, "alert_class_names");
        copyJsonIfPresent(body, fields, "face_library_ids");
        copyJsonIfPresent(body, fields, "plate_library_ids");
        copyJsonIfPresent(body, fields, "matching_business_tags");
        copyJsonIfPresent(body, fields, "alert_notification_config");
        copyJsonIfPresent(body, fields, "defense_schedule");
        copyJsonIfPresent(body, fields, "sam_supplement_config");
        copyJsonIfPresent(body, fields, "motion_gate_config");
        copyJsonIfPresent(body, fields, "pose_analysis_config");
        copyJsonIfPresent(body, fields, "pose_library_ids");
        copyJsonIfPresent(body, fields, "pose_intent_config");
        if (!fields.isEmpty()) {
            taskRepository.updateFields(id, fields);
        }
        return taskRepository.findById(id)
                .orElseThrow(() -> new VideoBusinessException(500, "更新算法任务失败"));
    }

    public void delete(long id) {
        AlgorithmTaskRow task = taskRepository.findById(id)
                .orElseThrow(() -> new VideoBusinessException(404, "算法任务不存在"));
        if (Boolean.TRUE.equals(task.getIsEnabled())) {
            throw new VideoBusinessException(400, "任务运行中，无法删除，请先停止任务");
        }
        taskRepository.delete(id);
    }

    public List<Map<String, Object>> listStreams(long taskId) {
        taskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "算法任务不存在"));
        return taskRepository.listStreamDevices(taskId);
    }

    private static void copyIfPresent(Map<String, Object> from, Map<String, Object> to, String key) {
        if (from.containsKey(key)) {
            to.put(key, from.get(key));
        }
    }

    private static void copyJsonIfPresent(Map<String, Object> from, Map<String, Object> to, String key) {
        if (from.containsKey(key)) {
            to.put(key, toJson(from.get(key)));
        }
    }

    private static String asString(Object value) {
        return value == null ? null : String.valueOf(value);
    }

    private static boolean asBoolean(Object value, boolean defaultValue) {
        if (value == null) {
            return defaultValue;
        }
        if (value instanceof Boolean b) {
            return b;
        }
        return Boolean.parseBoolean(String.valueOf(value));
    }

    private static int asInt(Object value, int defaultValue) {
        if (value == null) {
            return defaultValue;
        }
        try {
            return Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }

    private static float asFloat(Object value, float defaultValue) {
        if (value == null) {
            return defaultValue;
        }
        try {
            return Float.parseFloat(String.valueOf(value));
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }

    private static List<String> parseStringList(Object raw) {
        if (raw == null) {
            return new ArrayList<>();
        }
        if (raw instanceof List<?> list) {
            List<String> out = new ArrayList<>();
            for (Object item : list) {
                if (item != null) {
                    out.add(String.valueOf(item));
                }
            }
            return out;
        }
        return new ArrayList<>();
    }

    private static String toJson(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof String s) {
            return s.isBlank() ? null : s;
        }
        try {
            return MAPPER.writeValueAsString(value);
        } catch (JsonProcessingException e) {
            return null;
        }
    }
}
