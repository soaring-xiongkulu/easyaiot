package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
@RequiredArgsConstructor
public class HeartbeatService {

    private final AlgorithmTaskRepository taskRepository;

    public Map<String, Object> receiveRealtime(Map<String, Object> body) {
        Object rawId = body.get("task_id");
        if (rawId == null) {
            throw new VideoBusinessException(400, "缺少必要参数：task_id");
        }
        long taskId = Long.parseLong(String.valueOf(rawId));
        AlgorithmTaskRow task = taskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "算法任务不存在：task_id=" + taskId));
        String serverIp = body.get("server_ip") != null ? String.valueOf(body.get("server_ip")) : null;
        Integer port = parseInt(body.get("port"));
        Integer processId = parseInt(body.get("process_id"));
        String logPath = body.get("log_path") != null ? String.valueOf(body.get("log_path")) : null;
        if (logPath == null && (task.getServiceLogPath() == null || task.getServiceLogPath().isBlank())) {
            logPath = defaultLogPath(taskId);
        }
        String runStatus = "stopped".equals(task.getRunStatus()) ? null : "running";
        taskRepository.updateHeartbeat(taskId, serverIp, port, processId, logPath, runStatus);
        return Map.of("task_id", taskId, "task_name", task.getTaskName());
    }

    public Map<String, Object> receivePatrol(Map<String, Object> body) {
        if (body == null) {
            body = Map.of();
        }
        Object rawId = body.get("task_id");
        if (rawId == null) {
            throw new VideoBusinessException(400, "缺少必要参数：task_id");
        }
        long taskId = Long.parseLong(String.valueOf(rawId));
        AlgorithmTaskRow task = taskRepository.findById(taskId)
                .orElseThrow(() -> new VideoBusinessException(400, "巡检任务不存在：task_id=" + taskId));
        if (!"patrol".equalsIgnoreCase(task.getTaskType())) {
            throw new VideoBusinessException(400, "巡检任务不存在：task_id=" + taskId);
        }
        String serverIp = body.get("server_ip") != null ? String.valueOf(body.get("server_ip")) : null;
        Integer processId = parseInt(body.get("process_id"));
        String logPath = body.get("log_path") != null ? String.valueOf(body.get("log_path")) : null;
        if (logPath == null && (task.getServiceLogPath() == null || task.getServiceLogPath().isBlank())) {
            logPath = defaultLogPath(taskId);
        }
        Integer totalPatrols = body.get("total_patrols") != null ? parseInt(body.get("total_patrols")) : null;
        Integer totalDetections = body.get("total_detections") != null ? parseInt(body.get("total_detections")) : null;
        taskRepository.updatePatrolHeartbeat(taskId, serverIp, processId, logPath, totalPatrols, totalDetections);
        return Map.of("task_id", taskId);
    }

    private String defaultLogPath(long taskId) {
        return System.getProperty("user.home") + "/.video-java/logs/task_" + taskId;
    }

    private Integer parseInt(Object value) {
        if (value == null) {
            return null;
        }
        try {
            return Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException e) {
            return null;
        }
    }
}
