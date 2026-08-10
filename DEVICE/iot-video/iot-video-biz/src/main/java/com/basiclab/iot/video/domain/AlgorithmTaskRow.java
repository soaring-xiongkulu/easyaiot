package com.basiclab.iot.video.domain;

import lombok.Data;

import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Data
public class AlgorithmTaskRow {
    private Long id;
    private String taskName;
    private String taskCode;
    private String taskType;
    private String executor;
    private Boolean isEnabled;
    private String runStatus;
    private Boolean alertEventEnabled;
    private Integer alertEventSuppressTime;
    private Float detectConf;
    private String modelNames;
    private String modelIds;
    private Integer runtimeControlPort;
    private String runtimeBinPath;
    private String schedulePolicy;
    private Boolean preferGpu;
    private Integer extractInterval;
    private Integer frameSkip;
    private String serviceServerIp;
    private Integer servicePort;
    private Integer serviceProcessId;
    private Instant serviceLastHeartbeat;
    private String serviceLogPath;
    private List<String> deviceIds;
    private List<String> deviceNames;

    public Map<String, Object> toMap() {
        Map<String, Object> m = new HashMap<>();
        m.put("id", id);
        m.put("task_name", taskName);
        m.put("task_code", taskCode);
        m.put("task_type", taskType);
        m.put("executor", executor != null ? executor : "cpp");
        m.put("is_enabled", Boolean.TRUE.equals(isEnabled));
        m.put("run_status", runStatus != null ? runStatus : "stopped");
        m.put("alert_event_enabled", Boolean.TRUE.equals(alertEventEnabled));
        m.put("alert_event_suppress_time", alertEventSuppressTime != null ? alertEventSuppressTime : 5);
        m.put("detect_conf", detectConf != null ? detectConf : 0.5f);
        m.put("model_names", modelNames);
        m.put("model_ids", modelIds);
        m.put("runtime_control_port", runtimeControlPort);
        m.put("runtime_bin_path", runtimeBinPath);
        m.put("schedule_policy", schedulePolicy != null ? schedulePolicy : "local");
        m.put("prefer_gpu", preferGpu == null || preferGpu);
        m.put("extract_interval", extractInterval);
        m.put("frame_skip", frameSkip != null ? frameSkip : 25);
        m.put("service_server_ip", serviceServerIp);
        m.put("service_port", servicePort);
        m.put("service_process_id", serviceProcessId);
        m.put("service_last_heartbeat", serviceLastHeartbeat != null ? serviceLastHeartbeat.toString() : null);
        m.put("service_log_path", serviceLogPath);
        m.put("device_ids", deviceIds != null ? deviceIds : new ArrayList<>());
        m.put("device_names", deviceNames != null ? deviceNames : new ArrayList<>());
        return m;
    }
}
