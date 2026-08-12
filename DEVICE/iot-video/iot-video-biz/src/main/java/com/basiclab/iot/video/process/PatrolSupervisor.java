package com.basiclab.iot.video.process;

import com.basiclab.iot.video.dal.PatrolSessionRepository;
import com.basiclab.iot.video.domain.PatrolSessionRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.PatrolRuntimeIniService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.annotation.PreDestroy;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * Patrol session supervisor — Part2 W2: launches C++ RUNTIME {@code PatrolScheduler}
 * instead of Python {@code run_deploy.py}. Does not reimplement detection/scheduling in Java.
 */
@Slf4j
@Component
public class PatrolSupervisor {

    private static final long RESTART_BACKOFF_MS = 5_000L;

    private final Map<Long, ManagedSession> sessions = new ConcurrentHashMap<>();
    private final Map<Long, Object> sessionLocks = new ConcurrentHashMap<>();
    private final ExecutorService workers = SupervisorExecutors.newDaemonPool("patrol-worker-");
    private final PatrolSessionRepository sessionRepository;
    private final PatrolRuntimeIniService patrolRuntimeIniService;
    private final AlgorithmRuntimeSupervisor algorithmRuntimeSupervisor;

    public PatrolSupervisor(
            PatrolSessionRepository sessionRepository,
            PatrolRuntimeIniService patrolRuntimeIniService,
            AlgorithmRuntimeSupervisor algorithmRuntimeSupervisor
    ) {
        this.sessionRepository = sessionRepository;
        this.patrolRuntimeIniService = patrolRuntimeIniService;
        this.algorithmRuntimeSupervisor = algorithmRuntimeSupervisor;
    }

    public boolean isAlive(long sessionId) {
        ManagedSession managed = sessions.get(sessionId);
        if (managed == null || managed.stopping) {
            return false;
        }
        return algorithmRuntimeSupervisor.isAlive(runtimeTaskKey(sessionId));
    }

    public int countAlive() {
        int count = 0;
        for (Long sessionId : sessions.keySet()) {
            if (isAlive(sessionId)) {
                count++;
            }
        }
        return count;
    }

    public Integer currentPid(long sessionId) {
        return algorithmRuntimeSupervisor.currentPid(runtimeTaskKey(sessionId));
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
        }
        algorithmRuntimeSupervisor.stop(runtimeTaskKey(sessionId), true);
        if (remove) {
            sessions.remove(sessionId);
            sessionLocks.remove(sessionId);
        }
    }

    private void daemonLoop(long sessionId, Path logDir, ManagedSession managed) {
        Path logFile = logDir.resolve(LocalDate.now() + ".log");
        try {
            PatrolSessionRow session = sessionRepository.findById(sessionId)
                    .orElseThrow(() -> new VideoBusinessException(400, "巡检会话不存在: " + sessionId));
            PatrolRuntimeIniService.PatrolIni ini = patrolRuntimeIniService.generate(session, logDir);
            appendLogHeader(logFile, sessionId, ini.runtimeBin(), ini.iniPath());
            algorithmRuntimeSupervisor.start(runtimeTaskKey(sessionId), ini.runtimeBin(), ini.iniPath(), logDir);
            // Rely on AlgorithmRuntimeSupervisor restart; only wait until stop requested.
            while (!managed.stopping) {
                sleepQuietly(1_000L);
            }
        } catch (Exception e) {
            if (!managed.stopping) {
                log.error("patrol RUNTIME start failed sessionId={}: {}", sessionId, e.getMessage(), e);
                try {
                    Files.writeString(
                            logFile,
                            "\n# ERROR " + Instant.now() + " " + e.getMessage() + "\n",
                            StandardOpenOption.CREATE,
                            StandardOpenOption.APPEND
                    );
                } catch (IOException ignored) {
                    // non-fatal
                }
            }
        }
    }

    /** Negative key space so patrol sessions do not collide with algorithm task ids. */
    static long runtimeTaskKey(long sessionId) {
        return -1_000_000L - sessionId;
    }

    private static void appendLogHeader(Path logFile, long sessionId, String bin, String ini) {
        try {
            Files.writeString(
                    logFile,
                    "\n# 启动 patrol session " + sessionId + " via RUNTIME " + Instant.now()
                            + "\n# bin=" + bin + "\n# ini=" + ini + "\n",
                    StandardOpenOption.CREATE,
                    StandardOpenOption.APPEND
            );
        } catch (IOException ignored) {
            // non-fatal
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
    }
}
