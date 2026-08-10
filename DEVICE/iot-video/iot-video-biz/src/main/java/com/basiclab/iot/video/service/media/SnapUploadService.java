package com.basiclab.iot.video.service.media;

import com.basiclab.iot.video.dal.SnapSpaceRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Map;

/**
 * Snap upload pipeline — mini/certify path acknowledges events without MinIO upload.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SnapUploadService {

    private final SnapSpaceRepository snapSpaceRepository;
    private final MediaKafkaProducer mediaKafkaProducer;

    public boolean processSnapEvent(Map<String, Object> event) {
        if (event == null || event.isEmpty()) {
            return false;
        }
        String deviceId = stringField(event, "device_id");
        String filePath = stringField(event, "file_path");
        if (deviceId.isBlank() || filePath.isBlank()) {
            return false;
        }

        if (snapSpaceRepository.findByDeviceId(deviceId).isEmpty()) {
            log.warn("设备无抓拍空间 device_id={}", deviceId);
            return false;
        }

        log.debug(
                "snap event accepted (mini) deviceId={} file={} source={}",
                deviceId,
                filePath,
                event.get("source")
        );
        return true;
    }

    public void publishDlq(Map<String, Object> event, String error) {
        mediaKafkaProducer.publishSnapDlq(event, error);
    }

    private static String stringField(Map<String, Object> data, String key) {
        if (data == null || data.get(key) == null) {
            return "";
        }
        return String.valueOf(data.get(key)).trim();
    }
}
