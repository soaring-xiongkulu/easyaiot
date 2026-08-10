package com.basiclab.iot.video.service.snap;

import com.basiclab.iot.video.dal.DeviceStorageRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.minio.VideoMinioService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class SnapStorageService {

    private final DeviceStorageRepository storageRepository;
    private final VideoMinioService videoMinioService;

    public Map<String, Object> getOrCreate(String deviceId) {
        if (!storageRepository.deviceExists(deviceId)) {
            throw new VideoBusinessException(400, "设备不存在: " + deviceId);
        }
        storageRepository.insertDefault(deviceId);
        Map<String, Object> config = storageRepository.findByDeviceId(deviceId)
                .orElseThrow(() -> new VideoBusinessException(500, "获取设备存储配置失败"));
        return enrichWithStorageStats(config);
    }

    /**
     * Mirrors Python {@code storage_service.get_device_storage_info}:
     * list+stat MinIO objects under {@code device_id/} when bucket configured;
     * honest zeros when MinIO disabled or bucket unset.
     */
    private Map<String, Object> enrichWithStorageStats(Map<String, Object> config) {
        Map<String, Object> result = new LinkedHashMap<>(config);
        String deviceId = stringField(config.get("device_id"));

        long snapSize = 0L;
        int snapCount = 0;
        String snapBucket = stringField(config.get("snap_storage_bucket"));
        if (!snapBucket.isBlank()) {
            VideoMinioService.BucketUsage snapUsage = videoMinioService.getBucketUsage(snapBucket, deviceId + "/");
            snapSize = snapUsage.sizeBytes();
            snapCount = snapUsage.objectCount();
        }

        long videoSize = 0L;
        int videoCount = 0;
        String videoBucket = stringField(config.get("video_storage_bucket"));
        if (!videoBucket.isBlank()) {
            VideoMinioService.BucketUsage videoUsage = videoMinioService.getBucketUsage(videoBucket, deviceId + "/");
            videoSize = videoUsage.sizeBytes();
            videoCount = videoUsage.objectCount();
        }

        Long snapMaxSize = toLongOrNull(config.get("snap_storage_max_size"));
        Long videoMaxSize = toLongOrNull(config.get("video_storage_max_size"));

        result.put("snap_size", snapSize);
        result.put("snap_count", snapCount);
        result.put("snap_usage_ratio", usageRatio(snapSize, snapMaxSize));
        result.put("video_size", videoSize);
        result.put("video_count", videoCount);
        result.put("video_usage_ratio", usageRatio(videoSize, videoMaxSize));
        return result;
    }

    public Map<String, Object> update(String deviceId, Map<String, Object> data) {
        getOrCreate(deviceId);
        Map<String, Object> fields = new LinkedHashMap<>();
        for (String key : new String[]{
                "snap_storage_bucket", "snap_storage_max_size", "snap_storage_cleanup_enabled",
                "snap_storage_cleanup_threshold", "snap_storage_cleanup_ratio",
                "video_storage_bucket", "video_storage_max_size", "video_storage_cleanup_enabled",
                "video_storage_cleanup_threshold", "video_storage_cleanup_ratio"
        }) {
            if (data.containsKey(key)) {
                fields.put(key, data.get(key));
            }
        }
        storageRepository.updateFields(deviceId, fields);
        return getOrCreate(deviceId);
    }

    /**
     * Mirrors Python {@code storage_service.check_and_cleanup_storage}:
     * threshold-based quota cleanup on MinIO {@code device_id/} prefix when enabled;
     * honest no-op when MinIO disabled or bucket unset.
     */
    public Map<String, Object> cleanup(String deviceId) {
        getOrCreate(deviceId);
        Map<String, Object> config = storageRepository.findByDeviceId(deviceId)
                .orElseThrow(() -> new VideoBusinessException(500, "获取设备存储配置失败"));

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("snap_cleaned", false);
        result.put("video_cleaned", false);
        result.put("snap_deleted_count", 0);
        result.put("snap_freed_size", 0);
        result.put("video_deleted_count", 0);
        result.put("video_freed_size", 0);

        if (!videoMinioService.isStorageEnabled()) {
            result.put("message", "MinIO 未启用，跳过存储清理");
            return result;
        }

        String devicePrefix = deviceId + "/";

        String snapBucket = stringField(config.get("snap_storage_bucket"));
        Long snapMaxSize = toLongOrNull(config.get("snap_storage_max_size"));
        boolean snapCleanupEnabled = Boolean.TRUE.equals(config.get("snap_storage_cleanup_enabled"));
        double snapThreshold = toDoubleOrDefault(config.get("snap_storage_cleanup_threshold"), 0.8);
        double snapRatio = toDoubleOrDefault(config.get("snap_storage_cleanup_ratio"), 0.3);

        if (!snapBucket.isBlank() && snapMaxSize != null && snapMaxSize > 0 && snapCleanupEnabled) {
            VideoMinioService.BucketUsage snapUsage = videoMinioService.getBucketUsage(snapBucket, devicePrefix);
            double snapUsageRatio = (double) snapUsage.sizeBytes() / snapMaxSize;
            if (snapUsageRatio >= snapThreshold) {
                VideoMinioService.CleanupResult snapCleanup =
                        videoMinioService.cleanupOldFiles(snapBucket, devicePrefix, snapRatio);
                result.put("snap_cleaned", true);
                result.put("snap_deleted_count", snapCleanup.deletedCount());
                result.put("snap_freed_size", snapCleanup.freedSizeBytes());
                storageRepository.touchLastSnapCleanupTime(deviceId);
            }
        }

        String videoBucket = stringField(config.get("video_storage_bucket"));
        Long videoMaxSize = toLongOrNull(config.get("video_storage_max_size"));
        boolean videoCleanupEnabled = Boolean.TRUE.equals(config.get("video_storage_cleanup_enabled"));
        double videoThreshold = toDoubleOrDefault(config.get("video_storage_cleanup_threshold"), 0.8);
        double videoRatio = toDoubleOrDefault(config.get("video_storage_cleanup_ratio"), 0.3);

        if (!videoBucket.isBlank() && videoMaxSize != null && videoMaxSize > 0 && videoCleanupEnabled) {
            VideoMinioService.BucketUsage videoUsage = videoMinioService.getBucketUsage(videoBucket, devicePrefix);
            double videoUsageRatio = (double) videoUsage.sizeBytes() / videoMaxSize;
            if (videoUsageRatio >= videoThreshold) {
                VideoMinioService.CleanupResult videoCleanup =
                        videoMinioService.cleanupOldFiles(videoBucket, devicePrefix, videoRatio);
                result.put("video_cleaned", true);
                result.put("video_deleted_count", videoCleanup.deletedCount());
                result.put("video_freed_size", videoCleanup.freedSizeBytes());
                storageRepository.touchLastVideoCleanupTime(deviceId);
            }
        }

        return result;
    }

    private static double usageRatio(long size, Long maxSize) {
        if (maxSize == null || maxSize <= 0L) {
            return 0.0;
        }
        return (double) size / maxSize;
    }

    private static String stringField(Object value) {
        return value == null ? "" : String.valueOf(value).trim();
    }

    private static Long toLongOrNull(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number number) {
            return number.longValue();
        }
        try {
            String text = String.valueOf(value).trim();
            if (text.isEmpty()) {
                return null;
            }
            return Long.parseLong(text);
        } catch (NumberFormatException ignored) {
            return null;
        }
    }

    private static double toDoubleOrDefault(Object value, double defaultValue) {
        if (value == null) {
            return defaultValue;
        }
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        try {
            String text = String.valueOf(value).trim();
            if (text.isEmpty()) {
                return defaultValue;
            }
            return Double.parseDouble(text);
        } catch (NumberFormatException ignored) {
            return defaultValue;
        }
    }
}
