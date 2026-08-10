package com.basiclab.iot.video.service.minio;

import com.basiclab.iot.video.dal.AlertRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * Uploads match/alert images to MinIO {@code alert-images}, mirroring Python
 * {@code alert_consumer_service.upload_image_to_minio}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AlertImageUploadService {

    private static final String ALERT_IMAGES_BUCKET = "alert-images";

    private final VideoMinioService videoMinioService;
    private final AlertRepository alertRepository;

    public void uploadAndLinkAlertImage(String imagePath, long alertId, String deviceId) {
        if (imagePath == null || imagePath.isBlank() || alertId <= 0) {
            return;
        }
        if (!videoMinioService.isStorageEnabled()) {
            log.debug("skip alert image MinIO upload alertId={}: storage disabled", alertId);
            return;
        }
        try {
            Path local = Path.of(imagePath);
            if (!Files.isRegularFile(local)) {
                log.warn("告警图片文件不存在: {}", imagePath);
                return;
            }
            long size = waitForStableSize(local, 5, 100);
            if (size <= 0) {
                log.warn("告警图片不可用或大小为0: {}", imagePath);
                return;
            }
            byte[] content = Files.readAllBytes(local);
            if (content.length != size) {
                log.warn("告警图片读取大小不匹配 alertId={}: expected {} got {}", alertId, size, content.length);
                return;
            }
            String fileName = local.getFileName().toString();
            String ext = fileName.contains(".") ? fileName.substring(fileName.lastIndexOf('.')) : ".jpg";
            LocalDateTime now = LocalDateTime.now();
            String objectName = String.format(
                    "%d/%02d/%02d/alert_%d_%s_%s%s",
                    now.getYear(),
                    now.getMonthValue(),
                    now.getDayOfMonth(),
                    alertId,
                    sanitize(deviceId),
                    now.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss")),
                    ext
            );
            String contentType = contentTypeForExt(ext);
            videoMinioService.uploadBytes(ALERT_IMAGES_BUCKET, objectName, content, contentType, false);
            String downloadUrl = videoMinioService.buildDownloadUrl(ALERT_IMAGES_BUCKET, objectName);
            alertRepository.updateImageUrl(alertId, downloadUrl);
            log.debug("告警图片上传成功 alertId={} -> {}/{}", alertId, ALERT_IMAGES_BUCKET, objectName);
        } catch (Exception ex) {
            log.error("上传告警图片到 MinIO 失败 alertId={} path={}: {}", alertId, imagePath, ex.getMessage(), ex);
        }
    }

    private static long waitForStableSize(Path path, int maxWaitMs, int checkIntervalMs) {
        long last = -1;
        int stable = 0;
        int elapsed = 0;
        while (elapsed < maxWaitMs) {
            try {
                if (!Files.isRegularFile(path)) {
                    return -1;
                }
                long size = Files.size(path);
                if (size > 0 && size == last) {
                    stable++;
                    if (stable >= 2) {
                        return size;
                    }
                } else {
                    stable = 0;
                    last = size;
                }
                Thread.sleep(checkIntervalMs);
                elapsed += checkIntervalMs;
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return -1;
            } catch (Exception e) {
                return -1;
            }
        }
        return last > 0 ? last : -1;
    }

    private static String contentTypeForExt(String ext) {
        String lower = ext.toLowerCase();
        if (".jpg".equals(lower) || ".jpeg".equals(lower)) {
            return "image/jpeg";
        }
        if (".png".equals(lower)) {
            return "image/png";
        }
        return "application/octet-stream";
    }

    private static String sanitize(String deviceId) {
        if (deviceId == null || deviceId.isBlank()) {
            return "unknown";
        }
        return deviceId.replaceAll("[^a-zA-Z0-9._-]", "_");
    }
}
