package com.basiclab.iot.sink.consumer;

import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.domain.model.FaceMatchingMessage;
import com.basiclab.iot.sink.service.FaceMatchingService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Component;

/**
 * 人脸匹配 Kafka 消费者（可集群部署，同一 group 负载均衡）
 */
@Slf4j
@Component
public class FaceMatchingConsumer {

    @Autowired
    private FaceMatchingService faceMatchingService;

    @KafkaListener(
            topics = "${spring.kafka.face-matching.topic:iot-face-matching}",
            groupId = "${spring.kafka.face-matching.group-id:iot-sink-face-matching-consumer}",
            containerFactory = "iotKafkaListenerContainerFactory"
    )
    public void consumeFaceMatching(
            @Payload String messageJson,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            @Header(KafkaHeaders.RECEIVED_PARTITION_ID) int partition,
            @Header(KafkaHeaders.OFFSET) long offset,
            Acknowledgment acknowledgment) {
        try {
            log.debug("收到人脸匹配消息: topic={}, partition={}, offset={}", topic, partition, offset);
            if (messageJson == null || messageJson.isEmpty()) {
                if (acknowledgment != null) {
                    acknowledgment.acknowledge();
                }
                return;
            }

            FaceMatchingMessage message = JsonUtils.parseObject(messageJson, FaceMatchingMessage.class);
            if (message == null) {
                log.error("人脸匹配消息解析失败");
                if (acknowledgment != null) {
                    acknowledgment.acknowledge();
                }
                return;
            }

            faceMatchingService.process(message);

            if (acknowledgment != null) {
                acknowledgment.acknowledge();
            }
        } catch (Exception e) {
            log.error("处理人脸匹配消息失败: error={}", e.getMessage(), e);
            // 失败不 ACK，允许 Kafka 重投
        }
    }
}
