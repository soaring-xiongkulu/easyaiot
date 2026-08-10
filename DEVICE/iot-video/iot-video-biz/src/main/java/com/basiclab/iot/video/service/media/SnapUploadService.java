package com.basiclab.iot.video.service.media;

import com.basiclab.iot.video.dal.SnapImageRepository;
import com.basiclab.iot.video.dal.SnapSpaceRepository;
import com.basiclab.iot.video.service.minio.SpaceFileMetadataService;
import com.basiclab.iot.video.service.minio.VideoMinioService;
import com.basiclab.iot.video.support.MediaDvrPathSupport;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Timestamp;
import java.time.Instant;
import java.time.ZoneId;
import java.util.Map;

/**
 * Snap upload pipeline aligned with Python {@code snap_upload_service}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SnapUploadService {

    private static final ZoneId SHANGHAI = ZoneId.of("Asia/Shanghai");

    private final SnapSpaceRepository snapSpaceRepository;
    private final SnapImageRepository snapImageRepository;
    private final MediaKafkaProducer mediaKafkaProducer;
    private final VideoMinioService videoMinioService;
    private final SpaceFileMetadataService spaceFileMetadataService;

    public boolean processSnapEvent(Map<String, Object> event) {
        if (event == null || event.isEmpty()) {
            return false;
        }
        String deviceId = stringField(event, "device_id");
        String filePath = stringField(event, "file_path");
        if (deviceId.isBlank() || filePath.isBlank()) {
            return false;
        }

        Path absolutePath = MediaDvrPathSupport.resolvePlaybackAbsolutePath(filePath, stringField(event, "cwd"));
        long fileSize = MediaDvrPathSupport.waitDvrFileStable(absolutePath, 6, 0.5);
        if (fileSize <= 0) {
            log.warn("抓拍文件未就绪 file={}", absolutePath);
            return false;
        }

        Map<String, Object> snapSpace = snapSpaceRepository.findByDeviceId(deviceId).orElse(null);
        if (snapSpace == null) {
            log.warn("设备无抓拍空间 device_id={}", deviceId);
            return false;
        }

        String filename = absolutePath.getFileName().toString();
        String objectName = deviceId + "/" + filename;
        String bucketName = snapSpace.get("bucket_name") != null
                ? String.valueOf(snapSpace.get("bucket_name"))
                : videoMinioService.snapBucket();

        if (snapImageRepository.existsByBucketAndObjectName(bucketName, objectName)) {
            if (videoMinioService.isStorageEnabled()) {
                removeLocalFile(absolutePath);
            }
            return true;
        }

        int spaceId = ((Number) snapSpace.get("id")).intValue();
        Integer taskId = event.get("task_id") instanceof Number n ? n.intValue() : null;
        String source = stringField(event, "source");
        if (source.isBlank()) {
            source = "algorithm";
        }
        Timestamp capturedAt = Timestamp.from(Instant.now().atZone(SHANGHAI).toInstant());

        if (!videoMinioService.isStorageEnabled()) {
            try {
                spaceFileMetadataService.upsertSnapImage(
                        spaceId, deviceId, objectName, bucketName, filename, fileSize,
                        MediaDvrPathSupport.imageContentType(filename), absolutePath.toString(),
                        capturedAt, taskId, source
                );
            } catch (Exception e) {
                log.error("mini 形态抓拍元数据写入失败 device={} error={}", deviceId, e.getMessage(), e);
                return false;
            }
            log.info("mini 形态抓拍保留本地路径 device={} path={} size={}", deviceId, absolutePath, fileSize);
            return true;
        }

        try {
            videoMinioService.uploadFile(
                    bucketName,
                    objectName,
                    absolutePath,
                    MediaDvrPathSupport.imageContentType(filename),
                    false
            );
        } catch (Exception e) {
            log.error("MinIO 抓拍上传失败 device_id={} object={} error={}", deviceId, objectName, e.getMessage(), e);
            publishDlq(event, e.getMessage());
            return false;
        }

        String fileUrl = videoMinioService.buildDownloadUrl(bucketName, objectName);
        spaceFileMetadataService.upsertSnapImage(
                spaceId, deviceId, objectName, bucketName, filename, fileSize,
                MediaDvrPathSupport.imageContentType(filename), fileUrl,
                capturedAt, taskId, source
        );
        removeLocalFile(absolutePath);
        log.info("抓拍上传完成 device_id={} object={} size={}", deviceId, objectName, fileSize);
        return true;
    }

    public void publishDlq(Map<String, Object> event, String error) {
        mediaKafkaProducer.publishSnapDlq(event, error);
    }

    private void removeLocalFile(Path absolutePath) {
        try {
            Files.deleteIfExists(absolutePath);
        } catch (Exception e) {
            log.warn("删除本地抓拍文件失败 file={} error={}", absolutePath, e.getMessage());
        }
    }

    private static String stringField(Map<String, Object> data, String key) {
        if (data == null || data.get(key) == null) {
            return "";
        }
        return String.valueOf(data.get(key)).trim();
    }
}
