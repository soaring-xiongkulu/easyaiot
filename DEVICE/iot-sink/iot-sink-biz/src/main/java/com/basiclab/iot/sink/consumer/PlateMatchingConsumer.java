package com.basiclab.iot.sink.consumer;

import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.domain.model.PlateMatchingMessage;
import com.basiclab.iot.sink.service.PlateMatchingService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Component;

/**
 * 车牌匹配 Kafka 消费者（可集群部署，同一 group 负载均衡）
 */
@Slf4j
@Component
public class PlateMatchingConsumer {

    @Autowired
    private PlateMatchingService plateMatchingService;

    @KafkaListener(
            topics = "${spring.kafka.plate-matching.topic:iot-plate-matching}",
            groupId = "${spring.kafka.plate-matching.group-id:iot-sink-plate-matching-consumer}",
            containerFactory = "iotKafkaListenerContainerFactory"
    )
    public void consumePlateMatching(
            @Payload String messageJson,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            @Header(KafkaHeaders.RECEIVED_PARTITION_ID) int partition,
            @Header(KafkaHeaders.OFFSET) long offset,
            Acknowledgment acknowledgment) {
        try {
            log.debug("收到车牌匹配消息: topic={}, partition={}, offset={}", topic, partition, offset);
            if (messageJson == null || messageJson.isEmpty()) {
                if (acknowledgment != null) {
                    acknowledgment.acknowledge();
                }
                return;
            }

            PlateMatchingMessage message = JsonUtils.parseObject(messageJson, PlateMatchingMessage.class);
            if (message == null) {
                log.error("车牌匹配消息解析失败");
                if (acknowledgment != null) {
                    acknowledgment.acknowledge();
                }
                return;
            }

            plateMatchingService.process(message);

            if (acknowledgment != null) {
                acknowledgment.acknowledge();
            }
        } catch (Exception e) {
            log.error("处理车牌匹配消息失败: error={}", e.getMessage(), e);
            // 失败不 ACK，允许 Kafka 重投
        }
    }
}
