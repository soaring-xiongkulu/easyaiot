package com.basiclab.iot.video.process;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.annotation.PreDestroy;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * 巡检会话守护进程，对齐 Python {@code PatrolSessionDaemon}。
 */
@Slf4j
@Component
public class PatrolSupervisor {

    private static final long RESTART_BACKOFF_MS = 5_000L;

    private final Map<Long, ManagedSession> sessions = new ConcurrentHashMap<>();
    private final Map<Long, Object> sessionLocks = new ConcurrentHashMap<>();
    private final ExecutorService workers = SupervisorExecutors.newDaemonPool("patrol-worker-");
    private final VideoProperties videoProperties;

    public PatrolSupervisor(VideoProperties videoProperties) {
        this.videoProperties = videoProperties;
    }

    public boolean isAlive(long sessionId) {
        ManagedSession managed = sessions.get(sessionId);
        if (managed == null || managed.stopping) {
            return false;
        }
        Process process = managed.process;
        return process != null && process.isAlive();
    }

    public Integer currentPid(long sessionId) {
        ManagedSession managed = sessions.get(sessionId);
        if (managed == null || managed.process == null || !managed.process.isAlive()) {
            return null;
        }
        return (int) managed.process.pid();
    }

    public void start(long sessionId, Path logDir) throws IOException {
        synchronized (lockFor(sessionId)) {
            stopUnlocked(sessionId, false);
            Files.createDirectories(logDir);
            ManagedSession managed = new ManagedSession();
            sessions.put(sessionId, managed);
            workers.submit(() -> daemonLoop(sessionId, logDir, managed));
        }
    }

    public void stop(long sessionId) {
        synchronized (lockFor(sessionId)) {
            stopUnlocked(sessionId, true);
        }
    }

    @PreDestroy
    public void shutdown() {
        for (Long sessionId : List.copyOf(sessions.keySet())) {
            stop(sessionId);
        }
        workers.shutdownNow();
        try {
            workers.awaitTermination(5, TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private Object lockFor(long sessionId) {
        return sessionLocks.computeIfAbsent(sessionId, ignored -> new Object());
    }

    private void stopUnlocked(long sessionId, boolean remove) {
        ManagedSession managed = sessions.get(sessionId);
        if (managed != null) {
            managed.stopping = true;
            destroyProcess(managed.process);
            managed.process = null;
        }
        if (remove) {
            sessions.remove(sessionId);
            sessionLocks.remove(sessionId);
        }
    }

    private void daemonLoop(long sessionId, Path logDir, ManagedSession managed) {
        Path logFile = logDir.resolve(LocalDate.now() + ".log");
        while (!managed.stopping) {
            try {
                List<String> command = buildCommand(sessionId, logDir);
                if (command.isEmpty()) {
                    sleepQuietly(10_000L);
                    continue;
                }
                appendLogHeader(logFile, sessionId);
                ProcessBuilder builder = new ProcessBuilder(command);
                builder.directory(resolveDeployDir().toFile());
                builder.redirectOutput(ProcessBuilder.Redirect.appendTo(logFile.toFile()));
                builder.redirectError(ProcessBuilder.Redirect.appendTo(logFile.toFile()));
                Map<String, String> env = builder.environment();
                propagatePatrolEnv(env, sessionId, logDir);
                env.put("PYTHONUNBUFFERED", "1");
                env.put("PATROL_SESSION_ID", String.valueOf(sessionId));
                env.put("LOG_PATH", logDir.toString());
                String heartbeatBase = videoProperties.getRuntime().getHeartbeatBaseUrl();
                env.put("VIDEO_CONTROL_URL", heartbeatBase);
                env.put("VIDEO_HEARTBEAT_URL", heartbeatBase + "/video/patrol/heartbeat");

                managed.process = builder.start();
                int exit = managed.process.waitFor();
                managed.process = null;
                if (managed.stopping) {
                    break;
                }
                log.warn("patrol process exited sessionId={} code={}, restarting in {}ms", sessionId, exit, RESTART_BACKOFF_MS);
                sleepQuietly(RESTART_BACKOFF_MS);
            } catch (Exception e) {
                if (!managed.stopping) {
                    log.error("patrol daemon error sessionId={}: {}", sessionId, e.getMessage(), e);
                    sleepQuietly(RESTART_BACKOFF_MS);
                }
            }
        }
    }

    private static void appendLogHeader(Path logFile, long sessionId) {
        try {
            Files.writeString(
                    logFile,
                    "\n# 启动 patrol session " + sessionId + " " + Instant.now() + "\n",
                    StandardOpenOption.CREATE,
                    StandardOpenOption.APPEND
            );
        } catch (IOException ignored) {
            // non-fatal
        }
    }

    private void propagatePatrolEnv(Map<String, String> env, long sessionId, Path logDir) {
        String videoEnv = System.getenv("VIDEO_ENV");
        if (videoEnv != null && !videoEnv.isBlank()) {
            env.put("VIDEO_ENV", videoEnv.trim());
        }
        for (String key : List.of(
                "DATABASE_URL", "GATEWAY_URL", "GB28181_SERVICE_URL", "JWT_TOKEN", "JAVA_BACKEND_URL",
                "GB28181_HTTP_READ_TIMEOUT", "GB28181_PLAY_PROTOCOL", "GB28181_HEVC_RTSP_FIRST",
                "GB28181_OPENCV_RTMP_FALLBACK_RTSP", "POD_IP", "HOST_IP", "AI_SERVICE_URL",
                "USE_GPU", "GPU_IDS", "GPU_POLICY", "INFER_GPU_POLICY",
                "KAFKA_BOOTSTRAP_SERVERS", "MINIO_ENDPOINT", "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY",
                "MINIO_SECURE"
        )) {
            String value = System.getenv(key);
            if (value != null && !value.isBlank()) {
                env.put(key, value);
            }
        }
        String servicePort = System.getenv("VIDEO_SERVICE_PORT");
        if (servicePort == null || servicePort.isBlank()) {
            servicePort = System.getenv("FLASK_RUN_PORT");
        }
        if (servicePort != null && !servicePort.isBlank()) {
            env.put("VIDEO_SERVICE_PORT", servicePort.trim());
        }
        String kafka = env.getOrDefault("KAFKA_BOOTSTRAP_SERVERS", System.getenv("KAFKA_BOOTSTRAP_SERVERS"));
        if (kafka != null && !kafka.isBlank()) {
            if (kafka.contains("Kafka") || kafka.contains("kafka-server")) {
                env.put("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092");
            } else {
                env.put("KAFKA_BOOTSTRAP_SERVERS", kafka);
            }
        }
        log.debug("patrol env propagated sessionId={} logDir={}", sessionId, logDir);
    }

    private List<String> buildCommand(long sessionId, Path logDir) {
        Path script = resolveDeployScript();
        if (!Files.isRegularFile(script)) {
            log.error("patrol script missing: {}", script);
            return List.of();
        }
        String python = System.getenv("PYTHON_EXECUTABLE");
        if (python == null || python.isBlank()) {
            python = "python";
        }
        List<String> cmd = new ArrayList<>();
        cmd.add(python);
        cmd.add(script.toString());
        return cmd;
    }

    private Path resolveDeployScript() {
        Path root = repoRoot();
        Path edge = root.resolve("EDGE/runtime/services/patrol_algorithm_service/run_deploy.py");
        if (Files.isRegularFile(edge)) {
            return edge;
        }
        Path legacy = root.resolve("VIDEO/services/patrol_algorithm_service/run_deploy.py");
        if (Files.isRegularFile(legacy)) {
            return legacy;
        }
        return edge;
    }

    private Path resolveDeployDir() {
        return resolveDeployScript().getParent();
    }

    private Path repoRoot() {
        String configured = videoProperties.getRuntime().getRepoRoot();
        if (configured != null && !configured.isBlank()) {
            return Path.of(configured.trim());
        }
        String envRoot = System.getenv("ACME_ROOT");
        if (envRoot == null || envRoot.isBlank()) {
            envRoot = System.getenv("RUNTIME_ROOT");
        }
        if (envRoot != null && !envRoot.isBlank()) {
            return Path.of(envRoot.trim());
        }
        Path cwd = Path.of(System.getProperty("user.dir"));
        if (Files.isDirectory(cwd.resolve("EDGE"))) {
            return cwd;
        }
        Path parent = cwd.getParent();
        if (parent != null && Files.isDirectory(parent.resolve("EDGE"))) {
            return parent;
        }
        throw new VideoBusinessException(500, "无法定位仓库根目录（ACME_ROOT / video.runtime.repo-root）");
    }

    private static void destroyProcess(Process process) {
        if (process == null || !process.isAlive()) {
            return;
        }
        process.destroy();
        try {
            if (!process.waitFor(10, TimeUnit.SECONDS)) {
                process.destroyForcibly();
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            process.destroyForcibly();
        }
    }

    private static void sleepQuietly(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private static final class ManagedSession {
        private volatile boolean stopping;
        private volatile Process process;
    }
}
