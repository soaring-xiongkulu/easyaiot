package com.basiclab.iot.video.service.minio;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.support.VideoMinioBucketPolicy;
import io.minio.BucketExistsArgs;
import io.minio.ListObjectsArgs;
import io.minio.MakeBucketArgs;
import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import io.minio.RemoveObjectArgs;
import io.minio.Result;
import io.minio.SetBucketPolicyArgs;
import io.minio.StatObjectArgs;
import io.minio.UploadObjectArgs;
import io.minio.messages.Item;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;

@Slf4j
@Service
@RequiredArgsConstructor
public class VideoMinioService {

    private final VideoProperties videoProperties;
    private final AtomicReference<MinioClient> clientRef = new AtomicReference<>();

    public boolean isStorageEnabled() {
        String env = trimToNull(System.getenv("MINIO_ENABLED"));
        if (env != null) {
            return isTruthy(env);
        }
        return videoProperties.getMinio().isEnabled();
    }

    public String snapBucket() {
        return videoProperties.getMinio().getSnapBucket();
    }

    public String recordBucket() {
        return videoProperties.getMinio().getRecordBucket();
    }

    public String buildDownloadUrl(String bucketName, String objectName) {
        return "/api/v1/buckets/" + bucketName + "/objects/download?prefix="
                + URLEncoder.encode(objectName, StandardCharsets.UTF_8);
    }

    public Map<String, Object> skippedSyncResult(int totalSpaces) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("total_spaces", totalSpaces);
        result.put("created_count", 0);
        result.put("skipped_count", totalSpaces);
        result.put("error_count", 0);
        result.put("message", "MinIO 未启用，跳过空间同步（设置 video.minio.enabled=true 或 MINIO_ENABLED=true）");
        return result;
    }

    public Map<String, Object> syncDeviceDirectories(String bucketName, List<Map<String, Object>> spaces,
                                                     boolean publicReadWrite) {
        int totalSpaces = spaces.size();
        if (!isStorageEnabled()) {
            return skippedSyncResult(totalSpaces);
        }

        MinioClient client = requireClient();
        ensureBucket(client, bucketName, publicReadWrite);

        int createdCount = 0;
        int skippedCount = 0;
        int errorCount = 0;

        for (Map<String, Object> space : spaces) {
            String deviceId = stringField(space.get("device_id"));
            if (deviceId.isBlank()) {
                skippedCount++;
                continue;
            }
            try {
                String devicePrefix = deviceId + "/";
                if (hasObjects(client, bucketName, devicePrefix)) {
                    skippedCount++;
                } else if (ensureDeviceDirectory(client, bucketName, deviceId)) {
                    createdCount++;
                } else {
                    skippedCount++;
                }
            } catch (Exception e) {
                errorCount++;
                log.error("同步空间目录失败 space={} device={} error={}",
                        space.get("space_name"), deviceId, e.getMessage(), e);
            }
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("total_spaces", totalSpaces);
        result.put("created_count", createdCount);
        result.put("skipped_count", skippedCount);
        result.put("error_count", errorCount);
        return result;
    }

    public void ensureBucketForSpace(String bucketName, boolean publicReadWrite) {
        if (!isStorageEnabled()) {
            return;
        }
        ensureBucket(requireClient(), bucketName, publicReadWrite);
    }

    public void ensureDeviceDirectoryForSpace(String bucketName, String deviceId, boolean publicReadWrite) {
        if (!isStorageEnabled() || deviceId == null || deviceId.isBlank()) {
            return;
        }
        MinioClient client = requireClient();
        ensureBucket(client, bucketName, publicReadWrite);
        ensureDeviceDirectory(client, bucketName, deviceId);
    }

    public void deleteDevicePrefix(String bucketName, String deviceId) {
        if (!isStorageEnabled() || deviceId == null || deviceId.isBlank()) {
            return;
        }
        MinioClient client = requireClient();
        try {
            if (!client.bucketExists(BucketExistsArgs.builder().bucket(bucketName).build())) {
                return;
            }
            String prefix = deviceId + "/";
            for (String objectName : listObjectNames(client, bucketName, prefix, true)) {
                removeObject(client, bucketName, objectName);
            }
            log.info("删除 MinIO 设备目录: {}/{}", bucketName, prefix);
        } catch (Exception e) {
            log.warn("删除 MinIO 设备目录失败 bucket={} device={} error={}", bucketName, deviceId, e.getMessage());
        }
    }

    public void uploadFile(String bucketName, String objectName, Path localPath, String contentType,
                           boolean publicReadWrite) {
        if (!isStorageEnabled()) {
            throw new VideoBusinessException(503, "MinIO 未启用，无法上传对象（设置 video.minio.enabled=true）");
        }
        if (!Files.isRegularFile(localPath)) {
            throw new VideoBusinessException(400, "本地文件不存在: " + localPath);
        }
        MinioClient client = requireClient();
        ensureBucket(client, bucketName, publicReadWrite);
        try {
            client.uploadObject(
                    UploadObjectArgs.builder()
                            .bucket(bucketName)
                            .object(objectName)
                            .filename(localPath.toString())
                            .contentType(contentType != null ? contentType : "application/octet-stream")
                            .build()
            );
        } catch (Exception e) {
            throw new VideoBusinessException(500, "MinIO 上传失败: " + e.getMessage());
        }
    }

    public void uploadBytes(String bucketName, String objectName, byte[] data, String contentType,
                            boolean publicReadWrite) {
        if (!isStorageEnabled()) {
            throw new VideoBusinessException(503, "MinIO 未启用，无法上传对象（设置 video.minio.enabled=true）");
        }
        MinioClient client = requireClient();
        ensureBucket(client, bucketName, publicReadWrite);
        try (InputStream stream = new ByteArrayInputStream(data)) {
            client.putObject(
                    PutObjectArgs.builder()
                            .bucket(bucketName)
                            .object(objectName)
                            .stream(stream, data.length, -1)
                            .contentType(contentType != null ? contentType : "application/octet-stream")
                            .build()
            );
        } catch (Exception e) {
            throw new VideoBusinessException(500, "MinIO 上传失败: " + e.getMessage());
        }
    }

    public void removeObject(String bucketName, String objectName) {
        if (!isStorageEnabled() || objectName == null || objectName.isBlank()) {
            return;
        }
        try {
            MinioClient client = requireClient();
            if (!client.bucketExists(BucketExistsArgs.builder().bucket(bucketName).build())) {
                return;
            }
            removeObject(client, bucketName, objectName);
        } catch (Exception e) {
            log.warn("MinIO 删除对象失败 bucket={} object={} error={}", bucketName, objectName, e.getMessage());
        }
    }

    public List<MinioObjectInfo> listObjects(String bucketName, String prefix, boolean recursive) {
        if (!isStorageEnabled()) {
            return List.of();
        }
        MinioClient client = requireClient();
        try {
            if (!client.bucketExists(BucketExistsArgs.builder().bucket(bucketName).build())) {
                return List.of();
            }
            List<MinioObjectInfo> items = new ArrayList<>();
            for (String objectName : listObjectNames(client, bucketName, prefix, recursive)) {
                try {
                    var stat = client.statObject(
                            StatObjectArgs.builder().bucket(bucketName).object(objectName).build()
                    );
                    items.add(new MinioObjectInfo(
                            objectName,
                            stat.size(),
                            stat.lastModified() != null ? stat.lastModified().toInstant() : null,
                            stat.contentType()
                    ));
                } catch (Exception e) {
                    items.add(new MinioObjectInfo(objectName, 0L, null, null));
                }
            }
            return items;
        } catch (Exception e) {
            throw new VideoBusinessException(500, "MinIO 列举对象失败: " + e.getMessage());
        }
    }

    public record MinioObjectInfo(String objectName, long size, java.time.Instant lastModified, String contentType) {
    }

    /** Mirrors Python {@code storage_service.get_bucket_size} — (bytes, object count). */
    public record BucketUsage(long sizeBytes, int objectCount) {
        public static final BucketUsage EMPTY = new BucketUsage(0L, 0);
    }

    public BucketUsage getBucketUsage(String bucketName, String prefix) {
        if (!isStorageEnabled() || bucketName == null || bucketName.isBlank()) {
            return BucketUsage.EMPTY;
        }
        try {
            List<MinioObjectInfo> objects = listObjects(bucketName, prefix, true);
            long totalSize = 0L;
            for (MinioObjectInfo object : objects) {
                totalSize += object.size();
            }
            return new BucketUsage(totalSize, objects.size());
        } catch (Exception e) {
            log.warn("计算 bucket 大小失败 bucket={} prefix={} error={}", bucketName, prefix, e.getMessage());
            return BucketUsage.EMPTY;
        }
    }

    private MinioClient requireClient() {
        if (!isStorageEnabled()) {
            throw new VideoBusinessException(503,
                    "MinIO 未启用（video.minio.enabled=false / MINIO_ENABLED 未设置）");
        }
        MinioClient existing = clientRef.get();
        if (existing != null) {
            return existing;
        }
        synchronized (clientRef) {
            existing = clientRef.get();
            if (existing != null) {
                return existing;
            }
            VideoProperties.Minio cfg = videoProperties.getMinio();
            String endpoint = firstNonBlank(System.getenv("MINIO_ENDPOINT"), cfg.getEndpoint());
            String accessKey = firstNonBlank(System.getenv("MINIO_ACCESS_KEY"), cfg.getAccessKey());
            String secretKey = firstNonBlank(System.getenv("MINIO_SECRET_KEY"), cfg.getSecretKey());
            if (endpoint == null || accessKey == null || secretKey == null) {
                throw new VideoBusinessException(503,
                        "MinIO 已启用但配置不完整（需要 minio.endpoint/accessKey/secretKey 或 MINIO_* 环境变量）");
            }
            try {
                MinioClient client = MinioClient.builder()
                        .endpoint(normalizeEndpoint(endpoint, cfg.isSecure()))
                        .credentials(accessKey, secretKey)
                        .build();
                clientRef.set(client);
                log.info("MinIO 客户端已创建 endpoint={}", endpoint);
                return client;
            } catch (Exception e) {
                throw new VideoBusinessException(503, "MinIO 客户端创建失败: " + e.getMessage());
            }
        }
    }

    private void ensureBucket(MinioClient client, String bucketName, boolean publicReadWrite) {
        try {
            boolean exists = client.bucketExists(BucketExistsArgs.builder().bucket(bucketName).build());
            if (!exists) {
                client.makeBucket(MakeBucketArgs.builder().bucket(bucketName).build());
                log.info("创建 MinIO bucket: {}", bucketName);
            }
            if (publicReadWrite) {
                client.setBucketPolicy(
                        SetBucketPolicyArgs.builder()
                                .bucket(bucketName)
                                .config(VideoMinioBucketPolicy.buildPublicReadWritePolicy(bucketName))
                                .build()
                );
            }
        } catch (Exception e) {
            throw new VideoBusinessException(500, "MinIO bucket 操作失败: " + e.getMessage());
        }
    }

    private boolean ensureDeviceDirectory(MinioClient client, String bucketName, String deviceId) {
        String devicePrefix = deviceId + "/";
        if (hasObjects(client, bucketName, devicePrefix)) {
            return false;
        }
        try {
            client.putObject(
                    PutObjectArgs.builder()
                            .bucket(bucketName)
                            .object(devicePrefix)
                            .stream(new ByteArrayInputStream(new byte[0]), 0, -1)
                            .build()
            );
            log.info("创建 MinIO 设备目录: {}/{}", bucketName, devicePrefix);
            return true;
        } catch (Exception e) {
            log.warn("创建设备目录标记失败 bucket={} prefix={} error={}", bucketName, devicePrefix, e.getMessage());
            return false;
        }
    }

    private static boolean hasObjects(MinioClient client, String bucketName, String prefix) {
        try {
            Iterable<Result<Item>> results = client.listObjects(
                    ListObjectsArgs.builder().bucket(bucketName).prefix(prefix).recursive(false).build()
            );
            return results.iterator().hasNext();
        } catch (Exception e) {
            return false;
        }
    }

    private static List<String> listObjectNames(MinioClient client, String bucketName, String prefix,
                                                boolean recursive) {
        List<String> names = new ArrayList<>();
        try {
            Iterable<Result<Item>> results = client.listObjects(
                    ListObjectsArgs.builder()
                            .bucket(bucketName)
                            .prefix(prefix != null ? prefix : "")
                            .recursive(recursive)
                            .build()
            );
            for (Result<Item> result : results) {
                Item item = result.get();
                if (!item.isDir()) {
                    names.add(item.objectName());
                }
            }
        } catch (Exception e) {
            throw new VideoBusinessException(500, "MinIO 列举失败: " + e.getMessage());
        }
        return names;
    }

    private static void removeObject(MinioClient client, String bucketName, String objectName) throws Exception {
        client.removeObject(
                RemoveObjectArgs.builder().bucket(bucketName).object(objectName).build()
        );
    }

    private static String normalizeEndpoint(String endpoint, boolean secureDefault) {
        String trimmed = endpoint.trim();
        if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
            return trimmed;
        }
        return (secureDefault ? "https://" : "http://") + trimmed;
    }

    private static boolean isTruthy(String value) {
        String normalized = value.trim().toLowerCase();
        return normalized.equals("1") || normalized.equals("true") || normalized.equals("yes") || normalized.equals("on");
    }

    private static String stringField(Object value) {
        return value == null ? "" : String.valueOf(value).trim();
    }

    private static String trimToNull(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }

    private static String firstNonBlank(String... values) {
        for (String value : values) {
            if (value != null && !value.isBlank()) {
                return value.trim();
            }
        }
        return null;
    }
}
