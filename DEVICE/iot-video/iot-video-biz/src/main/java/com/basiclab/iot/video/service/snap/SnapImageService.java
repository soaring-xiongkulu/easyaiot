package com.basiclab.iot.video.service.snap;

import com.basiclab.iot.video.dal.SnapImageRepository;
import com.basiclab.iot.video.dal.SnapSpaceRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.minio.SpaceFileMetadataService;
import com.basiclab.iot.video.service.minio.VideoMinioService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class SnapImageService {

    private final SnapImageRepository snapImageRepository;
    private final SnapSpaceRepository snapSpaceRepository;
    private final SpaceFileMetadataService spaceFileMetadataService;
    private final VideoMinioService videoMinioService;

    public Map<String, Object> list(int spaceId, String deviceId, int pageNo, int pageSize, String search,
                                    String source, String startTime, String endTime) {
        snapSpaceRepository.findById(spaceId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍空间不存在: ID=" + spaceId));
        Timestamp start = parseDateTime(startTime);
        Timestamp end = parseDateTime(endTime);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("items", snapImageRepository.list(spaceId, deviceId, pageNo, pageSize, search, source, start, end));
        result.put("total", snapImageRepository.countBySpace(spaceId, deviceId, search, source));
        return result;
    }

    public byte[] getImageContent(int spaceId, String objectName) {
        snapSpaceRepository.findById(spaceId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍空间不存在: ID=" + spaceId));
        return snapImageRepository.findByObjectName(spaceId, objectName)
                .map(row -> {
                    String url = String.valueOf(row.getOrDefault("url", ""));
                    if (!url.isBlank() && !url.startsWith("/video/") && Files.isRegularFile(Path.of(url))) {
                        try {
                            return Files.readAllBytes(Path.of(url));
                        } catch (Exception e) {
                            throw new VideoBusinessException(500, "读取图片失败: " + e.getMessage());
                        }
                    }
                    throw new VideoBusinessException(400, "图片不存在: " + objectName);
                })
                .orElseThrow(() -> new VideoBusinessException(400, "图片不存在: " + objectName));
    }

    public String imageContentType(String objectName) {
        String lower = objectName.toLowerCase();
        if (lower.endsWith(".png")) {
            return "image/png";
        }
        if (lower.endsWith(".gif")) {
            return "image/gif";
        }
        return "image/jpeg";
    }

    public String imageFilename(String objectName) {
        int idx = objectName.lastIndexOf('/');
        return idx >= 0 ? objectName.substring(idx + 1) : objectName;
    }

    public Map<String, Object> deleteImages(int spaceId, List<String> objectNames) {
        snapSpaceRepository.findById(spaceId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍空间不存在: ID=" + spaceId));
        if (objectNames == null || objectNames.isEmpty()) {
            throw new VideoBusinessException(400, "object_names必须是非空数组");
        }
        Map<String, Object> space = snapSpaceRepository.findById(spaceId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍空间不存在: ID=" + spaceId));
        String bucketName = space.get("bucket_name") != null
                ? String.valueOf(space.get("bucket_name"))
                : videoMinioService.snapBucket();
        for (String objectName : objectNames) {
            videoMinioService.removeObject(bucketName, objectName);
        }
        snapImageRepository.deleteByObjectNames(spaceId, objectNames);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("deleted_count", objectNames.size());
        result.put("failed_count", 0);
        result.put("failed_objects", List.of());
        return result;
    }

    public Map<String, Object> syncMetadata(int spaceId) {
        Map<String, Object> space = snapSpaceRepository.findById(spaceId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍空间不存在: ID=" + spaceId));
        return spaceFileMetadataService.syncSnapImagesFromMinio(space);
    }

    public Map<String, Object> cleanup(int spaceId, int saveTimeHours) {
        if (saveTimeHours <= 0) {
            throw new VideoBusinessException(400, "save_time_hours 必须大于 0");
        }
        Map<String, Object> space = snapSpaceRepository.findById(spaceId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍空间不存在: ID=" + spaceId));
        return spaceFileMetadataService.cleanupExpiredSnapImages(space, saveTimeHours);
    }

    private static Timestamp parseDateTime(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        String text = value.trim().replace(" ", "T");
        try {
            Instant instant = Instant.parse(text);
            return Timestamp.from(instant);
        } catch (Exception ignored) {
        }
        try {
            LocalDateTime ldt = LocalDateTime.parse(text, DateTimeFormatter.ISO_LOCAL_DATE_TIME);
            return Timestamp.from(ldt.atZone(ZoneId.systemDefault()).toInstant());
        } catch (Exception e) {
            throw new VideoBusinessException(400, "时间格式错误: " + value);
        }
    }
}
