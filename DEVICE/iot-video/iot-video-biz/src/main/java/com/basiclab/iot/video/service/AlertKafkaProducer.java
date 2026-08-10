package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.stereotype.Service;
import org.springframework.util.concurrent.ListenableFuture;

import java.util.Map;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
public class AlertKafkaProducer {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final KafkaTemplate<String, String> alertKafkaTemplate;
    private final VideoProperties videoProperties;

    public String resolveTopic(String taskType) {
        String tt = taskType != null ? taskType : "realtime";
        if ("snapshot".equals(tt)) {
            tt = "snap";
        }
        if ("snap".equals(tt)) {
            return videoProperties.getAlert().getSnapshotAlertTopic();
        }
        return videoProperties.getAlert().getAlertNotificationTopic();
    }

    public SendResult<String, String> send(String topic, String deviceId, Map<String, Object> message) throws Exception {
        String payload = MAPPER.writeValueAsString(message);
        ListenableFuture<SendResult<String, String>> future = alertKafkaTemplate.send(topic, deviceId, payload);
        long timeoutMs = videoProperties.getKafka().getSendTimeoutMs();
        SendResult<String, String> result = future.get(timeoutMs, TimeUnit.MILLISECONDS);
        log.info(
                "alert hook kafka sent: deviceId={}, topic={}, partition={}, offset={}",
                deviceId,
                result.getRecordMetadata().topic(),
                result.getRecordMetadata().partition(),
                result.getRecordMetadata().offset()
        );
        return result;
    }
}
