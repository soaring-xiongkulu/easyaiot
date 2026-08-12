package com.basiclab.iot.video.service;

import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.support.JsonFields;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Triggers face/plate matching publish from alert hook orchestration (Python {@code _try_*_matching}).
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AlertMatchingTriggerService {

    private final FaceMatchingService faceMatchingService;
    private final PlateMatchingService plateMatchingService;

    public void tryFaceMatching(
            AlgorithmTaskRow task,
            String deviceId,
            String deviceName,
            String imagePath,
            int frameNumber,
            String correlationId,
            String sourceEvent
    ) {
        if (!Boolean.TRUE.equals(task.getFaceMatchingEnabled())) {
            return;
        }
        List<Object> libraryIds = JsonFields.parseJsonList(task.getFaceLibraryIds());
        if (libraryIds.isEmpty()) {
            log.warn("人脸匹配已开启但未配置人脸库，跳过 taskId={}", task.getId());
            return;
        }
        if (imagePath == null || imagePath.isBlank() || !Files.isRegularFile(Path.of(imagePath))) {
            log.warn("告警帧后编排：无法加载告警图，跳过人脸匹配 taskId={} frame={}", task.getId(), frameNumber);
            return;
        }
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("taskId", task.getId());
        payload.put("taskName", task.getTaskName());
        payload.put("taskType", task.getTaskType() != null ? task.getTaskType() : "realtime");
        payload.put("deviceId", deviceId);
        payload.put("deviceName", deviceName);
        payload.put("faceImagePath", imagePath);
        payload.put("correlationId", correlationId);
        payload.put("sourceEvent", sourceEvent);
        if (task.getFaceMatchingThreshold() != null) {
            payload.put("threshold", task.getFaceMatchingThreshold());
        }
        try {
            faceMatchingService.publish(payload);
            log.info("cpp 告警 hook 已尝试人脸匹配 publish: taskId={} deviceId={} frame={}", task.getId(), deviceId, frameNumber);
        } catch (Exception ex) {
            log.warn("cpp 告警 hook 人脸匹配 publish 失败 taskId={}: {}", task.getId(), ex.getMessage());
        }
    }

    public void tryPlateMatching(
            AlgorithmTaskRow task,
            String deviceId,
            String deviceName,
            String imagePath,
            int frameNumber,
            String correlationId,
            List<Map<String, Object>> detections
    ) {
        if (!Boolean.TRUE.equals(task.getPlateMatchingEnabled())) {
            return;
        }
        List<Object> libraryIds = JsonFields.parseJsonList(task.getPlateLibraryIds());
        if (libraryIds.isEmpty()) {
            log.warn("车牌匹配已开启但未配置车牌库，跳过 taskId={}", task.getId());
            return;
        }
        String plateNo = extractPlateNo(detections);
        if (plateNo == null || plateNo.isBlank()) {
            log.warn("告警帧后编排：detections 无车牌号，跳过车牌匹配 taskId={} frame={}", task.getId(), frameNumber);
            return;
        }
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("taskId", task.getId());
        payload.put("taskName", task.getTaskName());
        payload.put("taskType", task.getTaskType() != null ? task.getTaskType() : "realtime");
        payload.put("deviceId", deviceId);
        payload.put("deviceName", deviceName);
        payload.put("plateNo", plateNo);
        payload.put("plateImagePath", imagePath);
        payload.put("correlationId", correlationId);
        try {
            plateMatchingService.publish(payload);
            log.info("cpp 告警 hook 已尝试车牌匹配 publish: taskId={} deviceId={} plateNo={}", task.getId(), deviceId, plateNo);
        } catch (Exception ex) {
            log.warn("cpp 告警 hook 车牌匹配 publish 失败 taskId={}: {}", task.getId(), ex.getMessage());
        }
    }

    private static String extractPlateNo(List<Map<String, Object>> detections) {
        if (detections == null) {
            return null;
        }
        for (Map<String, Object> det : detections) {
            String plate = firstNonBlank(det, "plate_no", "plateNo", "plate_number", "plateNumber");
            if (plate != null) {
                return plate;
            }
            Object attrs = det.get("attributes");
            if (attrs instanceof Map<?, ?> map) {
                plate = firstNonBlank(cast(map), "plate_no", "plateNo", "plate_number");
                if (plate != null) {
                    return plate;
                }
            }
        }
        return null;
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> cast(Map<?, ?> map) {
        Map<String, Object> out = new LinkedHashMap<>();
        for (Map.Entry<?, ?> entry : map.entrySet()) {
            out.put(String.valueOf(entry.getKey()), entry.getValue());
        }
        return out;
    }

    private static String firstNonBlank(Map<String, Object> data, String... keys) {
        for (String key : keys) {
            Object value = data.get(key);
            if (value != null && !String.valueOf(value).isBlank()) {
                return String.valueOf(value).trim();
            }
        }
        return null;
    }
}
