package com.basiclab.iot.video.service.face;

import com.basiclab.iot.video.dal.FaceAutoEnrollRepository;
import com.basiclab.iot.video.dal.FaceEntryRepository;
import com.basiclab.iot.video.dal.FaceLibraryRepository;
import com.basiclab.iot.video.dal.FaceMatchRecordRepository;
import com.basiclab.iot.video.dal.FacePersonRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.minio.VideoMinioService;
import com.basiclab.iot.video.support.JsonFields;
import com.basiclab.iot.video.support.RequestParams;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class FaceLibraryService {

    private final FaceLibraryRepository libraryRepository;
    private final FaceEntryRepository entryRepository;
    private final FacePersonRepository personRepository;
    private final FaceAutoEnrollRepository autoEnrollRepository;
    private final FaceMatchRecordRepository matchRecordRepository;
    private final FaceRecognitionService recognitionService;
    private final VideoMinioService videoMinioService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    private static final String DEFAULT_FACE_BUCKET = "face-library";

    public List<Map<String, Object>> listLibraries(String search, Boolean isEnabled) {
        return libraryRepository.list(search, isEnabled).stream().map(this::enrichLibrary).toList();
    }

    public Map<String, Object> getLibrary(int libraryId, boolean includeEntries) {
        Map<String, Object> library = libraryRepository.findById(libraryId)
                .map(this::enrichLibrary)
                .orElseThrow(() -> new VideoBusinessException(404, "查询失败: 人脸库不存在"));
        if (includeEntries) {
            library.put("entries", entryRepository.listByLibrary(libraryId, null));
        }
        return library;
    }

    public Map<String, Object> createLibrary(Map<String, Object> data) {
        String name = RequestParams.str(data, "name");
        if (name.isEmpty()) {
            throw new VideoBusinessException(400, "人脸库名称不能为空");
        }
        String code = libraryRepository.generateCode();
        String tagsJson = toJsonTags(data.get("business_tags"));
        int id = libraryRepository.insert(
                name,
                code,
                tagsJson,
                RequestParams.strOrNull(data, "description"),
                RequestParams.toDouble(data.get("similarity_threshold"), 0.55),
                RequestParams.bool(data, "is_enabled", true)
        );
        return getLibrary(id, false);
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
        if (data.containsKey("similarity_threshold")) {
            fields.put("similarity_threshold", RequestParams.toDouble(data.get("similarity_threshold"), 0.55));
        }
        if (data.containsKey("is_enabled")) {
            fields.put("is_enabled", RequestParams.bool(data, "is_enabled", true));
        }
        libraryRepository.update(libraryId, fields);
        return getLibrary(libraryId, false);
    }

    public void deleteLibrary(int libraryId) {
        requireLibrary(libraryId);
        libraryRepository.delete(libraryId);
    }

    public List<Map<String, Object>> listEntries(int libraryId, String search) {
        requireLibrary(libraryId);
        return entryRepository.listByLibrary(libraryId, search);
    }

    public Map<String, Object> listPersons(int libraryId, String search, int page, int pageSize) {
        requireLibrary(libraryId);
        List<Map<String, Object>> items = personRepository.listByLibrary(libraryId, search, page, pageSize).stream()
                .map(p -> personRepository.enrichPerson(p, false))
                .toList();
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("data", items);
        result.put("total", personRepository.countByLibrary(libraryId, search));
        result.put("page", page);
        result.put("page_size", pageSize);
        return result;
    }

    public Map<String, Object> getPerson(int personId, boolean includeEntries) {
        Map<String, Object> person = personRepository.findById(personId)
                .orElseThrow(() -> new VideoBusinessException(404, "查询失败: 人员不存在"));
        return personRepository.enrichPerson(person, includeEntries);
    }

    public void deletePerson(int personId) {
        personRepository.findById(personId)
                .orElseThrow(() -> new VideoBusinessException(500, "删除失败: 人员不存在"));
        int libraryId = (Integer) personRepository.findById(personId).get().get("library_id");
        personRepository.delete(personId);
        libraryRepository.refreshFaceCount(libraryId);
    }

    public Map<String, Object> batchDeletePersons(List<Integer> personIds) {
        int deleted = personRepository.batchDelete(personIds);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("deleted", deleted);
        return result;
    }

    public Map<String, Object> setPersonCover(int personId, int entryId) {
        Map<String, Object> person = personRepository.findById(personId)
                .orElseThrow(() -> new VideoBusinessException(400, "人员不存在"));
        Map<String, Object> entry = entryRepository.findById(entryId)
                .orElseThrow(() -> new VideoBusinessException(400, "人脸条目不存在"));
        Object entryPersonId = entry.get("person_id");
        if (entryPersonId == null || personId != ((Number) entryPersonId).intValue()) {
            throw new VideoBusinessException(400, "封面条目不属于该人员");
        }
        Map<String, Object> fields = new LinkedHashMap<>();
        fields.put("cover_entry_id", entryId);
        personRepository.update(personId, fields);
        return getPerson(personId, false);
    }

    public Map<String, Object> addEntry(int libraryId, String personName, byte[] imageBytes, String personCode,
                                        String remark, Integer personId, boolean isEnabled) {
        requireLibrary(libraryId);
        if (personName.isEmpty()) {
            throw new VideoBusinessException(400, "person_name 不能为空");
        }
        if (imageBytes == null || imageBytes.length == 0) {
            throw new VideoBusinessException(400, "请上传文件字段 file");
        }
        // Python face_library_service.add_entry L319-328: extract_and_crop_largest_face hard-fail.
        FaceRecognitionService.FaceCropResult cropResult = recognitionService.extractCropForEntry(imageBytes);
        UploadedFaceImage uploaded = uploadFaceImage(libraryId, cropResult.cropJpegBytes());

        if (personId == null) {
            personId = personRepository.insert(libraryId, personName, personCode, null, isEnabled);
        }
        int entryId = entryRepository.insert(
                libraryId,
                personId,
                personName,
                personCode,
                uploaded.objectName(),
                uploaded.imageUrl(),
                remark,
                isEnabled
        );
        String milvusId = recognitionService.addFaceToLibrary(
                libraryId,
                entryId,
                personName,
                personCode,
                cropResult.embedding()
        );
        if (milvusId != null) {
            entryRepository.update(entryId, Map.of("milvus_id", milvusId));
        }
        personRepository.refreshFaceCount(personId);
        libraryRepository.refreshFaceCount(libraryId);
        return entryRepository.findById(entryId).orElseThrow();
    }

    public Map<String, Object> addEntriesBatch(int libraryId, String personName, List<byte[]> imageFiles,
                                               String personCode, String remark, Integer personId, boolean isEnabled) {
        if (imageFiles == null || imageFiles.isEmpty()) {
            throw new VideoBusinessException(400, "上传文件不能为空");
        }
        int success = 0;
        int failed = 0;
        List<Map<String, Object>> entries = new ArrayList<>();
        for (byte[] bytes : imageFiles) {
            try {
                Map<String, Object> entry = addEntry(libraryId, personName, bytes, personCode, remark, personId, isEnabled);
                entries.add(entry);
                personId = (Integer) entry.get("person_id");
                success++;
            } catch (VideoBusinessException ex) {
                failed++;
            }
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("success_count", success);
        result.put("failed_count", failed);
        result.put("entries", entries);
        return result;
    }

    public Map<String, Object> updateEntry(int entryId, byte[] imageBytes, Map<String, Object> data) {
        Map<String, Object> entry = entryRepository.findById(entryId)
                .orElseThrow(() -> new VideoBusinessException(400, "人脸条目不存在"));
        int libraryId = (Integer) entry.get("library_id");
        Map<String, Object> fields = new LinkedHashMap<>();
        if (data.containsKey("person_name")) {
            fields.put("person_name", RequestParams.str(data, "person_name"));
        }
        if (data.containsKey("person_code")) {
            fields.put("person_code", RequestParams.strOrNull(data, "person_code"));
        }
        if (data.containsKey("remark")) {
            fields.put("remark", RequestParams.strOrNull(data, "remark"));
        }
        if (data.containsKey("is_enabled")) {
            fields.put("is_enabled", RequestParams.bool(data, "is_enabled", true));
        }
        // Python face_library_service.update_entry L445-476: delete old MinIO, re-extract, Milvus upsert.
        if (imageBytes != null && imageBytes.length > 0) {
            FaceRecognitionService.FaceCropResult cropResult = recognitionService.extractCropForEntry(imageBytes);
            deleteFaceImageObject((String) entry.get("image_path"));
            UploadedFaceImage uploaded = uploadFaceImage(libraryId, cropResult.cropJpegBytes());
            fields.put("image_path", uploaded.objectName());
            fields.put("image_url", uploaded.imageUrl());
            String oldMilvusId = (String) entry.get("milvus_id");
            recognitionService.deleteFaceByMilvusId(oldMilvusId);
            String personName = fields.containsKey("person_name")
                    ? (String) fields.get("person_name")
                    : (String) entry.get("person_name");
            String personCode = fields.containsKey("person_code")
                    ? (String) fields.get("person_code")
                    : (String) entry.get("person_code");
            String milvusId = recognitionService.addFaceToLibrary(
                    libraryId,
                    entryId,
                    personName,
                    personCode,
                    cropResult.embedding()
            );
            if (milvusId != null) {
                fields.put("milvus_id", milvusId);
            }
        }
        entryRepository.update(entryId, fields);
        Integer personId = (Integer) entry.get("person_id");
        if (personId != null) {
            syncPersonCoverFields(personId, entryId, data);
            personRepository.refreshFaceCount(personId);
        }
        libraryRepository.refreshFaceCount(libraryId);
        return entryRepository.findById(entryId).orElseThrow();
    }

    public void deleteEntry(int entryId) {
        Map<String, Object> entry = entryRepository.findById(entryId)
                .orElseThrow(() -> new VideoBusinessException(500, "删除失败: 人脸条目不存在"));
        entryRepository.delete(entryId);
        Integer personId = (Integer) entry.get("person_id");
        if (personId != null) {
            personRepository.refreshFaceCount(personId);
        }
        libraryRepository.refreshFaceCount((Integer) entry.get("library_id"));
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
        String prefix = RequestParams.str(data, "person_name_prefix", "personNamePrefix");
        if (prefix.isEmpty()) {
            prefix = "摄像头自动录入";
        }
        try {
            autoEnrollRepository.upsert(libraryId, objectMapper.writeValueAsString(deviceIds), duration, interval, prefix);
        } catch (Exception ex) {
            throw new VideoBusinessException(500, "保存失败: " + ex.getMessage());
        }
        return getAutoEnroll(libraryId);
    }

    public Map<String, Object> startAutoEnroll(int libraryId) {
        Map<String, Object> task = getAutoEnroll(libraryId);
        if (task == null) {
            throw new VideoBusinessException(400, "请先配置自动录入参数");
        }
        @SuppressWarnings("unchecked")
        List<Object> deviceIds = (List<Object>) task.getOrDefault("device_ids", List.of());
        if (deviceIds.isEmpty()) {
            throw new VideoBusinessException(400, "请至少绑定一个摄像头后再开启");
        }
        autoEnrollRepository.updateRunning(libraryId, true);
        return getAutoEnroll(libraryId);
    }

    public Map<String, Object> stopAutoEnroll(int libraryId) {
        Map<String, Object> task = getAutoEnroll(libraryId);
        if (task == null) {
            throw new VideoBusinessException(400, "自动录入任务不存在");
        }
        autoEnrollRepository.updateRunning(libraryId, false);
        return getAutoEnroll(libraryId);
    }

    public List<Map<String, Object>> previewNormalize(int libraryId, double threshold) {
        requireLibrary(libraryId);
        return List.of();
    }

    public Map<String, Object> mergeNormalize(int libraryId, Map<String, Object> data) {
        requireLibrary(libraryId);
        Object targetPersonId = RequestParams.first(data, "target_person_id", "targetPersonId");
        Object targetEntryId = RequestParams.first(data, "target_entry_id", "targetEntryId");
        if (targetPersonId == null && targetEntryId == null) {
            throw new VideoBusinessException(400, "target_person_id 或 target_entry_id 不能为空");
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("merged", 0);
        return result;
    }

    public Map<String, Object> mergeAllNormalize(int libraryId, double threshold) {
        requireLibrary(libraryId);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("merged_groups", 0);
        result.put("merged_persons", 0);
        return result;
    }

    public Map<String, Object> matchInLibrary(int libraryId, byte[] imageBytes, Double threshold, int topK) {
        requireLibrary(libraryId);
        if (imageBytes == null || imageBytes.length == 0) {
            throw new VideoBusinessException(400, "请上传文件字段 file");
        }
        return recognitionService.matchInLibrary(libraryId, imageBytes, threshold, topK);
    }

    public Map<String, Object> listMatchRecords(int page, int pageSize, Integer libraryId, String deviceId,
                                                Boolean matched, String correlationId) {
        return matchRecordRepository.listRecords(page, pageSize, libraryId, deviceId, matched, correlationId);
    }

    private Map<String, Object> enrichLibrary(Map<String, Object> library) {
        Map<String, Object> data = new LinkedHashMap<>(library);
        int libraryId = (Integer) library.get("id");
        data.put("face_count", entryRepository.listByLibrary(libraryId, null).size());
        data.put("person_count", libraryRepository.countPersons(libraryId));
        return data;
    }

    private void requireLibrary(int libraryId) {
        libraryRepository.findById(libraryId)
                .orElseThrow(() -> new VideoBusinessException(404, "查询失败: 人脸库不存在"));
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

    /** Python face_library_service._upload_face_image L62-68 → bucket face-library. */
    private UploadedFaceImage uploadFaceImage(int libraryId, byte[] imageBytes) {
        String suffix = "jpg";
        String objectName = libraryId + "/" + UUID.randomUUID().toString().replace("-", "") + "." + suffix;
        String bucket = faceImageBucket();
        if (!videoMinioService.isStorageEnabled()) {
            return new UploadedFaceImage(null, null);
        }
        videoMinioService.uploadBytes(bucket, objectName, imageBytes, "image/" + suffix, false);
        return new UploadedFaceImage(objectName, videoMinioService.buildDownloadUrl(bucket, objectName));
    }

    /** Python face_library_service.update_entry L432-439 → sync person when cover entry. */
    private void syncPersonCoverFields(int personId, int entryId, Map<String, Object> data) {
        personRepository.findById(personId).ifPresent(person -> {
            Integer coverEntryId = (Integer) person.get("cover_entry_id");
            if (coverEntryId == null || coverEntryId != entryId) {
                return;
            }
            Map<String, Object> personFields = new LinkedHashMap<>();
            if (data.containsKey("person_name")) {
                personFields.put("person_name", RequestParams.str(data, "person_name"));
            }
            if (data.containsKey("person_code")) {
                personFields.put("person_code", RequestParams.strOrNull(data, "person_code"));
            }
            if (!personFields.isEmpty()) {
                personRepository.update(personId, personFields);
            }
        });
    }

    /** Python face_library_service._delete_minio_object L71-79 (best-effort). */
    private void deleteFaceImageObject(String objectName) {
        if (objectName == null || objectName.isBlank()) {
            return;
        }
        if (!videoMinioService.isStorageEnabled()) {
            return;
        }
        try {
            videoMinioService.removeObject(faceImageBucket(), objectName);
        } catch (Exception ex) {
            // Python _delete_minio_object L78-79: best-effort, log warning only.
        }
    }

    private static String faceImageBucket() {
        String env = System.getenv("FACE_IMAGE_BUCKET");
        return env != null && !env.isBlank() ? env.trim() : DEFAULT_FACE_BUCKET;
    }

    private record UploadedFaceImage(String objectName, String imageUrl) {}
}
