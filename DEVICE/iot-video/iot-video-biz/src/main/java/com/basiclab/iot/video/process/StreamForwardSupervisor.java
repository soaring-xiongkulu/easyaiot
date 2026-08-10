package com.basiclab.iot.video.process;

import com.basiclab.iot.video.util.PathSegmentSanitizer;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.annotation.PreDestroy;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.function.Supplier;

@Slf4j
@Component
public class StreamForwardSupervisor {

    private static final long RESTART_BACKOFF_MS = 10_000L;

    private final Map<Long, ManagedTask> tasks = new ConcurrentHashMap<>();
    private final Map<Long, Object> taskLocks = new ConcurrentHashMap<>();
    private final ExecutorService workers = SupervisorExecutors.newDaemonPool("stream-forward-worker-");

    private Object lockFor(long taskId) {
        return taskLocks.computeIfAbsent(taskId, ignored -> new Object());
    }

    public boolean isAlive(long taskId) {
        ManagedTask managed = tasks.get(taskId);
        if (managed == null || managed.stopping) {
            return false;
        }
        synchronized (managed) {
            for (DeviceWorker worker : managed.workers) {
                if (worker.process != null && worker.process.isAlive()) {
                    return true;
                }
            }
        }
        // Match Python StreamForwardDaemon: supervisor thread still active counts as running
        // even while ffmpeg restarts between backoff intervals.
        return true;
    }

    public Integer currentPid(long taskId) {
        ManagedTask managed = tasks.get(taskId);
        if (managed == null) {
            return null;
        }
        synchronized (managed) {
            for (DeviceWorker worker : managed.workers) {
                if (worker.process != null && worker.process.isAlive()) {
                    return (int) worker.process.pid();
                }
            }
        }
        return null;
    }

    public void start(
            long taskId,
            Map<String, Supplier<List<String>>> deviceCommands,
            Path logDir,
            Supplier<Boolean> keepRunning
    ) throws IOException {
        synchronized (lockFor(taskId)) {
            stopUnlocked(taskId, false);
            Files.createDirectories(logDir);
            ManagedTask managed = new ManagedTask(keepRunning);
            tasks.put(taskId, managed);
            for (Map.Entry<String, Supplier<List<String>>> entry : deviceCommands.entrySet()) {
                String deviceId = entry.getKey();
                Path deviceLogDir = logDir.resolve(PathSegmentSanitizer.sanitizeDeviceId(deviceId));
                Files.createDirectories(deviceLogDir);
                DeviceWorker worker = new DeviceWorker(deviceId, entry.getValue(), deviceLogDir);
                managed.workers.add(worker);
                workers.submit(() -> runDeviceDaemon(taskId, managed, worker));
            }
        }
    }

    public void stop(long taskId) {
        synchronized (lockFor(taskId)) {
            stopUnlocked(taskId, true);
        }
    }

    private void stopUnlocked(long taskId, boolean remove) {
        ManagedTask managed = tasks.get(taskId);
        if (managed == null) {
            return;
        }
        managed.stopping = true;
        synchronized (managed) {
            for (DeviceWorker worker : managed.workers) {
                destroyProcess(worker.process);
            }
        }
        if (remove) {
            tasks.remove(taskId);
            taskLocks.remove(taskId);
        }
        log.info("STREAM_FORWARD stopped task_id={}", taskId);
    }

    @PreDestroy
    public void shutdownAll() {
        log.info("STREAM_FORWARD supervisor shutting down — stopping all managed children");
        for (Long taskId : new ArrayList<>(tasks.keySet())) {
            synchronized (lockFor(taskId)) {
                stopUnlocked(taskId, true);
            }
        }
        SupervisorExecutors.shutdownAndAwait(workers, "STREAM_FORWARD");
        taskLocks.clear();
    }

    private void runDeviceDaemon(long taskId, ManagedTask managed, DeviceWorker worker) {
        while (!managed.stopping) {
            if (!Boolean.TRUE.equals(managed.keepRunning.get())) {
                log.info("STREAM_FORWARD task disabled task_id={} device_id={}", taskId, worker.deviceId);
                break;
            }
            try {
                List<String> command = worker.commandSupplier.get();
                Path stdoutLog = worker.logDir.resolve("ffmpeg.stdout.log");
                ProcessBuilder builder = buildProcess(command);
                builder.redirectErrorStream(true);
                builder.redirectOutput(stdoutLog.toFile());
                Process process = builder.start();
                worker.process = process;
                log.info(
                        "STREAM_FORWARD started task_id={} device_id={} pid={}",
                        taskId,
                        worker.deviceId,
                        process.pid()
                );
                int code = process.waitFor();
                log.info(
                        "STREAM_FORWARD exited task_id={} device_id={} code={}",
                        taskId,
                        worker.deviceId,
                        code
                );
            } catch (IOException | InterruptedException e) {
                if (e instanceof InterruptedException) {
                    Thread.currentThread().interrupt();
                }
                log.warn(
                        "STREAM_FORWARD error task_id={} device_id={}: {}",
                        taskId,
                        worker.deviceId,
                        e.getMessage()
                );
            }
            worker.process = null;
            if (managed.stopping || !Boolean.TRUE.equals(managed.keepRunning.get())) {
                break;
            }
            try {
                Thread.sleep(RESTART_BACKOFF_MS);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }

    private static void destroyProcess(Process process) {
        if (process == null || !process.isAlive()) {
            return;
        }
        process.destroy();
        try {
            if (!process.waitFor(5, TimeUnit.SECONDS)) {
                process.destroyForcibly();
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            process.destroyForcibly();
        }
    }

    private static ProcessBuilder buildProcess(List<String> command) {
        if (command.isEmpty()) {
            return new ProcessBuilder(command);
        }
        String binary = command.get(0).toLowerCase(Locale.ROOT);
        if (binary.endsWith(".bat") || binary.endsWith(".cmd")) {
            List<String> wrapped = new ArrayList<>();
            wrapped.add("cmd.exe");
            wrapped.add("/c");
            wrapped.addAll(command);
            return new ProcessBuilder(wrapped);
        }
        return new ProcessBuilder(command);
    }

    private static final class ManagedTask {
        private final Supplier<Boolean> keepRunning;
        private final List<DeviceWorker> workers = new ArrayList<>();
        private volatile boolean stopping;

        private ManagedTask(Supplier<Boolean> keepRunning) {
            this.keepRunning = keepRunning;
        }
    }

    private static final class DeviceWorker {
        private final String deviceId;
        private final Supplier<List<String>> commandSupplier;
        private final Path logDir;
        private volatile Process process;

        private DeviceWorker(String deviceId, Supplier<List<String>> commandSupplier, Path logDir) {
            this.deviceId = deviceId;
            this.commandSupplier = commandSupplier;
            this.logDir = logDir;
        }
    }
}
