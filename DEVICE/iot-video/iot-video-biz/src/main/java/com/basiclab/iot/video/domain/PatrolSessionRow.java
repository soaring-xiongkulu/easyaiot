package com.basiclab.iot.video.domain;

import com.basiclab.iot.video.support.JsonFields;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Data;

import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Data
public class PatrolSessionRow {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private Long id;
    private String sessionName;
    private String patrolMode;
    private Integer intervalSec;
    private Integer poolSize;
    private String deviceIdsJson;
    private String modelIdsJson;
    private String focusDeviceId;
    private Long algorithmTaskId;
    private Boolean alertEventEnabled;
    private Integer alertEventSuppressTime;
    private Boolean faceDetectionEnabled;
    private Boolean plateDetectionEnabled;
    private String status;
    private String exceptionReason;
    private String serviceServerIp;
    private Integer serviceProcessId;
    private Instant serviceLastHeartbeat;
    private String serviceLogPath;
    private String progressJson;
    private Integer totalPatrols;
    private Integer totalDetections;
    private Instant lastPatrolTime;
    private Instant createdAt;
    private Instant updatedAt;
    private List<String> deviceNames = new ArrayList<>();

    public Map<String, Object> toMap() {
        List<Object> deviceIds = JsonFields.parseJsonList(deviceIdsJson);
        List<Object> modelIds = JsonFields.parseJsonList(modelIdsJson);
        Object progress = JsonFields.parseJsonObject(progressJson);
        if (progress == null) {
            progress = new LinkedHashMap<>();
        }

        List<String> names = deviceNames != null ? deviceNames : List.of();
        if (names.isEmpty() && !deviceIds.isEmpty()) {
            names = deviceIds.stream().map(String::valueOf).toList();
        }

        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", id);
        m.put("session_name", sessionName);
        m.put("patrol_mode", patrolMode != null ? patrolMode : "pool");
        m.put("interval_sec", intervalSec != null ? intervalSec : 10);
        m.put("pool_size", poolSize != null ? poolSize : 4);
        m.put("device_ids", deviceIds);
        m.put("device_names", names);
        m.put("model_ids", modelIds);
        m.put("focus_device_id", focusDeviceId);
        m.put("algorithm_task_id", algorithmTaskId);
        m.put("alert_event_enabled", Boolean.TRUE.equals(alertEventEnabled));
        m.put("alert_event_suppress_time", alertEventSuppressTime != null ? alertEventSuppressTime : 5);
        m.put("face_detection_enabled", faceDetectionEnabled == null || faceDetectionEnabled);
        m.put("plate_detection_enabled", plateDetectionEnabled == null || plateDetectionEnabled);
        m.put("status", status != null ? status : "stopped");
        m.put("exception_reason", exceptionReason);
        m.put("service_server_ip", serviceServerIp);
        m.put("service_process_id", serviceProcessId);
        m.put("service_last_heartbeat", formatInstant(serviceLastHeartbeat));
        m.put("service_log_path", serviceLogPath);
        m.put("progress", progress);
        m.put("total_patrols", totalPatrols != null ? totalPatrols : 0);
        m.put("total_detections", totalDetections != null ? totalDetections : 0);
        m.put("last_patrol_time", formatInstant(lastPatrolTime));
        m.put("created_at", formatInstant(createdAt));
        m.put("updated_at", formatInstant(updatedAt));
        return m;
    }

    public static String toJsonList(List<?> values) {
        try {
            return MAPPER.writeValueAsString(values != null ? values : List.of());
        } catch (Exception e) {
            return "[]";
        }
    }

    public static String toJsonObject(Object value) {
        try {
            return MAPPER.writeValueAsString(value != null ? value : new HashMap<>());
        } catch (Exception e) {
            return "{}";
        }
    }

    private static String formatInstant(Instant instant) {
        if (instant == null) {
            return null;
        }
        String s = instant.toString();
        if (!s.endsWith("Z") && !s.contains("+")) {
            return s + "Z";
        }
        return s;
    }
}
