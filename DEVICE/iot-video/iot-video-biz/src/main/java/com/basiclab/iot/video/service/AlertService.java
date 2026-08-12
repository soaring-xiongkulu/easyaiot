package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.AlertRepository;
import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.dal.FaceMatchRecordRepository;
import com.basiclab.iot.video.dal.PlateMatchRecordRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

@Service
@RequiredArgsConstructor
@Slf4j
public class AlertService {

    private static final ZoneId SHANGHAI = ZoneId.of("Asia/Shanghai");
    private static final Duration STATS_CACHE_TTL = Duration.ofSeconds(5);
    private static final Duration QUERY_CACHE_TTL = Duration.ofSeconds(5);

    private final AlertRepository alertRepository;
    private final DeviceRepository deviceRepository;
    private final AlgorithmTaskRepository algorithmTaskRepository;
    private final FaceMatchRecordRepository faceMatchRecordRepository;
    private final PlateMatchRecordRepository plateMatchRecordRepository;

    private volatile Map<String, Object> statsCache;
    private volatile long statsCacheTs;
    private final ConcurrentHashMap<String, CachedQuery> recordQueryCache = new ConcurrentHashMap<>();

    public Map<String, Object> getPage(Map<String, String> args) {
        return alertRepository.list(args);
    }

    public Map<String, Object> getCount(Map<String, String> args) {
        return alertRepository.count(args);
    }

    public Map<String, Object> getDashboardStatistics() {
        long now = System.currentTimeMillis();
        Map<String, Object> cached = statsCache;
        if (cached != null && now - statsCacheTs < STATS_CACHE_TTL.toMillis()) {
            return cached;
        }
        try {
            ZonedDateTime todayStart = ZonedDateTime.now(SHANGHAI)
                    .toLocalDate()
                    .atStartOfDay(SHANGHAI);
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("alarm_count", alertRepository.countAll());
            result.put("today_alarm_count", alertRepository.countSince(todayStart.toLocalDateTime()));
            result.put("camera_count", deviceRepository.count(null));
            result.put("algorithm_count", algorithmTaskRepository.count(null, null));
            result.put("model_count", fetchModelCount());
            statsCache = result;
            statsCacheTs = now;
            return result;
        } catch (Exception ex) {
            log.warn("告警统计查询失败，返回 degraded: {}", ex.getMessage());
            Map<String, Object> degraded = new LinkedHashMap<>();
            degraded.put("degraded", true);
            degraded.put("error", ex.getMessage());
            return degraded;
        }
    }

    public Map<String, Object> getCorrelationEvents(String correlationId) {
        String cid = correlationId != null ? correlationId.trim() : "";
        if (cid.isEmpty()) {
            throw new VideoBusinessException(400, "correlation_id 不能为空");
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("correlation_id", cid);
        result.put("alerts", alertRepository.listByCorrelationId(cid));
        result.put("face_match_records", faceMatchRecordRepository.listByCorrelationId(cid));
        result.put("plate_match_records", plateMatchRecordRepository.listByCorrelationId(cid));
        return result;
    }

    public Map<String, Object> clearByTaskName(String taskName) {
        String name = taskName != null ? taskName.trim() : "";
        if (name.isEmpty()) {
            throw new VideoBusinessException(400, "task_name参数不能为空");
        }
        int deleted = alertRepository.deleteByObjectEquals(name);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("deleted_count", deleted);
        result.put("task_name", name);
        return result;
    }

    public Map<String, Object> clearAll() {
        int deleted = alertRepository.deleteAll();
        return Map.of("deleted_count", deleted);
    }

    public Path resolveLocalImagePath(String path) {
        if (path == null || path.isBlank()) {
            throw new VideoBusinessException(400, "路径参数不能为空");
        }
        if (isMinioDownloadPath(path)) {
            throw new VideoBusinessException(400, "MinIO 图片请通过对象存储网关访问（本地路径模式不支持）: " + path);
        }
        Path file = resolvePlaybackAbsolutePath(path.trim());
        if (!Files.isRegularFile(file)) {
            throw new VideoBusinessException(400, "文件不存在: " + path);
        }
        return file;
    }

    public Path resolveLocalRecordPath(String path) {
        if (path == null || path.isBlank()) {
            throw new VideoBusinessException(400, "路径参数不能为空");
        }
        Path file = resolvePlaybackAbsolutePath(path.trim());
        if (!Files.isRegularFile(file)) {
            throw new VideoBusinessException(404, "文件不存在: " + path);
        }
        return file;
    }

    public String recordMimetype(Path file) {
        String name = file.getFileName().toString().toLowerCase();
        if (name.endsWith(".flv")) {
            return "video/x-flv";
        }
        if (name.endsWith(".mp4")) {
            return "video/mp4";
        }
        if (name.endsWith(".ts")) {
            return "video/mp2t";
        }
        if (name.endsWith(".mkv")) {
            return "video/x-matroska";
        }
        return "application/octet-stream";
    }

    public Map<String, Object> queryAlertRecord(
            String deviceId,
            String alertTimeStr,
            String alertId,
            int timeRange) {
        String cacheKey = deviceId + ":" + (alertId != null ? alertId : "") + ":"
                + (alertTimeStr != null ? alertTimeStr : "") + ":" + timeRange;
        long now = System.currentTimeMillis();
        CachedQuery cached = recordQueryCache.get(cacheKey);
        if (cached != null && now - cached.ts < QUERY_CACHE_TTL.toMillis()) {
            return cached.payload;
        }

        if ((deviceId == null || deviceId.isBlank()) && (alertId == null || alertId.isBlank())) {
            throw new VideoBusinessException(400, "设备ID不能为空");
        }
        if ((alertTimeStr == null || alertTimeStr.isBlank()) && (alertId == null || alertId.isBlank())) {
            throw new VideoBusinessException(400, "告警时间不能为空");
        }

        String resolvedDeviceId = deviceId;
        LocalDateTime alertTime = null;
        if (alertId != null && !alertId.isBlank()) {
            try {
                Optional<Map<String, Object>> row = alertRepository.findById(Long.parseLong(alertId.trim()));
                if (row.isPresent()) {
                    if (resolvedDeviceId == null || resolvedDeviceId.isBlank()) {
                        resolvedDeviceId = String.valueOf(row.get().get("device_id"));
                    }
                    Object time = row.get().get("time");
                    if (time instanceof String s && !s.isBlank()) {
                        alertTime = parseAlertTime(s);
                    }
                }
            } catch (NumberFormatException ignored) {
                // keep caller-provided device/time
            }
        }
        if (alertTime == null && alertTimeStr != null && !alertTimeStr.isBlank()) {
            alertTime = parseAlertTime(alertTimeStr.trim());
            if (alertTime == null) {
                throw new VideoBusinessException(400, "告警时间格式无效，请使用 YYYY-MM-DD HH:MM:SS");
            }
        }
        if (resolvedDeviceId == null || resolvedDeviceId.isBlank()) {
            throw new VideoBusinessException(400, "设备ID不能为空");
        }
        if (alertTime == null) {
            throw new VideoBusinessException(400, "告警时间不能为空");
        }

        Optional<Map<String, Object>> resolved = resolveAlertRecordVideo(
                resolvedDeviceId, alertTime, timeRange, alertId);
        if (resolved.isEmpty()) {
            Map<String, Object> miss = new LinkedHashMap<>();
            miss.put("code", 400);
            miss.put("message", "该设备在告警时间前后" + timeRange + "秒内暂无录像记录，请稍后再试");
            miss.put("data", null);
            recordQueryCache.put(cacheKey, new CachedQuery(miss, now));
            return miss;
        }
        return Map.of(
                "code", 0,
                "msg", "success",
                "message", "success",
                "data", resolved.get()
        );
    }

    public Optional<Map<String, Object>> resolveAlertRecordVideo(
            String deviceId,
            LocalDateTime alertTime,
            int timeRange,
            String alertId) {
        String resolvedDeviceId = deviceId;
        LocalDateTime resolvedTime = alertTime;
        if (alertId != null && !alertId.isBlank()) {
            try {
                Optional<Map<String, Object>> row = alertRepository.findById(Long.parseLong(alertId.trim()));
                if (row.isPresent()) {
                    Map<String, Object> alert = row.get();
                    if (resolvedDeviceId == null || resolvedDeviceId.isBlank()) {
                        resolvedDeviceId = String.valueOf(alert.get("device_id"));
                    }
                    Object time = alert.get("time");
                    if (time instanceof String s && !s.isBlank()) {
                        LocalDateTime parsed = parseAlertTime(s);
                        if (parsed != null) {
                            resolvedTime = parsed;
                        }
                    }
                    Object recordPath = alert.get("record_path");
                    if (recordPath != null && !String.valueOf(recordPath).isBlank()) {
                        Map<String, Object> payload = recordPathPayload(
                                String.valueOf(recordPath), String.valueOf(alert.get("device_id")));
                        if (!payload.isEmpty()) {
                            return Optional.of(payload);
                        }
                    }
                }
            } catch (NumberFormatException ignored) {
                // fall through to playback match
            }
        }
        if (resolvedDeviceId == null || resolvedTime == null) {
            return Optional.empty();
        }
        Optional<Map<String, Object>> playback = alertRepository.findNearestPlayback(
                resolvedDeviceId, resolvedTime, timeRange);
        if (playback.isPresent()) {
            Map<String, Object> pb = playback.get();
            String filePath = pb.get("file_path") != null ? String.valueOf(pb.get("file_path")) : "";
            if (!filePath.isBlank()) {
                Map<String, Object> out = new LinkedHashMap<>();
                out.put("playback_id", pb.get("id"));
                out.put("file_path", filePath);
                out.put("video_url", resolvePlaybackDisplayUrl(filePath));
                out.put("event_time", pb.get("event_time"));
                out.put("duration", pb.get("duration"));
                out.put("device_id", pb.get("device_id"));
                out.put("device_name", pb.get("device_name"));
                out.put("source", "playback_match");
                return Optional.of(out);
            }
        }
        return Optional.empty();
    }

    private Map<String, Object> recordPathPayload(String recordPath, String deviceId) {
        String path = recordPath != null ? recordPath.trim() : "";
        if (path.isEmpty()) {
            return Map.of();
        }
        if (isMinioDownloadPath(path)) {
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("video_url", path);
            out.put("file_path", path);
            out.put("device_id", deviceId);
            out.put("source", "alert_record_path");
            return out;
        }
        if (isLocalFilesystemPath(path)) {
            String apiPath = "/video/alert/record?path="
                    + URLEncoder.encode(path, StandardCharsets.UTF_8);
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("video_url", apiPath);
            out.put("file_path", path);
            out.put("device_id", deviceId);
            out.put("source", "alert_record_path");
            return out;
        }
        return Map.of();
    }

    private String resolvePlaybackDisplayUrl(String filePath) {
        if (filePath == null || filePath.isBlank()) {
            return filePath;
        }
        String trimmed = filePath.trim();
        if (isLocalFilesystemPath(trimmed)) {
            return "/video/alert/record?path="
                    + URLEncoder.encode(trimmed, StandardCharsets.UTF_8);
        }
        return trimmed;
    }

    private Path resolvePlaybackAbsolutePath(String localPath) {
        Path candidate = Path.of(localPath).normalize();
        if (Files.isRegularFile(candidate)) {
            return candidate;
        }
        String mediaRoot = System.getenv("MEDIA_HOST_DATA_ROOT");
        if (mediaRoot == null || mediaRoot.isBlank()) {
            mediaRoot = System.getenv("SRS_HOST_DATA_ROOT");
        }
        if (mediaRoot != null && !mediaRoot.isBlank()) {
            for (String prefix : new String[]{"/data", "/mnt/easyaiot-media"}) {
                String normalized = localPath.replace('\\', '/');
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

    private boolean isMinioDownloadPath(String path) {
        if (path == null || path.isBlank()) {
            return false;
        }
        String p = path.trim();
        return p.startsWith("/api/v1/buckets/") && p.contains("/objects/download");
    }

    private boolean isLocalFilesystemPath(String path) {
        if (path == null || path.isBlank()) {
            return false;
        }
        String p = path.trim();
        return p.startsWith("/") || (p.length() > 2 && Character.isLetter(p.charAt(0)) && p.charAt(1) == ':');
    }

    private LocalDateTime parseAlertTime(String raw) {
        if (raw == null || raw.isBlank()) {
            return null;
        }
        String s = raw.trim();
        for (String fmt : new String[]{
                "yyyy-MM-dd HH:mm:ss",
                "yyyy-MM-dd HH:mm:ss.SSS",
                "yyyy-MM-dd'T'HH:mm:ss",
                "yyyy-MM-dd'T'HH:mm:ss.SSS"}) {
            try {
                if (s.contains("T")) {
                    return LocalDateTime.parse(s, java.time.format.DateTimeFormatter.ofPattern(fmt));
                }
                return LocalDateTime.parse(s, java.time.format.DateTimeFormatter.ofPattern(
                        fmt.contains("T") ? fmt : "yyyy-MM-dd HH:mm:ss"));
            } catch (Exception ignored) {
                // try next
            }
        }
        try {
            return LocalDateTime.parse(s.replace(" ", "T"));
        } catch (Exception ignored) {
            return null;
        }
    }

    private int fetchModelCount() {
        String gateway = System.getenv("DEVICE_GATEWAY_URL");
        if (gateway == null || gateway.isBlank()) {
            gateway = "http://localhost:48080";
        }
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(gateway.replaceAll("/$", "") + "/admin-api/model/list?pageNo=1&pageSize=1"))
                    .timeout(Duration.ofSeconds(2))
                    .GET()
                    .build();
            HttpResponse<String> response = HttpClient.newHttpClient()
                    .send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() == 200 && response.body() != null) {
                String body = response.body();
                int totalIdx = body.indexOf("\"total\"");
                if (totalIdx >= 0) {
                    int colon = body.indexOf(':', totalIdx);
                    int end = body.indexOf(',', colon);
                    if (end < 0) {
                        end = body.indexOf('}', colon);
                    }
                    if (colon > 0 && end > colon) {
                        return Integer.parseInt(body.substring(colon + 1, end).trim());
                    }
                }
            }
        } catch (Exception ignored) {
            // AI service unavailable — mirror Python fallback
        }
        return 0;
    }

    private record CachedQuery(Map<String, Object> payload, long ts) {}
}
