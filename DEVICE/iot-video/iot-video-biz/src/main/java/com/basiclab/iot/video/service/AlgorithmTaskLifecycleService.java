package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.process.AlgorithmRuntimeSupervisor;
import com.basiclab.iot.video.config.VideoProperties;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class AlgorithmTaskLifecycleService {

    private final AlgorithmTaskRepository taskRepository;
    private final RuntimeIniGenerator iniGenerator;
    private final AlgorithmRuntimeSupervisor supervisor;
    private final VideoProperties videoProperties;

    public Map<String, Object> getTask(long id) {
        AlgorithmTaskRow row = taskRepository.findById(id)
                .orElseThrow(() -> new VideoBusinessException(400, "算法任务不存在"));
        return row.toMap();
    }

    public Map<String, Object> listTasks(int pageNo, int pageSize, String search, String taskType) {
        return listTasks(pageNo, pageSize, search, taskType, null, null);
    }

    public Map<String, Object> listTasks(
            int pageNo, int pageSize, String search, String taskType, String deviceId, Boolean isEnabled
    ) {
        var items = taskRepository.list(pageNo, pageSize, search, taskType, deviceId, isEnabled)
                .stream().map(AlgorithmTaskRow::toMap).toList();
        return Map.of(
                "items", items,
                "total", taskRepository.count(search, taskType, deviceId, isEnabled)
        );
    }

    public Map<String, Object> start(long id) {
        AlgorithmTaskRow task = taskRepository.findById(id)
                .orElseThrow(() -> new VideoBusinessException(400, "算法任务不存在"));
        normalizeExecutor(task.getExecutor());
        if (!"local".equalsIgnoreCase(task.getSchedulePolicy() != null ? task.getSchedulePolicy() : "local")) {
            throw new VideoBusinessException(400, "Phase 0 仅支持本机 schedule_policy=local（远程 node 见 EXEMPTIONS）");
        }
        if (supervisor.isAlive(id)) {
            Map<String, Object> data = new HashMap<>(task.toMap());
            data.put("already_running", true);
            return Map.of("message", "任务运行中", "data", data);
        }
        Path logDir = Path.of(videoProperties.getRuntime().getLogsDir(), "task_" + id);
        Path logPath = logDir.resolve("runtime.log");
        try {
            String iniPath = iniGenerator.generate(task, logPath);
            String runtimeBin = iniGenerator.resolveRuntimeBin(task);
            supervisor.start(id, runtimeBin, iniPath, logDir);
        } catch (java.io.IOException e) {
            throw new VideoBusinessException(400, "生成 RUNTIME 配置失败: " + e.getMessage());
        } catch (VideoBusinessException e) {
            throw e;
        } catch (Exception e) {
            throw new VideoBusinessException(400, "启动 RUNTIME 失败: " + e.getMessage());
        }
        Integer pid = supervisor.currentPid(id);
        int port = task.getRuntimeControlPort() != null ? task.getRuntimeControlPort() : 8000 + (int) (id % 1000);
        // Match oracle: DB run_status may lag while daemon is alive; services/status uses process probe.
        taskRepository.updateRunState(id, true, "stopped", logDir.toString(), port, pid);
        AlgorithmTaskRow updated = taskRepository.findById(id).orElse(task);
        Map<String, Object> data = new HashMap<>(updated.toMap());
        data.put("already_running", false);
        return Map.of("message", "启动成功", "data", data);
    }

    public Map<String, Object> stop(long id) {
        taskRepository.findById(id)
                .orElseThrow(() -> new VideoBusinessException(400, "算法任务不存在"));
        supervisor.stop(id, true);
        taskRepository.updateRunState(id, false, "stopped", null, null, null);
        AlgorithmTaskRow updated = taskRepository.findById(id)
                .orElseThrow(() -> new VideoBusinessException(400, "算法任务不存在"));
        return Map.of("message", "停止成功", "data", updated.toMap());
    }

    public Map<String, Object> restart(long id) {
        stop(id);
        return start(id);
    }

    public Map<String, Object> getServicesStatus(long id) {
        AlgorithmTaskRow task = taskRepository.findById(id)
                .orElseThrow(() -> new VideoBusinessException(400, "算法任务不存在"));
        String serviceStatus = resolveServiceStatus(id, task);
        Map<String, Object> result = new HashMap<>();
        result.put("realtime_service", null);
        result.put("snap_service", null);
        result.put("patrol_service", null);
        result.put("extractor", null);
        result.put("sorter", null);
        result.put("pusher", null);
        String taskType = normalizeTaskType(task.getTaskType());
        Map<String, Object> svc = buildServiceRow(task, serviceStatus);
        if ("realtime".equals(taskType)) {
            result.put("realtime_service", svc);
        } else if ("snap".equals(taskType)) {
            result.put("snap_service", svc);
        } else if ("patrol".equals(taskType)) {
            svc.put("patrol_mode", task.getPatrolMode());
            svc.put("patrol_interval_sec", task.getPatrolIntervalSec());
            svc.put("patrol_pool_size", task.getPatrolPoolSize());
            result.put("patrol_service", svc);
        }
        return result;
    }

    private String resolveServiceStatus(long id, AlgorithmTaskRow task) {
        if (supervisor.isAlive(id)) {
            return "running";
        }
        Instant heartbeat = task.getServiceLastHeartbeat();
        if (heartbeat != null && Duration.between(heartbeat, Instant.now()).getSeconds() < 60) {
            return "running";
        }
        return "stopped";
    }

    private Map<String, Object> buildServiceRow(AlgorithmTaskRow task, String serviceStatus) {
        Map<String, Object> svc = new HashMap<>();
        svc.put("task_id", task.getId());
        svc.put("task_name", task.getTaskName());
        svc.put("server_ip", task.getServiceServerIp());
        svc.put("port", task.getServicePort());
        svc.put("process_id", task.getServiceProcessId());
        svc.put("last_heartbeat", task.getServiceLastHeartbeat() != null ? task.getServiceLastHeartbeat().toString() : null);
        svc.put("log_path", task.getServiceLogPath());
        svc.put("status", serviceStatus);
        svc.put("run_status", task.getRunStatus() != null ? task.getRunStatus() : "stopped");
        return svc;
    }

    private String normalizeTaskType(String taskType) {
        String tt = taskType != null ? taskType.trim().toLowerCase() : "realtime";
        if ("snapshot".equals(tt)) {
            return "snap";
        }
        return tt;
    }

    public void normalizeExecutor(String executor) {
        if (executor == null || executor.isBlank()) {
            return;
        }
        String v = executor.trim().toLowerCase();
        if ("python".equals(v) || "py".equals(v)) {
            throw new VideoBusinessException(400, "executor=python 已停用；算法热路径仅支持 executor=cpp（C++ RUNTIME）");
        }
        if (!"cpp".equals(v) && !"c++".equals(v) && !"runtime".equals(v) && !"cxx".equals(v)) {
            throw new VideoBusinessException(400, "不支持的 executor=" + executor + "；仅允许 cpp");
        }
    }
}
