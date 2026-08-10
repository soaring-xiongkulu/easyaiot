package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.StreamForwardTaskRepository;
import com.basiclab.iot.video.domain.StreamForwardTaskRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Remote stream_forward deploy via iot-node (mirrors Python {@code _deploy_task_on_remote_node}).
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class StreamForwardRemoteDeployService {

    private final IotNodeClient iotNodeClient;
    private final RemoteScheduleSupport remoteScheduleSupport;
    private final StreamForwardTaskRepository taskRepository;
    private final VideoProperties videoProperties;

    public Map<String, Object> deploy(StreamForwardTaskRow task) {
        long taskId = task.getId();
        List<String> deviceIds = task.getDeviceIds();
        if (deviceIds == null || deviceIds.isEmpty()) {
            throw new VideoBusinessException(400, "任务未关联可用摄像头");
        }

        String policy = task.getSchedulePolicy() != null ? task.getSchedulePolicy() : "local";
        Long targetNodeId = task.getTargetNodeId();
        if ("node".equalsIgnoreCase(policy) && targetNodeId == null) {
            throw new VideoBusinessException(400, "已选择指定节点但未配置目标节点");
        }

        try {
            Map<String, Object> allocation = iotNodeClient.allocateNode(
                    RemoteScheduleSupport.WORKLOAD_STREAM_FORWARD,
                    String.valueOf(taskId),
                    List.of("stream_forward", "srs_live"),
                    task.getPreferGpu() == null || task.getPreferGpu(),
                    true,
                    "node".equalsIgnoreCase(policy) ? targetNodeId : null,
                    null
            );

            long nodeId = toLong(allocation.get("nodeId"));
            String host = stringOrEmpty(allocation.get("host"));
            String gpuIds = allocation.get("gpuIds") != null ? String.valueOf(allocation.get("gpuIds")) : null;

            String videoRootRemote = remoteScheduleSupport.remoteVideoRoot();
            String workDir = videoRootRemote + "/services/stream_forward_service";
            String logDir = videoRootRemote + "/logs/stream_forward_task_" + taskId;
            String deployScript = workDir + "/run_deploy.py";
            List<String> command = List.of(remoteScheduleSupport.remotePython(), deployScript);

            Map<String, String> env = buildStreamForwardEnv(taskId, logDir, host, deviceIds, String.valueOf(taskId));
            env.put("VIDEO_ROOT", videoRootRemote);

            Map<String, Object> result = iotNodeClient.deployWorkload(
                    nodeId,
                    RemoteScheduleSupport.WORKLOAD_STREAM_FORWARD,
                    String.valueOf(taskId),
                    command,
                    workDir,
                    logDir,
                    env,
                    gpuIds,
                    null
            );

            Integer pid = toInteger(result.get("pid"));
            taskRepository.updateRemoteDeployState(
                    taskId, true, logDir, pid, nodeId, host, serializeDeployments(taskId, deviceIds, nodeId, host, pid, logDir)
            );

            log.info(
                    "推流转发远程部署成功 task_id={} node_id={} host={} pid={}",
                    taskId, nodeId, host, pid
            );

            StreamForwardTaskRow updated = taskRepository.findById(taskId).orElse(task);
            Map<String, Object> data = new LinkedHashMap<>(updated.toMap());
            data.put("already_running", false);
            return Map.of(
                    "message", "已下发到节点 " + host,
                    "data", data
            );
        } catch (IotNodeClient.NodeClientException ex) {
            throw new VideoBusinessException(400, "远程节点部署失败: " + ex.getMessage());
        }
    }

    public void stopRemote(StreamForwardTaskRow task) {
        Long nodeId = task.getNodeId();
        long taskId = task.getId();
        if (nodeId != null) {
            iotNodeClient.stopWorkload(nodeId, RemoteScheduleSupport.WORKLOAD_STREAM_FORWARD, String.valueOf(taskId));
        }
        iotNodeClient.releaseWorkload(RemoteScheduleSupport.WORKLOAD_STREAM_FORWARD, String.valueOf(taskId));
        taskRepository.clearRemoteBinding(taskId);
    }

    public boolean isRemoteHealthy(StreamForwardTaskRow task) {
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

    private Map<String, String> buildStreamForwardEnv(
            long taskId, String logDir, String host, List<String> deviceIds, String workloadId
    ) {
        Map<String, String> env = remoteScheduleSupport.copyProcessEnv();
        String videoControlUrl = remoteScheduleSupport.resolveVideoControlUrl();
        env.put("PYTHONUNBUFFERED", "1");
        env.put("TASK_ID", String.valueOf(taskId));
        env.put("VIDEO_CONTROL_URL", videoControlUrl);
        env.put("VIDEO_HEARTBEAT_URL", videoControlUrl + "/stream-forward/heartbeat");
        env.put("LOG_PATH", logDir);
        env.put("POD_IP", host);
        env.put("HOST_IP", host);
        env.put("DEVICE_IDS", deviceIds.stream().collect(Collectors.joining(",")));
        env.put("WORKLOAD_ID", workloadId);
        env.put("VIEW_EXTRACT_INTERVAL", "1");
        return env;
    }

    private static String serializeDeployments(
            long taskId, List<String> deviceIds, long nodeId, String host, Integer pid, String logDir
    ) {
        try {
            var mapper = new com.fasterxml.jackson.databind.ObjectMapper();
            List<Map<String, Object>> dep = List.of(Map.of(
                    "device_ids", deviceIds,
                    "node_id", nodeId,
                    "host", host,
                    "workload_id", String.valueOf(taskId),
                    "pid", pid,
                    "log_dir", logDir
            ));
            return mapper.writeValueAsString(dep);
        } catch (Exception e) {
            return "[]";
        }
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
