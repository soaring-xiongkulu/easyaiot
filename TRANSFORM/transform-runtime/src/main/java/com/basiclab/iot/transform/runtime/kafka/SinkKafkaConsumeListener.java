package com.basiclab.iot.transform.runtime.kafka;

import com.basiclab.iot.transform.channel.kafka.KafkaIngressChannel;
import com.basiclab.iot.transform.core.contract.SinkKafkaTopics;
import com.basiclab.iot.transform.core.envelope.TransformEnvelope;
import com.basiclab.iot.transform.core.group.GroupNames;
import com.basiclab.iot.transform.core.spi.TransformChannel;
import com.basiclab.iot.transform.runtime.service.DeliveryPipelineService;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.autoconfigure.condition.ConditionalOnExpression;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * 从 iot-sink Kafka 消费并归一化。使用约定 Group，多实例自动再均衡扩展消费能力。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Component
@ConditionalOnProperty(prefix = "transform.channels", name = "kafka", havingValue = "true", matchIfMissing = true)
@ConditionalOnExpression("'${transform.role:full}' != 'edge'")
public class SinkKafkaConsumeListener {

    private final KafkaIngressChannel kafkaIngressChannel;
    private final DeliveryPipelineService pipeline;

    public SinkKafkaConsumeListener(List<TransformChannel> channels,
                                    DeliveryPipelineService pipeline) {
        this.kafkaIngressChannel = channels.stream()
                .filter(c -> c instanceof KafkaIngressChannel)
                .map(c -> (KafkaIngressChannel) c)
                .findFirst()
                .orElseThrow(() -> new IllegalStateException("KafkaIngressChannel not enabled"));
        this.pipeline = pipeline;
    }

    @KafkaListener(
            topics = {
                    SinkKafkaTopics.DEVICE_MESSAGE,
                    SinkKafkaTopics.ALERT_NOTIFICATION,
                    SinkKafkaTopics.SNAPSHOT_ALERT,
                    SinkKafkaTopics.FACE_MATCHING,
                    SinkKafkaTopics.PLATE_MATCHING,
                    SinkKafkaTopics.POST_PROCESS_RESULT
            },
            groupId = GroupNames.KAFKA_CONSUME_DEVICE,
            autoStartup = "${transform.channels.kafka:true}"
    )
    public void onSinkRecord(ConsumerRecord<String, String> record, Acknowledgment acknowledgment) {
        try {
            TransformEnvelope envelope = kafkaIngressChannel.normalize(record.topic(), record.key(), record.value());
            boolean accepted = pipeline.accept(envelope);
            if (accepted) {
                acknowledgment.acknowledge();
            } else {
                // 已写入 DLQ，提交以避免坏消息无限阻塞分区。
                acknowledgment.acknowledge();
            }
        } catch (Exception e) {
            log.error("[SinkKafkaConsumeListener] processing failed topic={}", record.topic(), e);
            acknowledgment.acknowledge();
        }
    }
}
