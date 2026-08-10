package com.basiclab.iot.video.service.record;

import com.basiclab.iot.video.dal.RecordFileRepository;
import com.basiclab.iot.video.dal.RecordSpaceRepository;
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
public class RecordVideoService {

    private final RecordFileRepository recordFileRepository;
    private final RecordSpaceRepository recordSpaceRepository;
    private final SpaceFileMetadataService spaceFileMetadataService;
    private final VideoMinioService videoMinioService;

    public List<String> listDates(int spaceId, String deviceId) {
        ensureSpace(spaceId);
        return recordFileRepository.listDates(spaceId, deviceId);
    }

    public Map<String, Object> listDayDetail(int spaceId, String date, String deviceId) {
        ensureSpace(spaceId);
        if (date == null || date.isBlank()) {
            throw new VideoBusinessException(400, "date 参数不能为空（格式 YYYY-MM-DD）");
        }
        List<Map<String, Object>> segments = recordFileRepository.listByDate(spaceId, date, deviceId);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("date", date);
        result.put("segments", segments);
        result.put("alerts", List.of());
        return result;
    }

    public Map<String, Object> resolveAlertSegment(String deviceId, int alertId) {
        return recordFileRepository.findAlertSegment(deviceId, alertId)
                .orElseThrow(() -> new VideoBusinessException(404, "未找到告警或关联录像空间"));
    }

    public Map<String, Object> listVideos(int spaceId, String deviceId, int pageNo, int pageSize,
                                          String search, String startTime, String endTime) {
        ensureSpace(spaceId);
        Timestamp start = parseDateTime(startTime);
        Timestamp end = parseDateTime(endTime);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("items", recordFileRepository.list(spaceId, deviceId, pageNo, pageSize, search, start, end));
        result.put("total", recordFileRepository.count(spaceId, deviceId, search, start, end));
        return result;
    }

    public byte[] getVideoContent(int spaceId, String objectName) {
        ensureSpace(spaceId);
        return recordFileRepository.findByObjectName(spaceId, objectName)
                .map(row -> {
                    String url = String.valueOf(row.getOrDefault("url", ""));
                    if (!url.isBlank() && !url.startsWith("/video/") && Files.isRegularFile(Path.of(url))) {
                        try {
                            return Files.readAllBytes(Path.of(url));
                        } catch (Exception e) {
                            throw new VideoBusinessException(500, "读取录像失败: " + e.getMessage());
                        }
                    }
                    throw new VideoBusinessException(400, "录像不存在: " + objectName);
                })
                .orElseThrow(() -> new VideoBusinessException(400, "录像不存在: " + objectName));
    }

    public String videoContentType(String objectName) {
        String lower = objectName.toLowerCase();
        if (lower.endsWith(".flv")) {
            return "video/x-flv";
        }
        if (lower.endsWith(".ts")) {
            return "video/mp2t";
        }
        return "video/mp4";
    }

    public String videoFilename(String objectName) {
        int idx = objectName.lastIndexOf('/');
        return idx >= 0 ? objectName.substring(idx + 1) : objectName;
    }

    public Map<String, Object> deleteVideos(int spaceId, List<String> objectNames) {
        ensureSpace(spaceId);
        if (objectNames == null || objectNames.isEmpty()) {
            throw new VideoBusinessException(400, "object_names 必须是非空数组");
        }
        Map<String, Object> space = recordSpaceRepository.findById(spaceId)
                .orElseThrow(() -> new VideoBusinessException(400, "监控录像空间不存在: ID=" + spaceId));
        String bucketName = space.get("bucket_name") != null
                ? String.valueOf(space.get("bucket_name"))
                : videoMinioService.recordBucket();
        for (String objectName : objectNames) {
            videoMinioService.removeObject(bucketName, objectName);
        }
        recordFileRepository.deleteByObjectNames(spaceId, objectNames);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("deleted_count", objectNames.size());
        result.put("failed_count", 0);
        result.put("failed_objects", List.of());
        return result;
    }

    public Map<String, Object> syncMetadata(int spaceId) {
        Map<String, Object> space = ensureSpaceMap(spaceId);
        return spaceFileMetadataService.syncRecordFilesFromMinio(space);
    }

    public Map<String, Object> cleanup(int spaceId, int saveTimeHours) {
        if (saveTimeHours <= 0) {
            throw new VideoBusinessException(400, "save_time_hours 必须大于 0");
        }
        Map<String, Object> space = ensureSpaceMap(spaceId);
        return spaceFileMetadataService.cleanupExpiredRecordFiles(space, saveTimeHours);
    }

    private Map<String, Object> ensureSpaceMap(int spaceId) {
        return recordSpaceRepository.findById(spaceId)
                .orElseThrow(() -> new VideoBusinessException(400, "监控录像空间不存在: ID=" + spaceId));
    }

    private void ensureSpace(int spaceId) {
        ensureSpaceMap(spaceId);
    }

    private static Timestamp parseDateTime(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        String text = value.trim().replace(' ', 'T');
        try {
            return Timestamp.from(Instant.parse(text));
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
