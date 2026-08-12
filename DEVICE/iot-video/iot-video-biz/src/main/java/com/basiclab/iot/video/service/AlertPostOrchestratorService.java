package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class AlertPostOrchestratorService {

    private final AlgorithmTaskRepository taskRepository;
    private final PostProcessService postProcessService;
    private final PostProcessSinkClient postProcessSinkClient;
    private final AlertMatchingTriggerService alertMatchingTriggerService;

    public void schedulePostAlertOrchestration(Map<String, Object> alertData, Map<String, Object> alertEventTask) {
        Map<String, Object> payload = alertData != null ? new java.util.LinkedHashMap<>(alertData) : Map.of();
        Map<String, Object> taskSnapshot = alertEventTask != null ? new java.util.LinkedHashMap<>(alertEventTask) : null;
        Thread thread = new Thread(() -> runPostAlertOrchestration(payload, taskSnapshot), "alert-post-orchestrator");
        thread.setDaemon(true);
        thread.start();
    }

    void runPostAlertOrchestration(Map<String, Object> alertData, Map<String, Object> alertEventTask) {
        try {
            AlgorithmTaskRow task = resolveTask(alertData, alertEventTask);
            if (task == null) {
                return;
            }
            if (!isCppExecutor(task)) {
                return;
            }
            String deviceId = stringOrEmpty(alertData.get("device_id"));
            if (deviceId.isEmpty()) {
                return;
            }
            String deviceName = stringOrNull(alertData.get("device_name"));
            if (deviceName == null) {
                deviceName = deviceId;
            }

            Map<String, Object> info = parseInformation(alertData.get("information"));
            List<Map<String, Object>> detections = extractDetections(info);
            int frameNumber = extractFrameNumber(info);
            double timestamp = extractTimestamp(alertData, info);
            String correlationId = stringOrNull(firstNonNull(
                    alertData.get("correlation_id"),
                    alertData.get("correlationId"),
                    info.get("correlation_id")
            ));
            String imagePath = stringOrNull(firstNonNull(
                    alertData.get("image_path"),
                    alertData.get("imagePath")
            ));
            String sourceEvent = stringOrNull(alertData.get("event"));

            boolean needsMatching = Boolean.TRUE.equals(task.getFaceMatchingEnabled())
                    || Boolean.TRUE.equals(task.getPlateMatchingEnabled());
            boolean needsSink = postProcessService.taskNeedsSinkProcessing(task);

            if (!needsMatching && !needsSink) {
                return;
            }

            if (needsMatching) {
                alertMatchingTriggerService.tryFaceMatching(
                        task, deviceId, deviceName, imagePath, frameNumber, correlationId, sourceEvent);
                alertMatchingTriggerService.tryPlateMatching(
                        task, deviceId, deviceName, imagePath, frameNumber, correlationId, detections);
            }

            if (!needsSink) {
                return;
            }
            if (detections.isEmpty() && imagePath == null) {
                return;
            }

            List<Map<String, Object>> regions = postProcessService.loadRegionsForDevice(deviceId);

            Map<String, Object> ctx = postProcessService.buildTaskContext(
                    task,
                    deviceId,
                    deviceName,
                    frameNumber,
                    timestamp,
                    detections,
                    detections,
                    regions,
                    imagePath,
                    correlationId
            );
            postProcessSinkClient.publishPostProcessRequestAsync(ctx, imagePath);
            log.info(
                    "alert hook post-process enqueue scheduled: taskId={}, deviceId={}, frame={}",
                    task.getId(),
                    deviceId,
                    frameNumber
            );
        } catch (Exception ex) {
            log.warn("alert post orchestration failed: {}", ex.getMessage());
        }
    }

    private AlgorithmTaskRow resolveTask(Map<String, Object> alertData, Map<String, Object> alertEventTask) {
        Object taskIdRaw = firstNonNull(alertData.get("task_id"), alertData.get("taskId"));
        if (taskIdRaw != null && !String.valueOf(taskIdRaw).isBlank()) {
            try {
                long taskId = Long.parseLong(String.valueOf(taskIdRaw));
                Optional<AlgorithmTaskRow> byId = taskRepository.findById(taskId);
                if (byId.isPresent()) {
                    return byId.get();
                }
            } catch (NumberFormatException ignored) {
                // fall through
            }
        }
        if (alertEventTask == null || alertEventTask.get("task_id") == null) {
            return null;
        }
        try {
            long taskId = Long.parseLong(String.valueOf(alertEventTask.get("task_id")));
            return taskRepository.findById(taskId).orElse(null);
        } catch (NumberFormatException ex) {
            return null;
        }
    }

    private static boolean isCppExecutor(AlgorithmTaskRow task) {
        String executor = task.getExecutor() != null ? task.getExecutor().trim().toLowerCase() : "cpp";
        return executor.equals("cpp") || executor.equals("c++") || executor.equals("runtime") || executor.equals("cxx");
    }

    private static Map<String, Object> parseInformation(Object raw) {
        if (raw instanceof Map<?, ?> map) {
            Map<String, Object> out = new java.util.LinkedHashMap<>();
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                out.put(String.valueOf(entry.getKey()), entry.getValue());
            }
            return out;
        }
        if (raw instanceof String text && !text.isBlank()) {
            try {
                Object parsed = new com.fasterxml.jackson.databind.ObjectMapper().readValue(text, Map.class);
                if (parsed instanceof Map<?, ?> map) {
                    Map<String, Object> out = new java.util.LinkedHashMap<>();
                    for (Map.Entry<?, ?> entry : map.entrySet()) {
                        out.put(String.valueOf(entry.getKey()), entry.getValue());
                    }
                    return out;
                }
            } catch (Exception ignored) {
                return Map.of();
            }
        }
        return Map.of();
    }

    @SuppressWarnings("unchecked")
    private static List<Map<String, Object>> extractDetections(Map<String, Object> info) {
        Object dets = info.get("detections");
        if (dets instanceof List<?> list) {
            List<Map<String, Object>> out = new java.util.ArrayList<>();
            for (Object item : list) {
                if (item instanceof Map<?, ?> map) {
                    out.add((Map<String, Object>) map);
                }
            }
            return out;
        }
        return List.of();
    }

    private static int extractFrameNumber(Map<String, Object> info) {
        Object val = firstNonNull(info.get("frame_number"), info.get("frameNumber"));
        if (val == null) {
            return 0;
        }
        try {
            return Integer.parseInt(String.valueOf(val));
        } catch (NumberFormatException ex) {
            return 0;
        }
    }

    private static double extractTimestamp(Map<String, Object> alertData, Map<String, Object> info) {
        Object tsMs = info.get("runtime_ts_ms");
        if (tsMs instanceof Number number && number.doubleValue() > 0) {
            return number.doubleValue() / 1000.0;
        }
        return System.currentTimeMillis() / 1000.0;
    }

    private static Object firstNonNull(Object... values) {
        for (Object value : values) {
            if (value != null) {
                return value;
            }
        }
        return null;
    }

    private static String stringOrNull(Object value) {
        if (value == null) {
            return null;
        }
        String text = String.valueOf(value).trim();
        return text.isEmpty() ? null : text;
    }

    private static String stringOrEmpty(Object value) {
        return value != null ? String.valueOf(value).trim() : "";
    }
}
