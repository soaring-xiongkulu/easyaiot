package com.basiclab.iot.video.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "video")
public class VideoProperties {

    private final Alert alert = new Alert();
    private final Matching matching = new Matching();
    private final PostProcess postProcess = new PostProcess();
    private final Runtime runtime = new Runtime();
    private final HealthMonitor healthMonitor = new HealthMonitor();

    /**
     * Mirrors Python {@code VIDEO_SKIP_BACKGROUND_TASKS=1} — disables scheduled health recovery
     * and other background timers (certify / dual-run safe mode).
     */
    private boolean skipBackgroundTasks = false;

    @Data
    public static class Alert {
        /** mini / local: persist alerts directly to DB (no Kafka). */
        private boolean useDirectPersist = true;
    }

    @Data
    public static class Matching {
        /**
         * mini / local: mock Kafka publish success (certify-safe when broker unavailable).
         * Mirrors Python mini path documented in P2-S3.
         */
        private boolean useDirectProcess = true;
    }

    @Data
    public static class PostProcess {
        /**
         * mini / local: stub sink HTTP enqueue (certify-safe when iot-sink unavailable).
         * Mirrors Python post_process_sink_client mini path in P2-S5.
         */
        private boolean useStubEnqueue = true;
        private String workspaceRoot = System.getProperty("user.home") + "/.video-java/post-process-workspaces";
        private String sinkHost = "127.0.0.1";
        private String sinkPort = "48092";
        /** When set, overrides host/port (e.g. http://127.0.0.1:48092). */
        private String sinkApiUrl = "";
    }

    @Data
    public static class Runtime {
        private String configDir = System.getProperty("user.home") + "/.video-java/runtime-config";
        private String logsDir = System.getProperty("user.home") + "/.video-java/logs";
        private String hookBaseUrl = "http://127.0.0.1:48096";
        private String heartbeatBaseUrl = "http://127.0.0.1:48096";
        /** Repo root for RUNTIME binaries/models; env ACME_ROOT or RUNTIME_ROOT overrides. */
        private String repoRoot;
    }

    /** Optional explicit ffmpeg binary; env FFMPEG_PATH still wins when set. */
    private String ffmpegPath;

    @Data
    public static class HealthMonitor {
        /** Mirrors {@code ALGORITHM_HEALTH_MONITOR_ENABLED} (default on). */
        private boolean enabled = true;
        /** Mirrors {@code ALGORITHM_HEALTH_INTERVAL_SECONDS} (default 60s). */
        private long intervalMs = 60_000L;
        /** Mirrors {@code ALGORITHM_HEARTBEAT_FAILOVER_SECONDS} (default 90s). */
        private int heartbeatFailoverSeconds = 90;
    }
}
