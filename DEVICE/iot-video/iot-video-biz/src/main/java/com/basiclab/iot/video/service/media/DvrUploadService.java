package com.basiclab.iot.video.service.media;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Map;

/**
 * DVR upload pipeline — mini/certify path acknowledges events without MinIO upload.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DvrUploadService {

    private final DvrDeviceResolver dvrDeviceResolver;
    private final MediaKafkaProducer mediaKafkaProducer;

    public boolean processDvrEvent(Map<String, Object> event) {
        if (event == null || event.isEmpty()) {
            return true;
        }
        String stream = stringField(event, "stream");
        String filePath = stringField(event, "file_path");
        String deviceId = stringField(event, "device_id");
        if (deviceId.isBlank()) {
            deviceId = stream;
        }

        DvrDeviceResolver.ResolvedDevice resolved = dvrDeviceResolver.resolve(stream, filePath);
        if (resolved.device() == null) {
            log.info("DVR 上传：设备不存在，已丢弃本地回放 stream={} file={}", stream, filePath);
            return true;
        }

        log.debug(
                "DVR event accepted (mini) deviceId={} stream={} file={} source={}",
                resolved.deviceId(),
                stream,
                filePath,
                event.get("source")
        );
        return true;
    }

    public void publishDlq(Map<String, Object> event, String error) {
        mediaKafkaProducer.publishDvrDlq(event, error);
    }

    private static String stringField(Map<String, Object> data, String key) {
        if (data == null || data.get(key) == null) {
            return "";
        }
        return String.valueOf(data.get(key)).trim();
    }
}
