package com.basiclab.iot.video.process;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
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
    private final ExecutorService logPump = Executors.newCachedThreadPool(r -> {
        Thread t = new Thread(r, "video-runtime-log-pump");
        t.setDaemon(true);
        return t;
    });

    public boolean isAlive(long taskId) {
        ManagedProcess mp = processes.get(taskId);
        return mp != null && mp.process != null && mp.process.isAlive();
    }

    public void start(long taskId, String runtimeBin, String iniPath, Path logDir) throws IOException {
        stop(taskId, false);
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
        }
        log.info("RUNTIME stopped task_id={}", taskId);
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
                        start(taskId, mp.runtimeBin, mp.iniPath, mp.logDir);
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
