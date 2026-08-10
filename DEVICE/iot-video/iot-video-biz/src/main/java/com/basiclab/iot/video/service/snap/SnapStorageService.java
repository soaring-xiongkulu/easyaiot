package com.basiclab.iot.video.service.snap;

import com.basiclab.iot.video.dal.DeviceStorageRepository;
import com.basiclab.iot.video.dal.SnapSpaceRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.minio.SpaceFileMetadataService;
import com.basiclab.iot.video.service.minio.VideoMinioService;
import com.basiclab.iot.video.support.SpaceSaveTimeSupport;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class SnapStorageService {

    private final DeviceStorageRepository storageRepository;
    private final SnapSpaceRepository snapSpaceRepository;
    private final VideoMinioService videoMinioService;
    private final SpaceFileMetadataService spaceFileMetadataService;

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

    public Map<String, Object> cleanup(String deviceId) {
        getOrCreate(deviceId);
        Map<String, Object> space = snapSpaceRepository.findByDeviceId(deviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "设备 " + deviceId + " 没有关联的抓拍空间"));
        int saveTimeHours = SpaceSaveTimeSupport.effectiveSaveTimeHours(space);
        if (saveTimeHours <= 0) {
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("deleted_snap_count", 0);
            result.put("deleted_video_count", 0);
            result.put("message", "空间为永久保存，跳过清理");
            return result;
        }
        Map<String, Object> cleanup = spaceFileMetadataService.cleanupExpiredSnapImages(space, saveTimeHours);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("deleted_snap_count", cleanup.getOrDefault("deleted_count", 0));
        result.put("deleted_video_count", 0);
        result.put("processed_count", cleanup.getOrDefault("processed_count", 0));
        result.put("error_count", cleanup.getOrDefault("error_count", 0));
        if (!videoMinioService.isStorageEnabled()) {
            result.put("message", "MinIO 未启用，仅清理数据库元数据");
        } else {
            result.put("message", "存储清理完成");
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
}
