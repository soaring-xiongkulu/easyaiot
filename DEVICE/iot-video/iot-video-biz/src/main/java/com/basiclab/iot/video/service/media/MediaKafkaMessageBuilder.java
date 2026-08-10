package com.basiclab.iot.video.service.media;

import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@Component
public class MediaKafkaMessageBuilder {

    public Map<String, Object> buildFromSrsHook(Map<String, Object> data, String deviceId) {
        String stream = stringField(data, "stream");
        String filePath = firstNonBlank(
                stringField(data, "file"),
                stringField(data, "file_path")
        );
        Long segmentStartMs = parseSegmentStartMs(filePath);
        Map<String, Object> event = new HashMap<>();
        event.put("event_id", UUID.randomUUID().toString());
        event.put("device_id", deviceId != null && !deviceId.isBlank() ? deviceId : stream);
        event.put("app", data.getOrDefault("app", "live"));
        event.put("stream", stream);
        event.put("file_path", filePath);
        event.put("cwd", stringField(data, "cwd"));
        event.put("source", "srs");
        Object mediaNodeId = data.get("media_node_id");
        if (mediaNodeId == null) {
            mediaNodeId = data.get("server_id");
        }
        event.put("media_node_id", mediaNodeId);
        event.put("segment_start_ms", segmentStartMs);
        event.put("created_at", Instant.now().toString());
        return event;
    }

    public Map<String, Object> buildFromZlmHook(Map<String, Object> data, String deviceId) {
        String stream = stringField(data, "stream");
        String filePath = firstNonBlank(
                stringField(data, "file_path"),
                stringField(data, "file_name")
        );
        Map<String, Object> event = new HashMap<>();
        event.put("event_id", UUID.randomUUID().toString());
        event.put("device_id", deviceId != null && !deviceId.isBlank() ? deviceId : stream);
        event.put("app", data.getOrDefault("app", "record"));
        event.put("stream", stream);
        event.put("file_path", filePath);
        event.put("cwd", "");
        event.put("source", "zlm");
        event.put("media_node_id", data.get("mediaServerId"));
        event.put("segment_start_ms", data.get("start_time"));
        event.put("created_at", Instant.now().toString());
        return event;
    }

    public Map<String, Object> buildSnapEvent(
            String deviceId,
            String filePath,
            String source,
            Object taskId,
            Object spaceId
    ) {
        Map<String, Object> event = new HashMap<>();
        event.put("event_id", UUID.randomUUID().toString());
        event.put("device_id", deviceId);
        event.put("file_path", filePath);
        event.put("source", source != null && !source.isBlank() ? source : "algorithm");
        event.put("task_id", taskId);
        event.put("space_id", spaceId);
        event.put("created_at", Instant.now().toString() + "Z");
        return event;
    }

    private static Long parseSegmentStartMs(String filePath) {
        if (filePath == null || filePath.isBlank()) {
            return null;
        }
        String normalized = filePath.replace('\\', '/');
        int slash = normalized.lastIndexOf('/');
        String filename = slash >= 0 ? normalized.substring(slash + 1) : normalized;
        int dot = filename.lastIndexOf('.');
        String stem = dot > 0 ? filename.substring(0, dot) : filename;
        if (stem.chars().allMatch(Character::isDigit)) {
            try {
                return Long.parseLong(stem);
            } catch (NumberFormatException ignored) {
                return null;
            }
        }
        return null;
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
