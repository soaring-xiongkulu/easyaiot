package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.AlertRepository;
import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.support.SendResult;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class AlertHookService {

    private final AlgorithmTaskRepository taskRepository;
    private final AlertRepository alertRepository;
    private final VideoProperties videoProperties;
    private final AlertPostOrchestratorService alertPostOrchestratorService;
    private final AlertKafkaProducer alertKafkaProducer;
    private final AlertKafkaMessageBuilder alertKafkaMessageBuilder;
    private final AlertEventKafkaSuppressor alertEventKafkaSuppressor;

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

        Map<String, Boolean> detectionSwitches = alertKafkaMessageBuilder.resolveDetectionSwitches(alertData, taskRow);

        if (videoProperties.getAlert().isUseDirectPersist()) {
            return persistDirectly(alertData, taskRow, detectionSwitches);
        }

        int suppressSeconds = resolveAlertEventSuppressSeconds(taskRow);
        if (alertEventKafkaSuppressor.shouldSuppress(deviceId, taskType, suppressSeconds)) {
            return Map.of("status", "suppressed", "reason", "alert_event_suppress_interval");
        }

        return sendViaKafka(alertData, taskRow, detectionSwitches, deviceId, taskType);
    }

    private Map<String, Object> sendViaKafka(
            Map<String, Object> alertData,
            Map<String, Object> taskRow,
            Map<String, Boolean> detectionSwitches,
            String deviceId,
            String taskType
    ) {
        Map<String, Object> message = alertKafkaMessageBuilder.buildMinimal(alertData, taskRow, detectionSwitches);
        String topic = alertKafkaProducer.resolveTopic(taskType);
        try {
            SendResult<String, String> result = alertKafkaProducer.send(topic, deviceId, message);
            Map<String, Object> out = new HashMap<>();
            out.put("status", "success");
            out.put("topic", result.getRecordMetadata().topic());
            out.put("partition", result.getRecordMetadata().partition());
            out.put("offset", result.getRecordMetadata().offset());
            out.put("mode", "kafka");
            return out;
        } catch (Exception ex) {
            // Part1 zero-fallback: commercial local must not silent-persist on Kafka failure.
            log.error("Kafka alert hook send failed: deviceId={}, error={}", deviceId, ex.getMessage());
            Map<String, Object> failed = new HashMap<>();
            failed.put("status", "failed");
            failed.put("error", ex.getMessage());
            failed.put("mode", "kafka");
            return failed;
        }
    }

    private Map<String, Object> persistDirectly(
            Map<String, Object> alertData,
            Map<String, Object> taskRow,
            Map<String, Boolean> detectionSwitches
    ) {
        Map<String, Object> task = taskRow;
        Long taskId = task.get("task_id") != null ? Long.parseLong(String.valueOf(task.get("task_id"))) : null;
        String taskName = task.get("task_name") != null ? String.valueOf(task.get("task_name")) : String.valueOf(alertData.get("event"));
        Map<String, Object> persistData = new HashMap<>(alertData);
        if (detectionSwitches != null) {
            persistData.putIfAbsent("face_detection_enabled", detectionSwitches.getOrDefault("face_detection_enabled", false));
            persistData.putIfAbsent("plate_detection_enabled", detectionSwitches.getOrDefault("plate_detection_enabled", false));
        }
        long alertId = alertRepository.insertAlert(persistData, taskId, taskName);
        Map<String, Object> result = new HashMap<>();
        result.put("status", "success");
        result.put("alert_id", alertId);
        result.put("mode", "direct_persist");
        return result;
    }

    private static int resolveAlertEventSuppressSeconds(Map<String, Object> taskRow) {
        if (taskRow == null || taskRow.get("alert_event_suppress_time") == null) {
            return 5;
        }
        try {
            return Math.max(0, Integer.parseInt(String.valueOf(taskRow.get("alert_event_suppress_time"))));
        } catch (NumberFormatException ex) {
            return 5;
        }
    }
}
