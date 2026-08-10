package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.dal.FaceLibraryRepository;
import com.basiclab.iot.video.dal.FaceMatchRecordRepository;
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
public class FaceMatchingService {

    private final AlgorithmTaskRepository taskRepository;
    private final FaceLibraryRepository faceLibraryRepository;
    private final FaceMatchRecordRepository faceMatchRecordRepository;
    private final VideoProperties videoProperties;

    public Map<String, Object> publish(Map<String, Object> data) {
        if (data == null) {
            data = Map.of();
        }
        Object taskIdRaw = firstNonNull(data, "taskId", "task_id");
        Object faceImagePathRaw = firstNonNull(data, "faceImagePath", "face_image_path");
        if (taskIdRaw == null || String.valueOf(taskIdRaw).isBlank()) {
            throw new VideoBusinessException(400, "taskId 不能为空");
        }
        String faceImagePath = faceImagePathRaw != null ? String.valueOf(faceImagePathRaw).trim() : "";
        if (faceImagePath.isEmpty()) {
            throw new VideoBusinessException(400, "faceImagePath 不能为空");
        }

        Map<String, Object> message = buildMessage(data, Long.parseLong(String.valueOf(taskIdRaw)), faceImagePath);
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
            throw new VideoBusinessException(400, "任务不存在或未配置人脸库");
        }
        long taskId;
        try {
            taskId = Long.parseLong(String.valueOf(taskIdRaw));
        } catch (NumberFormatException ex) {
            throw new VideoBusinessException(400, "任务不存在或未配置人脸库");
        }

        AlgorithmTaskRow task = taskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "任务不存在或未配置人脸库"));

        List<Map<String, Object>> libraries = resolveLibraries(task);
        if (libraries.isEmpty()) {
            throw new VideoBusinessException(400, "任务未配置有效的人脸库");
        }

        String faceImagePath = stringOrNull(firstNonNull(payload, "faceImagePath", "face_image_path"));
        String deviceId = stringOrNull(firstNonNull(payload, "deviceId", "device_id"));
        if (deviceId == null) {
            deviceId = "";
        }
        String deviceName = stringOrNull(firstNonNull(payload, "deviceName", "device_name"));
        String taskName = stringOrNull(firstNonNull(payload, "taskName", "task_name"));
        String taskType = stringOrNull(firstNonNull(payload, "taskType", "task_type"));
        String correlationId = stringOrNull(firstNonNull(payload, "correlationId", "correlation_id"));
        Float threshold = parseFloat(firstNonNull(payload, "threshold", "faceMatchingThreshold", "face_matching_threshold"));
        String libraryName = stringOrNull(firstNonNull(payload, "libraryName", "library_name"));

        // P2-S3: no InsightFace — record unmatched when image missing/unreadable (oracle parity).
        boolean matched = false;
        Integer libraryId = null;
        if (faceImagePath != null && !faceImagePath.isBlank()) {
            log.debug("face matching skipped (no recognition engine): path={}", faceImagePath);
        }

        return faceMatchRecordRepository.insert(
                taskId,
                taskName,
                deviceId,
                deviceName,
                libraryId,
                libraryName,
                faceImagePath,
                matched,
                correlationId,
                taskType != null ? taskType : "realtime",
                threshold
        );
    }

    private List<Map<String, Object>> resolveLibraries(AlgorithmTaskRow task) {
        List<Object> rawIds = JsonFields.parseJsonList(task.getFaceLibraryIds());
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
        return faceLibraryRepository.findEnabledByIds(ids);
    }

    private Map<String, Object> buildMessage(Map<String, Object> data, long taskId, String faceImagePath) {
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
        message.put("faceImagePath", faceImagePath);

        Float threshold = parseFloat(firstNonNull(data, "threshold", "faceMatchingThreshold", "face_matching_threshold"));
        message.put("threshold", threshold);
        message.put("faceMatchingThreshold", threshold);

        Object alertId = firstNonNull(data, "alertId", "alert_id");
        if (alertId != null) {
            message.put("alertId", alertId);
        }
        Object bbox = data.get("bbox");
        if (bbox != null) {
            message.put("bbox", bbox);
        }
        Object confidence = data.get("confidence");
        if (confidence != null) {
            message.put("confidence", confidence);
        }
        message.put("timestamp", Instant.now().toString());

        String correlationId = stringOrNull(firstNonNull(data, "correlationId", "correlation_id"));
        if (correlationId != null) {
            message.put("correlationId", correlationId);
        }
        String sourceEvent = stringOrNull(firstNonNull(data, "sourceEvent", "source_event"));
        if (sourceEvent != null) {
            message.put("sourceEvent", sourceEvent);
        }
        return message;
    }

    /**
     * Mini/local path: mock Kafka producer success (no broker required). Real Kafka can be wired later.
     */
    private boolean sendToKafka(Map<String, Object> message) {
        if (videoProperties.getMatching().isUseDirectProcess()) {
            log.info(
                    "face matching mini path (mock kafka): deviceId={}, libraryId={}, path={}",
                    message.get("deviceId"),
                    message.get("libraryId"),
                    message.get("faceImagePath")
            );
            return true;
        }
        log.warn("Kafka producer not configured for face matching");
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
