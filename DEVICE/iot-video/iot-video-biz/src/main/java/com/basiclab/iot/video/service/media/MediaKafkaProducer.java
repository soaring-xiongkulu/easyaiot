package com.basiclab.iot.video.service.media;

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
public class MediaKafkaProducer {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final KafkaTemplate<String, String> alertKafkaTemplate;
    private final VideoProperties videoProperties;

    public boolean publishDvrEvent(Map<String, Object> event) {
        String deviceId = firstNonBlank(
                stringField(event, "device_id"),
                stringField(event, "stream"),
                "unknown"
        );
        return send(videoProperties.getMedia().getDvrCompletedTopic(), deviceId, event);
    }

    public void publishDvrDlq(Map<String, Object> event, String error) {
        Map<String, Object> payload = new java.util.HashMap<>(event);
        payload.put("error", error);
        payload.put("dlq_at", java.time.Instant.now().toString());
        send(videoProperties.getMedia().getDvrDlqTopic(), stringField(event, "device_id"), payload);
    }

    public boolean publishSnapEvent(Map<String, Object> event) {
        String deviceId = firstNonBlank(stringField(event, "device_id"), "unknown");
        return send(videoProperties.getMedia().getSnapCompletedTopic(), deviceId, event);
    }

    public void publishSnapDlq(Map<String, Object> event, String error) {
        Map<String, Object> payload = new java.util.HashMap<>(event);
        payload.put("error", error);
        payload.put("dlq_at", java.time.Instant.now().toString());
        send(videoProperties.getMedia().getSnapDlqTopic(), stringField(event, "device_id"), payload);
    }

    private boolean send(String topic, String key, Map<String, Object> message) {
        try {
            String payload = MAPPER.writeValueAsString(message);
            ListenableFuture<SendResult<String, String>> future = alertKafkaTemplate.send(topic, key, payload);
            future.get(videoProperties.getKafka().getSendTimeoutMs(), TimeUnit.MILLISECONDS);
            log.debug("media kafka sent topic={} deviceId={} file={}", topic, key, message.get("file_path"));
            return true;
        } catch (Exception ex) {
            log.error("media kafka send failed topic={} deviceId={} error={}", topic, key, ex.getMessage());
            return false;
        }
    }

    private static String stringField(Map<String, Object> data, String key) {
        if (data == null || data.get(key) == null) {
            return "";
        }
        return String.valueOf(data.get(key)).trim();
    }

    private static String firstNonBlank(String... values) {
        for (String value : values) {
            if (value != null && !value.isBlank()) {
                return value;
            }
        }
        return "";
    }
}
