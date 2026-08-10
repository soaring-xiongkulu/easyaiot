package com.basiclab.iot.video.service.plate;

import com.basiclab.iot.video.dal.PlateAutoEnrollRepository;
import com.basiclab.iot.video.dal.PlateEntryRepository;
import com.basiclab.iot.video.dal.PlateLibraryRepository;
import com.basiclab.iot.video.dal.PlateMatchRecordRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.support.JsonFields;
import com.basiclab.iot.video.support.RequestParams;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class PlateLibraryService {

    private final PlateLibraryRepository libraryRepository;
    private final PlateEntryRepository entryRepository;
    private final PlateAutoEnrollRepository autoEnrollRepository;
    private final PlateMatchRecordRepository matchRecordRepository;
    private final PlateRecognitionService recognitionService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public List<Map<String, Object>> listLibraries(String search, Boolean isEnabled) {
        return libraryRepository.list(search, isEnabled);
    }

    public Map<String, Object> getLibrary(int libraryId, boolean includeEntries) {
        Map<String, Object> library = libraryRepository.findById(libraryId)
                .orElseThrow(() -> new VideoBusinessException(500, "查询失败: 车牌库不存在"));
        if (includeEntries) {
            library.put("entries", entryRepository.listByLibrary(libraryId, null, 1, 1000));
        }
        return library;
    }

    public Map<String, Object> createLibrary(Map<String, Object> data) {
        String name = RequestParams.str(data, "name");
        if (name.isEmpty()) {
            throw new VideoBusinessException(400, "车牌库名称不能为空");
        }
        int id = libraryRepository.insert(
                name,
                libraryRepository.generateCode(),
                toJsonTags(data.get("business_tags")),
                RequestParams.strOrNull(data, "description"),
                RequestParams.bool(data, "is_enabled", true)
        );
        return libraryRepository.findById(id).orElseThrow();
    }

    public Map<String, Object> updateLibrary(int libraryId, Map<String, Object> data) {
        requireLibrary(libraryId);
        Map<String, Object> fields = new LinkedHashMap<>();
        if (data.containsKey("name")) {
            fields.put("name", RequestParams.str(data, "name"));
        }
        if (data.containsKey("business_tags")) {
            fields.put("business_tags", toJsonTags(data.get("business_tags")));
        }
        if (data.containsKey("description")) {
            fields.put("description", RequestParams.strOrNull(data, "description"));
        }
        if (data.containsKey("is_enabled")) {
            fields.put("is_enabled", RequestParams.bool(data, "is_enabled", true));
        }
        libraryRepository.update(libraryId, fields);
        return libraryRepository.findById(libraryId).orElseThrow();
    }

    public void deleteLibrary(int libraryId) {
        requireLibrary(libraryId);
        libraryRepository.delete(libraryId);
    }

    public Map<String, Object> listEntries(int libraryId, String search, int page, int pageSize) {
        requireLibrary(libraryId);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("data", entryRepository.listByLibrary(libraryId, search, page, pageSize));
        result.put("total", entryRepository.countByLibrary(libraryId, search));
        result.put("page", page);
        result.put("page_size", pageSize);
        return result;
    }

    public Map<String, Object> addEntry(int libraryId, String plateNo, String plateColor, String ownerName,
                                        String ownerPhone, String remark, byte[] imageBytes, boolean isEnabled) {
        requireLibrary(libraryId);
        if (plateNo == null || plateNo.isBlank()) {
            throw new VideoBusinessException(400, "plate_no 不能为空");
        }
        String imagePath = null;
        String imageUrl = null;
        if (imageBytes != null && imageBytes.length > 0) {
            recognitionService.ensurePlateEngine();
        }
        int id = entryRepository.insert(libraryId, plateNo.trim(), plateColor, ownerName, ownerPhone,
                imagePath, imageUrl, remark, isEnabled);
        libraryRepository.refreshPlateCount(libraryId);
        return entryRepository.findById(id).orElseThrow();
    }

    public Map<String, Object> updateEntry(int entryId, Map<String, Object> data, byte[] imageBytes) {
        Map<String, Object> entry = entryRepository.findById(entryId)
                .orElseThrow(() -> new VideoBusinessException(400, "车牌条目不存在"));
        Map<String, Object> fields = new LinkedHashMap<>();
        if (data.containsKey("plate_no")) {
            fields.put("plate_no", RequestParams.str(data, "plate_no"));
        }
        if (data.containsKey("plate_color")) {
            fields.put("plate_color", RequestParams.strOrNull(data, "plate_color"));
        }
        if (data.containsKey("owner_name")) {
            fields.put("owner_name", RequestParams.strOrNull(data, "owner_name"));
        }
        if (data.containsKey("owner_phone")) {
            fields.put("owner_phone", RequestParams.strOrNull(data, "owner_phone"));
        }
        if (data.containsKey("remark")) {
            fields.put("remark", RequestParams.strOrNull(data, "remark"));
        }
        if (data.containsKey("is_enabled")) {
            fields.put("is_enabled", RequestParams.bool(data, "is_enabled", true));
        }
        if (imageBytes != null && imageBytes.length > 0) {
            recognitionService.ensurePlateEngine();
        }
        entryRepository.update(entryId, fields);
        libraryRepository.refreshPlateCount((Integer) entry.get("library_id"));
        return entryRepository.findById(entryId).orElseThrow();
    }

    public void deleteEntry(int entryId) {
        Map<String, Object> entry = entryRepository.findById(entryId)
                .orElseThrow(() -> new VideoBusinessException(500, "删除失败: 车牌条目不存在"));
        entryRepository.delete(entryId);
        libraryRepository.refreshPlateCount((Integer) entry.get("library_id"));
    }

    public Map<String, Object> batchDeleteEntries(List<Integer> entryIds) {
        int deleted = entryRepository.batchDelete(entryIds);
        return Map.of("deleted", deleted);
    }

    public List<Map<String, Object>> previewNormalize(int libraryId, double threshold) {
        requireLibrary(libraryId);
        return List.of();
    }

    public Map<String, Object> mergeNormalize(int libraryId, int targetEntryId, List<Integer> sourceEntryIds) {
        requireLibrary(libraryId);
        entryRepository.findById(targetEntryId)
                .orElseThrow(() -> new VideoBusinessException(400, "target_entry_id 不存在"));
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("merged_entries", sourceEntryIds != null ? sourceEntryIds.size() : 0);
        return result;
    }

    public Map<String, Object> mergeAllNormalize(int libraryId, double threshold) {
        requireLibrary(libraryId);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("merged_groups", 0);
        result.put("merged_entries", 0);
        return result;
    }

    public Map<String, Object> getAutoEnroll(int libraryId) {
        requireLibrary(libraryId);
        return autoEnrollRepository.findByLibrary(libraryId)
                .map(autoEnrollRepository::enrichDeviceNames)
                .orElse(null);
    }

    public Map<String, Object> saveAutoEnroll(int libraryId, Map<String, Object> data) {
        requireLibrary(libraryId);
        List<Object> deviceIds = RequestParams.list(data, "device_ids", "deviceIds");
        int duration = RequestParams.toInt(RequestParams.first(data, "duration_minutes", "durationMinutes"), 60);
        int interval = RequestParams.toInt(RequestParams.first(data, "capture_interval_sec", "captureIntervalSec"), 5);
        try {
            autoEnrollRepository.upsert(libraryId, objectMapper.writeValueAsString(deviceIds), duration, interval);
        } catch (Exception ex) {
            throw new VideoBusinessException(500, "保存失败: " + ex.getMessage());
        }
        return getAutoEnroll(libraryId);
    }

    public Map<String, Object> startAutoEnroll(int libraryId) {
        if (getAutoEnroll(libraryId) == null) {
            throw new VideoBusinessException(400, "请先配置自动录入参数");
        }
        autoEnrollRepository.updateRunning(libraryId, true);
        return getAutoEnroll(libraryId);
    }

    public Map<String, Object> stopAutoEnroll(int libraryId) {
        autoEnrollRepository.updateRunning(libraryId, false);
        return getAutoEnroll(libraryId);
    }

    public Map<String, Object> matchInLibrary(int libraryId, String plateNo) {
        requireLibrary(libraryId);
        if (plateNo == null || plateNo.isBlank()) {
            throw new VideoBusinessException(400, "plate_no 不能为空");
        }
        Map<String, Object> result = new LinkedHashMap<>();
        entryRepository.findByPlateNo(libraryId, plateNo).ifPresentOrElse(entry -> {
            result.put("matched", true);
            result.put("entry", entry);
        }, () -> result.put("matched", false));
        return result;
    }

    public Map<String, Object> listMatchRecords(int page, int pageSize, Integer libraryId, String deviceId,
                                                Boolean matched, String correlationId) {
        return matchRecordRepository.listRecords(page, pageSize, libraryId, deviceId, matched, correlationId);
    }

    private void requireLibrary(int libraryId) {
        libraryRepository.findById(libraryId)
                .orElseThrow(() -> new VideoBusinessException(500, "查询失败: 车牌库不存在"));
    }

    private String toJsonTags(Object raw) {
        if (raw == null) {
            return "[]";
        }
        try {
            if (raw instanceof String s) {
                if (s.isBlank()) {
                    return "[]";
                }
                return objectMapper.writeValueAsString(JsonFields.parseJsonList(s));
            }
            return objectMapper.writeValueAsString(raw);
        } catch (Exception ex) {
            return "[]";
        }
    }
}
