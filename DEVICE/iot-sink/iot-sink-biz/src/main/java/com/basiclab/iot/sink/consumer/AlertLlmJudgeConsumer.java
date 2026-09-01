package com.basiclab.iot.sink.consumer;

import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.domain.model.LlmJudgeRequestMessage;
import com.basiclab.iot.sink.service.LlmJudgeService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Component;

/**
 * 大模型（LLM）研判请求独立队列消费者（与告警消费线程隔离，慢链路不阻塞主链路）。
 *
 * 处理失败不 ack，触发 Kafka 重新投递；LLM 调用与回写均在本线程完成。
 */
@Slf4j
@Component
public class AlertLlmJudgeConsumer {

    @Autowired(required = false)
    private LlmJudgeService llmJudgeService;

    @KafkaListener(
            topics = "${spring.kafka.llm-judge.request-topic:iot-alert-llm-judge}",
            groupId = "${spring.kafka.llm-judge.group-id:iot-sink-llm-judge}",
            containerFactory = "iotLlmJudgeKafkaListenerContainerFactory"
    )
    public void consumeJudgeRequest(
            @Payload String messageJson,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            @Header(KafkaHeaders.RECEIVED_PARTITION_ID) int partition,
            @Header(KafkaHeaders.OFFSET) long offset,
            Acknowledgment acknowledgment) {
        try {
            if (messageJson == null || messageJson.isEmpty()) {
                ack(acknowledgment);
                return;
            }
            LlmJudgeRequestMessage message = JsonUtils.parseObject(messageJson, LlmJudgeRequestMessage.class);
            if (message == null || message.getAlertId() == null) {
                log.warn("LLM 研判消息无效 topic={} offset={}", topic, offset);
                ack(acknowledgment);
                return;
            }
            llmJudgeService.executeAndWriteBack(message);
            ack(acknowledgment);
        } catch (Exception e) {
            // 不 ack：由 Kafka 重新投递（重试），仍失败时人工通过 DLT/监控处理
            log.error("LLM 研判消费失败 topic={} partition={} offset={}: {}",
                    topic, partition, offset, e.getMessage(), e);
        }
    }

    private static void ack(Acknowledgment acknowledgment) {
        if (acknowledgment != null) {
            acknowledgment.acknowledge();
        }
    }
}
