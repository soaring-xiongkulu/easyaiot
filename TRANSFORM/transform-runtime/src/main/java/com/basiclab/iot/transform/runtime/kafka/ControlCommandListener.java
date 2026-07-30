package com.basiclab.iot.transform.runtime.kafka;

import com.basiclab.iot.transform.core.control.TransformCommand;
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
 * 下行指令通道：每实例独立 Group，保证广播可达。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ControlCommandListener {

    private final ObjectMapper objectMapper;
    private final ClusterControlService clusterControlService;

    @KafkaListener(
            topics = TransformTopics.COMMAND,
            groupId = "transform.command.${transform.instance-id:local}",
            autoStartup = "true"
    )
    public void onCommand(ConsumerRecord<String, String> record, Acknowledgment ack) {
        try {
            TransformCommand command = objectMapper.readValue(record.value(), TransformCommand.class);
            clusterControlService.handleCommand(command);
            ack.acknowledge();
        } catch (Exception e) {
            log.error("[ControlCommandListener] handle failed", e);
            ack.acknowledge();
        }
    }
}
