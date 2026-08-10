package com.basiclab.iot.video.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "video")
public class VideoProperties {

    private final Alert alert = new Alert();
    private final Kafka kafka = new Kafka();
    private final Matching matching = new Matching();
    private final PostProcess postProcess = new PostProcess();
    private final Runtime runtime = new Runtime();
    private final HealthMonitor healthMonitor = new HealthMonitor();
    private final Media media = new Media();
    private final SpaceCleanup spaceCleanup = new SpaceCleanup();
    private final PlaybackDiskGuard playbackDiskGuard = new PlaybackDiskGuard();
    private final MediaJanitor mediaJanitor = new MediaJanitor();
    private final Minio minio = new Minio();
    private final SnapTaskScheduler snapTaskScheduler = new SnapTaskScheduler();
    private final NodeRemote nodeRemote = new NodeRemote();
    private final StreamForwardHealth streamForwardHealth = new StreamForwardHealth();

    /**
     * Mirrors Python {@code VIDEO_SKIP_BACKGROUND_TASKS=1} — disables scheduled health recovery
     * and other background timers (certify / dual-run safe mode).
     */
    private boolean skipBackgroundTasks = false;

    @Data
    public static class Alert {
        /** mini / local: persist alerts directly to DB (no Kafka). */
        private boolean useDirectPersist = true;
        /** Mirrors Python {@code KAFKA_ALERT_NOTIFICATION_TOPIC}. */
        private String alertNotificationTopic = "iot-alert-notification";
        /** Mirrors Python {@code KAFKA_SNAPSHOT_ALERT_TOPIC}. */
        private String snapshotAlertTopic = "iot-snapshot-alert";
    }

    @Data
    public static class Kafka {
        private String bootstrapServers = "localhost:9092";
        private String clientId = "video-alert-producer";
        private int requestTimeoutMs = 30_000;
        private int retries = 3;
        private long maxBlockMs = 60_000;
        private long sendTimeoutMs = 10_000;
    }

    @Data
    public static class Matching {
        /**
         * mini / local: mock Kafka publish success (certify-safe when broker unavailable).
         * Mirrors Python mini path documented in P2-S3.
         */
        private boolean useDirectProcess = true;
        /** Mirrors Python {@code KAFKA_FACE_MATCHING_TOPIC}. */
        private String faceMatchingTopic = "iot-face-matching";
        /** Mirrors Python {@code KAFKA_PLATE_MATCHING_TOPIC}. */
        private String plateMatchingTopic = "iot-plate-matching";
    }

    @Data
    public static class PostProcess {
        /**
         * mini / local: stub sink HTTP enqueue (certify-safe when iot-sink unavailable).
         * When false, POST to iot-sink /post-process/enqueue (mirrors Python publish_post_process_request).
         */
        private boolean useStubEnqueue = true;
        private String workspaceRoot = System.getProperty("user.home") + "/.video-java/post-process-workspaces";
        private String sinkHost = "127.0.0.1";
        private String sinkPort = "48092";
        /** When set, overrides host/port (e.g. http://127.0.0.1:48092). Env IOT_SINK_API_URL wins. */
        private String sinkApiUrl = "";
        /** Route via gateway admin-api instead of direct sink-server (env IOT_SINK_USE_GATEWAY). */
        private boolean sinkUseGateway = false;
        /** Gateway base URL when sinkUseGateway=true (env JAVA_BACKEND_URL / GATEWAY_URL). */
        private String gatewayUrl = "http://localhost:48080";
        /** HTTP timeout for sink enqueue (Python requests timeout=5). */
        private int enqueueTimeoutMs = 5_000;
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
    public static class Media {
        /** Mirrors Python {@code MEDIA_UPLOAD_MODE}: sync | kafka | hybrid. */
        private String uploadMode = "sync";
        /** Mirrors {@code MEDIA_SNAP_UPLOAD_MODE}; empty inherits uploadMode. */
        private String snapUploadMode = "";
        private String dvrCompletedTopic = "media.dvr.completed";
        private String dvrDlqTopic = "media.dvr.dlq";
        private String snapCompletedTopic = "media.snap.completed";
        private String snapDlqTopic = "media.snap.dlq";
        /** SRS HTTP API host for on_publish conflict resolution. */
        private String srsHost = "localhost";
    }

    @Data
    public static class HealthMonitor {
        /** Mirrors {@code ALGORITHM_HEALTH_MONITOR_ENABLED} (default on). */
        private boolean enabled = true;
        /** Mirrors {@code ALGORITHM_HEALTH_INTERVAL_SECONDS} (default 60s). */
        private long intervalMs = 60_000L;
        /** Mirrors {@code ALGORITHM_HEARTBEAT_FAILOVER_SECONDS} (default 90s). */
        private int heartbeatFailoverSeconds = 90;
    }

    @Data
    public static class SpaceCleanup {
        /** Mirrors Python {@code auto_cleanup_*_spaces} APScheduler jobs (default 30 min). */
        private boolean enabled = true;
        private long intervalMs = 1_800_000L;
    }

    @Data
    public static class PlaybackDiskGuard {
        /** Mirrors {@code PLAYBACK_CLEANUP_ENABLED} (default on). */
        private boolean enabled = true;
        /** Mirrors {@code PLAYBACK_GUARD_INTERVAL_MINUTES} (default 10 min). */
        private long intervalMs = 600_000L;
        private int maxAgeHours = 1;
        private int deviceMaxFiles = 30;
        private int globalMaxFiles = 2000;
        private double keepRatio = 0.2;
        private double diskWarnPercent = 80.0;
        private double diskCriticalPercent = 90.0;
        private double diskTargetPercent = 75.0;
        private int emergencyBatchSize = 50;
        private int emergencyMaxRounds = 200;
        /** Optional override for SRS playbacks root ({@code MEDIA_RECORD_DIR} / {@code SRS_RECORD_DIR}). */
        private String recordDir = "";
        private String hostDataRoot = "";
    }

    @Data
    public static class Minio {
        /**
         * mini / local default off — mirrors Python {@code minio_storage_enabled()}.
         * Override with env {@code MINIO_ENABLED=true} for prod MinIO paths.
         */
        private boolean enabled = false;
        /** MinIO endpoint (http://host:port or host:port). Env MINIO_ENDPOINT wins. */
        private String endpoint = "http://localhost:9000";
        private String accessKey = "minioadmin";
        private String secretKey = "minioadmin";
        private boolean secure = false;
        private String snapBucket = "snap-space";
        private String recordBucket = "record-space";
        private String snapArchiveBucket = "snap-archive";
        private String recordArchiveBucket = "record-archive";
        /** Minimum DVR segment bytes before upload (env SRS_DVR_MIN_FILE_BYTES). */
        private int dvrMinFileBytes = 8192;
    }

    @Data
    public static class MediaJanitor {
        /** Mirrors {@code MEDIA_JANITOR_ENABLED} (default on). */
        private boolean enabled = true;
        /** Mirrors {@code JANITOR_INTERVAL_SECONDS} (default 60s). */
        private long intervalMs = 60_000L;
        private int orphanMinAgeMinutes = 10;
        private String snapDir = "";
        private String hostDataRoot = "";
    }

    @Data
    public static class SnapTaskScheduler {
        /**
         * Mirrors Python snap APScheduler init on startup ({@code init_all_tasks}).
         * Disabled when {@code video.skip-background-tasks=true}.
         */
        private boolean enabled = true;
    }

    @Data
    public static class StreamForwardHealth {
        /** Mirrors {@code STREAM_FORWARD_HEALTH_MONITOR_ENABLED} (default on when remote deploy on). */
        private boolean enabled = true;
        /** Mirrors {@code STREAM_FORWARD_HEALTH_INTERVAL_SECONDS} (default 60s). */
        private long intervalMs = 60_000L;
    }

    @Data
    public static class NodeRemote {
        /**
         * Mirrors Python {@code NODE_REMOTE_DEPLOY}. When unset, mini profile defaults false;
         * otherwise true. Env {@code NODE_REMOTE_DEPLOY} wins.
         */
        private Boolean remoteDeployEnabled;
        /** Gateway / JAVA_BACKEND_URL for {@code /admin-api/node/*}. */
        private String gatewayUrl = "http://localhost:48080";
        /** Remote VIDEO tree on compute nodes ({@code NODE_REMOTE_VIDEO_ROOT}). */
        private String remoteVideoRoot = "/opt/easyaiot/VIDEO";
        /** Remote RUNTIME binary ({@code REMOTE_RUNTIME_BIN}). */
        private String remoteRuntimeBin = "/opt/easyaiot/RUNTIME/bin/RUNTIME";
        private String remoteRuntimeLdLibraryPath = "/opt/easyaiot/RUNTIME/lib:/opt/easyaiot/RUNTIME/build/lib";
        /** Python interpreter on remote nodes for stream_forward run_deploy.py. */
        private String remotePython = "python3";
        private int requestTimeoutMs = 90_000;
        private int devicesPerShard = 4;
    }
}
