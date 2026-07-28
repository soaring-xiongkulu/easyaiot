package com.basiclab.iot.transform.channel.kafka;

import com.basiclab.iot.transform.core.channel.ChannelType;
import com.basiclab.iot.transform.core.contract.SinkKafkaTopics;
import com.basiclab.iot.transform.core.envelope.FlowType;
import com.basiclab.iot.transform.core.envelope.TransformEnvelope;
import com.basiclab.iot.transform.core.group.GroupNames;
import com.basiclab.iot.transform.core.spi.EnvelopeNormalizer;
import com.basiclab.iot.transform.core.spi.TransformChannel;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;

import java.time.Instant;
import java.util.UUID;

/**
 * Kafka 渠道：TRANSFORM 主输入渠道。
 * <p>
 * 订阅 DEVICE/iot-sink 投递的 Topic，按约定 Group 自动加入消费集群；
 * 多实例部署即横向扩展，Kafka 负责再均衡，本渠道保持无状态。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
public class KafkaIngressChannel implements TransformChannel, EnvelopeNormalizer {

    private final ObjectMapper objectMapper;
    private volatile boolean joined;

    public KafkaIngressChannel(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    @Override
    public ChannelType type() {
        return ChannelType.KAFKA;
    }

    @Override
    public String consumeGroup() {
        return GroupNames.KAFKA_CONSUME_DEVICE;
    }

    @Override
    public void join() {
        joined = true;
        log.info("[KafkaIngressChannel] joined consume group={}, topics=[{}, {}, {}, ...]",
                consumeGroup(),
                SinkKafkaTopics.DEVICE_MESSAGE,
                SinkKafkaTopics.ALERT_NOTIFICATION,
                SinkKafkaTopics.SNAPSHOT_ALERT);
    }

    @Override
    public void leave() {
        joined = false;
        log.info("[KafkaIngressChannel] left group={}", consumeGroup());
    }

    @Override
    public boolean healthy() {
        return joined;
    }

    @Override
    public TransformEnvelope normalize(String topic, String key, String valueJson) {
        try {
            JsonNode root = objectMapper.readTree(valueJson == null ? "{}" : valueJson);
            FlowType flowType = resolveFlowType(topic);
            String eventId = text(root, "id");
            if (eventId == null || eventId.isEmpty()) {
                eventId = UUID.randomUUID().toString().replace("-", "");
            }
            String deviceId = text(root, "deviceId");
            if (deviceId == null) {
                deviceId = text(root, "device_id");
            }
            return TransformEnvelope.builder()
                    .eventId(eventId)
                    .traceId(eventId)
                    .flowType(flowType)
                    .tenantId(text(root, "tenantId"))
                    .deviceId(deviceId)
                    .sourceTopic(topic)
                    .method(text(root, "method"))
                    .eventTime(Instant.now())
                    .ingestTime(Instant.now())
                    .payload(root)
                    .partitionHint(deviceId == null ? null : Math.abs(deviceId.hashCode()))
                    .build();
        } catch (Exception e) {
            throw new IllegalArgumentException("normalize sink kafka message failed, topic=" + topic, e);
        }
    }

    private static FlowType resolveFlowType(String topic) {
        if (topic == null) {
            return FlowType.DATA;
        }
        if (SinkKafkaTopics.ALERT_NOTIFICATION.equals(topic)
                || SinkKafkaTopics.SNAPSHOT_ALERT.equals(topic)) {
            return FlowType.ALERT;
        }
        if (SinkKafkaTopics.FACE_MATCHING.equals(topic)
                || SinkKafkaTopics.PLATE_MATCHING.equals(topic)
                || SinkKafkaTopics.POST_PROCESS_RESULT.equals(topic)
                || SinkKafkaTopics.POST_PROCESS_REQUEST.equals(topic)) {
            return FlowType.VIDEO_META;
        }
        return FlowType.DATA;
    }

    private static String text(JsonNode root, String field) {
        JsonNode n = root.get(field);
        return n == null || n.isNull() ? null : n.asText();
    }
}
