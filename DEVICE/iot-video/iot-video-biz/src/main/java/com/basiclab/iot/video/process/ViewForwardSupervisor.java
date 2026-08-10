package com.basiclab.iot.video.process;

import com.basiclab.iot.video.dal.DeviceRepository;
import lombok.RequiredArgsConstructor;
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
@RequiredArgsConstructor
public class ViewForwardSupervisor {

    private static final long RESTART_BACKOFF_MS = 10_000L;

    private final DeviceRepository deviceRepository;
    private final Map<String, ManagedForward> processes = new ConcurrentHashMap<>();
    private final Map<String, Object> deviceLocks = new ConcurrentHashMap<>();
    private final ExecutorService workers = SupervisorExecutors.newDaemonPool("view-forward-worker-");

    private Object lockFor(String deviceId) {
        return deviceLocks.computeIfAbsent(deviceId, ignored -> new Object());
    }

    public boolean isAlive(String deviceId) {
        ManagedForward managed = processes.get(deviceId);
        return managed != null && managed.process != null && managed.process.isAlive();
    }

    public Integer currentPid(String deviceId) {
        ManagedForward managed = processes.get(deviceId);
        if (managed != null && managed.process != null && managed.process.isAlive()) {
            return (int) managed.process.pid();
        }
        return null;
    }

    public void start(String deviceId, Supplier<List<String>> commandSupplier, Path logDir) throws IOException {
        synchronized (lockFor(deviceId)) {
            stopUnlocked(deviceId, false);
            Files.createDirectories(logDir);
            ManagedForward managed = new ManagedForward(commandSupplier, logDir);
            processes.put(deviceId, managed);
            workers.submit(() -> runDaemon(deviceId, managed));
        }
    }

    public void stop(String deviceId) {
        synchronized (lockFor(deviceId)) {
            stopUnlocked(deviceId, true);
        }
    }

    private void stopUnlocked(String deviceId, boolean remove) {
        ManagedForward managed = processes.get(deviceId);
        if (managed == null) {
            return;
        }
        managed.stopping = true;
        Process process = managed.process;
        if (process != null && process.isAlive()) {
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
        if (remove) {
            processes.remove(deviceId);
            deviceLocks.remove(deviceId);
        }
        log.info("VIEW_FORWARD stopped device_id={}", deviceId);
    }

    @PreDestroy
    public void shutdownAll() {
        log.info("VIEW_FORWARD supervisor shutting down — stopping all managed children");
        for (String deviceId : new ArrayList<>(processes.keySet())) {
            synchronized (lockFor(deviceId)) {
                stopUnlocked(deviceId, true);
            }
        }
        SupervisorExecutors.shutdownAndAwait(workers, "VIEW_FORWARD");
        deviceLocks.clear();
    }

    private void runDaemon(String deviceId, ManagedForward managed) {
        while (!managed.stopping) {
            if (!isForwardEnabled(deviceId)) {
                log.info("VIEW_FORWARD enable_forward=false device_id={}", deviceId);
                break;
            }
            try {
                List<String> command = managed.commandSupplier.get();
                Path stdoutLog = managed.logDir.resolve("ffmpeg.stdout.log");
                ProcessBuilder builder = buildProcess(command);
                builder.redirectErrorStream(true);
                builder.redirectOutput(stdoutLog.toFile());
                Process process = builder.start();
                managed.process = process;
                log.info("VIEW_FORWARD started device_id={} pid={}", deviceId, process.pid());
                int code = process.waitFor();
                log.info("VIEW_FORWARD exited device_id={} code={}", deviceId, code);
            } catch (IOException | InterruptedException e) {
                if (e instanceof InterruptedException) {
                    Thread.currentThread().interrupt();
                }
                log.warn("VIEW_FORWARD error device_id={}: {}", deviceId, e.getMessage());
            }
            managed.process = null;
            if (managed.stopping || !isForwardEnabled(deviceId)) {
                break;
            }
            try {
                Thread.sleep(RESTART_BACKOFF_MS);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
        if (!managed.stopping) {
            synchronized (lockFor(deviceId)) {
                processes.remove(deviceId);
                deviceLocks.remove(deviceId);
            }
        }
    }

    private boolean isForwardEnabled(String deviceId) {
        return deviceRepository.findById(deviceId)
                .map(row -> Boolean.TRUE.equals(row.getEnableForward()))
                .orElse(false);
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

    private static final class ManagedForward {
        private final Supplier<List<String>> commandSupplier;
        private final Path logDir;
        private volatile Process process;
        private volatile boolean stopping;

        private ManagedForward(Supplier<List<String>> commandSupplier, Path logDir) {
            this.commandSupplier = commandSupplier;
            this.logDir = logDir;
        }
    }
}
