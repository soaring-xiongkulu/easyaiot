package com.basiclab.iot.video.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "video")
public class VideoProperties {

    private final Alert alert = new Alert();
    private final Runtime runtime = new Runtime();

    @Data
    public static class Alert {
        /** mini / local: persist alerts directly to DB (no Kafka). */
        private boolean useDirectPersist = true;
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
}
