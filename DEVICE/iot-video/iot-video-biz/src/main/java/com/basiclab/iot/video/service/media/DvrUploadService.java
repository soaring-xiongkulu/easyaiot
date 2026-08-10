package com.basiclab.iot.video.service.media;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.AlertRepository;
import com.basiclab.iot.video.dal.DeviceSpaceRepository;
import com.basiclab.iot.video.dal.RecordFileRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.service.minio.SpaceFileMetadataService;
import com.basiclab.iot.video.service.minio.VideoMinioService;
import com.basiclab.iot.video.service.ops.PlaybackDiskGuardService;
import com.basiclab.iot.video.support.MediaDvrPathSupport;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Timestamp;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;

/**
 * DVR upload pipeline aligned with Python {@code dvr_upload_service}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DvrUploadService {

    private static final ZoneId SHANGHAI = ZoneId.of("Asia/Shanghai");

    private final DvrDeviceResolver dvrDeviceResolver;
    private final MediaKafkaProducer mediaKafkaProducer;
    private final VideoProperties videoProperties;
    private final VideoMinioService videoMinioService;
    private final DeviceSpaceRepository deviceSpaceRepository;
    private final RecordFileRepository recordFileRepository;
    private final SpaceFileMetadataService spaceFileMetadataService;
    private final AlertRepository alertRepository;
    private final PlaybackDiskGuardService playbackDiskGuardService;

    public boolean processDvrEvent(Map<String, Object> event) {
        if (event == null || event.isEmpty()) {
            return true;
        }
        String stream = stringField(event, "stream");
        String filePath = stringField(event, "file_path");
        String cwd = stringField(event, "cwd");
        String deviceId = stringField(event, "device_id");
        if (deviceId.isBlank()) {
            deviceId = stream;
        }

        DvrDeviceResolver.ResolvedDevice resolved = dvrDeviceResolver.resolve(stream, filePath);
        DeviceRow device = resolved.device();
        if (device == null) {
            Path absolute = MediaDvrPathSupport.resolvePlaybackAbsolutePath(filePath, cwd);
            removeLocalFile(absolute);
            log.info("DVR 上传：设备不存在，已丢弃本地回放 stream={} file={}", stream, filePath);
            return true;
        }
        deviceId = resolved.deviceId();

        Map<String, Object> recordSpace = deviceSpaceRepository.findRecordSpaceByDeviceId(deviceId).orElse(null);
        if (recordSpace == null) {
            try {
                deviceSpaceRepository.createRecordSpace(deviceId, device.getName());
                recordSpace = deviceSpaceRepository.findRecordSpaceByDeviceId(deviceId).orElse(null);
            } catch (Exception e) {
                log.error("创建设备录像空间失败 device_id={} error={}", deviceId, e.getMessage(), e);
                return false;
            }
        }
        if (recordSpace == null) {
            log.error("创建设备录像空间失败 device_id={}", deviceId);
            return false;
        }

        Path absoluteFilePath = MediaDvrPathSupport.resolvePlaybackAbsolutePath(filePath, cwd);
        long fileSize = MediaDvrPathSupport.waitDvrFileStable(absoluteFilePath, 12, 0.5);
        int minBytes = MediaDvrPathSupport.srsDvrMinFileBytes(videoProperties);
        if (fileSize <= 0) {
            if (Files.isRegularFile(absoluteFilePath)) {
                try {
                    long sz = Files.size(absoluteFilePath);
                    if (sz > 0 && sz < minBytes) {
                        log.info("DVR 片段过小已丢弃 file={} size={} min={}", absoluteFilePath, sz, minBytes);
                        removeLocalFile(absoluteFilePath);
                        return true;
                    }
                } catch (Exception ignored) {
                }
            }
            log.warn("DVR 文件未就绪或过小 file={}", absoluteFilePath);
            return false;
        }

        String filename = absoluteFilePath.getFileName().toString();
        Map<String, Object> parsed = MediaDvrPathSupport.parseSrsDvrPathDate(absoluteFilePath);
        String dateDir;
        ZonedDateTime recordTime;
        if (!parsed.isEmpty()) {
            dateDir = String.valueOf(parsed.get("date_dir"));
            recordTime = (ZonedDateTime) parsed.get("record_time");
        } else {
            try {
                recordTime = Files.getLastModifiedTime(absoluteFilePath).toInstant().atZone(SHANGHAI);
            } catch (Exception e) {
                recordTime = ZonedDateTime.now(SHANGHAI);
            }
            dateDir = recordTime.format(DateTimeFormatter.ofPattern("yyyy/MM/dd"));
        }

        String objectName = deviceId + "/" + dateDir + "/" + filename;
        String bucketName = recordSpace.get("bucket_name") != null
                ? String.valueOf(recordSpace.get("bucket_name"))
                : videoMinioService.recordBucket();

        if (recordFileRepository.existsByDeviceAndObjectName(deviceId, objectName)) {
            if (videoMinioService.isStorageEnabled()) {
                removeLocalFile(absoluteFilePath);
            }
            String existingUrl = videoMinioService.isStorageEnabled()
                    ? videoMinioService.buildDownloadUrl(bucketName, objectName)
                    : absoluteFilePath.toString();
            patchAlertRecord(deviceId, recordTime, 1, existingUrl);
            return true;
        }

        if (!videoMinioService.isStorageEnabled()) {
            String localUrl = absoluteFilePath.toString();
            int duration = 1;
            upsertMetadata(recordSpace, device, deviceId, objectName, bucketName, filename, fileSize,
                    MediaDvrPathSupport.videoContentType(filename), localUrl, null, duration, recordTime);
            patchAlertRecord(deviceId, recordTime, duration, localUrl);
            log.info("mini 形态 DVR 保留本地路径 device_id={} path={} size={}", deviceId, absoluteFilePath, fileSize);
            return true;
        }

        try {
            videoMinioService.uploadFile(
                    bucketName,
                    objectName,
                    absoluteFilePath,
                    MediaDvrPathSupport.videoContentType(filename),
                    true
            );
        } catch (Exception e) {
            log.error("MinIO 上传失败 device_id={} object={} error={}", deviceId, objectName, e.getMessage(), e);
            publishDlq(event, e.getMessage());
            return false;
        }

        String filePathUrl = videoMinioService.buildDownloadUrl(bucketName, objectName);
        int duration = 1;
        upsertMetadata(recordSpace, device, deviceId, objectName, bucketName, filename, fileSize,
                MediaDvrPathSupport.videoContentType(filename), filePathUrl, null, duration, recordTime);
        patchAlertRecord(deviceId, recordTime, duration, filePathUrl);
        removeLocalFile(absoluteFilePath);
        log.info("DVR 上传完成 device_id={} object={} size={}", deviceId, objectName, fileSize);
        return true;
    }

    public void publishDlq(Map<String, Object> event, String error) {
        mediaKafkaProducer.publishDvrDlq(event, error);
    }

    private void upsertMetadata(Map<String, Object> recordSpace, DeviceRow device, String deviceId,
                                String objectName, String bucketName, String filename, long fileSize,
                                String contentType, String url, String thumbnailUrl, int duration,
                                ZonedDateTime recordTime) {
        int spaceId = ((Number) recordSpace.get("id")).intValue();
        Timestamp eventTime = Timestamp.from(recordTime.toInstant());
        spaceFileMetadataService.upsertRecordFile(
                spaceId, deviceId, objectName, bucketName, filename, fileSize, contentType,
                url, thumbnailUrl, duration, eventTime, "dvr"
        );
        spaceFileMetadataService.upsertPlayback(
                deviceId,
                device.getName(),
                url,
                objectName,
                eventTime,
                fileSize,
                duration,
                thumbnailUrl
        );
    }

    private void patchAlertRecord(String deviceId, ZonedDateTime recordTime, int duration, String filePathUrl) {
        try {
            String eventTime = recordTime.withZoneSameInstant(SHANGHAI)
                    .format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
            alertRepository.patchAlertsRecord(
                    deviceId,
                    eventTime,
                    duration,
                    filePathUrl,
                    !videoMinioService.isStorageEnabled()
            );
        } catch (Exception e) {
            log.error("关联告警 record_path 失败 device_id={} error={}", deviceId, e.getMessage(), e);
        }
    }

    private void removeLocalFile(Path absoluteFilePath) {
        if (absoluteFilePath == null || absoluteFilePath.toString().isBlank()) {
            return;
        }
        try {
            if (Files.deleteIfExists(absoluteFilePath)) {
                log.debug("已删除本地 DVR 文件 {}", absoluteFilePath);
            }
        } catch (Exception e) {
            log.warn("删除本地 DVR 文件失败 file={} error={}", absoluteFilePath, e.getMessage());
        }
        try {
            playbackDiskGuardService.runGuard();
        } catch (Exception ignored) {
        }
    }

    private static String stringField(Map<String, Object> data, String key) {
        if (data == null || data.get(key) == null) {
            return "";
        }
        return String.valueOf(data.get(key)).trim();
    }
}
