package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.dal.PlateLibraryRepository;
import com.basiclab.iot.video.dal.PlateMatchRecordRepository;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.support.JsonFields;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class PlateMatchingService {

    private final AlgorithmTaskRepository taskRepository;
    private final PlateLibraryRepository plateLibraryRepository;
    private final PlateMatchRecordRepository plateMatchRecordRepository;
    private final VideoProperties videoProperties;

    public Map<String, Object> publish(Map<String, Object> data) {
        if (data == null) {
            data = Map.of();
        }
        Object taskIdRaw = firstNonNull(data, "taskId", "task_id");
        Object plateNoRaw = firstNonNull(data, "plateNo", "plate_no");
        if (taskIdRaw == null || String.valueOf(taskIdRaw).isBlank()) {
            throw new VideoBusinessException(400, "taskId 不能为空");
        }
        String plateNo = plateNoRaw != null ? String.valueOf(plateNoRaw).trim() : "";
        if (plateNo.isEmpty()) {
            throw new VideoBusinessException(400, "plateNo 不能为空");
        }

        Map<String, Object> message = buildMessage(data, Long.parseLong(String.valueOf(taskIdRaw)), plateNo);
        boolean sent = sendToKafka(message);
        if (!sent) {
            throw new VideoBusinessException(500, "Kafka 投递失败");
        }
        return message;
    }

    public Map<String, Object> process(Map<String, Object> payload) {
        if (payload == null) {
            payload = Map.of();
        }
        Object taskIdRaw = firstNonNull(payload, "taskId", "task_id");
        if (taskIdRaw == null) {
            throw new VideoBusinessException(400, "任务不存在或未配置车牌库");
        }
        long taskId;
        try {
            taskId = Long.parseLong(String.valueOf(taskIdRaw));
        } catch (NumberFormatException ex) {
            throw new VideoBusinessException(400, "任务不存在或未配置车牌库");
        }

        AlgorithmTaskRow task = taskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "任务不存在或未配置车牌库"));

        List<Map<String, Object>> libraries = resolveLibraries(task);
        if (libraries.isEmpty()) {
            throw new VideoBusinessException(400, "任务未配置有效的车牌库");
        }

        String plateNo = stringOrNull(firstNonNull(payload, "plateNo", "plate_no"));
        String plateColor = stringOrNull(firstNonNull(payload, "plateColor", "plate_color"));
        String plateImagePath = stringOrNull(firstNonNull(payload, "plateImagePath", "plate_image_path"));
        String deviceId = stringOrNull(firstNonNull(payload, "deviceId", "device_id"));
        if (deviceId == null) {
            deviceId = "";
        }
        String deviceName = stringOrNull(firstNonNull(payload, "deviceName", "device_name"));
        String taskName = stringOrNull(firstNonNull(payload, "taskName", "task_name"));
        String taskType = stringOrNull(firstNonNull(payload, "taskType", "task_type"));
        String correlationId = stringOrNull(firstNonNull(payload, "correlationId", "correlation_id"));
        String libraryName = stringOrNull(firstNonNull(payload, "libraryName", "library_name"));
        Float detectConf = parseFloat(firstNonNull(payload, "detectConf", "detect_conf"));

        Object libraryIdRaw = firstNonNull(payload, "libraryId", "library_id");
        Integer libraryId = null;
        if (libraryIdRaw != null && !String.valueOf(libraryIdRaw).isBlank()) {
            libraryId = Integer.parseInt(String.valueOf(libraryIdRaw));
        }

        // P2-S4: no plate recognition engine — record unmatched (oracle parity for certify side_effect).
        boolean matched = false;
        if (plateNo != null && !plateNo.isBlank()) {
            log.debug("plate matching skipped (no recognition engine): plateNo={}", plateNo);
        }

        return plateMatchRecordRepository.insert(
                taskId,
                taskName,
                deviceId,
                deviceName,
                libraryId,
                libraryName,
                plateNo,
                plateColor,
                plateImagePath,
                matched,
                correlationId,
                taskType != null ? taskType : "realtime",
                detectConf
        );
    }

    private List<Map<String, Object>> resolveLibraries(AlgorithmTaskRow task) {
        List<Object> rawIds = JsonFields.parseJsonList(task.getPlateLibraryIds());
        List<Integer> ids = new ArrayList<>();
        for (Object raw : rawIds) {
            if (raw == null) {
                continue;
            }
            try {
                ids.add(Integer.parseInt(String.valueOf(raw)));
            } catch (NumberFormatException ignored) {
                // skip invalid id
            }
        }
        return plateLibraryRepository.findEnabledByIds(ids);
    }

    private Map<String, Object> buildMessage(Map<String, Object> data, long taskId, String plateNo) {
        Map<String, Object> message = new LinkedHashMap<>();
        message.put("taskId", taskId);
        message.put("taskName", stringOrNull(firstNonNull(data, "taskName", "task_name")));
        message.put("taskType", defaultString(stringOrNull(firstNonNull(data, "taskType", "task_type")), "realtime"));
        message.put("deviceId", stringOrNull(firstNonNull(data, "deviceId", "device_id")));
        message.put("deviceName", stringOrNull(firstNonNull(data, "deviceName", "device_name")));

        Object libraryIdRaw = firstNonNull(data, "libraryId", "library_id");
        if (libraryIdRaw != null && !String.valueOf(libraryIdRaw).isBlank()) {
            message.put("libraryId", Integer.parseInt(String.valueOf(libraryIdRaw)));
        } else {
            message.put("libraryId", null);
        }
        message.put("libraryName", stringOrNull(firstNonNull(data, "libraryName", "library_name")));
        message.put("plateNo", plateNo);
        message.put("plateColor", stringOrNull(firstNonNull(data, "plateColor", "plate_color")));
        message.put("plateImagePath", stringOrNull(firstNonNull(data, "plateImagePath", "plate_image_path")));

        Float detectConf = parseFloat(firstNonNull(data, "detectConf", "detect_conf"));
        message.put("detectConf", detectConf);

        Object alertId = firstNonNull(data, "alertId", "alert_id");
        if (alertId != null) {
            message.put("alertId", alertId);
        }
        Object rect = data.get("rect");
        if (rect != null) {
            message.put("rect", rect);
        }
        Object landmarks = data.get("landmarks");
        if (landmarks != null) {
            message.put("landmarks", landmarks);
        }
        message.put("timestamp", Instant.now().toString());

        String correlationId = stringOrNull(firstNonNull(data, "correlationId", "correlation_id"));
        if (correlationId != null) {
            message.put("correlationId", correlationId);
        }
        return message;
    }

    /**
     * Mini/local path: mock Kafka producer success (no broker required). Real Kafka can be wired later.
     */
    private boolean sendToKafka(Map<String, Object> message) {
        if (videoProperties.getMatching().isUseDirectProcess()) {
            log.info(
                    "plate matching mini path (mock kafka): deviceId={}, libraryId={}, plateNo={}",
                    message.get("deviceId"),
                    message.get("libraryId"),
                    message.get("plateNo")
            );
            return true;
        }
        log.warn("Kafka producer not configured for plate matching");
        return false;
    }

    private static Object firstNonNull(Map<String, Object> data, String... keys) {
        for (String key : keys) {
            if (data.containsKey(key) && data.get(key) != null) {
                return data.get(key);
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

    private static String defaultString(String value, String fallback) {
        return value != null ? value : fallback;
    }

    private static Float parseFloat(Object value) {
        if (value == null || String.valueOf(value).isBlank()) {
            return null;
        }
        try {
            return Float.parseFloat(String.valueOf(value));
        } catch (NumberFormatException ex) {
            return null;
        }
    }
}
