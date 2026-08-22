package com.basiclab.iot.sink.protocol.emqx.router;

import cn.hutool.core.util.StrUtil;
import cn.hutool.extra.spring.SpringUtil;
import com.baomidou.dynamic.datasource.toolkit.DynamicDataSourceContextHolder;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.domain.model.AlertNotificationMessage;
import com.basiclab.iot.sink.domain.model.PostProcessRequestMessage;
import com.basiclab.iot.sink.service.AlertService;
import com.basiclab.iot.sink.service.PostProcessService;
import com.basiclab.iot.sink.util.AlertClassFilter;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.kafka.core.KafkaTemplate;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 订阅 EMQX 算法总线（mqtt/iot-*）：告警落库/归档、通知 enrichment、后处理入队。
 * 执行侧只发检测事实 + image_path；通知配置由本处理器从 VIDEO 库补齐。
 */
@Slf4j
public class IotAlgoBusMqttHandler {

    private final AlertService alertService;
    private final PostProcessService postProcessService;
    private final ObjectMapper objectMapper;
    private final JdbcTemplate jdbcTemplate;
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final String notificationSendTopic;

    public IotAlgoBusMqttHandler() {
        this.alertService = SpringUtil.getBean(AlertService.class);
        PostProcessService pps = null;
        try {
            pps = SpringUtil.getBean(PostProcessService.class);
        } catch (Exception ignored) {
            // optional
        }
        this.postProcessService = pps;
        ObjectMapper om = null;
        try {
            om = SpringUtil.getBean(ObjectMapper.class);
        } catch (Exception ignored) {
            om = new ObjectMapper();
        }
        this.objectMapper = om;
        JdbcTemplate jt = null;
        try {
            jt = SpringUtil.getBean(JdbcTemplate.class);
        } catch (Exception ignored) {
            // optional
        }
        this.jdbcTemplate = jt;
        KafkaTemplate<String, String> kt = null;
        try {
            @SuppressWarnings("unchecked")
            KafkaTemplate<String, String> bean =
                    (KafkaTemplate<String, String>) SpringUtil.getBean("iotKafkaTemplate");
            kt = bean;
        } catch (Exception ignored) {
            try {
                @SuppressWarnings("unchecked")
                KafkaTemplate<String, String> bean =
                        (KafkaTemplate<String, String>) SpringUtil.getBean(KafkaTemplate.class);
                kt = bean;
            } catch (Exception ignored2) {
                // optional
            }
        }
        this.kafkaTemplate = kt;
        String topic = "iot-alert-notification-send";
        try {
            String env = System.getenv("SPRING_KAFKA_ALERT_NOTIFICATION_SEND_TOPIC");
            if (StrUtil.isNotBlank(env)) {
                topic = env.trim();
            }
        } catch (Exception ignored) {
            // keep default
        }
        this.notificationSendTopic = topic;
    }

    public boolean supports(String topic) {
        return StrUtil.isNotBlank(topic) && topic.startsWith("mqtt/iot-");
    }

    public void handle(String topic, byte[] payloadBytes) {
        String json = new String(payloadBytes, StandardCharsets.UTF_8);
        try {
            JsonNode root = objectMapper.readTree(json);
            JsonNode payload = root.has("payload") ? root.get("payload") : root;
            if (topic.endsWith("iot-alert-notification") || topic.contains("iot-alert-notification")) {
                handleAlert(payload, root, false);
            } else if (topic.contains("iot-snapshot-alert")) {
                handleAlert(payload, root, true);
            } else if (topic.contains("iot-post-process-request")) {
                handlePostProcess(payload, root);
            } else {
                log.debug("[IotAlgoBusMqttHandler] 忽略未处理算法 Topic: {}", topic);
            }
        } catch (Exception e) {
            log.error("[IotAlgoBusMqttHandler] 处理失败 topic={} err={}", topic, e.getMessage(), e);
        }
    }

    private void handleAlert(JsonNode payload, JsonNode root, boolean snapshot) throws Exception {
        JsonNode normalized = normalizeAlertPayload(payload);
        AlertNotificationMessage msg = objectMapper.treeToValue(normalized, AlertNotificationMessage.class);
        if (msg.getAlert() == null) {
            AlertNotificationMessage.AlertInfo info =
                    objectMapper.treeToValue(normalized, AlertNotificationMessage.AlertInfo.class);
            msg.setAlert(info);
        }
        ensureAlertRequiredFields(msg, normalized, snapshot);
        if (msg.getDeviceId() == null && normalized.has("device_id")) {
            msg.setDeviceId(normalized.get("device_id").asText());
        }
        if (msg.getDeviceName() == null && normalized.has("device_name")) {
            msg.setDeviceName(normalized.get("device_name").asText());
        }
        if (msg.getTaskId() == null) {
            Long tid = readLong(normalized, "task_id", "taskId");
            if (tid != null) {
                msg.setTaskId(tid.intValue());
            }
        }
        fillEdgeFromNodes(msg, normalized, root);
        enrichNotificationFromVideoDb(msg, snapshot);

        if (!applyAlertClassFilter(msg, snapshot)) {
            log.info("[IotAlgoBusMqttHandler] 告警类别过滤跳过 deviceId={}", msg.getDeviceId());
            return;
        }

        Integer alertId;
        if (snapshot) {
            alertId = alertService.processSnapshotAlert(msg);
        } else {
            alertId = alertService.processAlert(msg);
        }
        if (alertId != null) {
            msg.setAlertId(alertId);
        }
        maybeForwardNotification(msg, alertId);
        log.debug("[IotAlgoBusMqttHandler] 告警已处理 alertId={} deviceId={} snapshot={}",
                alertId, msg.getDeviceId(), snapshot);
    }

    private void handlePostProcess(JsonNode payload, JsonNode root) throws Exception {
        if (postProcessService == null) {
            log.warn("[IotAlgoBusMqttHandler] PostProcessService 不可用，跳过");
            return;
        }
        PostProcessRequestMessage req = objectMapper.treeToValue(payload, PostProcessRequestMessage.class);
        postProcessService.enqueue(req);
        log.debug("[IotAlgoBusMqttHandler] 后处理已入队 taskId={} deviceId={}",
                req.getTaskId(), req.getDeviceId());
    }

    /**
     * 兼容扁平 hook JSON：若无嵌套 alert，则构造 AlertNotificationMessage 结构。
     */
    private JsonNode normalizeAlertPayload(JsonNode payload) {
        if (payload == null || payload.isNull()) {
            return objectMapper.createObjectNode();
        }
        if (payload.has("alert") && payload.get("alert").isObject()) {
            return payload;
        }
        ObjectNode out = objectMapper.createObjectNode();
        copyText(payload, out, "device_id", "deviceId");
        copyText(payload, out, "device_name", "deviceName");
        if (payload.has("task_id")) {
            out.set("task_id", payload.get("task_id"));
        } else if (payload.has("taskId")) {
            out.set("task_id", payload.get("taskId"));
        }
        if (payload.has("task_name")) {
            out.set("task_name", payload.get("task_name"));
        } else if (payload.has("taskName")) {
            out.set("task_name", payload.get("taskName"));
        }
        if (payload.has("correlation_id")) {
            out.set("correlation_id", payload.get("correlation_id"));
        } else if (payload.has("correlationId")) {
            out.set("correlation_id", payload.get("correlationId"));
        }
        if (payload.has("timestamp")) {
            out.set("timestamp", payload.get("timestamp"));
        } else if (payload.has("time")) {
            out.set("timestamp", payload.get("time"));
        }
        if (payload.has("faceDetectionEnabled")) {
            out.set("faceDetectionEnabled", payload.get("faceDetectionEnabled"));
        } else if (payload.has("face_detection_enabled")) {
            out.set("faceDetectionEnabled", payload.get("face_detection_enabled"));
        }
        if (payload.has("plateDetectionEnabled")) {
            out.set("plateDetectionEnabled", payload.get("plateDetectionEnabled"));
        } else if (payload.has("plate_detection_enabled")) {
            out.set("plateDetectionEnabled", payload.get("plate_detection_enabled"));
        }

        ObjectNode alert = objectMapper.createObjectNode();
        if (payload.has("object")) {
            alert.set("object", payload.get("object"));
        } else if (payload.has("type")) {
            // 兼容 type 误用为检测对象名的扁平 payload
            alert.set("object", payload.get("type"));
        } else {
            alert.put("object", "object");
        }
        if (payload.has("event")) {
            alert.set("event", payload.get("event"));
        } else {
            alert.put("event", "detection");
        }
        if (payload.has("region")) alert.set("region", payload.get("region"));
        if (payload.has("information")) alert.set("information", payload.get("information"));
        if (payload.has("image_path")) {
            alert.set("image_path", payload.get("image_path"));
        } else if (payload.has("imagePath")) {
            alert.set("image_path", payload.get("imagePath"));
        }
        if (payload.has("record_path")) {
            alert.set("record_path", payload.get("record_path"));
        } else if (payload.has("recordPath")) {
            alert.set("record_path", payload.get("recordPath"));
        }
        if (payload.has("time")) alert.set("time", payload.get("time"));
        if (payload.has("task_type")) {
            alert.set("task_type", payload.get("task_type"));
            out.set("task_type", payload.get("task_type"));
        }
        out.set("alert", alert);
        return out;
    }

    /**
     * 保证 alert.object / event 非空（PG NOT NULL），兼容 type 别名与缺省字段。
     */
    private void ensureAlertRequiredFields(AlertNotificationMessage msg, JsonNode normalized, boolean snapshot) {
        if (msg.getAlert() == null) {
            msg.setAlert(new AlertNotificationMessage.AlertInfo());
        }
        AlertNotificationMessage.AlertInfo alert = msg.getAlert();
        if (StrUtil.isBlank(alert.getObject())) {
            String fallback = null;
            if (normalized != null) {
                if (normalized.has("object") && !normalized.get("object").isNull()) {
                    fallback = normalized.get("object").asText();
                } else if (normalized.has("type") && !normalized.get("type").isNull()) {
                    fallback = normalized.get("type").asText();
                } else if (normalized.has("alert") && normalized.get("alert").isObject()) {
                    JsonNode nested = normalized.get("alert");
                    if (nested.has("object") && !nested.get("object").isNull()) {
                        fallback = nested.get("object").asText();
                    } else if (nested.has("type") && !nested.get("type").isNull()) {
                        fallback = nested.get("type").asText();
                    }
                }
            }
            alert.setObject(StrUtil.isNotBlank(fallback) ? fallback : "object");
        }
        if (StrUtil.isBlank(alert.getEvent())) {
            alert.setEvent("detection");
        }
        if (StrUtil.isBlank(alert.getTaskType())) {
            alert.setTaskType(snapshot ? "snap" : "realtime");
        }
    }

    private void copyText(JsonNode src, ObjectNode dst, String snake, String camel) {
        if (src.has(snake) && !src.get(snake).isNull()) {
            dst.set(snake, src.get(snake));
        } else if (src.has(camel) && !src.get(camel).isNull()) {
            dst.set(snake, src.get(camel));
        }
    }

    /**
     * 从 VIDEO.algorithm_task 补齐通知渠道（执行侧不查库）。
     */
    private void enrichNotificationFromVideoDb(AlertNotificationMessage msg, boolean snapshot) {
        if (msg == null || jdbcTemplate == null) {
            return;
        }
        if (Boolean.TRUE.equals(msg.getShouldNotify())
                && msg.getChannels() != null && !msg.getChannels().isEmpty()) {
            return;
        }
        String deviceId = msg.getDeviceId();
        if (StrUtil.isBlank(deviceId)) {
            return;
        }
        String taskType = null;
        if (msg.getAlert() != null && StrUtil.isNotBlank(msg.getAlert().getTaskType())) {
            taskType = msg.getAlert().getTaskType();
        }
        if (StrUtil.isBlank(taskType)) {
            taskType = snapshot ? "snap" : "realtime";
        }
        if ("snapshot".equalsIgnoreCase(taskType)) {
            taskType = "snap";
        }

        try {
            DynamicDataSourceContextHolder.push("video");
            String sql = "SELECT at.id, at.task_name, at.alert_notification_config, "
                    + "at.face_detection_enabled, at.plate_detection_enabled "
                    + "FROM algorithm_task at "
                    + "INNER JOIN algorithm_task_device atd ON at.id = atd.task_id "
                    + "WHERE atd.device_id = ? AND at.alert_event_enabled = true "
                    + "AND at.alert_notification_enabled = true AND at.is_enabled = true "
                    + "AND at.task_type = ? LIMIT 1";
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(sql, deviceId, taskType);
            if (rows == null || rows.isEmpty()) {
                // 仍允许仅落库：确认是否有启用的告警事件任务
                String eventSql = "SELECT at.id FROM algorithm_task at "
                        + "INNER JOIN algorithm_task_device atd ON at.id = atd.task_id "
                        + "WHERE atd.device_id = ? AND at.alert_event_enabled = true "
                        + "AND at.is_enabled = true AND at.task_type = ? LIMIT 1";
                List<Map<String, Object>> eventRows = jdbcTemplate.queryForList(eventSql, deviceId, taskType);
                if (eventRows == null || eventRows.isEmpty()) {
                    log.debug("[IotAlgoBusMqttHandler] 设备未关联告警事件任务，仍尝试落库: deviceId={} taskType={}",
                            deviceId, taskType);
                }
                msg.setShouldNotify(false);
                return;
            }
            Map<String, Object> row = rows.get(0);
            Object tid = row.get("id");
            if (tid instanceof Number && msg.getTaskId() == null) {
                msg.setTaskId(((Number) tid).intValue());
            }
            Object tname = row.get("task_name");
            if (tname != null && StrUtil.isBlank(msg.getTaskName())) {
                msg.setTaskName(String.valueOf(tname));
            }
            Object face = row.get("face_detection_enabled");
            if (msg.getFaceDetectionEnabled() == null && face instanceof Boolean) {
                msg.setFaceDetectionEnabled((Boolean) face);
            }
            Object plate = row.get("plate_detection_enabled");
            if (msg.getPlateDetectionEnabled() == null && plate instanceof Boolean) {
                msg.setPlateDetectionEnabled((Boolean) plate);
            }

            Object cfgRaw = row.get("alert_notification_config");
            if (cfgRaw == null || StrUtil.isBlank(String.valueOf(cfgRaw))) {
                msg.setShouldNotify(false);
                return;
            }
            JsonNode cfgNode = objectMapper.readTree(String.valueOf(cfgRaw));
            List<Map<String, Object>> channels = new ArrayList<>();
            List<Map<String, Object>> notifyUsers = new ArrayList<>();
            List<String> notifyMethods = new ArrayList<>();
            if (cfgNode != null && cfgNode.isObject()) {
                JsonNode channelsNode = cfgNode.get("channels");
                if (channelsNode != null && channelsNode.isArray()) {
                    for (JsonNode ch : channelsNode) {
                        @SuppressWarnings("unchecked")
                        Map<String, Object> m = objectMapper.convertValue(ch, Map.class);
                        channels.add(m);
                        Object method = m.get("method");
                        if (method != null) {
                            notifyMethods.add(String.valueOf(method));
                        }
                    }
                }
                JsonNode usersNode = cfgNode.get("notify_users");
                if (usersNode != null && usersNode.isArray()) {
                    for (JsonNode u : usersNode) {
                        @SuppressWarnings("unchecked")
                        Map<String, Object> m = objectMapper.convertValue(u, Map.class);
                        notifyUsers.add(m);
                    }
                }
            }
            msg.setChannels(channels);
            msg.setNotifyUsers(notifyUsers);
            msg.setNotifyMethods(notifyMethods);
            boolean hasConfig = hasAlertNotificationConfig(channels, notifyUsers);
            msg.setShouldNotify(hasConfig);
            log.debug("[IotAlgoBusMqttHandler] 已从 VIDEO 库补齐通知配置 deviceId={} channels={} users={}",
                    deviceId, channels.size(), notifyUsers.size());
        } catch (Exception e) {
            log.warn("[IotAlgoBusMqttHandler] 通知 enrichment 失败 deviceId={}: {}", deviceId, e.getMessage());
            if (msg.getShouldNotify() == null) {
                msg.setShouldNotify(false);
            }
        } finally {
            try {
                DynamicDataSourceContextHolder.poll();
            } catch (Exception ignored) {
                // ignore
            }
        }
    }

    private void maybeForwardNotification(AlertNotificationMessage msg, Integer alertId) {
        if (msg == null || alertId == null) {
            return;
        }
        List<Map<String, Object>> channels = msg.getChannels();
        List<Map<String, Object>> notifyUsers = msg.getNotifyUsers();
        Boolean shouldNotify = msg.getShouldNotify();
        boolean hasConfig = hasAlertNotificationConfig(channels, notifyUsers);
        if (shouldNotify == null) {
            shouldNotify = hasConfig;
        }
        if (!Boolean.TRUE.equals(shouldNotify) || !hasConfig) {
            return;
        }
        if (kafkaTemplate == null) {
            log.warn("[IotAlgoBusMqttHandler] KafkaTemplate 不可用，无法转发通知 alertId={}", alertId);
            return;
        }
        try {
            String json = JsonUtils.toJsonString(msg);
            kafkaTemplate.send(notificationSendTopic, msg.getDeviceId(), json);
            log.debug("[IotAlgoBusMqttHandler] 通知已转发 topic={} alertId={} deviceId={}",
                    notificationSendTopic, alertId, msg.getDeviceId());
        } catch (Exception e) {
            log.error("[IotAlgoBusMqttHandler] 通知转发失败 alertId={}: {}", alertId, e.getMessage(), e);
        }
    }

    private static boolean hasAlertNotificationConfig(
            List<Map<String, Object>> channels,
            List<Map<String, Object>> notifyUsers) {
        if (channels == null || channels.isEmpty()) {
            return false;
        }
        if (notifyUsers != null && !notifyUsers.isEmpty()) {
            return true;
        }
        return channels.stream().anyMatch(IotAlgoBusMqttHandler::isUserlessAlertChannel);
    }

    private static boolean isUserlessAlertChannel(Map<String, Object> channel) {
        if (channel == null) {
            return false;
        }
        if (Boolean.TRUE.equals(channel.get("userless"))) {
            return true;
        }
        Object method = channel.get("method");
        if (method == null) {
            return false;
        }
        String m = method.toString().toLowerCase();
        if ("http".equals(m) || "webhook".equals(m)) {
            return true;
        }
        Object templateId = channel.get("template_id");
        if (templateId == null) {
            return false;
        }
        return "wxcp".equals(m) || "wechat".equals(m) || "weixin".equals(m)
                || "ding".equals(m) || "dingtalk".equals(m)
                || "feishu".equals(m) || "lark".equals(m);
    }

    private void fillEdgeFromNodes(AlertNotificationMessage msg, JsonNode payload, JsonNode root) {
        if (msg.getEdgeNodeId() == null) {
            Long id = readLong(payload, "edge_node_id", "edgeNodeId");
            if (id == null) {
                id = readLong(root, "edge_node_id", "edgeNodeId");
            }
            msg.setEdgeNodeId(id);
        }
        if (StrUtil.isBlank(msg.getEdgeNodeName())) {
            msg.setEdgeNodeName(readText(payload, "edge_node_name", "edgeNodeName"));
        }
        if (StrUtil.isBlank(msg.getEdgeNodeHost())) {
            msg.setEdgeNodeHost(readText(payload, "edge_node_host", "edgeNodeHost"));
        }
        if (msg.getNodeId() == null) {
            msg.setNodeId(readLong(payload, "node_id", "nodeId", "compute_node_id"));
        }
    }

    private Long readLong(JsonNode node, String... names) {
        if (node == null) {
            return null;
        }
        for (String name : names) {
            if (node.has(name) && !node.get(name).isNull()) {
                return node.get(name).asLong();
            }
        }
        return null;
    }

    private String readText(JsonNode node, String... names) {
        if (node == null) {
            return null;
        }
        for (String name : names) {
            if (node.has(name) && !node.get(name).isNull()) {
                return node.get(name).asText();
            }
        }
        return null;
    }

    /**
     * 按 VIDEO 算法任务 alert_class_names 过滤 MQTT 告警（与 alert_hook_service 一致）。
     * @return false 表示应跳过落库
     */
    @SuppressWarnings("unchecked")
    private boolean applyAlertClassFilter(AlertNotificationMessage msg, boolean snapshot) {
        if (msg == null || msg.getAlert() == null || jdbcTemplate == null) {
            return true;
        }
        String deviceId = msg.getDeviceId();
        if (StrUtil.isBlank(deviceId)) {
            return true;
        }
        String taskType = msg.getAlert().getTaskType();
        if (StrUtil.isBlank(taskType)) {
            taskType = snapshot ? "snap" : "realtime";
        }
        if ("snapshot".equalsIgnoreCase(taskType)) {
            taskType = "snap";
        }

        Object alertClassNamesRaw = null;
        try {
            DynamicDataSourceContextHolder.push("video");
            String sql = "SELECT at.alert_class_names FROM algorithm_task at "
                    + "INNER JOIN algorithm_task_device atd ON at.id = atd.task_id "
                    + "WHERE atd.device_id = ? AND at.alert_event_enabled = true "
                    + "AND at.is_enabled = true AND at.task_type = ? "
                    + "ORDER BY at.id ASC LIMIT 1";
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(sql, deviceId, taskType);
            if (rows == null || rows.isEmpty()) {
                return true;
            }
            alertClassNamesRaw = rows.get(0).get("alert_class_names");
        } catch (Exception e) {
            log.warn("[IotAlgoBusMqttHandler] 查询 alert_class_names 失败 deviceId={}: {}",
                    deviceId, e.getMessage());
            return true;
        } finally {
            DynamicDataSourceContextHolder.clear();
        }

        List<String> allowed = AlertClassFilter.parseAlertClassNames(alertClassNamesRaw);
        if (allowed.isEmpty()) {
            return true;
        }

        AlertNotificationMessage.AlertInfo alert = msg.getAlert();
        Object information = alert.getInformation();
        Map<String, Object> infoMap = null;
        if (information instanceof Map) {
            infoMap = new LinkedHashMap<>((Map<String, Object>) information);
        } else if (information instanceof String && StrUtil.isNotBlank((String) information)) {
            try {
                infoMap = objectMapper.readValue((String) information, Map.class);
            } catch (Exception ignored) {
                infoMap = null;
            }
        }
        if (infoMap == null) {
            String objectName = alert.getObject();
            if (StrUtil.isBlank(objectName)) {
                return true;
            }
            List<Map<String, Object>> single = new ArrayList<>();
            Map<String, Object> det = new LinkedHashMap<>();
            det.put("class_name", objectName);
            single.add(det);
            List<Map<String, Object>> filtered = AlertClassFilter.filterDetectionsForAlert(single, allowed);
            if (filtered.isEmpty()) {
                return false;
            }
            return true;
        }

        Object detectionsObj = infoMap.get("detections");
        if (!(detectionsObj instanceof List)) {
            String objectName = alert.getObject();
            if (StrUtil.isBlank(objectName)) {
                return true;
            }
            List<Map<String, Object>> single = new ArrayList<>();
            Map<String, Object> det = new LinkedHashMap<>();
            det.put("class_name", objectName);
            single.add(det);
            return !AlertClassFilter.filterDetectionsForAlert(single, allowed).isEmpty();
        }

        List<Map<String, Object>> detections = (List<Map<String, Object>>) detectionsObj;
        List<Map<String, Object>> filtered = AlertClassFilter.filterDetectionsForAlert(detections, allowed);
        if (filtered.isEmpty()) {
            return false;
        }

        infoMap.put("detections", filtered);
        infoMap.put("detection_count", filtered.size());
        infoMap.put("total_count", filtered.size());
        Map<String, Integer> objectCounts = new LinkedHashMap<>();
        for (Map<String, Object> det : filtered) {
            Object rawName = det.get("class_name");
            if (rawName == null) {
                rawName = det.get("className");
            }
            String className = rawName != null ? String.valueOf(rawName) : "unknown";
            objectCounts.merge(className, 1, Integer::sum);
        }
        infoMap.put("object_counts", objectCounts);
        alert.setInformation(infoMap);
        String primary = objectCounts.entrySet().stream()
                .max(Map.Entry.comparingByValue())
                .map(Map.Entry::getKey)
                .orElse(alert.getObject());
        if (StrUtil.isNotBlank(primary)) {
            alert.setObject(primary);
        }
        return true;
    }

}
