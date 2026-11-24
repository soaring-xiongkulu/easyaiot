package com.basiclab.iot.sink.service.edge;

import cn.hutool.core.util.StrUtil;
import com.baomidou.dynamic.datasource.annotation.DS;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.List;
import java.util.Map;

/** Direct MQTT telemetry landing for heterogeneous edge compute boxes. */
@Slf4j
@Service
@DS("video")
public class EdgeNodeTelemetryService {

    public static final String SPEC_VERSION = "easyaiot.edge.telemetry/v1";
    private static final long MAX_CLOCK_SKEW_MS = 120_000L;

    @Resource
    private JdbcTemplate jdbcTemplate;
    @Resource
    private ObjectMapper objectMapper;

    @Transactional(rollbackFor = Exception.class)
    public void ingest(String topic, JsonNode envelope) {
        String[] parts = topic == null ? new String[0] : topic.split("/");
        if (parts.length != 4 || !"mqtt".equals(parts[0]) || !"iot-edge-node".equals(parts[1])) {
            throw new IllegalArgumentException("边缘节点 Topic 格式无效");
        }
        String action = parts[3];
        if (!("heartbeat".equals(action) || "status".equals(action) || "command-ack".equals(action))) {
            throw new IllegalArgumentException("不支持的边缘节点消息类型: " + action);
        }
        long nodeId = requiredLong(envelope, "nodeId");
        if (!String.valueOf(nodeId).equals(parts[2])) {
            throw new IllegalArgumentException("Topic nodeId 与消息信封不一致");
        }
        String specVersion = requiredText(envelope, "specVersion");
        String messageType = requiredText(envelope, "messageType");
        String messageId = requiredText(envelope, "messageId");
        long sentAt = requiredLong(envelope, "sentAt");
        String payload = requiredText(envelope, "payload");
        String signature = requiredText(envelope, "signature");
        if (!SPEC_VERSION.equals(specVersion) || !action.equals(messageType)) {
            throw new IllegalArgumentException("边缘节点协议版本或消息类型不匹配");
        }
        if (messageId.length() > 128 || Math.abs(System.currentTimeMillis() - sentAt) > MAX_CLOCK_SKEW_MS) {
            throw new IllegalArgumentException("边缘节点消息已过期或 messageId 超长");
        }

        try {
            NodeCredential credential = loadCredential(nodeId);
            verifySignature(credential.agentToken, specVersion, messageType, nodeId,
                    messageId, sentAt, payload, signature);
            JsonNode payloadNode = objectMapper.readTree(payload);
            if (!payloadNode.isObject()) {
                throw new IllegalArgumentException("边缘节点 payload 必须是 JSON 对象");
            }
            int accepted = jdbcTemplate.update(
                    "INSERT INTO edge_compute_message(node_id,message_id,message_type) VALUES (?,?,?) "
                            + "ON CONFLICT(node_id,message_id) DO NOTHING",
                    nodeId, messageId, messageType);
            if (accepted != 1) {
                throw new IllegalArgumentException("边缘节点消息重复");
            }
            if ("heartbeat".equals(action)) {
                persistHeartbeat(nodeId, messageId, payload, payloadNode);
            } else if ("status".equals(action)) {
                persistStatus(nodeId, messageId, payload, payloadNode);
            } else {
                persistCommandAck(nodeId, payload, payloadNode);
            }
        } catch (IllegalArgumentException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new IllegalArgumentException("边缘节点遥测落库失败: " + ex.getMessage(), ex);
        }
    }

    public void updateConnectionState(String username, boolean online) {
        if (StrUtil.isBlank(username) || !username.startsWith("edge-node-")) {
            return;
        }
        try {
            jdbcTemplate.update("UPDATE edge_compute_node SET status=?, "
                            + (online ? "connected_at=NOW()," : "disconnected_at=NOW(),")
                            + "updated_at=NOW() WHERE mqtt_username=? AND enabled=TRUE",
                    online ? "online" : "offline", username);
        } catch (Exception ex) {
            log.warn("[EdgeTelemetry] 更新 MQTT 连接状态失败 username={}: {}", username, ex.getMessage());
        }
    }

    private NodeCredential loadCredential(long nodeId) {
        List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                "SELECT agent_token FROM edge_compute_node WHERE id=? AND enabled=TRUE LIMIT 1", nodeId);
        if (rows.isEmpty() || rows.get(0).get("agent_token") == null) {
            throw new IllegalArgumentException("边缘节点不存在或已停用");
        }
        return new NodeCredential(String.valueOf(rows.get(0).get("agent_token")));
    }

    private void persistHeartbeat(long nodeId, String messageId, String rawPayload, JsonNode payload) {
        JsonNode remote = first(payload, "remoteAccess", "remote_access");
        JsonNode accelerator = first(payload, "acceleratorInfo", "accelerator_info");
        JsonNode pipelines = first(payload, "pipelines");
        int changed = jdbcTemplate.update("UPDATE edge_compute_node SET "
                        + "name=COALESCE(?,name), host=COALESCE(?,host), status='online', "
                        + "node_kind=COALESCE(?,node_kind), hardware_provider=COALESCE(?,hardware_provider), "
                        + "soc_model=COALESCE(?,soc_model), accelerator_type=COALESCE(?,accelerator_type), "
                        + "accelerator_count=COALESCE(?,accelerator_count), runtime_target=COALESCE(?,runtime_target), "
                        + "runtime_version=COALESCE(?,runtime_version), agent_version=COALESCE(?,agent_version), "
                        + "agent_port=COALESCE(?,agent_port), max_task_count=COALESCE(?,max_task_count), "
                        + "active_task_count=COALESCE(?,active_task_count), cpu_percent=?, mem_percent=?, "
                        + "disk_percent=?, temperature_c=?, mem_used_bytes=?, mem_total_bytes=?, "
                        + "disk_used_bytes=?, disk_total_bytes=?, "
                        + "accelerator_info=COALESCE(CAST(? AS jsonb),accelerator_info), "
                        + "pipelines=COALESCE(CAST(? AS jsonb),pipelines), "
                        + "remote_access=COALESCE(CAST(? AS jsonb),remote_access), "
                        + "latest_payload=CAST(? AS jsonb), last_message_id=?, "
                        + "last_heartbeat_at=NOW(), updated_at=NOW() WHERE id=? AND enabled=TRUE",
                text(payload, "name", "hostname"), text(payload, "host", "ip"),
                text(payload, "nodeKind", "node_kind"), text(payload, "hardwareProvider", "hardware_provider"),
                text(payload, "socModel", "soc_model"), text(payload, "acceleratorType", "accelerator_type"),
                integer(payload, "acceleratorCount", "accelerator_count"),
                text(payload, "runtimeTarget", "runtime_target"), text(payload, "runtimeVersion", "runtime_version"),
                text(payload, "agentVersion", "agent_version"), integer(payload, "agentPort", "agent_port"),
                integer(payload, "maxTaskCount", "max_task_count"), integer(payload, "activeTasks", "active_tasks"),
                decimal(payload, "cpuPercent", "cpu_percent"), decimal(payload, "memPercent", "mem_percent"),
                decimal(payload, "diskPercent", "disk_percent"), decimal(payload, "temperatureC", "temperature_c"),
                longValue(payload, "memUsedBytes", "mem_used_bytes"), longValue(payload, "memTotalBytes", "mem_total_bytes"),
                longValue(payload, "diskUsedBytes", "disk_used_bytes"), longValue(payload, "diskTotalBytes", "disk_total_bytes"),
                json(accelerator), json(pipelines), json(remote), rawPayload, messageId, nodeId);
        if (changed != 1) {
            throw new IllegalArgumentException("边缘节点不存在或已停用");
        }
        jdbcTemplate.update("INSERT INTO edge_compute_metric(node_id,cpu_percent,mem_percent,disk_percent,"
                        + "temperature_c,active_tasks,payload) VALUES (?,?,?,?,?,?,CAST(? AS jsonb))",
                nodeId, decimal(payload, "cpuPercent", "cpu_percent"),
                decimal(payload, "memPercent", "mem_percent"), decimal(payload, "diskPercent", "disk_percent"),
                decimal(payload, "temperatureC", "temperature_c"), integer(payload, "activeTasks", "active_tasks"),
                rawPayload);
    }

    private void persistStatus(long nodeId, String messageId, String rawPayload, JsonNode payload) {
        boolean online = payload.path("online").asBoolean(false);
        int changed = jdbcTemplate.update("UPDATE edge_compute_node SET status=?, latest_payload=CAST(? AS jsonb), "
                        + "last_message_id=?, updated_at=NOW(), "
                        + (online ? "connected_at=NOW() " : "disconnected_at=NOW() ")
                        + "WHERE id=? AND enabled=TRUE",
                online ? "online" : "offline", rawPayload, messageId, nodeId);
        if (changed != 1) {
            throw new IllegalArgumentException("边缘节点不存在或已停用");
        }
    }

    private void persistCommandAck(long nodeId, String rawPayload, JsonNode payload) {
        String commandId = text(payload, "commandId", "command_id");
        if (StrUtil.isBlank(commandId)) {
            throw new IllegalArgumentException("command-ack 缺少 commandId");
        }
        String status = StrUtil.blankToDefault(text(payload, "status"), "acknowledged");
        int changed = jdbcTemplate.update("UPDATE edge_compute_command SET status=?, ack_payload=CAST(? AS jsonb), ack_at=NOW() "
                        + "WHERE command_id=? AND node_id=?",
                status, rawPayload, commandId, nodeId);
        if (changed != 1) {
            throw new IllegalArgumentException("command-ack 未匹配到待处理命令");
        }
    }

    private void verifySignature(String token, String specVersion, String messageType, long nodeId,
                                 String messageId, long sentAt, String payload, String signature) throws Exception {
        String canonical = String.join("\n", specVersion, messageType, String.valueOf(nodeId),
                messageId, String.valueOf(sentAt), payload);
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(token.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        byte[] expected = mac.doFinal(canonical.getBytes(StandardCharsets.UTF_8));
        byte[] actual = hex(signature);
        if (!MessageDigest.isEqual(expected, actual)) {
            throw new IllegalArgumentException("边缘节点消息签名无效");
        }
    }

    private byte[] hex(String value) {
        if (value == null || !value.matches("[0-9a-fA-F]{64}")) {
            throw new IllegalArgumentException("边缘节点签名格式无效");
        }
        byte[] bytes = new byte[32];
        for (int i = 0; i < bytes.length; i++) {
            bytes[i] = (byte) Integer.parseInt(value.substring(i * 2, i * 2 + 2), 16);
        }
        return bytes;
    }

    private String requiredText(JsonNode node, String name) {
        String value = text(node, name);
        if (StrUtil.isBlank(value)) {
            throw new IllegalArgumentException("边缘节点消息缺少 " + name);
        }
        return value;
    }

    private long requiredLong(JsonNode node, String name) {
        Long value = longValue(node, name);
        if (value == null || value <= 0) {
            throw new IllegalArgumentException("边缘节点消息缺少 " + name);
        }
        return value;
    }

    private JsonNode first(JsonNode node, String... names) {
        if (node == null) return null;
        for (String name : names) {
            JsonNode value = node.get(name);
            if (value != null && !value.isNull()) return value;
        }
        return null;
    }

    private String text(JsonNode node, String... names) {
        JsonNode value = first(node, names);
        return value == null || value.isContainerNode() ? null : value.asText();
    }

    private Integer integer(JsonNode node, String... names) {
        JsonNode value = first(node, names);
        return value == null || !value.isNumber() ? null : value.asInt();
    }

    private Long longValue(JsonNode node, String... names) {
        JsonNode value = first(node, names);
        return value == null || !value.isNumber() ? null : value.asLong();
    }

    private Double decimal(JsonNode node, String... names) {
        JsonNode value = first(node, names);
        return value == null || !value.isNumber() ? null : value.asDouble();
    }

    private String json(JsonNode node) {
        return node == null ? null : node.toString();
    }

    private static final class NodeCredential {
        private final String agentToken;

        private NodeCredential(String agentToken) {
            this.agentToken = agentToken;
        }
    }
}
