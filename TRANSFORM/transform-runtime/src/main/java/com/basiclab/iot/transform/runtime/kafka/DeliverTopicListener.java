package com.basiclab.iot.transform.runtime.kafka;

import com.basiclab.iot.transform.capability.deliver.RetryDeliverSupport;
import com.basiclab.iot.transform.core.channel.ChannelType;
import com.basiclab.iot.transform.core.contract.TransformTopics;
import com.basiclab.iot.transform.core.domain.OutboxRecord;
import com.basiclab.iot.transform.core.envelope.TransformEnvelope;
import com.basiclab.iot.transform.core.spi.TransformChannel;
import com.basiclab.iot.transform.runtime.service.DeliveryPipelineService;
import com.basiclab.iot.transform.runtime.service.MetricsService;
import com.basiclab.iot.transform.runtime.dal.TransformRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.boot.autoconfigure.condition.ConditionalOnExpression;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.time.Instant;
import java.util.List;

/**
 * 内部投递 Topic 消费者：各渠道约定 Group 横向扩展投递。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnExpression("'${transform.role:full}' != 'consume' && '${transform.role:full}' != 'backup'")
public class DeliverTopicListener {

    private final List<TransformChannel> channels;
    private final ObjectMapper objectMapper;
    private final TransformRepository repository;
    private final DeliveryPipelineService pipeline;
    private final MetricsService metricsService;

    @KafkaListener(
            topics = TransformTopics.DELIVER,
            groupId = "transform.http.deliver",
            autoStartup = "${transform.channels.http:true}"
    )
    public void onHttp(ConsumerRecord<String, String> record, Acknowledgment ack) {
        consume(record, ack, "http", ChannelType.HTTP);
    }

    @KafkaListener(
            topics = TransformTopics.DELIVER,
            groupId = "transform.party.deliver",
            autoStartup = "${transform.channels.party:true}"
    )
    public void onParty(ConsumerRecord<String, String> record, Acknowledgment ack) {
        consume(record, ack, "party", ChannelType.PARTY);
    }

    private void consume(ConsumerRecord<String, String> record, Acknowledgment ack,
                         String expectedChannel, ChannelType type) {
        try {
            TransformEnvelope envelope = objectMapper.readValue(record.value(), TransformEnvelope.class);
            Object channel = envelope.getHeaders().get("channel");
            if (!expectedChannel.equals(String.valueOf(channel))) {
                ack.acknowledge();
                return;
            }
            String outboxId = String.valueOf(envelope.getHeaders().get("outboxId"));
            OutboxRecord outbox = repository.outbox(outboxId);
            try {
                RetryDeliverSupport.execute(() -> {
                    TransformChannel target = channels.stream()
                            .filter(c -> c.type() == type)
                            .findFirst()
                            .orElseThrow(() -> new IllegalStateException("channel not enabled: " + type));
                    target.deliver(envelope);
                    return null;
                }, 3, Duration.ofMillis(200));
                if (outbox != null) {
                    outbox.setStatus("DELIVERED");
                    outbox.setUpdatedAt(Instant.now());
                    repository.saveOutbox(outbox, null, null);
                }
                metricsService.incDelivered();
            } catch (Exception ex) {
                if (outbox != null) {
                    outbox.setStatus("FAILED");
                    outbox.setAttempts(outbox.getAttempts() + 1);
                    outbox.setError(ex.toString());
                    outbox.setUpdatedAt(Instant.now());
                    repository.saveOutbox(outbox, Instant.now(), null);
                }
                pipeline.dlq("deliver", outboxId, envelope, ex);
                metricsService.incFailed();
            }
            ack.acknowledge();
        } catch (Exception ex) {
            log.error("[DeliverTopicListener] deserialize/process failed", ex);
            ack.acknowledge();
        }
    }
}
