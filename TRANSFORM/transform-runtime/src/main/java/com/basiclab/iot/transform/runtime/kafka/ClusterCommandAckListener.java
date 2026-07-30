package com.basiclab.iot.transform.runtime.kafka;

import com.basiclab.iot.transform.core.control.TransformCommandAck;
import com.basiclab.iot.transform.core.contract.TransformTopics;
import com.basiclab.iot.transform.runtime.service.ClusterControlService;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;

/**
 * 汇聚各实例指令回执，供管理 API 轮询。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ClusterCommandAckListener {

    private final ObjectMapper objectMapper;
    private final ClusterControlService clusterControlService;

    @KafkaListener(
            topics = TransformTopics.COMMAND_ACK,
            groupId = "transform.command.ack.${transform.instance-id:local}",
            autoStartup = "true"
    )
    public void onAck(ConsumerRecord<String, String> record, Acknowledgment ack) {
        try {
            TransformCommandAck body = objectMapper.readValue(record.value(), TransformCommandAck.class);
            clusterControlService.ingestAck(body);
            ack.acknowledge();
        } catch (Exception e) {
            log.warn("[ClusterCommandAckListener] ingest failed: {}", e.getMessage());
            ack.acknowledge();
        }
    }
}
