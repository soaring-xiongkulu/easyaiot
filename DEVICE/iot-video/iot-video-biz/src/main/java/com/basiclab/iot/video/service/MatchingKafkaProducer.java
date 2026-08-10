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

/**
 * Publishes face/plate matching messages to the same Kafka topics as retired Python
 * ({@code iot-face-matching} / {@code iot-plate-matching}).
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class MatchingKafkaProducer {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final KafkaTemplate<String, String> alertKafkaTemplate;
    private final VideoProperties videoProperties;

    public boolean publishFace(Map<String, Object> message) {
        String topic = videoProperties.getMatching().getFaceMatchingTopic();
        String key = resolveKey(message, "face");
        return send(topic, key, message, "face");
    }

    public boolean publishPlate(Map<String, Object> message) {
        String topic = videoProperties.getMatching().getPlateMatchingTopic();
        String key = resolveKey(message, "plate");
        return send(topic, key, message, "plate");
    }

    private boolean send(String topic, String key, Map<String, Object> message, String kind) {
        try {
            String payload = MAPPER.writeValueAsString(message);
            ListenableFuture<SendResult<String, String>> future = alertKafkaTemplate.send(topic, key, payload);
            SendResult<String, String> result = future.get(
                    videoProperties.getKafka().getSendTimeoutMs(),
                    TimeUnit.MILLISECONDS
            );
            log.info(
                    "{} matching kafka sent: topic={}, deviceId={}, libraryId={}, partition={}, offset={}",
                    kind,
                    result.getRecordMetadata().topic(),
                    message.get("deviceId"),
                    message.get("libraryId"),
                    result.getRecordMetadata().partition(),
                    result.getRecordMetadata().offset()
            );
            return true;
        } catch (Exception ex) {
            log.error(
                    "{} matching kafka send failed: topic={}, deviceId={}, libraryId={}, error={}",
                    kind,
                    topic,
                    message.get("deviceId"),
                    message.get("libraryId"),
                    ex.getMessage()
            );
            return false;
        }
    }

    private static String resolveKey(Map<String, Object> message, String fallback) {
        Object deviceId = message.get("deviceId");
        if (deviceId != null && !String.valueOf(deviceId).isBlank()) {
            return String.valueOf(deviceId);
        }
        Object taskId = message.get("taskId");
        if (taskId != null && !String.valueOf(taskId).isBlank()) {
            return String.valueOf(taskId);
        }
        return fallback;
    }
}
