package com.basiclab.iot.video.domain;

import lombok.Data;

import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Data
public class StreamForwardTaskRow {
    private Long id;
    private String taskName;
    private String taskCode;
    private String outputFormat;
    private String outputQuality;
    private String outputBitrate;
    private Integer status;
    private Boolean isEnabled;
    private String exceptionReason;
    private String serviceServerIp;
    private Integer servicePort;
    private Integer serviceProcessId;
    private Instant serviceLastHeartbeat;
    private String serviceLogPath;
    private String schedulePolicy;
    private Boolean preferGpu;
    private Long targetNodeId;
    private Long nodeId;
    private String deviceDeployments;
    private Integer totalStreams;
    private Instant lastProcessTime;
    private Instant lastSuccessTime;
    private String description;
    private Instant createdAt;
    private Instant updatedAt;
    private List<String> deviceIds = new ArrayList<>();
    private List<String> deviceNames = new ArrayList<>();

    public Map<String, Object> toMap() {
        Map<String, Object> m = new HashMap<>();
        m.put("id", id);
        m.put("task_name", taskName);
        m.put("task_code", taskCode);
        m.put("device_ids", deviceIds != null ? deviceIds : List.of());
        m.put("device_names", deviceNames != null ? deviceNames : List.of());
        m.put("output_format", outputFormat != null ? outputFormat : "rtmp");
        m.put("output_quality", outputQuality != null ? outputQuality : "high");
        m.put("output_bitrate", outputBitrate);
        m.put("status", status != null ? status : 0);
        m.put("is_enabled", Boolean.TRUE.equals(isEnabled));
        m.put("exception_reason", exceptionReason);
        m.put("service_server_ip", serviceServerIp);
        m.put("service_port", servicePort);
        m.put("service_process_id", serviceProcessId);
        m.put("service_last_heartbeat", formatInstant(serviceLastHeartbeat));
        m.put("service_log_path", serviceLogPath);
        m.put("schedule_policy", schedulePolicy != null ? schedulePolicy : "local");
        m.put("prefer_gpu", preferGpu != null ? preferGpu : true);
        m.put("target_node_id", targetNodeId);
        m.put("node_id", nodeId);
        m.put("device_deployments", parseDeviceDeployments());
        m.put("total_streams", totalStreams != null ? totalStreams : 0);
        m.put("last_process_time", formatInstant(lastProcessTime));
        m.put("last_success_time", formatInstant(lastSuccessTime));
        m.put("description", description);
        m.put("created_at", formatInstant(createdAt));
        m.put("updated_at", formatInstant(updatedAt));
        return m;
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> parseDeviceDeployments() {
        if (deviceDeployments == null || deviceDeployments.isBlank()) {
            return List.of();
        }
        try {
            var mapper = new com.fasterxml.jackson.databind.ObjectMapper();
            Object parsed = mapper.readValue(deviceDeployments, Object.class);
            if (parsed instanceof List<?> list) {
                List<Map<String, Object>> out = new ArrayList<>();
                for (Object item : list) {
                    if (item instanceof Map<?, ?> map) {
                        out.add((Map<String, Object>) map);
                    }
                }
                return out;
            }
        } catch (Exception ignored) {
            return List.of();
        }
        return List.of();
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
