package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.dal.StreamForwardTaskRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.domain.StreamForwardTaskRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class StreamForwardAdminService {

    private final StreamForwardTaskRepository taskRepository;
    private final DeviceRepository deviceRepository;
    private final StreamForwardService lifecycleService;

    public Map<String, Object> listTasks(
            int pageNo, int pageSize, String search, String deviceId, Boolean isEnabled
    ) {
        List<Map<String, Object>> items = taskRepository.list(pageNo, pageSize, search, deviceId, isEnabled)
                .stream()
                .map(StreamForwardTaskRow::toMap)
                .toList();
        return Map.of(
                "items", items,
                "total", taskRepository.count(search, deviceId, isEnabled)
        );
    }

    public StreamForwardTaskRow create(Map<String, Object> body) {
        if (body == null || body.isEmpty()) {
            throw new VideoBusinessException(400, "请求数据不能为空");
        }
        String taskName = asString(body.get("task_name"));
        if (taskName == null || taskName.isBlank()) {
            throw new VideoBusinessException(400, "任务名称不能为空");
        }
        List<String> deviceIds = parseStringList(body.get("device_ids"));
        for (String deviceId : deviceIds) {
            deviceRepository.findById(deviceId)
                    .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: ID=" + deviceId));
        }
        String taskCode = "STREAM_FORWARD_" + UUID.randomUUID().toString().replace("-", "").substring(0, 8).toUpperCase();
        Map<String, Object> fields = new LinkedHashMap<>();
        fields.put("task_name", taskName.trim());
        fields.put("task_code", taskCode);
        fields.put("output_format", asString(body.getOrDefault("output_format", "rtmp")));
        fields.put("output_quality", asString(body.getOrDefault("output_quality", "high")));
        fields.put("output_bitrate", asString(body.get("output_bitrate")));
        fields.put("description", asString(body.get("description")));
        fields.put("is_enabled", parseEnabled(body.get("is_enabled"), false));
        fields.put("total_streams", deviceIds.size());
        fields.put("schedule_policy", asString(body.getOrDefault("schedule_policy", "local")));
        fields.put("prefer_gpu", parseEnabled(body.get("prefer_gpu"), true));
        fields.put("target_node_id", body.get("target_node_id"));
        long id = taskRepository.insert(fields);
        taskRepository.replaceDevices(id, deviceIds);
        return taskRepository.findById(id)
                .orElseThrow(() -> new VideoBusinessException(500, "创建推流转发任务失败"));
    }

    public Map<String, Object> update(long id, Map<String, Object> body) {
        if (body == null || body.isEmpty()) {
            throw new VideoBusinessException(400, "请求数据不能为空");
        }
        StreamForwardTaskRow existing = taskRepository.findById(id)
                .orElseThrow(() -> new VideoBusinessException(400, "推流转发任务不存在"));
        boolean wasEnabled = Boolean.TRUE.equals(existing.getIsEnabled());
        List<String> previousDeviceIds = existing.getDeviceIds() != null
                ? new ArrayList<>(existing.getDeviceIds()) : List.of();
        String previousSchedule = existing.getSchedulePolicy() != null ? existing.getSchedulePolicy() : "local";
        Long previousTargetNode = existing.getTargetNodeId();

        Map<String, Object> fields = new LinkedHashMap<>();
        if (body.containsKey("task_name")) {
            fields.put("task_name", asString(body.get("task_name")));
        }
        if (body.containsKey("output_format")) {
            fields.put("output_format", asString(body.get("output_format")));
        }
        if (body.containsKey("output_quality")) {
            fields.put("output_quality", asString(body.get("output_quality")));
        }
        if (body.containsKey("output_bitrate")) {
            fields.put("output_bitrate", asString(body.get("output_bitrate")));
        }
        if (body.containsKey("description")) {
            fields.put("description", asString(body.get("description")));
        }
        if (body.containsKey("is_enabled")) {
            fields.put("is_enabled", parseEnabled(body.get("is_enabled"), false));
        }
        if (body.containsKey("schedule_policy")) {
            fields.put("schedule_policy", asString(body.get("schedule_policy")));
        }
        if (body.containsKey("target_node_id")) {
            fields.put("target_node_id", body.get("target_node_id"));
        }
        if (body.containsKey("prefer_gpu")) {
            fields.put("prefer_gpu", parseEnabled(body.get("prefer_gpu"), true));
        }

        boolean deviceIdsChanged = false;
        if (body.containsKey("device_ids")) {
            List<String> deviceIds = parseStringList(body.get("device_ids"));
            for (String deviceId : deviceIds) {
                deviceRepository.findById(deviceId)
                        .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: ID=" + deviceId));
            }
            deviceIdsChanged = !Objects.equals(new ArrayList<>(deviceIds), previousDeviceIds);
            taskRepository.replaceDevices(id, deviceIds);
            fields.put("total_streams", deviceIds.size());
        }

        String newSchedule = body.containsKey("schedule_policy")
                ? asString(body.get("schedule_policy")) : previousSchedule;
        Long newTargetNode = body.containsKey("target_node_id")
                ? toLong(body.get("target_node_id")) : previousTargetNode;
        boolean scheduleChanged = !Objects.equals(
                newSchedule != null ? newSchedule : "local",
                previousSchedule != null ? previousSchedule : "local"
        ) || !Objects.equals(newTargetNode, previousTargetNode);

        if (!fields.isEmpty()) {
            taskRepository.updateFields(id, fields);
        }

        String syncAction = null;
        StreamForwardTaskRow updated = taskRepository.findById(id)
                .orElseThrow(() -> new VideoBusinessException(500, "更新推流转发任务失败"));
        if (wasEnabled && Boolean.TRUE.equals(updated.getIsEnabled()) && (deviceIdsChanged || scheduleChanged)) {
            syncAction = scheduleChanged ? "full_restart" : "rebalance";
            try {
                lifecycleService.restart(id);
            } catch (Exception ignored) {
                // align Python: sync failure is logged but update still succeeds
            }
            updated = taskRepository.findById(id).orElse(updated);
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("task", updated.toMap());
        result.put("sync_action", syncAction);
        return result;
    }

    public void delete(long id) {
        StreamForwardTaskRow task = taskRepository.findById(id)
                .orElseThrow(() -> new VideoBusinessException(400, "推流转发任务不存在"));
        if (Boolean.TRUE.equals(task.getIsEnabled())) {
            lifecycleService.stop(id);
        }
        taskRepository.delete(id);
    }

    public List<Map<String, Object>> listStreams(long taskId) {
        taskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "推流转发任务不存在"));
        return taskRepository.listStreamDevices(taskId);
    }

    public Map<String, Object> ensureDeviceTask(String deviceId) {
        DeviceRow device = deviceRepository.findById(deviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "设备 " + deviceId + " 不存在"));

        var existingId = taskRepository.findTaskIdByDeviceId(deviceId);
        if (existingId.isPresent()) {
            StreamForwardTaskRow task = taskRepository.findById(existingId.get())
                    .orElseThrow(() -> new VideoBusinessException(500, "查询推流转发任务失败"));
            Map<String, Object> data = new LinkedHashMap<>();
            data.put("task_id", task.getId());
            data.put("task_name", task.getTaskName());
            data.put("task_code", task.getTaskCode());
            data.put("is_enabled", Boolean.TRUE.equals(task.getIsEnabled()));
            return data;
        }

        String taskName = (device.getName() != null && !device.getName().isBlank() ? device.getName() : deviceId)
                + "-推流转发";
        Map<String, Object> createBody = new LinkedHashMap<>();
        createBody.put("task_name", taskName);
        createBody.put("device_ids", List.of(deviceId));
        createBody.put("output_format", "rtmp");
        createBody.put("output_quality", "high");
        createBody.put("description", "为设备 " + (device.getName() != null ? device.getName() : deviceId)
                + " 自动创建的推流转发任务");
        createBody.put("is_enabled", false);
        StreamForwardTaskRow task = create(createBody);
        try {
            lifecycleService.start(task.getId());
        } catch (Exception ignored) {
            // align Python: return task even if start fails
        }
        task = taskRepository.findById(task.getId()).orElse(task);
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("task_id", task.getId());
        data.put("task_name", task.getTaskName());
        data.put("task_code", task.getTaskCode());
        data.put("is_enabled", Boolean.TRUE.equals(task.getIsEnabled()));
        return data;
    }

    private static String asString(Object value) {
        return value == null ? null : String.valueOf(value);
    }

    private static Long toLong(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number number) {
            return number.longValue();
        }
        try {
            return Long.parseLong(String.valueOf(value));
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static boolean parseEnabled(Object value, boolean defaultValue) {
        if (value == null) {
            return defaultValue;
        }
        if (value instanceof Boolean b) {
            return b;
        }
        if (value instanceof Number number) {
            return number.intValue() != 0;
        }
        String s = String.valueOf(value).trim().toLowerCase();
        return "true".equals(s) || "1".equals(s) || "yes".equals(s) || "on".equals(s);
    }

    private static List<String> parseStringList(Object raw) {
        if (raw == null) {
            return new ArrayList<>();
        }
        if (raw instanceof List<?> list) {
            List<String> out = new ArrayList<>();
            for (Object item : list) {
                if (item != null) {
                    out.add(String.valueOf(item));
                }
            }
            return out;
        }
        return new ArrayList<>();
    }
}
