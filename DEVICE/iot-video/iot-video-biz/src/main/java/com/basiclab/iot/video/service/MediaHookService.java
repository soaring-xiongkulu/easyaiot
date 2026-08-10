package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.service.media.CameraPublishCallbackService;
import com.basiclab.iot.video.service.media.DvrDeviceResolver;
import com.basiclab.iot.video.service.media.DvrUploadService;
import com.basiclab.iot.video.service.media.MediaKafkaMessageBuilder;
import com.basiclab.iot.video.service.media.MediaKafkaProducer;
import com.basiclab.iot.video.service.media.SnapUploadService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class MediaHookService {

    private final VideoProperties videoProperties;
    private final DvrDeviceResolver dvrDeviceResolver;
    private final MediaKafkaMessageBuilder mediaKafkaMessageBuilder;
    private final MediaKafkaProducer mediaKafkaProducer;
    private final DvrUploadService dvrUploadService;
    private final SnapUploadService snapUploadService;
    private final CameraPublishCallbackService cameraPublishCallbackService;

    public void srsOnDvr(Map<String, Object> payload) {
        if (payload == null) {
            return;
        }
        String stream = stringField(payload, "stream");
        String file = firstNonBlank(stringField(payload, "file"), stringField(payload, "file_path"));
        if (stream.isEmpty() && file.isEmpty()) {
            return;
        }
        DvrDeviceResolver.ResolvedDevice resolved = dvrDeviceResolver.resolve(stream, file);
        String deviceId = resolved.deviceId();
        if (isKafkaUploadMode()) {
            mediaKafkaProducer.publishDvrEvent(
                    mediaKafkaMessageBuilder.buildFromSrsHook(payload, deviceId)
            );
            if (!isHybridUploadMode()) {
                return;
            }
        }
        if (isHybridUploadMode() || !isKafkaUploadMode()) {
            dvrUploadService.processDvrEvent(mediaKafkaMessageBuilder.buildFromSrsHook(payload, deviceId));
        }
    }

    public void srsOnPublish(Map<String, Object> payload) {
        cameraPublishCallbackService.handleOnPublish(payload);
    }

    public void srsOnUnpublish(Map<String, Object> payload) {
        // Python: immediate ack only
        if (payload != null) {
            log.debug("SRS on_unpublish stream={}", stringField(payload, "stream"));
        }
    }

    public void snapCompleted(Map<String, Object> payload) {
        if (payload == null) {
            return;
        }
        String deviceId = stringField(payload, "device_id");
        String filePath = firstNonBlank(stringField(payload, "file_path"), stringField(payload, "file"));
        if (deviceId.isEmpty() || filePath.isEmpty()) {
            return;
        }
        Map<String, Object> event = mediaKafkaMessageBuilder.buildSnapEvent(
                deviceId,
                filePath,
                stringField(payload, "source").isBlank() ? "algorithm" : stringField(payload, "source"),
                payload.get("task_id"),
                payload.get("space_id")
        );
        if (isSnapKafkaMode()) {
            mediaKafkaProducer.publishSnapEvent(event);
            return;
        }
        snapUploadService.processSnapEvent(event);
    }

    public void zlmOnRecord(Map<String, Object> payload) {
        if (payload == null) {
            return;
        }
        String filePath = firstNonBlank(stringField(payload, "file_path"), stringField(payload, "file_name"));
        String stream = stringField(payload, "stream");
        if (filePath.isEmpty() && stream.isEmpty()) {
            return;
        }
        DvrDeviceResolver.ResolvedDevice resolved = dvrDeviceResolver.resolve(stream, filePath);
        String deviceId = resolved.deviceId();
        if (isKafkaUploadMode()) {
            mediaKafkaProducer.publishDvrEvent(
                    mediaKafkaMessageBuilder.buildFromZlmHook(payload, deviceId)
            );
            if (!isHybridUploadMode()) {
                return;
            }
        }
        if (isHybridUploadMode() || !isKafkaUploadMode()) {
            dvrUploadService.processDvrEvent(mediaKafkaMessageBuilder.buildFromZlmHook(payload, deviceId));
        }
    }

    private boolean isKafkaUploadMode() {
        String mode = videoProperties.getMedia().getUploadMode();
        if (mode == null) {
            return false;
        }
        String normalized = mode.trim().toLowerCase();
        return "kafka".equals(normalized) || "hybrid".equals(normalized);
    }

    private boolean isHybridUploadMode() {
        String mode = videoProperties.getMedia().getUploadMode();
        return mode != null && "hybrid".equalsIgnoreCase(mode.trim());
    }

    private boolean isSnapKafkaMode() {
        String snapMode = videoProperties.getMedia().getSnapUploadMode();
        if (snapMode != null && !snapMode.isBlank()) {
            String normalized = snapMode.trim().toLowerCase();
            if ("kafka".equals(normalized)) {
                return true;
            }
            if ("sync".equals(normalized)) {
                return false;
            }
        }
        return isKafkaUploadMode();
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
