package com.basiclab.iot.video.service.snap;

import com.basiclab.iot.video.dal.DetectionRegionRepository;
import com.basiclab.iot.video.dal.MediaAlgorithmRepository;
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
public class SnapAlgorithmService {

    private final MediaAlgorithmRepository algorithmRepository;
    private final SnapTaskRepository snapTaskRepository;
    private final DetectionRegionRepository regionRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public List<Map<String, Object>> listTaskServices(int taskId) {
        snapTaskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍任务不存在: ID=" + taskId));
        return algorithmRepository.listTaskServices(taskId);
    }

    public Map<String, Object> createTaskService(int taskId, Map<String, Object> data) {
        snapTaskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍任务不存在: ID=" + taskId));
        validateServicePayload(data);
        normalizeJsonFields(data);
        int id = algorithmRepository.insertTaskService(taskId, data);
        return algorithmRepository.findTaskService(id)
                .orElseThrow(() -> new VideoBusinessException(500, "创建算法服务配置失败"));
    }

    public Map<String, Object> updateTaskService(int serviceId, Map<String, Object> data) {
        algorithmRepository.findTaskService(serviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "算法服务配置不存在: ID=" + serviceId));
        Map<String, Object> fields = mapServiceFields(data);
        algorithmRepository.updateTaskService(serviceId, fields);
        return algorithmRepository.findTaskService(serviceId)
                .orElseThrow(() -> new VideoBusinessException(500, "更新算法服务配置失败"));
    }

    public void deleteTaskService(int serviceId) {
        algorithmRepository.findTaskService(serviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "算法服务配置不存在: ID=" + serviceId));
        algorithmRepository.deleteTaskService(serviceId);
    }

    public List<Map<String, Object>> listRegionServices(int regionId) {
        regionRepository.findById(regionId)
                .orElseThrow(() -> new VideoBusinessException(400, "检测区域不存在: ID=" + regionId));
        return algorithmRepository.listRegionServices(regionId);
    }

    public Map<String, Object> createRegionService(int regionId, Map<String, Object> data) {
        regionRepository.findById(regionId)
                .orElseThrow(() -> new VideoBusinessException(400, "检测区域不存在: ID=" + regionId));
        validateServicePayload(data);
        normalizeJsonFields(data);
        int id = algorithmRepository.insertRegionService(regionId, data);
        return algorithmRepository.findRegionService(id)
                .orElseThrow(() -> new VideoBusinessException(500, "创建区域算法服务配置失败"));
    }

    public Map<String, Object> updateRegionService(int serviceId, Map<String, Object> data) {
        algorithmRepository.findRegionService(serviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "区域算法服务配置不存在: ID=" + serviceId));
        Map<String, Object> fields = mapServiceFields(data);
        algorithmRepository.updateRegionService(serviceId, fields);
        return algorithmRepository.findRegionService(serviceId)
                .orElseThrow(() -> new VideoBusinessException(500, "更新区域算法服务配置失败"));
    }

    public void deleteRegionService(int serviceId) {
        algorithmRepository.findRegionService(serviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "区域算法服务配置不存在: ID=" + serviceId));
        algorithmRepository.deleteRegionService(serviceId);
    }

    private void validateServicePayload(Map<String, Object> data) {
        if (str(data.get("service_name")).isEmpty()) {
            throw new VideoBusinessException(400, "服务名称不能为空");
        }
        if (str(data.get("service_url")).isEmpty()) {
            throw new VideoBusinessException(400, "服务URL不能为空");
        }
    }

    private void normalizeJsonFields(Map<String, Object> data) {
        try {
            if (data.get("request_headers") != null && !(data.get("request_headers") instanceof String)) {
                data.put("request_headers", objectMapper.writeValueAsString(data.get("request_headers")));
            }
            if (data.get("request_body_template") != null && !(data.get("request_body_template") instanceof String)) {
                data.put("request_body_template", objectMapper.writeValueAsString(data.get("request_body_template")));
            }
        } catch (Exception ignored) {
        }
    }

    private Map<String, Object> mapServiceFields(Map<String, Object> data) {
        Map<String, Object> fields = new LinkedHashMap<>();
        for (String key : List.of("service_name", "service_url", "service_type", "model_id", "threshold",
                "request_method", "timeout", "is_enabled", "sort_order")) {
            if (data.containsKey(key)) {
                fields.put(key, data.get(key));
            }
        }
        normalizeJsonFields(data);
        if (data.containsKey("request_headers")) {
            fields.put("request_headers", data.get("request_headers"));
        }
        if (data.containsKey("request_body_template")) {
            fields.put("request_body_template", data.get("request_body_template"));
        }
        return fields;
    }

    private static String str(Object v) {
        return v == null ? "" : String.valueOf(v).trim();
    }
}
