package com.basiclab.iot.video.support;

import com.basiclab.iot.video.config.VideoProperties;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * DVR path utilities aligned with Python {@code media_dvr_utils}.
 */
public final class MediaDvrPathSupport {

    private static final ZoneId SHANGHAI = ZoneId.of("Asia/Shanghai");

    private MediaDvrPathSupport() {
    }

    public static int srsDvrMinFileBytes(VideoProperties properties) {
        String env = System.getenv("SRS_DVR_MIN_FILE_BYTES");
        if (env != null && !env.isBlank()) {
            try {
                return Math.max(512, Integer.parseInt(env.trim()));
            } catch (NumberFormatException ignored) {
            }
        }
        return properties != null ? Math.max(512, properties.getMinio().getDvrMinFileBytes()) : 8192;
    }

    public static Path resolvePlaybackAbsolutePath(String filePath, String cwd) {
        if (filePath == null || filePath.isBlank()) {
            return Path.of("");
        }
        String normalized = filePath.replace('\\', '/').trim();
        Path candidate;
        if (normalized.startsWith("/") || (normalized.length() > 2 && Character.isLetter(normalized.charAt(0))
                && normalized.charAt(1) == ':')) {
            candidate = Path.of(normalized).normalize();
        } else if (cwd != null && !cwd.isBlank()) {
            candidate = Path.of(cwd, normalized).normalize();
        } else {
            candidate = Path.of(normalized).normalize();
        }
        if (Files.isRegularFile(candidate)) {
            return candidate;
        }

        String mediaRoot = firstNonBlank(
                System.getenv("MEDIA_HOST_DATA_ROOT"),
                System.getenv("SRS_HOST_DATA_ROOT")
        );
        if (!mediaRoot.isEmpty()) {
            for (String prefix : List.of("/data", "/mnt/easyaiot-media")) {
                if (normalized.equals(prefix) || normalized.startsWith(prefix + "/")) {
                    String rel = normalized.substring(prefix.length());
                    if (rel.startsWith("/")) {
                        rel = rel.substring(1);
                    }
                    Path mapped = Path.of(mediaRoot, rel).normalize();
                    if (Files.isRegularFile(mapped)) {
                        return mapped;
                    }
                }
            }
        }
        return candidate;
    }

    public static long waitDvrFileStable(Path absolutePath, int maxRetries, double intervalSeconds) {
        long last = -1;
        int stable = 0;
        for (int i = 0; i < maxRetries; i++) {
            if (!Files.isRegularFile(absolutePath)) {
                stable = 0;
            } else {
                try {
                    long size = Files.size(absolutePath);
                    if (size == last && size > 0) {
                        stable++;
                        if (stable >= 2) {
                            return size;
                        }
                    } else {
                        stable = size > 0 ? 1 : 0;
                    }
                    last = size;
                } catch (Exception e) {
                    stable = 0;
                }
            }
            try {
                Thread.sleep((long) (intervalSeconds * 1000));
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
        return last > 0 ? last : 0;
    }

    public static Map<String, Object> parseSrsDvrPathDate(Path absolutePath) {
        String path = absolutePath.toString().replace('\\', '/');
        List<String> parts = MediaPathSupport.pathParts(path);
        ZonedDateTime segmentStart = parseSegmentStartFromFilename(absolutePath.getFileName().toString());
        int playbacksIdx = parts.indexOf("playbacks");
        if (playbacksIdx < 0 || parts.size() < playbacksIdx + 7) {
            if (segmentStart != null) {
                String dateDir = segmentStart.format(java.time.format.DateTimeFormatter.ofPattern("yyyy/MM/dd"));
                return Map.of("date_dir", dateDir, "record_time", segmentStart);
            }
            return Map.of();
        }
        String y = parts.get(playbacksIdx + 3);
        String mo = parts.get(playbacksIdx + 4);
        String d = parts.get(playbacksIdx + 5);
        if (y.length() != 4 || !y.chars().allMatch(Character::isDigit)) {
            return Map.of();
        }
        String dateDir = y + "/" + mo + "/" + d;
        if (segmentStart != null) {
            return Map.of("date_dir", dateDir, "record_time", segmentStart);
        }
        try {
            ZonedDateTime recordTime = LocalDateTime.of(
                    Integer.parseInt(y), Integer.parseInt(mo), Integer.parseInt(d), 0, 0
            ).atZone(SHANGHAI);
            return Map.of("date_dir", dateDir, "record_time", recordTime);
        } catch (Exception e) {
            return Map.of("date_dir", dateDir, "record_time", ZonedDateTime.now(SHANGHAI));
        }
    }

    public static String videoContentType(String filename) {
        String lower = filename.toLowerCase(Locale.ROOT);
        if (lower.endsWith(".flv")) {
            return "video/x-flv";
        }
        if (lower.endsWith(".avi")) {
            return "video/x-msvideo";
        }
        if (lower.endsWith(".mov")) {
            return "video/quicktime";
        }
        if (lower.endsWith(".mkv")) {
            return "video/x-matroska";
        }
        if (lower.endsWith(".ts")) {
            return "video/mp2t";
        }
        return "video/mp4";
    }

    public static String imageContentType(String filename) {
        String lower = filename.toLowerCase(Locale.ROOT);
        if (lower.endsWith(".png")) {
            return "image/png";
        }
        if (lower.endsWith(".gif")) {
            return "image/gif";
        }
        return "image/jpeg";
    }

    public static boolean isVideoFile(String filename) {
        String lower = filename.toLowerCase(Locale.ROOT);
        return lower.endsWith(".mp4") || lower.endsWith(".avi") || lower.endsWith(".mov")
                || lower.endsWith(".mkv") || lower.endsWith(".flv") || lower.endsWith(".wmv")
                || lower.endsWith(".m4v") || lower.endsWith(".ts");
    }

    private static ZonedDateTime parseSegmentStartFromFilename(String filename) {
        int dot = filename.lastIndexOf('.');
        String stem = dot > 0 ? filename.substring(0, dot) : filename;
        String ext = dot > 0 ? filename.substring(dot).toLowerCase(Locale.ROOT) : "";
        if (!ext.equals(".flv") || !stem.chars().allMatch(Character::isDigit)) {
            return null;
        }
        try {
            long ts = Long.parseLong(stem);
            if (ts > 1_000_000_000_000L) {
                return Instant.ofEpochMilli(ts).atZone(SHANGHAI);
            }
            return Instant.ofEpochSecond(ts).atZone(SHANGHAI);
        } catch (NumberFormatException e) {
            return null;
        }
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
