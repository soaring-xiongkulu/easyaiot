package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.dal.StreamForwardTaskRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.domain.StreamForwardTaskRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.process.StreamForwardSupervisor;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

@Service
@RequiredArgsConstructor
public class StreamForwardService {

    private final StreamForwardTaskRepository taskRepository;
    private final DeviceRepository deviceRepository;
    private final ViewForwardService viewForwardService;
    private final StreamForwardSupervisor supervisor;
    private final VideoProperties videoProperties;
    private final RemoteScheduleSupport remoteScheduleSupport;
    private final StreamForwardRemoteDeployService remoteDeployService;

    public Map<String, Object> getTask(long taskId) {
        StreamForwardTaskRow row = taskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "推流转发任务不存在"));
        return row.toMap();
    }

    public Map<String, Object> start(long taskId) {
        StreamForwardTaskRow task = taskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "推流转发任务不存在"));

        if (Boolean.TRUE.equals(task.getIsEnabled()) && supervisor.isAlive(taskId)) {
            Map<String, Object> data = new HashMap<>(task.toMap());
            data.put("already_running", true);
            return Map.of("message", "任务已在运行中", "data", data);
        }

        List<String> deviceIds = task.getDeviceIds();
        if (deviceIds == null || deviceIds.isEmpty()) {
            throw new VideoBusinessException(400, "推流转发任务必须关联至少一个摄像头");
        }

        if (remoteScheduleSupport.shouldUseRemoteDeploy(task)) {
            if (task.getNodeId() != null && remoteDeployService.isRemoteHealthy(task)) {
                Map<String, Object> data = new HashMap<>(task.toMap());
                data.put("already_running", true);
                return Map.of("message", "任务已在远程节点运行", "data", data);
            }
            return remoteDeployService.deploy(task);
        }

        Map<String, Supplier<List<String>>> deviceCommands = new LinkedHashMap<>();
        for (String deviceId : deviceIds) {
            DeviceRow device = deviceRepository.findById(deviceId)
                    .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: ID=" + deviceId));
            if (!viewForwardService.isDeviceAvailableForStream(device)) {
                throw new VideoBusinessException(400, "设备处于离线状态，无法启动推送: " + deviceId);
            }
            deviceCommands.put(deviceId, () -> viewForwardService.buildForwardCommand(device));
        }

        Path logDir = Path.of(videoProperties.getRuntime().getLogsDir(), "stream_forward_task_" + taskId);
        taskRepository.updateServiceState(taskId, true, logDir.toString(), null);
        try {
            supervisor.start(taskId, deviceCommands, logDir, () -> isTaskEnabled(taskId));
        } catch (IOException e) {
            taskRepository.updateEnabled(taskId, false, null);
            throw new VideoBusinessException(500, "启动推流转发服务失败: " + e.getMessage());
        }

        Integer pid = supervisor.currentPid(taskId);
        if (pid != null) {
            taskRepository.updateServiceState(taskId, true, logDir.toString(), pid);
        }
        StreamForwardTaskRow updated = taskRepository.findById(taskId).orElse(task);
        Map<String, Object> data = new HashMap<>(updated.toMap());
        data.put("already_running", false);
        return Map.of("message", "启动成功", "data", data);
    }

    public Map<String, Object> stop(long taskId) {
        StreamForwardTaskRow task = taskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "推流转发任务不存在"));

        if (task.getNodeId() != null) {
            remoteDeployService.stopRemote(task);
        }
        supervisor.stop(taskId);
        taskRepository.updateEnabled(taskId, false, null);
        StreamForwardTaskRow updated = taskRepository.findById(taskId).orElse(task);
        return Map.of("message", "停止成功", "data", updated.toMap());
    }

    public Map<String, Object> restart(long taskId) {
        StreamForwardTaskRow task = taskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "推流转发任务不存在"));
        if (!Boolean.TRUE.equals(task.getIsEnabled())) {
            return start(taskId);
        }
        supervisor.stop(taskId);
        return start(taskId);
    }

    public Map<String, Object> receiveHeartbeat(Map<String, Object> body) {
        if (body == null || body.get("task_id") == null) {
            throw new VideoBusinessException(400, "缺少必要参数：task_id");
        }
        long taskId = Long.parseLong(String.valueOf(body.get("task_id")));
        StreamForwardTaskRow task = taskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "推流转发任务不存在：task_id=" + taskId));

        String serverIp = body.get("server_ip") != null ? String.valueOf(body.get("server_ip")) : null;
        Integer port = toInteger(body.get("port"));
        Integer processId = toInteger(body.get("process_id"));
        String logPath = body.get("log_path") != null ? String.valueOf(body.get("log_path")) : null;
        if (logPath == null || logPath.isBlank()) {
            logPath = Path.of(videoProperties.getRuntime().getLogsDir(), "stream_forward_task_" + taskId).toString();
        }
        taskRepository.updateHeartbeat(taskId, serverIp, port, processId, logPath);

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("task_id", task.getId());
        data.put("task_name", task.getTaskName());
        return data;
    }

    public Map<String, Object> taskStatus(long taskId) {
        StreamForwardTaskRow task = taskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "推流转发任务不存在"));

        boolean daemonRunning = supervisor.isAlive(taskId);
        String serviceStatus = resolveServiceStatus(task, daemonRunning);

        Map<String, Object> info = new LinkedHashMap<>();
        info.put("task_id", task.getId());
        info.put("task_name", task.getTaskName());
        info.put("server_ip", task.getServiceServerIp());
        info.put("port", task.getServicePort());
        info.put("process_id", task.getServiceProcessId());
        info.put("last_heartbeat", formatInstant(task.getServiceLastHeartbeat()));
        info.put("log_path", task.getServiceLogPath());
        info.put("status", serviceStatus);
        info.put("total_streams", task.getTotalStreams());
        info.put("schedule_policy", task.getSchedulePolicy() != null ? task.getSchedulePolicy() : "local");
        info.put("target_node_id", task.getTargetNodeId());
        info.put("node_id", task.getNodeId());
        info.put("device_deployments", task.toMap().get("device_deployments"));
        info.put("deployment_count", task.getDeviceIds() != null ? task.getDeviceIds().size() : 0);
        info.put("output_quality", task.getOutputQuality());
        return info;
    }

    private String resolveServiceStatus(StreamForwardTaskRow task, boolean daemonRunning) {
        if (!Boolean.TRUE.equals(task.getIsEnabled())) {
            return "stopped";
        }
        Instant heartbeat = task.getServiceLastHeartbeat();
        boolean hasRecentHeartbeat = heartbeat != null
                && Duration.between(heartbeat, Instant.now()).getSeconds() < 60;
        boolean isRemote = task.getNodeId() != null
                || (task.getDeviceDeployments() != null && !task.getDeviceDeployments().isBlank());
        if (hasRecentHeartbeat) {
            return "running";
        }
        if (isRemote && task.getServiceProcessId() != null) {
            return "running";
        }
        if (daemonRunning) {
            return "running";
        }
        return "stopped";
    }

    private boolean isTaskEnabled(long taskId) {
        return taskRepository.findById(taskId)
                .map(row -> Boolean.TRUE.equals(row.getIsEnabled()))
                .orElse(false);
    }

    private static Integer toInteger(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number number) {
            return number.intValue();
        }
        try {
            return Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static String formatInstant(Instant instant) {
        if (instant == null) {
            return null;
        }
        String s = instant.toString();
        if (!s.endsWith("Z") && !s.contains("+")) {
            return s + "Z";
        }
        return s;
    }
}
