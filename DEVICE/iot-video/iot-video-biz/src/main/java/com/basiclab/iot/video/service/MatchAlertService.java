package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.AlertRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Creates library-match alerts mirroring Python {@code library_matching_service._create_match_alert}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class MatchAlertService {

    public static final String EVENT_FACE_LIBRARY_MATCH = "face_library_match";
    public static final String EVENT_PLATE_LIBRARY_MATCH = "plate_library_match";

    private final AlertRepository alertRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public Long createFaceLibraryMatchAlert(
            String personName,
            String deviceId,
            String deviceName,
            String imagePath,
            Long taskId,
            String taskName,
            String taskType,
            List<String> businessTags,
            String correlationId,
            Map<String, Object> information
    ) {
        return createMatchAlert(
                EVENT_FACE_LIBRARY_MATCH,
                personName != null && !personName.isBlank() ? personName : "未知人员",
                deviceId,
                deviceName,
                imagePath,
                taskId,
                taskName,
                taskType,
                businessTags,
                correlationId,
                information
        );
    }

    public Long createPlateLibraryMatchAlert(
            String plateNo,
            String deviceId,
            String deviceName,
            String imagePath,
            Long taskId,
            String taskName,
            String taskType,
            List<String> businessTags,
            String correlationId,
            Map<String, Object> information
    ) {
        return createMatchAlert(
                EVENT_PLATE_LIBRARY_MATCH,
                plateNo != null && !plateNo.isBlank() ? plateNo : "未知车牌",
                deviceId,
                deviceName,
                imagePath,
                taskId,
                taskName,
                taskType,
                businessTags,
                correlationId,
                information
        );
    }

    private Long createMatchAlert(
            String event,
            String objectLabel,
            String deviceId,
            String deviceName,
            String imagePath,
            Long taskId,
            String taskName,
            String taskType,
            List<String> businessTags,
            String correlationId,
            Map<String, Object> information
    ) {
        try {
            Map<String, Object> info = new LinkedHashMap<>(information != null ? information : Map.of());
            if (correlationId != null && !correlationId.isBlank()) {
                info.putIfAbsent("correlation_id", correlationId);
            }
            if (businessTags != null && !businessTags.isEmpty()) {
                info.putIfAbsent("business_tags", businessTags);
            }
            Map<String, Object> alertData = new LinkedHashMap<>();
            alertData.put("object", objectLabel);
            alertData.put("event", event);
            alertData.put("device_id", deviceId != null ? deviceId : "");
            alertData.put("device_name", deviceName != null && !deviceName.isBlank() ? deviceName : deviceId);
            if (imagePath != null && !imagePath.isBlank()) {
                alertData.put("image_path", imagePath);
            }
            alertData.put("task_type", taskType != null && !taskType.isBlank() ? taskType : "realtime");
            if (correlationId != null && !correlationId.isBlank()) {
                alertData.put("correlation_id", correlationId);
            }
            alertData.put("information", objectMapper.writeValueAsString(info));
            long alertId = alertRepository.insertAlert(alertData, taskId, taskName);
            return alertId > 0 ? alertId : null;
        } catch (Exception ex) {
            log.error("创建库匹配告警失败: event={}, deviceId={}, error={}", event, deviceId, ex.getMessage(), ex);
            return null;
        }
    }
}
