package com.basiclab.iot.video.service.minio;

import com.basiclab.iot.video.dal.PlaybackRepository;
import com.basiclab.iot.video.dal.RecordFileRepository;
import com.basiclab.iot.video.dal.SnapImageRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.support.MediaDvrPathSupport;
import com.basiclab.iot.video.support.S3BucketNameSupport;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Space file metadata aligned with Python {@code space_file_metadata_service}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SpaceFileMetadataService {

    private static final ZoneId SHANGHAI = ZoneId.of("Asia/Shanghai");

    private final VideoMinioService videoMinioService;
    private final RecordFileRepository recordFileRepository;
    private final SnapImageRepository snapImageRepository;
    private final PlaybackRepository playbackRepository;

    public void upsertRecordFile(int spaceId, String deviceId, String objectName, String bucketName,
                                 String filename, long fileSize, String contentType, String url,
                                 String thumbnailUrl, int duration, Timestamp eventTime, String source) {
        recordFileRepository.upsert(
                spaceId, deviceId, objectName, bucketName, filename, fileSize, contentType,
                url, thumbnailUrl, duration, eventTime, source
        );
    }

    public void upsertSnapImage(int spaceId, String deviceId, String objectName, String bucketName,
                                String filename, long fileSize, String contentType, String url,
                                Timestamp capturedAt, Integer taskId, String source) {
        snapImageRepository.upsert(
                spaceId, deviceId, objectName, bucketName, filename, fileSize, contentType,
                url, capturedAt, taskId, source
        );
    }

    public void upsertPlayback(String deviceId, String deviceName, String filePathUrl, String objectName,
                               Timestamp eventTime, long fileSize, int duration, String thumbnailPath) {
        Optional<Map<String, Object>> existing = playbackRepository.findByDeviceAndPaths(deviceId, filePathUrl, objectName);
        Map<String, Object> fields = new LinkedHashMap<>();
        fields.put("file_path", filePathUrl);
        fields.put("thumbnail_path", thumbnailPath);
        fields.put("file_size", fileSize);
        fields.put("event_time", eventTime);
        fields.put("duration", duration > 0 ? duration : 1);
        if (existing.isPresent()) {
            playbackRepository.updateFields(((Number) existing.get().get("id")).intValue(), fields);
        } else {
            fields.put("device_id", deviceId);
            fields.put("device_name", deviceName);
            playbackRepository.insert(fields);
        }
    }

    public Map<String, Object> syncRecordFilesFromMinio(Map<String, Object> space) {
        if (!videoMinioService.isStorageEnabled()) {
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("synced_count", 0);
            result.put("skipped_count", 0);
            result.put("error_count", 0);
            result.put("message", "MinIO 未启用，跳过录像元数据同步");
            return result;
        }
        int spaceId = ((Number) space.get("id")).intValue();
        String bucketName = bucketName(space, videoMinioService.recordBucket());
        S3BucketNameSupport.requireValid(bucketName);
        String deviceId = stringField(space.get("device_id"));
        String prefix = deviceId.isBlank() ? "" : deviceId + "/";

        int synced = 0;
        int skipped = 0;
        int errors = 0;
        for (VideoMinioService.MinioObjectInfo obj : videoMinioService.listObjects(bucketName, prefix, true)) {
            String filename = obj.objectName().contains("/")
                    ? obj.objectName().substring(obj.objectName().lastIndexOf('/') + 1)
                    : obj.objectName();
            if (!MediaDvrPathSupport.isVideoFile(filename)) {
                continue;
            }
            if (recordFileRepository.existsByBucketAndObjectName(bucketName, obj.objectName())) {
                skipped++;
                continue;
            }
            try {
                String objDeviceId = obj.objectName().contains("/")
                        ? obj.objectName().substring(0, obj.objectName().indexOf('/'))
                        : (deviceId.isBlank() ? "unknown" : deviceId);
                Timestamp eventTime = Timestamp.from(
                        obj.lastModified() != null ? obj.lastModified() : Instant.now()
                );
                String url = videoMinioService.buildDownloadUrl(bucketName, obj.objectName());
                upsertRecordFile(
                        spaceId, objDeviceId, obj.objectName(), bucketName, filename,
                        obj.size(), MediaDvrPathSupport.videoContentType(filename), url,
                        null, 1, eventTime, "sync"
                );
                synced++;
            } catch (Exception e) {
                errors++;
                log.error("同步录像元数据失败 object={} error={}", obj.objectName(), e.getMessage(), e);
            }
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("synced_count", synced);
        result.put("skipped_count", skipped);
        result.put("error_count", errors);
        return result;
    }

    public Map<String, Object> syncSnapImagesFromMinio(Map<String, Object> space) {
        if (!videoMinioService.isStorageEnabled()) {
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("synced_count", 0);
            result.put("skipped_count", 0);
            result.put("error_count", 0);
            result.put("message", "MinIO 未启用，跳过抓拍元数据同步");
            return result;
        }
        int spaceId = ((Number) space.get("id")).intValue();
        String bucketName = bucketName(space, videoMinioService.snapBucket());
        S3BucketNameSupport.requireValid(bucketName);
        String deviceId = stringField(space.get("device_id"));
        String prefix = deviceId.isBlank() ? "" : deviceId + "/";

        int synced = 0;
        int skipped = 0;
        int errors = 0;
        for (VideoMinioService.MinioObjectInfo obj : videoMinioService.listObjects(bucketName, prefix, true)) {
            String filename = obj.objectName().contains("/")
                    ? obj.objectName().substring(obj.objectName().lastIndexOf('/') + 1)
                    : obj.objectName();
            String lower = filename.toLowerCase();
            if (!(lower.endsWith(".jpg") || lower.endsWith(".jpeg") || lower.endsWith(".png") || lower.endsWith(".gif"))) {
                continue;
            }
            if (snapImageRepository.existsByBucketAndObjectName(bucketName, obj.objectName())) {
                skipped++;
                continue;
            }
            try {
                String objDeviceId = obj.objectName().contains("/")
                        ? obj.objectName().substring(0, obj.objectName().indexOf('/'))
                        : (deviceId.isBlank() ? "unknown" : deviceId);
                Timestamp capturedAt = Timestamp.from(
                        obj.lastModified() != null ? obj.lastModified() : Instant.now()
                );
                String url = videoMinioService.buildDownloadUrl(bucketName, obj.objectName());
                upsertSnapImage(
                        spaceId, objDeviceId, obj.objectName(), bucketName, filename,
                        obj.size(), MediaDvrPathSupport.imageContentType(filename), url,
                        capturedAt, null, "sync"
                );
                synced++;
            } catch (Exception e) {
                errors++;
                log.error("同步抓拍元数据失败 object={} error={}", obj.objectName(), e.getMessage(), e);
            }
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("synced_count", synced);
        result.put("skipped_count", skipped);
        result.put("error_count", errors);
        return result;
    }

    public int deleteRecordFilesMetadata(String bucketName, List<String> objectNames) {
        if (objectNames == null || objectNames.isEmpty()) {
            return 0;
        }
        for (String objectName : objectNames) {
            String url = videoMinioService.buildDownloadUrl(bucketName, objectName);
            playbackRepository.deleteByFilePaths(List.of(objectName, url));
        }
        return recordFileRepository.deleteByBucketAndObjectNames(bucketName, objectNames);
    }

    public int deleteSnapImagesMetadata(String bucketName, List<String> objectNames) {
        if (objectNames == null || objectNames.isEmpty()) {
            return 0;
        }
        return snapImageRepository.deleteByBucketAndObjectNames(bucketName, objectNames);
    }

    public Map<String, Object> cleanupExpiredRecordFiles(Map<String, Object> space, int saveTimeHours) {
        int spaceId = ((Number) space.get("id")).intValue();
        String deviceId = stringField(space.get("device_id"));
        String bucketName = bucketName(space, videoMinioService.recordBucket());
        Timestamp cutoff = cutoffBefore(saveTimeHours);
        if (cutoff == null) {
            return emptyCleanupResult(true);
        }

        List<Map<String, Object>> expired = recordFileRepository.listExpiredBefore(spaceId, deviceId, cutoff);
        if (expired.isEmpty()) {
            return emptyCleanupResult(true);
        }

        if (!videoMinioService.isStorageEnabled()) {
            int deleted = recordFileRepository.deleteExpiredBefore(spaceId, deviceId, cutoff);
            Map<String, Object> result = emptyCleanupResult(false);
            result.put("processed_count", deleted);
            result.put("deleted_count", deleted);
            return result;
        }

        int processed = 0;
        int deleted = 0;
        int errors = 0;
        for (Map<String, Object> row : expired) {
            String objectName = stringField(row.get("object_name"));
            try {
                videoMinioService.removeObject(bucketName, objectName);
                String thumbUrl = stringField(row.get("thumbnail_url"));
                String thumbPrefix = extractPrefixFromUrl(thumbUrl);
                if (!thumbPrefix.isBlank()) {
                    videoMinioService.removeObject(bucketName, thumbPrefix);
                }
                deleted++;
                processed++;
            } catch (Exception e) {
                errors++;
                log.error("删除过期录像失败 object={} error={}", objectName, e.getMessage(), e);
            }
        }
        deleteRecordFilesMetadata(bucketName, expired.stream().map(r -> stringField(r.get("object_name"))).toList());

        Map<String, Object> result = emptyCleanupResult(false);
        result.put("processed_count", processed);
        result.put("deleted_count", deleted);
        result.put("error_count", errors);
        return result;
    }

    public Map<String, Object> cleanupExpiredSnapImages(Map<String, Object> space, int saveTimeHours) {
        int spaceId = ((Number) space.get("id")).intValue();
        String deviceId = stringField(space.get("device_id"));
        String bucketName = bucketName(space, videoMinioService.snapBucket());
        Timestamp cutoff = cutoffBefore(saveTimeHours);
        if (cutoff == null || deviceId.isBlank()) {
            return emptyCleanupResult(false);
        }

        List<Map<String, Object>> expired = snapImageRepository.listExpiredBefore(spaceId, deviceId, cutoff);
        if (expired.isEmpty()) {
            return emptyCleanupResult(false);
        }

        if (!videoMinioService.isStorageEnabled()) {
            int deleted = snapImageRepository.deleteExpiredBefore(spaceId, deviceId, cutoff);
            Map<String, Object> result = emptyCleanupResult(false);
            result.put("processed_count", deleted);
            result.put("deleted_count", deleted);
            return result;
        }

        int processed = 0;
        int deleted = 0;
        int errors = 0;
        for (Map<String, Object> row : expired) {
            String objectName = stringField(row.get("object_name"));
            try {
                videoMinioService.removeObject(bucketName, objectName);
                deleted++;
                processed++;
            } catch (Exception e) {
                errors++;
                log.error("删除过期抓拍失败 object={} error={}", objectName, e.getMessage(), e);
            }
        }
        deleteSnapImagesMetadata(bucketName, expired.stream().map(r -> stringField(r.get("object_name"))).toList());

        Map<String, Object> result = emptyCleanupResult(false);
        result.put("processed_count", processed);
        result.put("deleted_count", deleted);
        result.put("error_count", errors);
        return result;
    }

    private static Map<String, Object> emptyCleanupResult(boolean record) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("processed_count", 0);
        result.put("deleted_count", 0);
        result.put("archived_count", 0);
        result.put("error_count", 0);
        if (record) {
            result.put("orphan_deleted_count", 0);
            result.put("orphan_scanned_count", 0);
            result.put("orphan_error_count", 0);
        }
        return result;
    }

    private static Timestamp cutoffBefore(int saveTimeHours) {
        if (saveTimeHours <= 0) {
            return null;
        }
        ZonedDateTime cutoff = ZonedDateTime.now(SHANGHAI).minusHours(saveTimeHours);
        return Timestamp.from(cutoff.toInstant());
    }

    private static String bucketName(Map<String, Object> space, String defaultBucket) {
        String bucket = stringField(space.get("bucket_name"));
        return bucket.isBlank() ? defaultBucket : bucket;
    }

    static String extractPrefixFromUrl(String url) {
        if (url == null || url.isBlank() || !url.startsWith("/api/v1/buckets/")) {
            return url != null ? url.trim() : "";
        }
        int idx = url.indexOf("prefix=");
        if (idx < 0) {
            return "";
        }
        return java.net.URLDecoder.decode(url.substring(idx + 7), java.nio.charset.StandardCharsets.UTF_8);
    }

    private static String stringField(Object value) {
        return value == null ? "" : String.valueOf(value).trim();
    }
}
