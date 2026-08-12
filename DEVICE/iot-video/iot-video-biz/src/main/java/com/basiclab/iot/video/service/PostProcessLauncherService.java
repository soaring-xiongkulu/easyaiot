package com.basiclab.iot.video.service;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.PreDestroy;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Mirrors retired Python {@code app.services.post_process_launcher_service}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PostProcessLauncherService {

    private static final int DEFAULT_WORKER_HTTP_PORT = 19_680;

    private final IotNodeClient iotNodeClient;
    private final RemoteScheduleSupport remoteScheduleSupport;
    private final VideoProperties videoProperties;

    private final Map<String, Process> localWorkers = new ConcurrentHashMap<>();
    private final Map<String, Long> remoteNodes = new ConcurrentHashMap<>();

    public record LaunchResult(boolean success, String message, boolean remoteAttempted) {}

    public LaunchResult startPostProcessWorkers(AlgorithmTaskRow task) {
        // Part2 W3: Java YAML rules replace Python run_worker as commercial default.
        if (javaRulesPrefer()) {
            return new LaunchResult(true, "后处理走 Java YAML 规则引擎（未拉起 Python worker）", false);
        }
        if (!postProcessWorkersGloballyEnabled()) {
            return new LaunchResult(true, "后处理 Worker 全局未启用（EASYAIOT_ENABLE_POST_PROCESS_WORKER=1 可开启）", false);
        }
        if (!taskNeedsWorkers(task)) {
            return new LaunchResult(true, "后处理/姿态分析/姿态意图未启用", false);
        }

        int replicas = taskReplicas(task);
        List<Long> assignedNodes = new ArrayList<>();
        try {
            for (int replica = 0; replica < replicas; replica++) {
                List<Long> exclude = spreadReplicasEnabled() ? assignedNodes : null;
                if (useRemoteForTask(task)) {
                    Map<String, Object> deployment = deployWorkerRemote(task, replica, exclude);
                    Object nodeId = deployment.get("node_id");
                    if (nodeId != null) {
                        long nid = Long.parseLong(String.valueOf(nodeId));
                        if (!assignedNodes.contains(nid)) {
                            assignedNodes.add(nid);
                        }
                    }
                } else {
                    deployWorkerLocal(task, replica);
                }
            }
            return new LaunchResult(true, "已启动 " + replicas + " 个后处理/姿态 Worker", useRemoteForTask(task));
        } catch (Exception ex) {
            log.error("启动后处理 Worker 失败 task={}: {}", task.getId(), ex.getMessage(), ex);
            return new LaunchResult(false, ex.getMessage(), useRemoteForTask(task));
        }
    }

    public void stopPostProcessWorkers(long taskId, AlgorithmTaskRow task) {
        int replicas = task != null ? taskReplicas(task) : 1;
        for (int replica = 0; replica < replicas; replica++) {
            if (task != null && useRemoteForTask(task)) {
                stopWorkerRemote(taskId, replica);
            } else {
                stopWorkerLocal(taskId, replica);
            }
        }
    }

    public void ensureRemoteStartSucceeded(LaunchResult result) {
        if (result == null || result.success() || !result.remoteAttempted()) {
            return;
        }
        throw new VideoBusinessException(400, "后处理集群启动失败: " + result.message());
    }

    @PreDestroy
    void shutdownLocalWorkers() {
        localWorkers.values().forEach(PostProcessLauncherService::terminateQuietly);
        localWorkers.clear();
    }

    private boolean postProcessWorkersGloballyEnabled() {
        String env = trimToNull(System.getenv("EASYAIOT_ENABLE_POST_PROCESS_WORKER"));
        if (env != null) {
            return isTruthy(env);
        }
        return false;
    }

    private boolean javaRulesPrefer() {
        String env = trimToNull(System.getenv("VIDEO_POST_PROCESS_JAVA_RULES"));
        if (env != null) {
            return isTruthy(env);
        }
        return videoProperties.getPostProcess().isJavaRulesEnabled();
    }

    private boolean spreadReplicasEnabled() {
        String env = trimToNull(System.getenv("POST_PROCESS_SPREAD_REPLICAS"));
        if (env == null) {
            return true;
        }
        return isTruthy(env);
    }

    private boolean taskNeedsWorkers(AlgorithmTaskRow task) {
        return Boolean.TRUE.equals(task.getPostProcessEnabled())
                || Boolean.TRUE.equals(task.getPoseAnalysisEnabled())
                || Boolean.TRUE.equals(task.getPoseIntentEnabled());
    }

    private int taskReplicas(AlgorithmTaskRow task) {
        Integer raw = task.getPostProcessReplicas();
        if (raw == null || raw < 1) {
            return 1;
        }
        return raw;
    }

    private boolean useRemoteForTask(AlgorithmTaskRow task) {
        if (!iotNodeClient.isRemoteDeployEnabled()) {
            return false;
        }
        String policy = task.getSchedulePolicy() != null ? task.getSchedulePolicy() : "local";
        return "auto".equalsIgnoreCase(policy) || "node".equalsIgnoreCase(policy);
    }

    private String workloadId(long taskId, int replica) {
        return "pp_" + taskId + "_r" + replica;
    }

    private int workerHttpPort(int replica) {
        String base = trimToNull(System.getenv("POST_PROCESS_WORKER_HTTP_PORT"));
        int portBase;
        try {
            portBase = base != null ? Integer.parseInt(base) : DEFAULT_WORKER_HTTP_PORT;
        } catch (NumberFormatException e) {
            portBase = DEFAULT_WORKER_HTTP_PORT;
        }
        return portBase + replica;
    }

    private Map<String, Object> deployWorkerRemote(
            AlgorithmTaskRow task,
            int replica,
            List<Long> excludeNodeIds
    ) {
        long taskId = task.getId();
        String workloadId = workloadId(taskId, replica);
        Long targetNodeId = "node".equalsIgnoreCase(task.getSchedulePolicy()) ? task.getTargetNodeId() : null;

        Map<String, Object> allocation = iotNodeClient.allocateNode(
                RemoteScheduleSupport.WORKLOAD_POST_PROCESS,
                workloadId,
                List.of("post_process"),
                false,
                true,
                targetNodeId,
                excludeNodeIds
        );

        long nodeId = Long.parseLong(String.valueOf(allocation.get("nodeId")));
        String host = String.valueOf(allocation.getOrDefault("host", ""));
        String videoRootRemote = remoteScheduleSupport.remoteVideoRoot();
        String workDir = videoRootRemote + "/services/post_process_worker";
        String logDir = videoRootRemote + "/logs/post_process_task_" + taskId + "/replica_" + replica;
        String pythonExec = remoteScheduleSupport.remotePython();
        List<String> command = List.of(pythonExec, workDir + "/run_worker.py");
        Map<String, String> env = buildWorkerEnv(task, replica, logDir, host);
        env.put("VIDEO_ROOT", videoRootRemote);

        Map<String, Object> result = iotNodeClient.deployWorkload(
                nodeId,
                RemoteScheduleSupport.WORKLOAD_POST_PROCESS,
                workloadId,
                command,
                workDir,
                logDir,
                env,
                null,
                null
        );
        remoteNodes.put(workloadId, nodeId);
        log.info(
                "后处理 Worker 远程部署成功 task={} replica={} node={} host={} port={} pid={}",
                taskId, replica, nodeId, host, workerHttpPort(replica), result.get("pid")
        );
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("node_id", nodeId);
        out.put("host", host);
        out.put("replica", replica);
        out.put("pid", result.get("pid"));
        return out;
    }

    private void deployWorkerLocal(AlgorithmTaskRow task, int replica) throws IOException {
        long taskId = task.getId();
        Path videoRoot = resolveLocalVideoRoot();
        Path workerScript = videoRoot.resolve("services/post_process_worker/run_worker.py");
        if (!Files.isRegularFile(workerScript)) {
            throw new IOException("后处理 Worker 脚本不存在: " + workerScript);
        }
        Path logDir = videoRoot.resolve("logs/post_process_task_" + taskId + "/replica_" + replica);
        Files.createDirectories(logDir);

        String pythonExec = resolveLocalPython();
        ProcessBuilder pb = new ProcessBuilder(pythonExec, workerScript.toString());
        pb.directory(videoRoot.toFile());
        pb.environment().putAll(buildWorkerEnv(task, replica, logDir.toString(), "127.0.0.1"));
        pb.environment().put("VIDEO_ROOT", videoRoot.toString());
        pb.redirectError(ProcessBuilder.Redirect.DISCARD);
        pb.redirectOutput(ProcessBuilder.Redirect.DISCARD);

        String key = workloadId(taskId, replica);
        Process old = localWorkers.remove(key);
        terminateQuietly(old);
        Process proc = pb.start();
        localWorkers.put(key, proc);
        log.info(
                "后处理 Worker 本机启动 task={} replica={} port={} pid={}",
                taskId, replica, workerHttpPort(replica), proc.pid()
        );
    }

    private void stopWorkerLocal(long taskId, int replica) {
        String key = workloadId(taskId, replica);
        Process proc = localWorkers.remove(key);
        terminateQuietly(proc);
    }

    private void stopWorkerRemote(long taskId, int replica) {
        String workloadId = workloadId(taskId, replica);
        Long nodeId = remoteNodes.remove(workloadId);
        if (nodeId != null) {
            try {
                iotNodeClient.stopWorkload(nodeId, RemoteScheduleSupport.WORKLOAD_POST_PROCESS, workloadId);
            } catch (Exception ex) {
                log.warn("远程停止后处理 Worker 失败 {}: {}", workloadId, ex.getMessage());
            }
        }
        try {
            iotNodeClient.releaseWorkload(RemoteScheduleSupport.WORKLOAD_POST_PROCESS, workloadId);
        } catch (Exception ex) {
            log.warn("释放后处理绑定失败 {}: {}", workloadId, ex.getMessage());
        }
    }

    private Map<String, String> buildWorkerEnv(AlgorithmTaskRow task, int replica, String logDir, String host) {
        Map<String, String> env = new LinkedHashMap<>(remoteScheduleSupport.copyProcessEnv());
        String gateway = trimToNull(System.getenv("JAVA_BACKEND_URL"));
        if (gateway == null) {
            gateway = trimToNull(System.getenv("GATEWAY_URL"));
        }
        if (gateway == null) {
            gateway = trimToNull(videoProperties.getPostProcess().getGatewayUrl());
        }
        if (gateway == null) {
            gateway = "http://localhost:48080";
        }
        gateway = gateway.replaceAll("/+$", "");
        env.put("POST_PROCESS_TASK_ID", String.valueOf(task.getId()));
        env.put("POST_PROCESS_REPLICA", String.valueOf(replica));
        env.put("POST_PROCESS_WORKER_HTTP_HOST", "0.0.0.0");
        env.put("POST_PROCESS_WORKER_HTTP_PORT", String.valueOf(workerHttpPort(replica)));
        env.put("POST_PROCESS_WORKSPACE_ROOT", videoProperties.getPostProcess().getWorkspaceRoot());
        env.put("JAVA_BACKEND_URL", gateway);
        env.put("LOG_PATH", logDir);
        env.put("SERVICE_HOST", host);
        env.put("PYTHONUNBUFFERED", "1");
        String databaseUrl = trimToNull(System.getenv("DATABASE_URL"));
        if (databaseUrl != null) {
            env.put("DATABASE_URL", databaseUrl);
        }
        return env;
    }

    private static Path resolveLocalVideoRoot() throws IOException {
        String explicit = trimToNull(System.getenv("VIDEO_ROOT"));
        if (explicit != null) {
            return Path.of(explicit);
        }
        Path cwd = Path.of(System.getProperty("user.dir"));
        for (Path base : new Path[]{cwd, cwd.getParent()}) {
            if (base == null) {
                continue;
            }
            Path retiredWorker = base.resolve("VIDEO/_retired_python_video/services/post_process_worker/run_worker.py");
            if (Files.isRegularFile(retiredWorker)) {
                return base.resolve("VIDEO/_retired_python_video");
            }
            if (Files.isDirectory(base.resolve("VIDEO"))) {
                return base.resolve("VIDEO");
            }
        }
        throw new IOException(
                "无法定位后处理 Python worker（商业默认请开 java-rules-enabled；"
                        + "或设置 VIDEO_ROOT / 保留 _retired_python_video）"
        );
    }

    private static String resolveLocalPython() {
        for (String key : List.of("VIDEO_PYTHON", "PYTHON", "PYTHON_EXECUTABLE")) {
            String value = trimToNull(System.getenv(key));
            if (value != null) {
                return value;
            }
        }
        return "python3";
    }

    private static void terminateQuietly(Process proc) {
        if (proc == null || !proc.isAlive()) {
            return;
        }
        proc.destroy();
        try {
            if (!proc.waitFor(5, java.util.concurrent.TimeUnit.SECONDS)) {
                proc.destroyForcibly();
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            proc.destroyForcibly();
        }
    }

    private static boolean isTruthy(String value) {
        String normalized = value.trim().toLowerCase(Locale.ROOT);
        return normalized.equals("1") || normalized.equals("true") || normalized.equals("yes") || normalized.equals("on");
    }

    private static String trimToNull(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }
}
