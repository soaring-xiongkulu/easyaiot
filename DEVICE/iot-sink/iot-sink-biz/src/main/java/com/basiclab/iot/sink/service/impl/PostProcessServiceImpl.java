package com.basiclab.iot.sink.service.impl;

import com.baomidou.dynamic.datasource.toolkit.DynamicDataSourceContextHolder;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.domain.model.AlertNotificationMessage;
import com.basiclab.iot.sink.domain.model.PostProcessRequestMessage;
import com.basiclab.iot.sink.service.AlertService;
import com.basiclab.iot.sink.service.PostProcessService;
import com.basiclab.iot.sink.service.PostProcessWorkerResolver;
import com.basiclab.iot.sink.util.AlertClassFilter;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestTemplate;

import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * 算法后处理：Kafka 入队/分发/落库/告警（全部由 iot-sink Java 承载）
 */
@Slf4j
@Service
public class PostProcessServiceImpl implements PostProcessService {

    @Autowired(required = false)
    private AlertService alertService;

    @Autowired(required = false)
    private KafkaTemplate<String, String> iotKafkaTemplate;

    @Autowired(required = false)
    private RestTemplate restTemplate;

    @Autowired(required = false)
    private JdbcTemplate jdbcTemplate;

    @Autowired
    private PostProcessWorkerResolver workerResolver;

    @Autowired(required = false)
    private ObjectMapper objectMapper;

    @Value("${spring.kafka.post-process.request-topic:iot-post-process-request}")
    private String requestTopic;

    @Value("${spring.kafka.post-process.result-topic:iot-post-process-result}")
    private String resultTopic;

    @Value("${basiclab.video.service-url:http://localhost:48080}")
    private String videoServiceUrl;

    @Value("${basiclab.video.api-prefix:/admin-api/video}")
    private String videoApiPrefix;

    @Override
    public void enqueue(PostProcessRequestMessage message) {
        if (message == null) {
            throw new IllegalArgumentException("后处理消息为空");
        }
        if (message.getTaskId() == null) {
            throw new IllegalArgumentException("taskId 不能为空");
        }
        if (!StringUtils.hasText(message.getDeviceId())) {
            throw new IllegalArgumentException("deviceId 不能为空");
        }
        if (!StringUtils.hasText(message.getCorrelationId())) {
            message.setCorrelationId(UUID.randomUUID().toString());
        }
        if (!StringUtils.hasText(message.getTimestamp())) {
            message.setTimestamp(Instant.now().atOffset(ZoneOffset.UTC).format(DateTimeFormatter.ISO_OFFSET_DATE_TIME));
        }
        publishKafka(requestTopic, message.getDeviceId(), message);
    }

    @Override
    public void dispatchAndPublishResult(PostProcessRequestMessage request) {
        if (request == null || request.getTaskId() == null) {
            return;
        }
        Map<String, Object> workerResponse = invokeWorker(request);
        if (workerResponse == null) {
            return;
        }
        Object resultObj = workerResponse.get("result");
        if (!(resultObj instanceof Map)) {
            return;
        }
        @SuppressWarnings("unchecked")
        Map<String, Object> result = (Map<String, Object>) resultObj;
        if (!shouldPublishResult(result)) {
            return;
        }
        Map<String, Object> resultMessage = buildResultMessage(request, result);
        String key = request.getDeviceId() != null ? request.getDeviceId() : String.valueOf(request.getTaskId());
        publishKafka(resultTopic, key, resultMessage);
    }

    @Override
    public void persistResultAndDispatchAlerts(Map<String, Object> message) {
        if (message == null || message.isEmpty()) {
            return;
        }
        Integer taskId = intValue(message.get("taskId"), message.get("task_id"));
        String deviceId = stringValue(message.get("deviceId"), message.get("device_id"));
        if (taskId == null || !StringUtils.hasText(deviceId)) {
            log.warn("后处理结果缺少 taskId/deviceId");
            return;
        }
        String correlationId = stringValue(message.get("correlationId"), message.get("correlation_id"));
        if (StringUtils.hasText(correlationId) && existsByCorrelationId(correlationId)) {
            log.debug("后处理结果已存在 correlationId={}", correlationId);
            return;
        }
        saveResult(message, taskId, deviceId, correlationId);
        dispatchAlerts(message);
    }

    private Map<String, Object> invokeWorker(PostProcessRequestMessage request) {
        if (restTemplate == null) {
            restTemplate = new RestTemplate();
        }
        String baseUrl = workerResolver.resolveWorkerBaseUrl(request.getTaskId());
        String url = baseUrl + "/execute";
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<PostProcessRequestMessage> entity = new HttpEntity<>(request, headers);
        try {
            ResponseEntity<String> response = restTemplate.postForEntity(url, entity, String.class);
            if (!response.getStatusCode().is2xxSuccessful() || !StringUtils.hasText(response.getBody())) {
                log.warn("后处理 Worker 返回异常 taskId={} url={} status={}",
                        request.getTaskId(), url, response.getStatusCodeValue());
                return null;
            }
            return JsonUtils.parseObject(response.getBody(), new TypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            log.error("调用后处理 Worker 失败 taskId={} url={}: {}", request.getTaskId(), url, e.getMessage());
            return null;
        }
    }

    private Map<String, Object> buildResultMessage(PostProcessRequestMessage request, Map<String, Object> result) {
        Map<String, Object> message = objectMapper.convertValue(request, new TypeReference<Map<String, Object>>() {});
        message.put("counts", result.get("counts"));
        message.put("events", result.get("events"));
        message.put("alerts", result.get("alerts"));
        message.put("payload", result);
        message.put("processedAt", Instant.now().atOffset(ZoneOffset.UTC).format(DateTimeFormatter.ISO_OFFSET_DATE_TIME));
        if (result.get("detections") != null) {
            message.put("detections", result.get("detections"));
        }
        if (result.get("pose_count") != null) {
            message.put("poseCount", result.get("pose_count"));
        }
        if (result.get("pose_result") != null) {
            message.put("poseResult", result.get("pose_result"));
        }
        if (result.get("suppress_default_alert") != null) {
            message.put("suppressDefaultAlert", result.get("suppress_default_alert"));
        }
        if (StringUtils.hasText(request.getAlertImagePath())) {
            message.put("alertImagePath", request.getAlertImagePath());
        }
        return message;
    }

    private boolean shouldPublishResult(Map<String, Object> result) {
        if (result == null || result.isEmpty()) {
            return false;
        }
        if (Boolean.TRUE.equals(result.get("suppress_kafka")) || Boolean.TRUE.equals(result.get("suppress_sink"))) {
            return false;
        }
        if (Boolean.TRUE.equals(result.get("publish_kafka")) || Boolean.TRUE.equals(result.get("publish_sink"))) {
            return true;
        }
        for (String key : new String[]{"counts", "events", "alerts", "payload", "detections", "pose_count", "pose_result", "pose_intent_matches"}) {
            Object value = result.get(key);
            if (value != null) {
                if (value instanceof Map && ((Map<?, ?>) value).isEmpty()) {
                    continue;
                }
                if (value instanceof List && ((List<?>) value).isEmpty()) {
                    continue;
                }
                return true;
            }
        }
        return false;
    }

    private void publishKafka(String topic, String key, Object payload) {
        if (iotKafkaTemplate == null) {
            log.warn("KafkaTemplate 不可用，跳过后处理投递 topic={}", topic);
            return;
        }
        try {
            String json = JsonUtils.toJsonString(payload);
            iotKafkaTemplate.send(topic, key, json);
        } catch (Exception e) {
            log.error("后处理 Kafka 投递失败 topic={}: {}", topic, e.getMessage(), e);
            throw new IllegalStateException("Kafka 投递失败: " + e.getMessage(), e);
        }
    }

    private boolean existsByCorrelationId(String correlationId) {
        if (jdbcTemplate == null) {
            return false;
        }
        try {
            DynamicDataSourceContextHolder.push("video");
            Integer count = jdbcTemplate.queryForObject(
                    "SELECT COUNT(1) FROM algorithm_post_process_result WHERE correlation_id = ?",
                    Integer.class,
                    correlationId);
            return count != null && count > 0;
        } catch (Exception e) {
            log.warn("查询后处理去重失败 correlationId={}: {}", correlationId, e.getMessage());
            return false;
        } finally {
            DynamicDataSourceContextHolder.clear();
        }
    }

    private void saveResult(Map<String, Object> message, Integer taskId, String deviceId, String correlationId) {
        if (jdbcTemplate == null) {
            log.warn("JdbcTemplate 不可用，跳过后处理落库");
            return;
        }
        Object payloadObj = message.get("payload");
        Map<String, Object> payload;
        if (payloadObj instanceof Map) {
            @SuppressWarnings("unchecked")
            Map<String, Object> cast = (Map<String, Object>) payloadObj;
            payload = cast;
        } else {
            payload = new LinkedHashMap<>();
            for (String key : new String[]{"counts", "events", "alerts", "detections", "suppress_default_alert", "pose_count", "pose_result"}) {
                if (message.get(key) != null) {
                    payload.put(key, message.get(key));
                }
            }
        }
        try {
            DynamicDataSourceContextHolder.push("video");
            jdbcTemplate.update(
                    "INSERT INTO algorithm_post_process_result "
                            + "(task_id, task_name, task_code, task_type, device_id, device_name, "
                            + "frame_number, event_time, counts, events, alerts, payload, correlation_id, created_at) "
                            + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())",
                    taskId,
                    stringValue(message.get("taskName"), message.get("task_name")),
                    stringValue(message.get("taskCode"), message.get("task_code")),
                    stringValue(message.get("taskType"), message.get("task_type")),
                    deviceId,
                    stringValue(message.get("deviceName"), message.get("device_name")),
                    intValue(message.get("frameNumber"), message.get("frame_number")),
                    parseEventTime(message),
                    toJson(message.get("counts")),
                    toJson(message.get("events")),
                    toJson(message.get("alerts")),
                    toJson(payload),
                    correlationId);
            log.info("后处理结果已入库 taskId={} deviceId={} correlationId={}", taskId, deviceId, correlationId);
        } catch (Exception e) {
            log.error("后处理落库失败 taskId={} deviceId={}: {}", taskId, deviceId, e.getMessage(), e);
            throw new IllegalStateException("后处理落库失败", e);
        } finally {
            DynamicDataSourceContextHolder.clear();
        }
    }

    private void dispatchAlerts(Map<String, Object> message) {
        Map<String, Object> payload = extractPayload(message);
        dispatchCustomAlertsOnly(message, payload);
        Boolean suppress = boolValue(payload.get("suppress_default_alert"), message.get("suppressDefaultAlert"));
        if (Boolean.TRUE.equals(suppress)) {
            return;
        }
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> detections = payload.get("detections") instanceof List
                ? (List<Map<String, Object>>) payload.get("detections")
                : message.get("detections") instanceof List
                ? (List<Map<String, Object>>) message.get("detections")
                : null;
        Object alertClassNames = message.get("alertClassNames");
        if (alertClassNames == null) {
            alertClassNames = message.get("alert_class_names");
        }
        List<Map<String, Object>> alertDetections = AlertClassFilter.filterDetectionsForAlert(
                detections, alertClassNames);
        Map<String, Object> defaultAlert = buildDefaultAlert(message, alertDetections, payload);
        if (defaultAlert != null) {
            postAlertHook(defaultAlert);
        }
    }

    private void dispatchCustomAlertsOnly(Map<String, Object> message, Map<String, Object> payload) {
        Object alertsObj = payload.get("alerts");
        if (alertsObj == null) {
            alertsObj = message.get("alerts");
        }
        if (!(alertsObj instanceof List)) {
            return;
        }
        @SuppressWarnings("unchecked")
        List<Object> alerts = (List<Object>) alertsObj;
        String deviceId = stringValue(message.get("deviceId"), message.get("device_id"));
        String deviceName = stringValue(message.get("deviceName"), message.get("device_name"));
        String taskType = stringValue(message.get("taskType"), message.get("task_type"));
        for (Object item : alerts) {
            if (!(item instanceof Map)) {
                continue;
            }
            @SuppressWarnings("unchecked")
            Map<String, Object> alert = new HashMap<>((Map<String, Object>) item);
            alert.putIfAbsent("device_id", deviceId);
            alert.putIfAbsent("device_name", deviceName);
            alert.putIfAbsent("task_type", taskType);
            postAlertHook(alert);
        }
    }

    private Map<String, Object> buildDefaultAlert(
            Map<String, Object> message,
            List<Map<String, Object>> detections,
            Map<String, Object> payload) {
        if (detections == null || detections.isEmpty()) {
            return null;
        }
        if (payload == null) {
            payload = extractPayload(message);
        }
        Map<String, Integer> objectCounts = new HashMap<>();
        String primary = "unknown";
        for (Map<String, Object> det : detections) {
            String className = stringValue(det.get("class_name"), det.get("className"));
            if (!StringUtils.hasText(className)) {
                className = "unknown";
            }
            objectCounts.merge(className, 1, Integer::sum);
        }
        if (!objectCounts.isEmpty()) {
            primary = objectCounts.entrySet().stream()
                    .max(Map.Entry.comparingByValue())
                    .map(Map.Entry::getKey)
                    .orElse("unknown");
        }
        Map<String, Object> information = new LinkedHashMap<>();
        information.put("total_count", detections.size());
        information.put("object_counts", objectCounts);
        information.put("detections", detections);
        information.put("frame_number", intValue(message.get("frameNumber"), message.get("frame_number")));
        information.put("correlation_id", stringValue(message.get("correlationId"), message.get("correlation_id")));
        information.put("source", "post_process_sink");
        Object poseResult = payload.get("pose_result");
        if (poseResult == null) {
            poseResult = message.get("poseResult");
        }
        if (poseResult != null) {
            information.put("pose_result", poseResult);
        }
        Object poseIntentMatches = payload.get("pose_intent_matches");
        if (poseIntentMatches == null) {
            poseIntentMatches = message.get("poseIntentMatches");
        }
        if (poseIntentMatches != null) {
            information.put("pose_intent_matches", poseIntentMatches);
        }

        Map<String, Object> alert = new HashMap<>();
        alert.put("object", primary);
        alert.put("event", stringValue(message.get("taskName"), message.get("task_name")));
        alert.put("device_id", stringValue(message.get("deviceId"), message.get("device_id")));
        alert.put("device_name", stringValue(message.get("deviceName"), message.get("device_name")));
        alert.put("task_type", stringValue(message.get("taskType"), message.get("task_type")));
        alert.put("correlation_id", stringValue(message.get("correlationId"), message.get("correlation_id")));
        alert.put("time", stringValue(message.get("timestamp"), message.get("eventTime")));
        alert.put("information", JsonUtils.toJsonString(information));
        alert.put("image_path", stringValue(message.get("alertImagePath"), message.get("alert_image_path")));
        return alert;
    }

    private void postAlertHook(Map<String, Object> alertData) {
        // VIDEO /video/alert/hook 已移除；后处理告警直接走本模块 AlertService
        if (alertService == null) {
            log.warn("AlertService 不可用，后处理告警无法落库 deviceId={}",
                    alertData != null ? alertData.get("device_id") : null);
            return;
        }
        try {
            AlertNotificationMessage msg = new AlertNotificationMessage();
            msg.setDeviceId(stringValue(alertData.get("device_id"), null));
            msg.setDeviceName(stringValue(alertData.get("device_name"), null));
            Object taskId = alertData.get("task_id");
            if (taskId == null) {
                taskId = alertData.get("taskId");
            }
            if (taskId instanceof Number) {
                msg.setTaskId(((Number) taskId).intValue());
            } else if (taskId != null && StringUtils.hasText(String.valueOf(taskId))) {
                try {
                    msg.setTaskId(Integer.parseInt(String.valueOf(taskId)));
                } catch (Exception ignored) {
                    // keep null
                }
            }
            msg.setTaskName(stringValue(alertData.get("task_name"), alertData.get("event")));
            msg.setCorrelationId(stringValue(alertData.get("correlation_id"), alertData.get("correlationId")));
            msg.setTimestamp(stringValue(alertData.get("time"), alertData.get("timestamp")));

            AlertNotificationMessage.AlertInfo alert = new AlertNotificationMessage.AlertInfo();
            alert.setObject(stringValue(alertData.get("object"), null));
            alert.setEvent(stringValue(alertData.get("event"), null));
            alert.setRegion(stringValue(alertData.get("region"), null));
            alert.setInformation(alertData.get("information"));
            alert.setImagePath(stringValue(alertData.get("image_path"), alertData.get("imagePath")));
            alert.setTime(stringValue(alertData.get("time"), null));
            alert.setTaskType(stringValue(alertData.get("task_type"), "realtime"));
            msg.setAlert(alert);

            String taskType = alert.getTaskType();
            if ("snap".equalsIgnoreCase(taskType) || "snapshot".equalsIgnoreCase(taskType)) {
                alertService.processSnapshotAlert(msg);
            } else {
                alertService.processAlert(msg);
            }
            log.info("后处理告警已落库(AlertService) deviceId={}", msg.getDeviceId());
        } catch (Exception e) {
            log.warn("后处理告警落库失败 deviceId={}: {}",
                    alertData != null ? alertData.get("device_id") : null, e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> extractPayload(Map<String, Object> message) {
        Object payloadObj = message.get("payload");
        if (payloadObj instanceof Map) {
            return (Map<String, Object>) payloadObj;
        }
        return message;
    }

    private OffsetDateTime parseEventTime(Map<String, Object> message) {
        Object raw = message.get("timestamp");
        if (raw == null) {
            raw = message.get("eventTime");
        }
        if (raw == null) {
            return null;
        }
        try {
            if (raw instanceof Number) {
                return Instant.ofEpochSecond(((Number) raw).longValue()).atOffset(ZoneOffset.UTC);
            }
            return OffsetDateTime.parse(raw.toString().replace("Z", "+00:00"));
        } catch (Exception e) {
            return null;
        }
    }

    private String toJson(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof String) {
            return (String) value;
        }
        return JsonUtils.toJsonString(value);
    }

    private static Integer intValue(Object primary, Object fallback) {
        Object raw = primary != null ? primary : fallback;
        if (raw == null) {
            return null;
        }
        if (raw instanceof Number) {
            return ((Number) raw).intValue();
        }
        try {
            return Integer.parseInt(raw.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static String stringValue(Object primary, Object fallback) {
        Object raw = primary != null ? primary : fallback;
        return raw == null ? null : raw.toString();
    }

    private static Boolean boolValue(Object primary, Object fallback) {
        Object raw = primary != null ? primary : fallback;
        if (raw == null) {
            return null;
        }
        if (raw instanceof Boolean) {
            return (Boolean) raw;
        }
        return Boolean.parseBoolean(raw.toString());
    }

    private static String normalizeBaseUrl(String baseUrl) {
        if (!StringUtils.hasText(baseUrl)) {
            return "http://localhost:48080";
        }
        return baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
    }

    private static String normalizeApiPrefix(String apiPrefix) {
        if (!StringUtils.hasText(apiPrefix)) {
            return "/admin-api/video";
        }
        return apiPrefix.startsWith("/") ? apiPrefix : "/" + apiPrefix;
    }
}
