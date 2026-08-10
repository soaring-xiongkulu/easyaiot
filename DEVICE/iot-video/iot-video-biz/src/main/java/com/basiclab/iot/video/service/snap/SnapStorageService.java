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
        Map<String, Object> result = new LinkedHashMap<>(config);
        result.put("snap_used_size", 0);
        result.put("snap_file_count", 0);
        result.put("video_used_size", 0);
        result.put("video_file_count", 0);
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
}
