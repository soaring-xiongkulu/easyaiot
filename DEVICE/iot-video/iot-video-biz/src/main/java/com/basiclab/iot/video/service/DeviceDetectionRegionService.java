package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.DeviceDetectionRegionRepository;
import com.basiclab.iot.video.dal.DeviceImageRepository;
import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.camera.CameraHardwareService;
import com.basiclab.iot.video.support.RequestParams;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class DeviceDetectionRegionService {

    private final DeviceDetectionRegionRepository regionRepository;
    private final DeviceRepository deviceRepository;
    private final DeviceImageRepository imageRepository;
    private final CameraHardwareService cameraHardwareService;

    public List<Map<String, Object>> listByDevice(String deviceId) {
        if (!regionRepository.deviceExists(deviceId)) {
            throw new VideoBusinessException(400, "设备不存在: ID=" + deviceId);
        }
        return regionRepository.listByDevice(deviceId);
    }

    public Map<String, Object> createRegion(String deviceId, Map<String, Object> data) {
        if (data == null || data.isEmpty()) {
            throw new VideoBusinessException(400, "请求数据不能为空");
        }
        if (!regionRepository.deviceExists(deviceId)) {
            throw new VideoBusinessException(400, "设备不存在: ID=" + deviceId);
        }
        validateRealtimeModelConfig(deviceId);

        String regionName = RequestParams.str(data, "region_name");
        if (regionName.isEmpty()) {
            throw new VideoBusinessException(400, "区域名称不能为空");
        }
        String regionType = RequestParams.str(data, "region_type");
        if (regionType.isEmpty()) {
            regionType = "polygon";
        }
        if (!List.of("polygon", "line", "rectangle").contains(regionType)) {
            throw new VideoBusinessException(400, "区域类型必须是 polygon、line 或 rectangle");
        }
        Object points = data.get("points");
        if (!(points instanceof List<?> list) || list.isEmpty()) {
            throw new VideoBusinessException(400, "区域坐标点不能为空");
        }
        Integer imageId = data.get("image_id") != null ? RequestParams.toInt(data.get("image_id"), 0) : null;
        if (imageId != null && imageId > 0 && !imageRepository.exists(imageId)) {
            throw new VideoBusinessException(400, "图片不存在: " + imageId);
        }
        Object modelIds = data.get("model_ids");
        String modelIdsJson = DeviceDetectionRegionRepository.toJson(modelIds);

        int regionId = regionRepository.insert(
                deviceId,
                regionName,
                regionType,
                DeviceDetectionRegionRepository.toJson(points),
                imageId != null && imageId > 0 ? imageId : null,
                RequestParams.str(data, "color").isEmpty() ? "#FF5252" : RequestParams.str(data, "color"),
                RequestParams.toDouble(data.get("opacity"), 0.3),
                RequestParams.bool(data, "is_enabled", true),
                RequestParams.toInt(data.get("sort_order"), 0),
                modelIdsJson
        );
        return regionRepository.findById(regionId).orElseThrow();
    }

    public Map<String, Object> updateRegion(int regionId, Map<String, Object> data) {
        if (data == null || data.isEmpty()) {
            throw new VideoBusinessException(400, "请求数据不能为空");
        }
        Map<String, Object> region = regionRepository.findById(regionId)
                .orElseThrow(() -> new VideoBusinessException(400, "检测区域不存在: ID=" + regionId));
        String deviceId = String.valueOf(region.get("device_id"));
        if (regionRepository.hasRealtimeTasks(deviceId) && !regionRepository.deviceHasRealtimeModelConfig(deviceId)) {
            data.put("is_enabled", false);
        }
        String regionType = RequestParams.str(data, "region_type");
        if (!regionType.isEmpty() && !List.of("polygon", "line", "rectangle").contains(regionType)) {
            throw new VideoBusinessException(400, "区域类型必须是 polygon、line 或 rectangle");
        }
        Map<String, Object> fields = new LinkedHashMap<>();
        if (data.containsKey("region_name")) {
            fields.put("region_name", RequestParams.str(data, "region_name"));
        }
        if (data.containsKey("region_type")) {
            fields.put("region_type", data.get("region_type"));
        }
        if (data.containsKey("points")) {
            fields.put("points", DeviceDetectionRegionRepository.toJson(data.get("points")));
        }
        if (data.containsKey("image_id")) {
            Integer imageId = RequestParams.toInt(data.get("image_id"), 0);
            if (imageId > 0 && !imageRepository.exists(imageId)) {
                throw new VideoBusinessException(400, "图片不存在: " + imageId);
            }
            fields.put("image_id", imageId > 0 ? imageId : null);
        }
        if (data.containsKey("color")) {
            fields.put("color", data.get("color"));
        }
        if (data.containsKey("opacity")) {
            fields.put("opacity", data.get("opacity"));
        }
        if (data.containsKey("is_enabled")) {
            fields.put("is_enabled", data.get("is_enabled"));
        }
        if (data.containsKey("sort_order")) {
            fields.put("sort_order", data.get("sort_order"));
        }
        if (data.containsKey("model_ids")) {
            fields.put("model_ids", DeviceDetectionRegionRepository.toJson(data.get("model_ids")));
        }
        regionRepository.update(regionId, fields);
        return regionRepository.findById(regionId).orElseThrow();
    }

    public void deleteRegion(int regionId) {
        if (regionRepository.findById(regionId).isEmpty()) {
            return;
        }
        regionRepository.delete(regionId);
    }

    public Map<String, Object> updateCoverImage(String deviceId) {
        if (!regionRepository.deviceExists(deviceId)) {
            throw new VideoBusinessException(400, "设备不存在: ID=" + deviceId);
        }
        Map<String, Object> imageRecord = imageRepository.findLatestByDevice(deviceId).orElse(null);
        String imageUrl;
        if (imageRecord != null && imageRecord.get("path") != null) {
            imageUrl = String.valueOf(imageRecord.get("path"));
        } else {
            DeviceRow device = deviceRepository.findById(deviceId)
                    .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: ID=" + deviceId));
            if (device.getSource() == null || device.getSource().isBlank()) {
                throw new VideoBusinessException(400, "设备源地址为空");
            }
            try {
                cameraHardwareService.captureSnapshot(deviceId);
            } catch (VideoBusinessException ex) {
                throw new VideoBusinessException(500, ex.getMessage());
            }
            imageRecord = imageRepository.findLatestByDevice(deviceId).orElse(null);
            imageUrl = imageRecord != null ? String.valueOf(imageRecord.get("path")) : null;
            if (imageUrl == null || imageUrl.isBlank()) {
                throw new VideoBusinessException(500, "图片上传失败");
            }
        }
        regionRepository.updateDeviceCoverImage(deviceId, imageUrl);
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("cover_image_path", imageUrl);
        data.put("image_url", imageUrl);
        if (imageRecord != null) {
            data.put("image_id", imageRecord.get("id"));
            data.put("width", imageRecord.get("width"));
            data.put("height", imageRecord.get("height"));
        }
        return data;
    }

    public Map<String, Object> captureSnapshot(String deviceId) {
        if (!regionRepository.deviceExists(deviceId)) {
            throw new VideoBusinessException(400, "设备不存在: ID=" + deviceId);
        }
        DeviceRow device = deviceRepository.findById(deviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: ID=" + deviceId));
        if (device.getSource() == null || device.getSource().isBlank()) {
            throw new VideoBusinessException(400, "设备源地址为空");
        }
        try {
            cameraHardwareService.captureSnapshot(deviceId);
        } catch (VideoBusinessException ex) {
            throw new VideoBusinessException(500, ex.getMessage());
        }
        Map<String, Object> imageRecord = imageRepository.findLatestByDevice(deviceId).orElse(null);
        String imageUrl = imageRecord != null ? String.valueOf(imageRecord.get("path")) : null;
        if (imageUrl == null || imageUrl.isBlank()) {
            throw new VideoBusinessException(500, "图片上传失败");
        }
        try {
            regionRepository.updateDeviceCoverImage(deviceId, imageUrl);
        } catch (Exception ignored) {
            // cover update failure should not block snapshot result
        }
        Map<String, Object> data = new LinkedHashMap<>();
        if (imageRecord != null) {
            data.put("image_id", imageRecord.get("id"));
            data.put("width", imageRecord.get("width"));
            data.put("height", imageRecord.get("height"));
        }
        data.put("image_url", imageUrl);
        return data;
    }

    private void validateRealtimeModelConfig(String deviceId) {
        if (regionRepository.hasRealtimeTasks(deviceId) && !regionRepository.deviceHasRealtimeModelConfig(deviceId)) {
            throw new VideoBusinessException(400, "该设备关联的算法任务未配置算法模型列表，无法配置区域检测");
        }
    }
}
