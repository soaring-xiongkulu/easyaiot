package com.basiclab.iot.video.process;

import javax.annotation.PreDestroy;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

@Slf4j
@Component
public class AlgorithmRuntimeSupervisor {

    private static final long RESTART_BACKOFF_MS = 5000L;

    private final Map<Long, ManagedProcess> processes = new ConcurrentHashMap<>();
    private final Map<Long, Object> taskLocks = new ConcurrentHashMap<>();
    private final ExecutorService logPump = Executors.newCachedThreadPool(r -> {
        Thread t = new Thread(r, "video-runtime-log-pump");
        t.setDaemon(true);
        return t;
    });

    private Object lockFor(long taskId) {
        return taskLocks.computeIfAbsent(taskId, ignored -> new Object());
    }

    public boolean isAlive(long taskId) {
        ManagedProcess mp = processes.get(taskId);
        return mp != null && mp.process != null && mp.process.isAlive();
    }

    public void start(long taskId, String runtimeBin, String iniPath, Path logDir) throws IOException {
        synchronized (lockFor(taskId)) {
            startUnlocked(taskId, runtimeBin, iniPath, logDir);
        }
    }

    private void startUnlocked(long taskId, String runtimeBin, String iniPath, Path logDir) throws IOException {
        stopUnlocked(taskId, false);
        Files.createDirectories(logDir);
        Path stdoutLog = logDir.resolve("runtime.stdout.log");
        ProcessBuilder pb;
        if (runtimeBin.toLowerCase().endsWith(".bat") || runtimeBin.toLowerCase().endsWith(".cmd")) {
            pb = new ProcessBuilder("cmd.exe", "/c", runtimeBin, iniPath);
        } else {
            pb = new ProcessBuilder(runtimeBin, iniPath);
        }
        pb.redirectErrorStream(true);
        pb.redirectOutput(stdoutLog.toFile());
        Process process = pb.start();
        ManagedProcess mp = new ManagedProcess(process, iniPath, runtimeBin, logDir);
        processes.put(taskId, mp);
        logPump.submit(() -> watchProcess(taskId, mp));
        log.info("RUNTIME started task_id={} pid={} ini={}", taskId, process.pid(), iniPath);
    }

    public void stop(long taskId, boolean remove) {
        synchronized (lockFor(taskId)) {
            stopUnlocked(taskId, remove);
        }
    }

    private void stopUnlocked(long taskId, boolean remove) {
        ManagedProcess mp = processes.get(taskId);
        if (mp == null) {
            return;
        }
        mp.stopping = true;
        Process p = mp.process;
        if (p != null && p.isAlive()) {
            p.destroy();
            try {
                if (!p.waitFor(5, TimeUnit.SECONDS)) {
                    p.destroyForcibly();
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                p.destroyForcibly();
            }
        }
        if (remove) {
            processes.remove(taskId);
            taskLocks.remove(taskId);
        }
        log.info("RUNTIME stopped task_id={}", taskId);
    }

    @PreDestroy
    public void shutdownAll() {
        log.info("RUNTIME supervisor shutting down — stopping all managed children");
        for (Long taskId : new ArrayList<>(processes.keySet())) {
            synchronized (lockFor(taskId)) {
                stopUnlocked(taskId, true);
            }
        }
        logPump.shutdownNow();
        try {
            if (!logPump.awaitTermination(10, TimeUnit.SECONDS)) {
                log.warn("RUNTIME log pump did not terminate within 10s");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        taskLocks.clear();
    }

    public Integer currentPid(long taskId) {
        ManagedProcess mp = processes.get(taskId);
        if (mp != null && mp.process != null && mp.process.isAlive()) {
            return (int) mp.process.pid();
        }
        return null;
    }

    private void watchProcess(long taskId, ManagedProcess mp) {
        Process p = mp.process;
        if (p == null) {
            return;
        }
        try {
            int code = p.waitFor();
            log.info("RUNTIME exited task_id={} code={}", taskId, code);
            if (!mp.stopping) {
                Thread.sleep(RESTART_BACKOFF_MS);
                if (!mp.stopping && processes.get(taskId) == mp) {
                    log.warn("RUNTIME unexpected exit; restarting task_id={}", taskId);
                    try {
                        synchronized (lockFor(taskId)) {
                            if (!mp.stopping && processes.get(taskId) == mp) {
                                startUnlocked(taskId, mp.runtimeBin, mp.iniPath, mp.logDir);
                            }
                        }
                    } catch (IOException e) {
                        log.error("RUNTIME restart failed task_id={}: {}", taskId, e.getMessage());
                    }
                }
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private static final class ManagedProcess {
        private final Process process;
        private final String iniPath;
        private final String runtimeBin;
        private final Path logDir;
        private volatile boolean stopping;

        private ManagedProcess(Process process, String iniPath, String runtimeBin, Path logDir) {
            this.process = process;
            this.iniPath = iniPath;
            this.runtimeBin = runtimeBin;
            this.logDir = logDir;
        }
    }
}
