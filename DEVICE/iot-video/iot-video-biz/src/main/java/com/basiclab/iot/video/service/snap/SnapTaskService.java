package com.basiclab.iot.video.service.snap;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.dal.SnapSpaceRepository;
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
public class SnapTaskService {

    private final SnapTaskRepository snapTaskRepository;
    private final SnapSpaceRepository snapSpaceRepository;
    private final DeviceRepository deviceRepository;
    private final SnapTaskSchedulerService snapTaskSchedulerService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public Map<String, Object> list(int pageNo, int pageSize, Integer spaceId, String deviceId,
                                  String search, Integer status) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("items", snapTaskRepository.list(pageNo, pageSize, spaceId, deviceId, search, status));
        result.put("total", snapTaskRepository.count(spaceId, deviceId, search, status));
        return result;
    }

    public Map<String, Object> get(int taskId) {
        return snapTaskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍任务不存在: ID=" + taskId));
    }

    public Map<String, Object> create(Map<String, Object> data) {
        String taskName = str(data.get("task_name"));
        if (taskName.isEmpty()) {
            throw new VideoBusinessException(400, "任务名称不能为空");
        }
        Object spaceId = data.get("space_id");
        if (spaceId == null) {
            throw new VideoBusinessException(400, "抓拍空间ID不能为空");
        }
        String deviceId = str(data.get("device_id"));
        if (deviceId.isEmpty()) {
            throw new VideoBusinessException(400, "设备ID不能为空");
        }
        snapSpaceRepository.findById(intVal(spaceId))
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍空间不存在"));
        deviceRepository.findById(deviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: " + deviceId));
        int id = snapTaskRepository.insert(data);
        if (Boolean.TRUE.equals(get(id).get("is_enabled"))) {
            snapTaskSchedulerService.addTaskToScheduler(id);
        }
        return get(id);
    }

    public Map<String, Object> update(int taskId, Map<String, Object> data) {
        snapTaskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍任务不存在: ID=" + taskId));
        Map<String, Object> fields = new LinkedHashMap<>();
        copyIfPresent(fields, data, "task_name", v -> String.valueOf(v).trim());
        copyIfPresent(fields, data, "space_id");
        copyIfPresent(fields, data, "device_id", v -> String.valueOf(v).trim());
        copyIfPresent(fields, data, "capture_type");
        copyIfPresent(fields, data, "cron_expression");
        copyIfPresent(fields, data, "frame_skip");
        copyIfPresent(fields, data, "algorithm_enabled");
        copyIfPresent(fields, data, "algorithm_type");
        copyIfPresent(fields, data, "algorithm_model_id");
        copyIfPresent(fields, data, "algorithm_threshold");
        copyIfPresent(fields, data, "algorithm_night_mode");
        copyIfPresent(fields, data, "alarm_enabled");
        copyIfPresent(fields, data, "alarm_type");
        copyIfPresent(fields, data, "phone_number");
        copyIfPresent(fields, data, "email");
        copyIfPresent(fields, data, "notify_methods");
        copyIfPresent(fields, data, "alarm_suppress_time");
        copyIfPresent(fields, data, "auto_filename");
        copyIfPresent(fields, data, "custom_filename_prefix");
        copyIfPresent(fields, data, "is_enabled");
        if (data.containsKey("notify_users")) {
            try {
                fields.put("notify_users", objectMapper.writeValueAsString(data.get("notify_users")));
            } catch (Exception e) {
                fields.put("notify_users", String.valueOf(data.get("notify_users")));
            }
        }
        snapTaskRepository.updateFields(taskId, fields);
        snapTaskSchedulerService.rescheduleTask(taskId);
        return get(taskId);
    }

    public void delete(int taskId) {
        snapTaskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍任务不存在: ID=" + taskId));
        snapTaskSchedulerService.removeTaskFromScheduler(taskId);
        snapTaskRepository.delete(taskId);
    }

    public Map<String, Object> start(int taskId) {
        snapTaskRepository.setRunState(taskId, true, "running");
        snapTaskSchedulerService.addTaskToScheduler(taskId);
        return get(taskId);
    }

    public Map<String, Object> stop(int taskId) {
        snapTaskRepository.setRunState(taskId, false, "stopped");
        snapTaskSchedulerService.removeTaskFromScheduler(taskId);
        return get(taskId);
    }

    public Map<String, Object> restart(int taskId) {
        Map<String, Object> task = snapTaskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍任务不存在: ID=" + taskId));
        snapTaskSchedulerService.removeTaskFromScheduler(taskId);
        boolean enabled = Boolean.TRUE.equals(task.get("is_enabled"));
        if (enabled) {
            snapTaskSchedulerService.addTaskToScheduler(taskId);
            snapTaskRepository.setRunState(taskId, true, "running");
        } else {
            snapTaskRepository.setRunState(taskId, false, "stopped");
        }
        return get(taskId);
    }

    public Map<String, Object> logs(int taskId, int pageNo, int pageSize, String level) {
        snapTaskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍任务不存在: ID=" + taskId));
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("logs", List.of());
        result.put("total", 0);
        return result;
    }

    private static void copyIfPresent(Map<String, Object> target, Map<String, Object> source, String key) {
        if (source.containsKey(key)) {
            target.put(key, source.get(key));
        }
    }

    private static void copyIfPresent(Map<String, Object> target, Map<String, Object> source, String key,
                                      java.util.function.Function<Object, Object> mapper) {
        if (source.containsKey(key)) {
            target.put(key, mapper.apply(source.get(key)));
        }
    }

    private static String str(Object v) {
        return v == null ? "" : String.valueOf(v).trim();
    }

    private static int intVal(Object v) {
        return v instanceof Number n ? n.intValue() : Integer.parseInt(String.valueOf(v));
    }
}
