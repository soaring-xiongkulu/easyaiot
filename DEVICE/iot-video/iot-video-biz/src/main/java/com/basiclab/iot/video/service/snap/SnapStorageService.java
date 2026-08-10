package com.basiclab.iot.video.service.snap;

import com.basiclab.iot.video.dal.DeviceStorageRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class SnapStorageService {

    private final DeviceStorageRepository storageRepository;

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
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("deleted_snap_count", 0);
        result.put("deleted_video_count", 0);
        result.put("message", "mini 形态跳过 MinIO 存储清理");
        return result;
    }
}
