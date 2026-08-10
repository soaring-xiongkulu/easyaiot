package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.StreamForwardTaskRepository;
import com.basiclab.iot.video.domain.StreamForwardTaskRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Remote stream_forward deploy via iot-node (mirrors Python {@code _deploy_task_on_remote_node}).
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class StreamForwardRemoteDeployService {

    private static final ObjectMapper JSON = new ObjectMapper();

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
        long failoverSec = resolveHeartbeatFailoverSeconds();
        return Duration.between(heartbeat, Instant.now()).getSeconds() <= failoverSec;
    }

    /**
     * Mirrors Python {@code migrate_unhealthy_stream_forward_task} — redeploy offline-node shards
     * or all shards on heartbeat timeout (auto policy only).
     */
    public int migrateUnhealthyTask(StreamForwardTaskRow task) {
        if (task == null || !Boolean.TRUE.equals(task.getIsEnabled())) {
            return 0;
        }
        if (!remoteScheduleSupport.shouldUseRemoteDeploy(task)) {
            return 0;
        }

        long taskId = task.getId();
        List<Map<String, Object>> deployments = parseDeployments(task);
        if (deployments.isEmpty()) {
            Long nodeId = task.getNodeId();
            if (nodeId == null) {
                return 0;
            }
            List<String> deviceIds = task.getDeviceIds() != null ? task.getDeviceIds() : List.of();
            Map<String, Object> synthetic = new LinkedHashMap<>();
            synthetic.put("device_ids", deviceIds);
            synthetic.put("node_id", nodeId);
            synthetic.put("workload_id", String.valueOf(taskId));
            synthetic.put("host", task.getServiceServerIp());
            deployments = new ArrayList<>(List.of(synthetic));
        }

        String policy = task.getSchedulePolicy() != null ? task.getSchedulePolicy() : "local";
        long heartbeatTimeout = resolveHeartbeatFailoverSeconds();
        boolean heartbeatStale = task.getServiceLastHeartbeat() == null
                || Duration.between(task.getServiceLastHeartbeat(), Instant.now()).getSeconds() > heartbeatTimeout;

        List<Map<String, Object>> updated = new ArrayList<>(deployments);
        int migrated = 0;
        List<Integer> offlineIndices = new ArrayList<>();

        for (int index = 0; index < deployments.size(); index++) {
            Map<String, Object> dep = deployments.get(index);
            Object nodeObj = dep.get("node_id");
            if (nodeObj != null) {
                long nodeId = Long.parseLong(String.valueOf(nodeObj));
                if (!iotNodeClient.isNodeOnline(nodeId)) {
                    offlineIndices.add(index);
                }
            }
        }

        if (!offlineIndices.isEmpty()) {
            for (int index : offlineIndices) {
                Map<String, Object> dep = deployments.get(index);
                Object nodeObj = dep.get("node_id");
                if ("node".equalsIgnoreCase(policy)) {
                    log.error(
                            "推流转发指定节点离线，无法自动迁移 task_id={} node_id={}",
                            taskId,
                            nodeObj
                    );
                    continue;
                }
                try {
                    List<Long> excludes = new ArrayList<>();
                    if (nodeObj != null) {
                        excludes.add(Long.parseLong(String.valueOf(nodeObj)));
                    }
                    updated.set(index, redeployExistingShard(task, dep, excludes));
                    migrated++;
                } catch (Exception e) {
                    log.error(
                            "推流转发分片迁移失败 task_id={} workload={}: {}",
                            taskId,
                            dep.get("workload_id"),
                            e.getMessage(),
                            e
                    );
                }
            }
        } else if (heartbeatStale && !"node".equalsIgnoreCase(policy)) {
            for (int index = 0; index < deployments.size(); index++) {
                Map<String, Object> dep = deployments.get(index);
                try {
                    updated.set(index, redeployExistingShard(task, dep, List.of()));
                    migrated++;
                } catch (Exception e) {
                    log.error(
                            "推流转发心跳超时重部署失败 task_id={} workload={}: {}",
                            taskId,
                            dep.get("workload_id"),
                            e.getMessage(),
                            e
                    );
                }
            }
        }

        if (migrated > 0) {
            applyDeploymentsToTask(taskId, updated);
            log.info("推流转发任务分片迁移完成 task_id={} migrated={}", taskId, migrated);
        }
        return migrated;
    }

    /**
     * Mirrors Python {@code redeploy_existing_shard} — stop old binding and deploy same workload elsewhere.
     */
    public Map<String, Object> redeployExistingShard(
            StreamForwardTaskRow task,
            Map<String, Object> deployment,
            List<Long> excludeNodeIds
    ) {
        List<String> deviceIds = toStringList(deployment.get("device_ids"));
        String workloadId = stringOrEmpty(deployment.get("workload_id"));
        if (deviceIds.isEmpty() || workloadId.isEmpty()) {
            throw new VideoBusinessException(400, "分片部署信息不完整");
        }

        if (isTruthyLocal(deployment.get("local"))) {
            log.warn(
                    "推流转发本机分片健康迁移未实现，跳过 task_id={} workload_id={}",
                    task.getId(),
                    workloadId
            );
            return deployment;
        }

        long taskId = task.getId();
        Long oldNodeId = toLongOrNull(deployment.get("node_id"));
        if (oldNodeId != null) {
            iotNodeClient.stopWorkload(oldNodeId, RemoteScheduleSupport.WORKLOAD_STREAM_FORWARD, workloadId);
        } else {
            iotNodeClient.releaseWorkload(RemoteScheduleSupport.WORKLOAD_STREAM_FORWARD, workloadId);
        }

        List<Long> excludes = new ArrayList<>(excludeNodeIds != null ? excludeNodeIds : List.of());
        if (oldNodeId != null && !excludes.contains(oldNodeId)) {
            excludes.add(oldNodeId);
        }

        return deployShardWithWorkloadId(task, deviceIds, workloadId, excludes, true);
    }

    private Map<String, Object> deployShardWithWorkloadId(
            StreamForwardTaskRow task,
            List<String> deviceIds,
            String workloadId,
            List<Long> excludeNodeIds,
            boolean freshAllocate
    ) {
        long taskId = task.getId();
        String policy = task.getSchedulePolicy() != null ? task.getSchedulePolicy() : "local";
        Long targetNodeId = task.getTargetNodeId();
        if ("node".equalsIgnoreCase(policy) && targetNodeId == null) {
            throw new VideoBusinessException(400, "已选择指定节点但未配置目标节点");
        }

        Map<String, Object> allocation = iotNodeClient.allocateNode(
                RemoteScheduleSupport.WORKLOAD_STREAM_FORWARD,
                workloadId,
                List.of("stream_forward", "srs_live"),
                task.getPreferGpu() == null || task.getPreferGpu(),
                !freshAllocate,
                "node".equalsIgnoreCase(policy) ? targetNodeId : null,
                excludeNodeIds
        );

        long nodeId = toLong(allocation.get("nodeId"));
        String host = stringOrEmpty(allocation.get("host"));
        String gpuIds = allocation.get("gpuIds") != null ? String.valueOf(allocation.get("gpuIds")) : null;

        String videoRootRemote = remoteScheduleSupport.remoteVideoRoot();
        String workDir = videoRootRemote + "/services/stream_forward_service";
        String logDir = videoRootRemote + "/logs/stream_forward_task_" + taskId + "/" + shardLogSuffix(workloadId);
        String deployScript = workDir + "/run_deploy.py";
        List<String> command = List.of(remoteScheduleSupport.remotePython(), deployScript);

        Map<String, String> env = buildStreamForwardEnv(taskId, logDir, host, deviceIds, workloadId);
        env.put("VIDEO_ROOT", videoRootRemote);

        Map<String, Object> result = iotNodeClient.deployWorkload(
                nodeId,
                RemoteScheduleSupport.WORKLOAD_STREAM_FORWARD,
                workloadId,
                command,
                workDir,
                logDir,
                env,
                gpuIds,
                null
        );

        Integer pid = toInteger(result.get("pid"));
        log.info(
                "推流转发分片远程重部署成功 task_id={} workload_id={} node_id={} host={} pid={}",
                taskId, workloadId, nodeId, host, pid
        );

        Map<String, Object> deployment = new LinkedHashMap<>();
        deployment.put("device_ids", deviceIds);
        deployment.put("node_id", nodeId);
        deployment.put("host", host);
        deployment.put("workload_id", workloadId);
        deployment.put("pid", pid);
        deployment.put("log_dir", logDir);
        return deployment;
    }

    private void applyDeploymentsToTask(long taskId, List<Map<String, Object>> deployments) {
        if (deployments == null || deployments.isEmpty()) {
            taskRepository.clearRemoteBinding(taskId);
            return;
        }

        Set<String> hosts = new LinkedHashSet<>();
        Set<Long> nodeIds = new LinkedHashSet<>();
        for (Map<String, Object> dep : deployments) {
            String host = stringOrEmpty(dep.get("host"));
            if (!host.isEmpty()) {
                hosts.add(host);
            }
            Long nodeId = toLongOrNull(dep.get("node_id"));
            if (nodeId != null) {
                nodeIds.add(nodeId);
            }
        }

        Map<String, Object> first = deployments.get(0);
        Integer pid = toInteger(first.get("pid"));
        String logDir = stringOrEmpty(first.get("log_dir"));
        if (logDir.isEmpty()) {
            logDir = stringOrEmpty(first.get("log_path"));
        }
        Long nodeId = nodeIds.size() == 1 ? nodeIds.iterator().next() : null;
        String serverIp = hosts.isEmpty() ? null : String.join(",", hosts);

        taskRepository.updateRemoteDeployState(
                taskId,
                true,
                logDir.isEmpty() ? null : logDir,
                pid,
                nodeId,
                serverIp,
                serializeDeployments(deployments)
        );
    }

    private List<Map<String, Object>> parseDeployments(StreamForwardTaskRow task) {
        String raw = task.getDeviceDeployments();
        if (raw == null || raw.isBlank()) {
            return new ArrayList<>();
        }
        try {
            List<Map<String, Object>> parsed = JSON.readValue(raw, new TypeReference<>() {});
            return parsed != null ? new ArrayList<>(parsed) : new ArrayList<>();
        } catch (Exception e) {
            log.warn("解析推流转发分片部署 JSON 失败 task_id={}: {}", task.getId(), e.getMessage());
            return new ArrayList<>();
        }
    }

    private static String serializeDeployments(List<Map<String, Object>> deployments) {
        try {
            return JSON.writeValueAsString(deployments);
        } catch (Exception e) {
            return "[]";
        }
    }

    private static String shardLogSuffix(String workloadId) {
        if (workloadId.contains(":s")) {
            return "shard_" + workloadId.substring(workloadId.lastIndexOf(":s") + 2);
        }
        return "shard_0";
    }

    private int resolveHeartbeatFailoverSeconds() {
        String env = trimToNull(System.getenv("STREAM_FORWARD_HEARTBEAT_FAILOVER_SECONDS"));
        if (env != null) {
            try {
                return Math.max(30, Integer.parseInt(env.trim()));
            } catch (NumberFormatException ignored) {
                // fall through
            }
        }
        return Math.max(30, videoProperties.getHealthMonitor().getHeartbeatFailoverSeconds());
    }

    private static List<String> toStringList(Object value) {
        if (value instanceof List<?> list) {
            List<String> out = new ArrayList<>();
            for (Object item : list) {
                if (item != null) {
                    out.add(String.valueOf(item));
                }
            }
            return out;
        }
        return List.of();
    }

    private static boolean isTruthyLocal(Object value) {
        if (value == null) {
            return false;
        }
        if (value instanceof Boolean bool) {
            return bool;
        }
        String normalized = String.valueOf(value).trim().toLowerCase(Locale.ROOT);
        return normalized.equals("1") || normalized.equals("true") || normalized.equals("yes") || normalized.equals("on");
    }

    private static Long toLongOrNull(Object value) {
        if (value == null) {
            return null;
        }
        try {
            return Long.parseLong(String.valueOf(value));
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static String trimToNull(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
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
        return serializeDeployments(List.of(Map.of(
                "device_ids", deviceIds,
                "node_id", nodeId,
                "host", host,
                "workload_id", String.valueOf(taskId),
                "pid", pid,
                "log_dir", logDir
        )));
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
