package com.basiclab.iot.video.service.ops;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.dal.RecordFileRepository;
import com.basiclab.iot.video.dal.SnapImageRepository;
import com.basiclab.iot.video.service.media.DvrDeviceResolver;
import com.basiclab.iot.video.service.media.DvrUploadService;
import com.basiclab.iot.video.service.media.MediaKafkaMessageBuilder;
import com.basiclab.iot.video.service.media.MediaKafkaProducer;
import com.basiclab.iot.video.service.media.SnapUploadService;
import com.basiclab.iot.video.support.MediaPathSupport;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Media janitor aligned with Python {@code media_janitor_service}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class MediaJanitorService {

    private final VideoProperties videoProperties;
    private final DeviceRepository deviceRepository;
    private final RecordFileRepository recordFileRepository;
    private final SnapImageRepository snapImageRepository;
    private final DvrUploadService dvrUploadService;
    private final SnapUploadService snapUploadService;
    private final MediaKafkaProducer mediaKafkaProducer;
    private final MediaKafkaMessageBuilder mediaKafkaMessageBuilder;
    private final PlaybackDiskGuardService playbackDiskGuardService;

    public Map<String, Object> runCycle() {
        if (!videoProperties.getMediaJanitor().isEnabled()) {
            return Map.of("enabled", false);
        }

        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("enabled", true);

        List<OrphanFile> dvrOrphans = scanOrphanDvrFiles();
        stats.put("dvr_orphans", dvrOrphans.size());
        int dvrRequeued = 0;
        for (OrphanFile orphan : dvrOrphans) {
            try {
                if (requeueOrphanDvr(orphan)) {
                    dvrRequeued++;
                }
            } catch (Exception e) {
                log.error("Janitor DVR 重入队失败 file={} error={}", orphan.filePath(), e.getMessage(), e);
            }
        }
        stats.put("dvr_requeued", dvrRequeued);

        List<OrphanFile> snapOrphans = scanOrphanSnapFiles();
        stats.put("snap_orphans", snapOrphans.size());
        int snapRequeued = 0;
        for (OrphanFile orphan : snapOrphans) {
            try {
                if (requeueOrphanSnap(orphan)) {
                    snapRequeued++;
                }
            } catch (Exception e) {
                log.error("Janitor 抓拍重入队失败 file={} error={}", orphan.filePath(), e.getMessage(), e);
            }
        }
        stats.put("snap_requeued", snapRequeued);

        if (videoProperties.getPlaybackDiskGuard().isEnabled()) {
            String recordDir = MediaPathSupport.getSrsRecordDir(videoProperties.getPlaybackDiskGuard());
            double diskPct = PlaybackDiskGuardService.getDiskUsagePercent(recordDir);
            stats.put("disk_percent", Math.round(diskPct * 100.0) / 100.0);
            if (diskPct >= videoProperties.getPlaybackDiskGuard().getDiskCriticalPercent()) {
                Map<String, Object> guardStats = playbackDiskGuardService.runGuard();
                stats.put("emergency", guardStats.get("emergency"));
            }
        }

        log.info(
                "Janitor 周期完成: dvr_orphans={} requeued={} snap_orphans={} requeued={} disk={}%",
                stats.get("dvr_orphans"),
                stats.get("dvr_requeued"),
                stats.get("snap_orphans"),
                stats.get("snap_requeued"),
                stats.getOrDefault("disk_percent", "-")
        );
        return stats;
    }

    private List<OrphanFile> scanOrphanDvrFiles() {
        int minAgeMin = videoProperties.getMediaJanitor().getOrphanMinAgeMinutes();
        double cutoff = Instant.now().getEpochSecond() - minAgeMin * 60.0;
        String recordDir = MediaPathSupport.getSrsRecordDir(videoProperties.getPlaybackDiskGuard());
        List<OrphanFile> orphans = new ArrayList<>();
        for (PlaybackDiskGuardService.FlvEntry entry : PlaybackDiskGuardService.iterFlvFiles(Path.of(recordDir))) {
            if (entry.mtime() >= cutoff || entry.sizeBytes() <= 0) {
                continue;
            }
            String deviceId = parseDeviceFromPlaybackPath(entry.path());
            if (deviceId.isBlank()) {
                continue;
            }
            if (isDvrAlreadyUploaded(deviceId, entry.path())) {
                PlaybackDiskGuardService.removePlaybackFile(entry.path(), "Janitor-已上传");
                continue;
            }
            if (!deviceRepository.existsById(deviceId)) {
                PlaybackDiskGuardService.removePlaybackFile(entry.path(), "Janitor-设备已删除");
                continue;
            }
            orphans.add(new OrphanFile(deviceId, entry.path(), entry.mtime(), entry.sizeBytes()));
        }
        return orphans;
    }

    private List<OrphanFile> scanOrphanSnapFiles() {
        int minAgeMin = videoProperties.getMediaJanitor().getOrphanMinAgeMinutes();
        double cutoff = Instant.now().getEpochSecond() - minAgeMin * 60.0;
        String snapDir = MediaPathSupport.getSnapStagingDir(videoProperties.getMediaJanitor());
        List<OrphanFile> orphans = new ArrayList<>();
        for (JpgEntry entry : iterJpgFiles(Path.of(snapDir))) {
            if (entry.mtime() >= cutoff || entry.sizeBytes() <= 0) {
                continue;
            }
            String deviceId = parseDeviceFromSnapPath(entry.path());
            if (deviceId.isBlank()) {
                continue;
            }
            if (isSnapAlreadyUploaded(deviceId, entry.path())) {
                PlaybackDiskGuardService.removePlaybackFile(entry.path(), "Janitor-抓拍已上传");
                continue;
            }
            if (!deviceRepository.existsById(deviceId)) {
                PlaybackDiskGuardService.removePlaybackFile(entry.path(), "Janitor-设备已删除");
                continue;
            }
            orphans.add(new OrphanFile(deviceId, entry.path(), entry.mtime(), entry.sizeBytes()));
        }
        return orphans;
    }

    private boolean requeueOrphanDvr(OrphanFile orphan) {
        Map<String, Object> hook = new LinkedHashMap<>();
        hook.put("stream", orphan.deviceId());
        hook.put("file", orphan.filePath());
        hook.put("app", "live");
        Map<String, Object> event = mediaKafkaMessageBuilder.buildFromSrsHook(hook, orphan.deviceId());
        event.put("event_id", UUID.randomUUID().toString());
        event.put("janitor_requeue", true);
        event.put("created_at", Instant.now().atOffset(ZoneOffset.UTC).format(DateTimeFormatter.ISO_OFFSET_DATE_TIME));
        if (isKafkaUploadMode()) {
            return mediaKafkaProducer.publishDvrEvent(event);
        }
        return dvrUploadService.processDvrEvent(event);
    }

    private boolean requeueOrphanSnap(OrphanFile orphan) {
        Map<String, Object> event = mediaKafkaMessageBuilder.buildSnapEvent(
                orphan.deviceId(),
                orphan.filePath(),
                "janitor",
                null,
                null
        );
        if (isSnapKafkaMode()) {
            return mediaKafkaProducer.publishSnapEvent(event);
        }
        return snapUploadService.processSnapEvent(event);
    }

    private boolean isDvrAlreadyUploaded(String deviceId, String absolutePath) {
        String objectName = buildDvrObjectName(deviceId, absolutePath);
        return recordFileRepository.existsByDeviceAndObjectName(deviceId, objectName);
    }

    private boolean isSnapAlreadyUploaded(String deviceId, String absolutePath) {
        String filename = Path.of(absolutePath).getFileName().toString();
        String objectName = deviceId + "/" + filename;
        return snapImageRepository.existsByDeviceAndObjectName(deviceId, objectName);
    }

    private static String buildDvrObjectName(String deviceId, String absolutePath) {
        List<String> parts = MediaPathSupport.pathParts(absolutePath);
        String filename = parts.isEmpty() ? "" : parts.get(parts.size() - 1);
        String dateDir = "";
        if (parts.size() >= 2) {
            dateDir = parts.get(parts.size() - 2);
        }
        if (dateDir.isBlank()) {
            try {
                dateDir = DateTimeFormatter.ofPattern("yyyy/MM/dd")
                        .withZone(ZoneOffset.UTC)
                        .format(Files.getLastModifiedTime(Path.of(absolutePath)).toInstant());
            } catch (IOException ignored) {
                dateDir = DateTimeFormatter.ofPattern("yyyy/MM/dd")
                        .withZone(ZoneOffset.UTC)
                        .format(Instant.now());
            }
        }
        return deviceId + "/" + dateDir + "/" + filename;
    }

    private static String parseDeviceFromPlaybackPath(String filePath) {
        List<String> parts = MediaPathSupport.pathParts(filePath);
        int pi = parts.indexOf("playbacks");
        if (pi >= 0 && pi + 2 < parts.size()) {
            String segment = parts.get(pi + 2);
            String inferId = DvrDeviceResolver.parseInferStreamDeviceId(segment);
            return inferId != null ? inferId : segment;
        }
        return "";
    }

    private static String parseDeviceFromSnapPath(String filePath) {
        List<String> parts = MediaPathSupport.pathParts(filePath);
        int pi = parts.indexOf("snaps");
        if (pi >= 0 && pi + 1 < parts.size()) {
            return parts.get(pi + 1);
        }
        if (parts.size() >= 2) {
            return parts.get(parts.size() - 2);
        }
        return "";
    }

    private static List<JpgEntry> iterJpgFiles(Path root) {
        if (!Files.isDirectory(root)) {
            return List.of();
        }
        List<JpgEntry> entries = new ArrayList<>();
        try {
            Files.walk(root)
                    .filter(Files::isRegularFile)
                    .filter(path -> {
                        String lower = path.getFileName().toString().toLowerCase();
                        return lower.endsWith(".jpg") || lower.endsWith(".jpeg");
                    })
                    .forEach(path -> {
                        try {
                            var attrs = Files.readAttributes(path, java.nio.file.attribute.BasicFileAttributes.class);
                            entries.add(new JpgEntry(
                                    path.toString(),
                                    attrs.lastModifiedTime().toMillis() / 1000.0,
                                    attrs.size()
                            ));
                        } catch (IOException ignored) {
                        }
                    });
        } catch (IOException e) {
            log.warn("遍历抓拍目录失败 root={} error={}", root, e.getMessage());
        }
        entries.sort(java.util.Comparator.comparingDouble(JpgEntry::mtime));
        return entries;
    }

    private boolean isKafkaUploadMode() {
        String mode = videoProperties.getMedia().getUploadMode();
        if (mode == null) {
            return false;
        }
        String normalized = mode.trim().toLowerCase();
        return "kafka".equals(normalized) || "hybrid".equals(normalized);
    }

    private boolean isSnapKafkaMode() {
        String snapMode = videoProperties.getMedia().getSnapUploadMode();
        if (snapMode != null && !snapMode.isBlank()) {
            String normalized = snapMode.trim().toLowerCase();
            if ("kafka".equals(normalized)) {
                return true;
            }
            if ("sync".equals(normalized)) {
                return false;
            }
        }
        return isKafkaUploadMode();
    }

    private record OrphanFile(String deviceId, String filePath, double mtime, long sizeBytes) {}

    private record JpgEntry(String path, double mtime, long sizeBytes) {}
}
