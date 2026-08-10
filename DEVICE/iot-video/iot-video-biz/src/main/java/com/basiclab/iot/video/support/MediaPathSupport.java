package com.basiclab.iot.video.support;

import com.basiclab.iot.video.config.VideoProperties;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * Local media path resolution aligned with Python {@code playback_disk_guard_service} /
 * {@code media_janitor_service}.
 */
public final class MediaPathSupport {

    private MediaPathSupport() {
    }

    public static String getSrsRecordDir(VideoProperties.PlaybackDiskGuard guard) {
        String explicit = firstNonBlank(
                guard != null ? guard.getRecordDir() : "",
                env("MEDIA_RECORD_DIR"),
                env("SRS_RECORD_DIR")
        );
        if (!explicit.isEmpty()) {
            return normalizePath(explicit);
        }
        String hostRoot = firstNonBlank(
                guard != null ? guard.getHostDataRoot() : "",
                env("MEDIA_HOST_DATA_ROOT")
        );
        if (!hostRoot.isEmpty()) {
            return Path.of(normalizePath(hostRoot), "playbacks").toString();
        }
        return Path.of(System.getProperty("user.home"), "easyaiot", "data", "playbacks").toString();
    }

    public static String getSnapStagingDir(VideoProperties.MediaJanitor janitor) {
        String explicit = firstNonBlank(
                janitor != null ? janitor.getSnapDir() : "",
                env("MEDIA_SNAP_DIR")
        );
        if (!explicit.isEmpty()) {
            return normalizePath(explicit);
        }
        String hostRoot = firstNonBlank(
                janitor != null ? janitor.getHostDataRoot() : "",
                env("MEDIA_HOST_DATA_ROOT"),
                "/mnt/easyaiot-media"
        );
        return Path.of(normalizePath(hostRoot), "snaps").toString();
    }

    public static List<String> pathParts(String filePath) {
        String normalized = filePath.replace('\\', '/');
        List<String> parts = new ArrayList<>();
        for (String part : normalized.split("/")) {
            if (!part.isEmpty()) {
                parts.add(part);
            }
        }
        return parts;
    }

    public static String normalizePath(String path) {
        if (path == null || path.isBlank()) {
            return "";
        }
        String expanded = path.trim();
        if (expanded.startsWith("~")) {
            expanded = System.getProperty("user.home") + expanded.substring(1);
        }
        return Path.of(expanded).normalize().toString();
    }

    private static String env(String name) {
        String value = System.getenv(name);
        return value != null ? value.trim() : "";
    }

    private static String firstNonBlank(String... values) {
        for (String value : values) {
            if (value != null && !value.isBlank()) {
                return value.trim();
            }
        }
        return "";
    }
}
