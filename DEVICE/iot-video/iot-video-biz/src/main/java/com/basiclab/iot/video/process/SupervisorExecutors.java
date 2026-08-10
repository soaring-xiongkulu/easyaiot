package com.basiclab.iot.video.process;

import com.basiclab.iot.video.util.FfmpegCompat;
import lombok.extern.slf4j.Slf4j;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

@Slf4j
final class SupervisorExecutors {

    private static final int DEFAULT_MAX_WORKERS = 64;
    private static final long SHUTDOWN_AWAIT_SECONDS = 10L;

    private SupervisorExecutors() {}

    static ExecutorService newDaemonPool(String threadNamePrefix) {
        int maxWorkers = Math.max(1, FfmpegCompat.envInt("VIDEO_SUPERVISOR_MAX_WORKERS", DEFAULT_MAX_WORKERS));
        AtomicInteger seq = new AtomicInteger();
        ThreadFactory factory = r -> {
            Thread t = new Thread(r, threadNamePrefix + seq.incrementAndGet());
            t.setDaemon(true);
            return t;
        };
        return Executors.newFixedThreadPool(maxWorkers, factory);
    }

    static void shutdownAndAwait(ExecutorService executor, String label) {
        executor.shutdownNow();
        try {
            if (!executor.awaitTermination(SHUTDOWN_AWAIT_SECONDS, TimeUnit.SECONDS)) {
                log.warn("{} worker pool did not terminate within {}s", label, SHUTDOWN_AWAIT_SECONDS);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
