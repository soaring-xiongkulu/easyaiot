package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Remote algorithm_task deploy via iot-node (mirrors Python {@code _deploy_task_on_remote_node}).
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AlgorithmRemoteDeployService {

    private final IotNodeClient iotNodeClient;
    private final RemoteScheduleSupport remoteScheduleSupport;
    private final RuntimeIniGenerator iniGenerator;
    private final AlgorithmTaskRepository taskRepository;
    private final VideoProperties videoProperties;

    public Map<String, Object> deploy(AlgorithmTaskRow task) {
        long taskId = task.getId();
        String policy = task.getSchedulePolicy() != null ? task.getSchedulePolicy() : "local";
        Long targetNodeId = task.getTargetNodeId();
        if ("node".equalsIgnoreCase(policy) && targetNodeId == null) {
            throw new VideoBusinessException(400, "已选择指定节点但未配置目标节点");
        }

        String taskType = normalizeTaskType(task.getTaskType());
        if (!List.of("realtime", "snap", "patrol").contains(taskType)) {
            throw new VideoBusinessException(400, "executor=cpp 不支持任务类型: " + taskType);
        }

        try {
            Map<String, Object> allocation = iotNodeClient.allocateNode(
                    RemoteScheduleSupport.WORKLOAD_ALGORITHM,
                    String.valueOf(taskId),
                    remoteScheduleSupport.algorithmCapabilities(taskType),
                    task.getPreferGpu() == null || task.getPreferGpu(),
                    true,
                    "node".equalsIgnoreCase(policy) ? targetNodeId : null,
                    null
            );

            long nodeId = toLong(allocation.get("nodeId"));
            String host = stringOrEmpty(allocation.get("host"));
            String gpuIds = allocation.get("gpuIds") != null ? String.valueOf(allocation.get("gpuIds")) : null;

            String videoRootRemote = remoteScheduleSupport.remoteVideoRoot();
            String logDir = videoRootRemote + "/logs/task_" + taskId;
            RuntimeIniGenerator.IniArtifact ini = iniGenerator.buildRemoteIniArtifact(task, logDir);

            List<String> command = List.of(
                    remoteScheduleSupport.remoteRuntimeBin(),
                    ini.deployIniPath()
            );
            String workDir = "/opt/easyaiot/RUNTIME";

            Map<String, String> env = remoteScheduleSupport.copyProcessEnv();
            env.put("PYTHONUNBUFFERED", "1");
            env.put("TASK_ID", String.valueOf(taskId));
            env.put("VIDEO_CONTROL_URL", remoteScheduleSupport.resolveVideoControlUrl());
            env.put("VIDEO_HEARTBEAT_URL", remoteScheduleSupport.resolveVideoControlUrl()
                    + "/algorithm/heartbeat/" + ("patrol".equals(taskType) ? "patrol" : "realtime"));
            env.put("LOG_PATH", logDir);
            env.put("POD_IP", host);
            env.put("HOST_IP", host);
            env.put("VIDEO_ROOT", videoRootRemote);
            env.put("RUNTIME_BIN", remoteScheduleSupport.remoteRuntimeBin());
            env.put("LD_LIBRARY_PATH", remoteScheduleSupport.remoteRuntimeLdLibraryPath());
            boolean preferGpu = task.getPreferGpu() == null || task.getPreferGpu();
            env.put("USE_GPU", preferGpu ? "true" : "false");
            env.put("RUNTIME_PREFER_GPU", preferGpu ? "true" : "false");

            List<Map<String, String>> files = List.of(Map.of(
                    "path", ini.deployIniPath(),
                    "content", ini.content(),
                    "mode", "0644"
            ));

            Map<String, Object> result = iotNodeClient.deployWorkload(
                    nodeId,
                    RemoteScheduleSupport.WORKLOAD_ALGORITHM,
                    String.valueOf(taskId),
                    command,
                    workDir,
                    logDir,
                    env,
                    gpuIds,
                    files
            );

            Integer pid = toInteger(result.get("pid"));
            int port = task.getRuntimeControlPort() != null
                    ? task.getRuntimeControlPort()
                    : 8000 + (int) (taskId % 1000);

            taskRepository.updateRemoteRunState(
                    taskId, true, "running", logDir, port, pid, nodeId, host
            );
            taskRepository.updateHeartbeat(taskId, host, port, pid, logDir, "running");

            log.info(
                    "算法任务远程部署成功 task_id={} node_id={} host={} pid={}",
                    taskId, nodeId, host, pid
            );

            AlgorithmTaskRow updated = taskRepository.findById(taskId).orElse(task);
            Map<String, Object> data = new LinkedHashMap<>(updated.toMap());
            data.put("already_running", false);
            return Map.of(
                    "message", "已下发到节点 " + host + " (cpp)",
                    "data", data
            );
        } catch (IotNodeClient.NodeClientException ex) {
            throw new VideoBusinessException(400, "远程节点部署失败: " + ex.getMessage());
        } catch (java.io.IOException ex) {
            throw new VideoBusinessException(400, "生成远程 RUNTIME 配置失败: " + ex.getMessage());
        }
    }

    public void stopRemote(AlgorithmTaskRow task) {
        Long nodeId = task.getNodeId();
        if (nodeId == null) {
            return;
        }
        long taskId = task.getId();
        iotNodeClient.stopWorkload(nodeId, RemoteScheduleSupport.WORKLOAD_ALGORITHM, String.valueOf(taskId));
        iotNodeClient.releaseWorkload(RemoteScheduleSupport.WORKLOAD_ALGORITHM, String.valueOf(taskId));
        taskRepository.clearRemoteBinding(taskId);
    }

    public boolean isRemoteHealthy(AlgorithmTaskRow task) {
        Long nodeId = task.getNodeId();
        if (nodeId == null) {
            return false;
        }
        if (!iotNodeClient.isNodeOnline(nodeId)) {
            return false;
        }
        Instant heartbeat = task.getServiceLastHeartbeat();
        if (heartbeat == null) {
            return false;
        }
        long failoverSec = videoProperties.getHealthMonitor().getHeartbeatFailoverSeconds();
        return Duration.between(heartbeat, Instant.now()).getSeconds() <= failoverSec;
    }

    private static String normalizeTaskType(String taskType) {
        String tt = taskType != null ? taskType.trim().toLowerCase() : "realtime";
        if ("snapshot".equals(tt)) {
            return "snap";
        }
        return tt;
    }

    private static long toLong(Object value) {
        return Long.parseLong(String.valueOf(value));
    }

    private static Integer toInteger(Object value) {
        if (value == null) {
            return null;
        }
        return Integer.parseInt(String.valueOf(value));
    }

    private static String stringOrEmpty(Object value) {
        return value == null ? "" : String.valueOf(value);
    }
}
