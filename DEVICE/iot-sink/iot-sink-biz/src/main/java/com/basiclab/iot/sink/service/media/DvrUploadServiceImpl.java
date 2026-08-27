package com.basiclab.iot.sink.service.media;

import com.baomidou.dynamic.datasource.toolkit.DynamicDataSourceContextHolder;
import io.minio.BucketExistsArgs;
import io.minio.MakeBucketArgs;
import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import com.basiclab.iot.sink.config.NfsMediaProperties;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
public class DvrUploadServiceImpl implements DvrUploadService {

    private static final ZoneId SHANGHAI = ZoneId.of("Asia/Shanghai");
    private static final int MIN_FILE_BYTES = 4096;

    private final NfsMediaPathResolver pathResolver;
    private final NfsMediaProperties mediaProperties;

    @Autowired(required = false)
    private MinioClient minioClient;

    @Autowired(required = false)
    private JdbcTemplate jdbcTemplate;

    @Value("${easyaiot.media.dvr-default-duration-seconds:${SINK_DVR_DEFAULT_DURATION_SECONDS:60}}")
    private int defaultDvrDurationSeconds;

    @Value("${easyaiot.media.ffprobe-path:${FFPROBE_PATH:ffprobe}}")
    private String ffprobePath;

    @Override
    public boolean processDvrEvent(Map<String, Object> event) {
        if (event == null || event.isEmpty()) {
            return false;
        }
        String stream = stringVal(event.get("stream"));
        String filePath = stringVal(event.get("file_path"));
        if (!StringUtils.hasText(filePath)) {
            filePath = stringVal(event.get("file"));
        }
        String cwd = stringVal(event.get("cwd"));
        String deviceId = stringVal(event.get("device_id"));
        Integer taskId = integerVal(event.get("task_id"));
        if (taskId == null) {
            taskId = integerVal(event.get("taskId"));
        }
        if (!StringUtils.hasText(deviceId)) {
            deviceId = stream;
        }

        Path absolute;
        try {
            absolute = pathResolver.resolveMediaPath(filePath, cwd);
        } catch (Exception e) {
            log.warn("DVR 路径解析失败 file={} cwd={}: {}", filePath, cwd, e.getMessage());
            return false;
        }
        if (!Files.isRegularFile(absolute)) {
            log.warn("DVR 文件不存在: {}", absolute);
            return false;
        }

        String resolvedDeviceId = resolveDeviceId(deviceId, stream);
        if (!StringUtils.hasText(resolvedDeviceId)) {
            log.info("DVR 设备不存在，丢弃 stream={} file={}", stream, absolute);
            tryDelete(absolute);
            return true;
        }

        long fileSize = waitFileStable(absolute);
        if (fileSize < MIN_FILE_BYTES) {
            log.warn("DVR 文件过小或未就绪: {} size={}", absolute, fileSize);
            return false;
        }

        String bucketName = ensureRecordBucket(resolvedDeviceId);
        if (!StringUtils.hasText(bucketName)) {
            return false;
        }

        String filename = absolute.getFileName().toString();
        String fileExt = filename.contains(".") ? filename.substring(filename.lastIndexOf('.')) : ".flv";
        LocalDateTime recordTime;
        try {
            recordTime = LocalDateTime.ofInstant(
                    Files.getLastModifiedTime(absolute).toInstant(), SHANGHAI);
        } catch (java.io.IOException e) {
            log.warn("读取 DVR 文件时间失败: {} {}", absolute, e.getMessage());
            recordTime = LocalDateTime.now(SHANGHAI);
        }
        String dateDir = recordTime.format(DateTimeFormatter.ofPattern("yyyy/MM/dd"));
        String taskPrefix = taskId == null ? "" : "task_" + taskId + "/";
        String objectName = resolvedDeviceId + "/" + taskPrefix + dateDir + "/" + filename;

        if (minioClient == null) {
            log.warn("MinIO 不可用，跳过 DVR 上传 device={} file={}", resolvedDeviceId, absolute);
            return false;
        }

        try {
            ensureBucket(bucketName);
            String contentType = contentTypeForExt(fileExt);
            try (InputStream in = new FileInputStream(absolute.toFile())) {
                minioClient.putObject(PutObjectArgs.builder()
                        .bucket(bucketName)
                        .object(objectName)
                        .stream(in, fileSize, -1)
                        .contentType(contentType)
                        .build());
            }
            String minioUrl = "/api/v1/buckets/" + bucketName + "/objects/download?prefix="
                    + URLEncoder.encode(objectName, StandardCharsets.UTF_8);
            int duration = resolveDurationSeconds(event, absolute);
            upsertPlayback(resolvedDeviceId, taskId, minioUrl, objectName, recordTime, fileSize, duration);
            // 录像空间前端读 record_file，必须与 Playback 同步写入，否则「录像回放」一直为空
            upsertRecordFile(resolvedDeviceId, taskId, bucketName, objectName, minioUrl, recordTime, fileSize, duration);
            patchAlertsRecord(resolvedDeviceId, taskId, recordTime, duration, minioUrl);
            if (mediaProperties.isRemoveLocalAfterUpload()) {
                tryDelete(absolute);
            }
            log.info("DVR 上传完成 device={} object={} size={}", resolvedDeviceId, objectName, fileSize);
            return true;
        } catch (Exception e) {
            log.error("DVR 上传失败 device={} file={}: {}", resolvedDeviceId, absolute, e.getMessage(), e);
            return false;
        }
    }

    private String resolveDeviceId(String deviceId, String stream) {
        if (jdbcTemplate == null) {
            return deviceId;
        }
        try {
            DynamicDataSourceContextHolder.push("video");
            if (StringUtils.hasText(deviceId)) {
                List<String> ids = jdbcTemplate.query(
                        "SELECT id FROM device WHERE id = ? LIMIT 1",
                        (rs, rowNum) -> rs.getString(1),
                        deviceId);
                if (!ids.isEmpty()) {
                    return ids.get(0);
                }
            }
            if (StringUtils.hasText(stream)) {
                List<String> ids = jdbcTemplate.query(
                        "SELECT id FROM device WHERE id = ? OR rtmp_stream LIKE ? LIMIT 1",
                        (rs, rowNum) -> rs.getString(1),
                        stream, "%/" + stream);
                if (!ids.isEmpty()) {
                    return ids.get(0);
                }
            }
            return null;
        } finally {
            DynamicDataSourceContextHolder.clear();
        }
    }

    private String ensureRecordBucket(String deviceId) {
        if (jdbcTemplate == null) {
            return "record-" + deviceId;
        }
        try {
            DynamicDataSourceContextHolder.push("video");
            List<String> buckets = jdbcTemplate.query(
                    "SELECT bucket_name FROM record_space WHERE device_id = ? LIMIT 1",
                    (rs, rowNum) -> rs.getString(1),
                    deviceId);
            if (!buckets.isEmpty() && StringUtils.hasText(buckets.get(0))) {
                return buckets.get(0);
            }
            String bucket = "record-" + deviceId.replaceAll("[^a-zA-Z0-9._-]", "-");
            jdbcTemplate.update(
                    "INSERT INTO record_space (space_name, space_code, bucket_name, save_mode, save_time, device_id, created_at, updated_at) "
                            + "VALUES (?, ?, ?, 0, 0, ?, NOW(), NOW()) ON CONFLICT DO NOTHING",
                    "录像空间-" + deviceId, deviceId, bucket, deviceId);
            return bucket;
        } catch (Exception e) {
            log.warn("record_space 查询失败 device={}: {}", deviceId, e.getMessage());
            return "record-" + deviceId;
        } finally {
            DynamicDataSourceContextHolder.clear();
        }
    }

    private void upsertPlayback(
            String deviceId, Integer taskId, String filePathUrl, String objectName,
            LocalDateTime recordTime, long fileSize, int duration) {
        if (jdbcTemplate == null) {
            return;
        }
        try {
            DynamicDataSourceContextHolder.push("video");
            String deviceName = jdbcTemplate.query(
                    "SELECT name FROM device WHERE id = ? LIMIT 1",
                    rs -> rs.next() ? rs.getString(1) : deviceId,
                    deviceId);
            Integer existing = jdbcTemplate.query(
                    "SELECT id FROM playback WHERE device_id = ? AND (file_path = ? OR file_path = ?) LIMIT 1",
                    rs -> rs.next() ? rs.getInt(1) : null,
                    deviceId, filePathUrl, objectName);
            if (existing != null) {
                jdbcTemplate.update(
                        "UPDATE playback SET task_id = ?, file_path = ?, file_size = ?, event_time = ?, duration = ?, updated_at = NOW() WHERE id = ?",
                        taskId, filePathUrl, fileSize, recordTime, duration, existing);
            } else {
                jdbcTemplate.update(
                        "INSERT INTO playback (file_path, event_time, device_id, task_id, device_name, duration, file_size, created_at, updated_at) "
                                + "VALUES (?, ?, ?, ?, ?, ?, ?, NOW(), NOW())",
                        filePathUrl, recordTime, deviceId, taskId, deviceName, duration, fileSize);
            }
        } finally {
            DynamicDataSourceContextHolder.clear();
        }
    }

    /**
     * 写入录像空间元数据表 record_file（WEB「录像回放」按此表查询，不能只写 playback）。
     */
    private void upsertRecordFile(
            String deviceId, Integer taskId, String bucketName, String objectName, String filePathUrl,
            LocalDateTime recordTime, long fileSize, int duration) {
        if (jdbcTemplate == null || !StringUtils.hasText(deviceId) || !StringUtils.hasText(objectName)) {
            return;
        }
        try {
            DynamicDataSourceContextHolder.push("video");
            Integer spaceId = jdbcTemplate.query(
                    "SELECT id FROM record_space WHERE device_id = ? LIMIT 1",
                    rs -> rs.next() ? rs.getInt(1) : null,
                    deviceId);
            if (spaceId == null) {
                log.warn("设备无录像空间，跳过 record_file device={}", deviceId);
                return;
            }
            String filename = objectName.contains("/")
                    ? objectName.substring(objectName.lastIndexOf('/') + 1)
                    : objectName;
            Integer existing = jdbcTemplate.query(
                    "SELECT id FROM record_file WHERE bucket_name = ? AND object_name = ? LIMIT 1",
                    rs -> rs.next() ? rs.getInt(1) : null,
                    bucketName, objectName);
            if (existing != null) {
                jdbcTemplate.update(
                        "UPDATE record_file SET space_id = ?, device_id = ?, task_id = ?, filename = ?, file_size = ?, "
                                + "url = ?, duration = ?, event_time = ?, source = ?, updated_at = NOW() WHERE id = ?",
                        spaceId, deviceId, taskId, filename, fileSize, filePathUrl, (short) duration, recordTime, "dvr",
                        existing);
            } else {
                jdbcTemplate.update(
                        "INSERT INTO record_file (space_id, device_id, task_id, object_name, bucket_name, filename, file_size, "
                                + "content_type, url, duration, event_time, source, created_at, updated_at) "
                                + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())",
                        spaceId, deviceId, taskId, objectName, bucketName, filename, fileSize,
                        "video/x-flv", filePathUrl, (short) duration, recordTime, "dvr");
            }
        } catch (Exception e) {
            log.warn("写入 record_file 失败 device={} object={}: {}", deviceId, objectName, e.getMessage());
        } finally {
            DynamicDataSourceContextHolder.clear();
        }
    }

    private void patchAlertsRecord(
            String deviceId, Integer taskId, LocalDateTime eventTime, int duration, String filePathUrl) {
        if (jdbcTemplate == null || !StringUtils.hasText(filePathUrl)) {
            return;
        }
        try {
            DynamicDataSourceContextHolder.push("video");
            LocalDateTime legacyStart = eventTime.minusSeconds(Math.max(duration, 1));
            LocalDateTime endTime = eventTime.plusSeconds(Math.max(duration, 1));
            String taskClause = taskId == null ? "" : "AND task_id = ? ";
            Object[] args = taskId == null
                    ? new Object[]{filePathUrl, deviceId, legacyStart, endTime}
                    : new Object[]{filePathUrl, deviceId, legacyStart, endTime, taskId};
            int updated = jdbcTemplate.update(
                    "UPDATE alert SET record_path = ? WHERE device_id = ? "
                            + "AND time >= ? AND time <= ? "
                            + taskClause
                            + "AND (record_path IS NULL OR TRIM(record_path) = '')",
                    args);
            if (updated > 0) {
                log.info("已回写 {} 条告警 record_path device={}", updated, deviceId);
            }
        } finally {
            DynamicDataSourceContextHolder.clear();
        }
    }

    private void ensureBucket(String bucketName) throws Exception {
        boolean exists = minioClient.bucketExists(BucketExistsArgs.builder().bucket(bucketName).build());
        if (!exists) {
            minioClient.makeBucket(MakeBucketArgs.builder().bucket(bucketName).build());
        }
    }

    private long waitFileStable(Path file) {
        long last = -1;
        int stable = 0;
        for (int i = 0; i < 20; i++) {
            try {
                if (!Files.isRegularFile(file)) {
                    stable = 0;
                } else {
                    long sz = Files.size(file);
                    if (sz == last && sz > 0) {
                        stable++;
                        if (stable >= 2) {
                            return sz;
                        }
                    } else {
                        stable = sz > 0 ? 1 : 0;
                    }
                    last = sz;
                }
            } catch (Exception ignored) {
                stable = 0;
            }
            try {
                Thread.sleep(500);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
        try {
            return Files.isRegularFile(file) ? Files.size(file) : 0;
        } catch (Exception e) {
            return 0;
        }
    }

    private static String contentTypeForExt(String ext) {
        return switch (ext.toLowerCase()) {
            case ".mp4" -> "video/mp4";
            case ".flv" -> "video/x-flv";
            case ".ts" -> "video/mp2t";
            case ".mkv" -> "video/x-matroska";
            default -> "application/octet-stream";
        };
    }

    private int resolveDurationSeconds(Map<String, Object> event, Path mediaFile) {
        Double hookDuration = positiveDouble(event.get("duration"));
        if (hookDuration == null) {
            hookDuration = positiveDouble(event.get("dvr_duration"));
        }
        if (hookDuration != null) {
            return Math.max(1, (int) Math.ceil(hookDuration));
        }

        Double durationMs = positiveDouble(event.get("duration_ms"));
        if (durationMs == null) {
            durationMs = positiveDouble(event.get("durationMs"));
        }
        if (durationMs != null) {
            return Math.max(1, (int) Math.ceil(durationMs / 1000.0d));
        }

        Double probed = probeDurationSeconds(mediaFile);
        if (probed != null) {
            return Math.max(1, (int) Math.ceil(probed));
        }
        int fallback = Math.max(1, defaultDvrDurationSeconds);
        log.warn("无法获取 DVR 真实时长，使用配置兜底 duration={}s file={}", fallback, mediaFile);
        return fallback;
    }

    private Double probeDurationSeconds(Path mediaFile) {
        Process process = null;
        try {
            process = new ProcessBuilder(
                    StringUtils.hasText(ffprobePath) ? ffprobePath : "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    mediaFile.toString())
                    .redirectErrorStream(true)
                    .start();
            if (!process.waitFor(15, TimeUnit.SECONDS)) {
                process.destroyForcibly();
                return null;
            }
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                return positiveDouble(reader.readLine());
            }
        } catch (Exception e) {
            log.debug("ffprobe DVR 时长失败 file={} error={}", mediaFile, e.getMessage());
            return null;
        } finally {
            if (process != null && process.isAlive()) {
                process.destroyForcibly();
            }
        }
    }

    private static Double positiveDouble(Object value) {
        if (value == null) {
            return null;
        }
        try {
            double parsed = value instanceof Number
                    ? ((Number) value).doubleValue()
                    : Double.parseDouble(String.valueOf(value).trim());
            return Double.isFinite(parsed) && parsed > 0 ? parsed : null;
        } catch (Exception ignored) {
            return null;
        }
    }

    private static String stringVal(Object o) {
        return o == null ? "" : String.valueOf(o).trim();
    }

    private static Integer integerVal(Object value) {
        if (value == null) {
            return null;
        }
        try {
            return value instanceof Number
                    ? ((Number) value).intValue()
                    : Integer.valueOf(String.valueOf(value).trim());
        } catch (Exception ignored) {
            return null;
        }
    }

    private static void tryDelete(Path path) {
        try {
            Files.deleteIfExists(path);
        } catch (Exception ignored) {
        }
    }
}
