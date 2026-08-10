package com.basiclab.iot.video.service.snap;

import com.basiclab.iot.video.dal.DetectionRegionRepository;
import com.basiclab.iot.video.dal.SnapTaskRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class SnapRegionService {

    private final DetectionRegionRepository regionRepository;
    private final SnapTaskRepository snapTaskRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public List<Map<String, Object>> listByTask(int taskId) {
        snapTaskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍任务不存在: ID=" + taskId));
        return regionRepository.listByTaskId(taskId);
    }

    public Map<String, Object> get(int regionId) {
        return regionRepository.findById(regionId)
                .orElseThrow(() -> new VideoBusinessException(400, "检测区域不存在: ID=" + regionId));
    }

    public Map<String, Object> create(Map<String, Object> data) {
        Object taskId = data.get("task_id");
        if (taskId == null) {
            throw new VideoBusinessException(400, "任务ID不能为空");
        }
        String regionName = str(data.get("region_name"));
        if (regionName.isEmpty()) {
            throw new VideoBusinessException(400, "区域名称不能为空");
        }
        Object points = data.get("points");
        if (!(points instanceof List<?> list) || list.size() < 3) {
            throw new VideoBusinessException(400, "区域坐标点不能为空，且至少需要3个点");
        }
        try {
            data.put("points", objectMapper.writeValueAsString(points));
        } catch (Exception e) {
            throw new VideoBusinessException(400, "区域坐标点格式错误");
        }
        int id = regionRepository.insert(data);
        return get(id);
    }

    public Map<String, Object> update(int regionId, Map<String, Object> data) {
        regionRepository.findById(regionId)
                .orElseThrow(() -> new VideoBusinessException(400, "检测区域不存在: ID=" + regionId));
        Map<String, Object> fields = new LinkedHashMap<>();
        if (data.containsKey("region_name")) {
            fields.put("region_name", String.valueOf(data.get("region_name")).trim());
        }
        if (data.containsKey("region_type")) {
            fields.put("region_type", data.get("region_type"));
        }
        if (data.containsKey("points")) {
            Object points = data.get("points");
            if (!(points instanceof List<?> list) || list.size() < 3) {
                throw new VideoBusinessException(400, "区域坐标点不能为空，且至少需要3个点");
            }
            try {
                fields.put("points", objectMapper.writeValueAsString(points));
            } catch (Exception e) {
                throw new VideoBusinessException(400, "区域坐标点格式错误");
            }
        }
        if (data.containsKey("image_id")) {
            fields.put("image_id", data.get("image_id"));
        }
        if (data.containsKey("algorithm_type")) {
            fields.put("algorithm_type", data.get("algorithm_type"));
        }
        if (data.containsKey("algorithm_model_id")) {
            fields.put("algorithm_model_id", data.get("algorithm_model_id"));
        }
        if (data.containsKey("algorithm_threshold")) {
            fields.put("algorithm_threshold", data.get("algorithm_threshold"));
        }
        if (data.containsKey("algorithm_enabled")) {
            fields.put("algorithm_enabled", data.get("algorithm_enabled"));
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
        regionRepository.updateFields(regionId, fields);
        return get(regionId);
    }

    public void delete(int regionId) {
        regionRepository.findById(regionId)
                .orElseThrow(() -> new VideoBusinessException(400, "检测区域不存在: ID=" + regionId));
        regionRepository.delete(regionId);
    }

    private static String str(Object v) {
        return v == null ? "" : String.valueOf(v).trim();
    }
}
