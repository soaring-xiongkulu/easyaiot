package com.basiclab.iot.video.service.ops;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.dal.RecordSpaceRepository;
import com.basiclab.iot.video.support.MediaPathSupport;
import com.basiclab.iot.video.support.SpaceSaveTimeSupport;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * SRS local playback disk guard aligned with Python {@code playback_disk_guard_service}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PlaybackDiskGuardService {

    private final VideoProperties videoProperties;
    private final RecordSpaceRepository recordSpaceRepository;

    public Map<String, Object> runGuard() {
        VideoProperties.PlaybackDiskGuard guard = videoProperties.getPlaybackDiskGuard();
        if (!guard.isEnabled()) {
            log.debug("回放磁盘守护已关闭 (video.playback-disk-guard.enabled=false)");
            return Map.of("enabled", false);
        }

        String recordDir = MediaPathSupport.getSrsRecordDir(guard);
        double diskPct = getDiskUsagePercent(recordDir);
        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("enabled", true);
        stats.put("record_dir", recordDir);
        stats.put("disk_percent", round2(diskPct));
        stats.put("devices", cleanupAllDevicesExpired(recordDir, guard));
        stats.put("expired", cleanupExpiredFiles(recordDir, guard.getMaxAgeHours()));
        stats.put("global", cleanupGlobalRecordings(recordDir, guard));

        if (diskPct >= guard.getDiskWarnPercent()) {
            stats.put("emergency", emergencyFreeDisk(recordDir, guard, diskPct));
        } else {
            stats.put("emergency", Map.of("skipped", 1, "disk_percent", round2(diskPct)));
        }

        log.info(
                "回放磁盘守护完成: dir={} disk={}% devices={} expired={} global={} emergency={}",
                recordDir,
                round2(diskPct),
                stats.get("devices"),
                stats.get("expired"),
                stats.get("global"),
                stats.get("emergency")
        );
        return stats;
    }

    private Map<String, Object> cleanupAllDevicesExpired(String recordDir, VideoProperties.PlaybackDiskGuard guard) {
        Path liveDir = Path.of(recordDir, "live");
        if (!Files.isDirectory(liveDir)) {
            return Map.of("devices_checked", 0, "deleted", 0, "freed_bytes", 0L);
        }

        Map<String, Integer> deviceHours = resolveDevicePlaybackMaxAgeMap();
        int defaultHours = guard.getMaxAgeHours();
        int totalDeleted = 0;
        long totalFreed = 0;
        Map<String, Map<String, Object>> byDevice = new LinkedHashMap<>();

        try (var stream = Files.list(liveDir)) {
            List<String> deviceIds = stream
                    .filter(Files::isDirectory)
                    .map(path -> path.getFileName().toString())
                    .sorted()
                    .toList();
            for (String deviceId : deviceIds) {
                int maxAge = deviceHours.getOrDefault(deviceId, defaultHours);
                if (maxAge <= 0) {
                    byDevice.put(deviceId, Map.of("skipped", 1, "reason", "permanent"));
                    continue;
                }
                Map<String, Object> result = cleanupDeviceExpired(recordDir, deviceId, maxAge);
                byDevice.put(deviceId, result);
                totalDeleted += ((Number) result.getOrDefault("deleted", 0)).intValue();
                totalFreed += ((Number) result.getOrDefault("freed_bytes", 0L)).longValue();
            }
            Map<String, Object> summary = new LinkedHashMap<>();
            summary.put("devices_checked", deviceIds.size());
            summary.put("deleted", totalDeleted);
            summary.put("freed_bytes", totalFreed);
            summary.put("by_device", byDevice);
            return summary;
        } catch (IOException e) {
            log.warn("扫描 live 设备目录失败: {}", e.getMessage());
            return Map.of("devices_checked", 0, "deleted", 0, "freed_bytes", 0L, "error", e.getMessage());
        }
    }

    private Map<String, Object> cleanupDeviceExpired(String recordDir, String deviceId, int maxAgeHours) {
        List<FlvEntry> entries = iterFlvFiles(Path.of(recordDir, "live", deviceId));
        if (entries.isEmpty()) {
            return Map.of("device_id", deviceId, "total", 0, "deleted", 0);
        }
        double cutoff = Instant.now().getEpochSecond() - maxAgeHours * 3600.0;
        List<FlvEntry> expired = entries.stream().filter(entry -> entry.mtime() < cutoff).toList();
        if (expired.isEmpty()) {
            return Map.of("device_id", deviceId, "total", entries.size(), "deleted", 0);
        }
        Map<String, Object> result = deleteOldestEntries(expired, expired.size(), "设备" + deviceId + "超过" + maxAgeHours + "小时");
        result.put("device_id", deviceId);
        result.put("total", entries.size());
        return result;
    }

    private Map<String, Object> cleanupExpiredFiles(String recordDir, int maxAgeHours) {
        if (maxAgeHours <= 0) {
            return Map.of("skipped", 1, "reason", "max_age_disabled");
        }
        List<FlvEntry> entries = iterFlvFiles(Path.of(recordDir));
        double cutoff = Instant.now().getEpochSecond() - maxAgeHours * 3600.0;
        List<FlvEntry> expired = entries.stream().filter(entry -> entry.mtime() < cutoff).toList();
        if (expired.isEmpty()) {
            return Map.of("total", entries.size(), "deleted", 0);
        }
        Map<String, Object> result = deleteOldestEntries(expired, expired.size(), "超过" + maxAgeHours + "小时");
        result.put("total", entries.size());
        return result;
    }

    private Map<String, Object> cleanupGlobalRecordings(String recordDir, VideoProperties.PlaybackDiskGuard guard) {
        List<FlvEntry> entries = iterFlvFiles(Path.of(recordDir));
        int total = entries.size();
        if (total <= guard.getGlobalMaxFiles()) {
            return Map.of("total", total, "deleted", 0);
        }
        double keepRatio = clampKeepRatio(guard.getKeepRatio());
        int keepCount = Math.max(1, (int) (total * keepRatio));
        int deleteCount = total - keepCount;
        Map<String, Object> result = deleteOldestEntries(entries, deleteCount, "全局数量超限");
        result.put("total", total);
        return result;
    }

    private Map<String, Object> emergencyFreeDisk(
            String recordDir,
            VideoProperties.PlaybackDiskGuard guard,
            double diskPctBefore
    ) {
        if (diskPctBefore < guard.getDiskCriticalPercent()) {
            return Map.of("disk_percent", round2(diskPctBefore), "deleted", 0, "skipped", 1);
        }

        log.warn(
                "磁盘使用率紧急: {}% >= {}%, 开始删除最旧回放录像, 目标={}%",
                round2(diskPctBefore),
                guard.getDiskCriticalPercent(),
                guard.getDiskTargetPercent()
        );

        int totalDeleted = 0;
        long totalFreed = 0;
        for (int round = 0; round < guard.getEmergencyMaxRounds(); round++) {
            double diskPct = getDiskUsagePercent(recordDir);
            if (diskPct < guard.getDiskTargetPercent()) {
                break;
            }
            List<FlvEntry> entries = iterFlvFiles(Path.of(recordDir));
            if (entries.isEmpty()) {
                break;
            }
            int batchSize = Math.min(guard.getEmergencyBatchSize(), entries.size());
            Map<String, Object> batch = deleteOldestEntries(entries.subList(0, batchSize), batchSize, "磁盘紧急清理");
            totalDeleted += ((Number) batch.getOrDefault("deleted", 0)).intValue();
            totalFreed += ((Number) batch.getOrDefault("freed_bytes", 0L)).longValue();
            if (((Number) batch.getOrDefault("deleted", 0)).intValue() == 0) {
                break;
            }
        }

        double finalPct = getDiskUsagePercent(recordDir);
        if (totalDeleted > 0) {
            log.warn(
                    "磁盘紧急清理完成: deleted={} freedMB={} disk {}% -> {}%",
                    totalDeleted,
                    totalFreed / (1024.0 * 1024.0),
                    round2(diskPctBefore),
                    round2(finalPct)
            );
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("deleted", totalDeleted);
        result.put("freed_bytes", totalFreed);
        result.put("disk_percent_before", round2(diskPctBefore));
        result.put("disk_percent_after", round2(finalPct));
        return result;
    }

    private Map<String, Integer> resolveDevicePlaybackMaxAgeMap() {
        Map<String, Integer> result = new LinkedHashMap<>();
        for (Map<String, Object> space : recordSpaceRepository.listAllSpaces()) {
            String deviceId = space.get("device_id") != null ? String.valueOf(space.get("device_id")) : "";
            if (deviceId.isBlank()) {
                continue;
            }
            result.put(deviceId, SpaceSaveTimeSupport.effectiveSaveTimeHours(space));
        }
        return result;
    }

    static List<FlvEntry> iterFlvFiles(Path root) {
        if (!Files.isDirectory(root)) {
            return List.of();
        }
        List<FlvEntry> entries = new ArrayList<>();
        try {
            Files.walkFileTree(root, new SimpleFileVisitor<>() {
                @Override
                public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
                    if (file.getFileName().toString().toLowerCase().endsWith(".flv") && Files.isRegularFile(file)) {
                        entries.add(new FlvEntry(file.toString(), attrs.lastModifiedTime().toMillis() / 1000.0, attrs.size()));
                    }
                    return FileVisitResult.CONTINUE;
                }
            });
        } catch (IOException e) {
            log.warn("遍历回放目录失败 root={} error={}", root, e.getMessage());
        }
        entries.sort(Comparator.comparingDouble(FlvEntry::mtime));
        return entries;
    }

    static boolean removePlaybackFile(String filePath, String reason) {
        if (filePath == null || filePath.isBlank()) {
            return false;
        }
        Path path = Path.of(filePath);
        if (!Files.isRegularFile(path)) {
            return false;
        }
        try {
            Files.delete(path);
            log.info("已删除本地回放录像: {} ({})", filePath, reason);
            pruneEmptyParents(path.getParent());
            return true;
        } catch (IOException e) {
            log.debug("删除本地回放录像失败: {} error={}", filePath, e.getMessage());
            return false;
        }
    }

    private static void pruneEmptyParents(Path start) {
        Path current = start;
        while (current != null) {
            try {
                if (!Files.isDirectory(current)) {
                    break;
                }
                try (var stream = Files.list(current)) {
                    if (stream.findAny().isPresent()) {
                        break;
                    }
                }
                Files.delete(current);
                current = current.getParent();
            } catch (IOException e) {
                break;
            }
        }
    }

    private Map<String, Object> deleteOldestEntries(List<FlvEntry> entries, int deleteCount, String reason) {
        int deleted = 0;
        long freedBytes = 0;
        int limit = Math.min(deleteCount, entries.size());
        for (int i = 0; i < limit; i++) {
            FlvEntry entry = entries.get(i);
            if (removePlaybackFile(entry.path(), reason)) {
                deleted++;
                freedBytes += entry.sizeBytes();
            }
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("deleted", deleted);
        result.put("freed_bytes", freedBytes);
        return result;
    }

    static double getDiskUsagePercent(String path) {
        try {
            Path checkPath = Files.exists(Path.of(path)) ? Path.of(path) : Path.of(path).getParent();
            if (checkPath == null) {
                return 0.0;
            }
            var store = Files.getFileStore(checkPath);
            long total = store.getTotalSpace();
            if (total <= 0) {
                return 0.0;
            }
            long usable = store.getUsableSpace();
            return ((total - usable) * 100.0) / total;
        } catch (IOException e) {
            log.warn("无法获取磁盘使用率 path={} error={}", path, e.getMessage());
            return 0.0;
        }
    }

    private static double clampKeepRatio(double keepRatio) {
        return Math.min(1.0, Math.max(0.05, keepRatio));
    }

    private static double round2(double value) {
        return Math.round(value * 100.0) / 100.0;
    }

    record FlvEntry(String path, double mtime, long sizeBytes) {}
}
