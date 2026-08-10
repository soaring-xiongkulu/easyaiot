package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.AlertRepository;
import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class AlertHookService {

    private final AlgorithmTaskRepository taskRepository;
    private final AlertRepository alertRepository;
    private final VideoProperties videoProperties;
    private final AlertPostOrchestratorService alertPostOrchestratorService;

    public Map<String, Object> processHook(Map<String, Object> alertData) {
        if (alertData == null || alertData.isEmpty()) {
            throw new VideoBusinessException(400, "请求数据不能为空");
        }
        for (String field : new String[]{"object", "event", "device_id", "device_name"}) {
            Object v = alertData.get(field);
            if (v == null || String.valueOf(v).isBlank()) {
                throw new VideoBusinessException(400, "必填字段 " + field + " 不能为空");
            }
        }
        String deviceId = String.valueOf(alertData.get("device_id"));
        String taskType = alertData.get("task_type") != null ? String.valueOf(alertData.get("task_type")) : "realtime";
        Optional<Map<String, Object>> alertTask = taskRepository.findAlertEventTask(deviceId, taskType);
        Map<String, Object> taskRow = alertTask.orElse(null);
        boolean hasExplicitTask = alertData.get("task_id") != null || alertData.get("taskId") != null;
        if (taskRow != null || hasExplicitTask) {
            try {
                alertPostOrchestratorService.schedulePostAlertOrchestration(alertData, taskRow);
            } catch (Exception ex) {
                // non-blocking — mirror Python alert hook orchestration
            }
        }
        if (alertTask.isEmpty()) {
            return Map.of("status", "skipped", "reason", "alert_event_disabled");
        }
        if (videoProperties.getAlert().isUseDirectPersist()) {
            Map<String, Object> task = taskRow;
            Long taskId = task.get("task_id") != null ? Long.parseLong(String.valueOf(task.get("task_id"))) : null;
            String taskName = task.get("task_name") != null ? String.valueOf(task.get("task_name")) : String.valueOf(alertData.get("event"));
            long alertId = alertRepository.insertAlert(alertData, taskId, taskName);
            Map<String, Object> result = new HashMap<>();
            result.put("status", "success");
            result.put("alert_id", alertId);
            result.put("mode", "direct_persist");
            return result;
        }
        return Map.of("status", "skipped", "reason", "kafka_path_not_implemented_p0");
    }
}
