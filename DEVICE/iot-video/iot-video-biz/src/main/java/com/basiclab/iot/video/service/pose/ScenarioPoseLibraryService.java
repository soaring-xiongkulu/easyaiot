package com.basiclab.iot.video.service.pose;

import com.basiclab.iot.video.dal.ScenarioPoseEntryRepository;
import com.basiclab.iot.video.dal.ScenarioPoseLibraryRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.support.RequestParams;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class ScenarioPoseLibraryService {

    private static final String POSE_BUCKET = "scenario-pose-library";

    private static final Map<String, Map<String, Object>> SCENE_TEMPLATES = Map.of(
            "fall", template(
                    "跌倒检测", "fall", "pose_fall_detected", "跌倒行为",
                    "combined", 0.72,
                    Map.of(
                            "torso_ground_angle_max", 40,
                            "head_below_hip", true,
                            "min_visible_keypoints", 8
                    )
            ),
            "climb", template(
                    "攀爬检测", "climb", "pose_climb_detected", "攀爬行为",
                    "combined", 0.70,
                    Map.of(
                            "wrists_above_shoulder", true,
                            "torso_tilt_min", 35,
                            "min_visible_keypoints", 8
                    )
            ),
            "squat", template(
                    "蹲伏检测", "squat", "pose_squat_detected", "蹲伏行为",
                    "angle", 0.68,
                    Map.of(
                            "knee_angle_max", 100,
                            "min_visible_keypoints", 8
                    )
            ),
            "hands_up", template(
                    "举手求助", "hands_up", "pose_hands_up_detected", "举手求助",
                    "angle", 0.65,
                    Map.of(
                            "wrists_above_shoulder", true,
                            "min_visible_keypoints", 6
                    )
            )
    );

    private final ScenarioPoseLibraryRepository libraryRepository;
    private final ScenarioPoseEntryRepository entryRepository;
    private final PoseAnalysisService poseAnalysisService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public List<Map<String, Object>> listLibraries(String search, Boolean isEnabled) {
        List<Map<String, Object>> libraries = libraryRepository.list(search, isEnabled);
        for (Map<String, Object> library : libraries) {
            int libraryId = (Integer) library.get("id");
            library.put("entry_count", libraryRepository.countEntries(libraryId));
        }
        return libraries;
    }

    public Map<String, Object> getLibrary(int libraryId, boolean includeEntries) {
        Map<String, Object> library = libraryRepository.findById(libraryId)
                .orElseThrow(() -> new VideoBusinessException(500, "查询失败: 场景姿态库不存在"));
        library.put("entry_count", libraryRepository.countEntries(libraryId));
        if (includeEntries) {
            library.put("entries", entryRepository.listByLibrary(libraryId, null));
        }
        return library;
    }

    public Map<String, Object> createLibrary(Map<String, Object> data) {
        String name = RequestParams.str(data, "name");
        if (name.isEmpty()) {
            throw new VideoBusinessException(400, "库名称不能为空");
        }
        String sceneCategory = orDefault(RequestParams.strOrNull(data, "scene_category"), "custom");
        double similarityThreshold = RequestParams.toDouble(data.get("similarity_threshold"), 0.72);
        String matchMode = orDefault(RequestParams.strOrNull(data, "match_mode"), "angle");
        String intentEvent = orDefault(RequestParams.strOrNull(data, "intent_event"), "pose_intent_match");
        String intentObject = orDefault(RequestParams.strOrNull(data, "intent_object"), "姿态意图");
        String alertLevel = orDefault(RequestParams.strOrNull(data, "alert_level"), "warning");
        boolean isEnabled = RequestParams.bool(data, "is_enabled", true);
        int id = libraryRepository.insert(
                name,
                libraryRepository.generateCode(),
                sceneCategory,
                toJsonTags(data.get("business_tags")),
                RequestParams.strOrNull(data, "description"),
                similarityThreshold,
                matchMode,
                intentEvent,
                intentObject,
                alertLevel,
                isEnabled
        );
        return libraryRepository.findById(id).orElseThrow();
    }

    public Map<String, Object> updateLibrary(int libraryId, Map<String, Object> data) {
        requireLibrary(libraryId);
        Map<String, Object> fields = new LinkedHashMap<>();
        if (data.containsKey("name") && data.get("name") != null) {
            String name = RequestParams.str(data, "name");
            if (name.isEmpty()) {
                throw new VideoBusinessException(400, "库名称不能为空");
            }
            fields.put("name", name);
        }
        if (data.containsKey("scene_category")) {
            fields.put("scene_category", orDefault(RequestParams.strOrNull(data, "scene_category"), "custom"));
        }
        if (data.containsKey("business_tags")) {
            fields.put("business_tags", toJsonTags(data.get("business_tags")));
        }
        if (data.containsKey("description")) {
            fields.put("description", RequestParams.strOrNull(data, "description"));
        }
        if (data.containsKey("similarity_threshold") && data.get("similarity_threshold") != null) {
            fields.put("similarity_threshold", RequestParams.toDouble(data.get("similarity_threshold"), 0.72));
        }
        if (data.containsKey("match_mode") && data.get("match_mode") != null) {
            String matchMode = RequestParams.str(data, "match_mode");
            if (!matchMode.isEmpty()) {
                fields.put("match_mode", matchMode);
            }
        }
        if (data.containsKey("intent_event") && data.get("intent_event") != null) {
            String intentEvent = RequestParams.str(data, "intent_event");
            if (!intentEvent.isEmpty()) {
                fields.put("intent_event", intentEvent);
            }
        }
        if (data.containsKey("intent_object") && data.get("intent_object") != null) {
            String intentObject = RequestParams.str(data, "intent_object");
            if (!intentObject.isEmpty()) {
                fields.put("intent_object", intentObject);
            }
        }
        if (data.containsKey("alert_level") && data.get("alert_level") != null) {
            String alertLevel = RequestParams.str(data, "alert_level");
            if (!alertLevel.isEmpty()) {
                fields.put("alert_level", alertLevel);
            }
        }
        if (data.containsKey("is_enabled")) {
            fields.put("is_enabled", RequestParams.bool(data, "is_enabled", true));
        }
        libraryRepository.update(libraryId, fields);
        return libraryRepository.findById(libraryId).orElseThrow();
    }

    public void deleteLibrary(int libraryId) {
        requireLibrary(libraryId);
        for (String imagePath : entryRepository.listImagePathsByLibrary(libraryId)) {
            deleteMinioObject(imagePath);
        }
        libraryRepository.delete(libraryId);
    }

    public List<Map<String, Object>> listEntries(int libraryId, String search) {
        requireLibrary(libraryId);
        return entryRepository.listByLibrary(libraryId, search);
    }

    public Map<String, Object> addEntry(int libraryId, String name, String remark, double conf,
                                        byte[] imageBytes, Map<String, Object> data) {
        requireLibrary(libraryId);
        String entryName = name != null && !name.isBlank() ? name.trim() : "参考姿态";
        if (imageBytes != null && imageBytes.length > 0) {
            return addEntryFromImage(libraryId, entryName, imageBytes, remark, conf);
        }
        String sourceType = RequestParams.str(data, "source_type");
        Object extraRules = data.get("extra_rules");
        if ("rule".equals(sourceType) || extraRules != null) {
            return addRuleEntry(libraryId, RequestParams.strOrNull(data, "name") != null ? name : entryName,
                    extraRules instanceof Map<?, ?> map ? castMap(map) : Map.of(),
                    remark != null ? remark : RequestParams.strOrNull(data, "remark"));
        }
        throw new VideoBusinessException(400, "请上传参考图片或提供规则条目");
    }

    public Map<String, Object> updateEntry(int entryId, Map<String, Object> data) {
        entryRepository.findById(entryId)
                .orElseThrow(() -> new VideoBusinessException(500, "更新失败: 场景姿态条目不存在"));
        Map<String, Object> fields = new LinkedHashMap<>();
        if (data.containsKey("name") && data.get("name") != null) {
            fields.put("name", RequestParams.str(data, "name"));
        }
        if (data.containsKey("remark")) {
            fields.put("remark", RequestParams.strOrNull(data, "remark"));
        }
        if (data.containsKey("is_enabled")) {
            fields.put("is_enabled", RequestParams.bool(data, "is_enabled", true));
        }
        if (data.containsKey("extra_rules") && data.get("extra_rules") != null) {
            fields.put("extra_rules", writeJson(data.get("extra_rules")));
        }
        entryRepository.update(entryId, fields);
        return entryRepository.findById(entryId).orElseThrow();
    }

    public void deleteEntry(int entryId) {
        Map<String, Object> entry = entryRepository.findById(entryId)
                .orElseThrow(() -> new VideoBusinessException(500, "删除失败: 场景姿态条目不存在"));
        deleteMinioObject((String) entry.get("image_path"));
        int libraryId = (Integer) entry.get("library_id");
        entryRepository.delete(entryId);
        libraryRepository.refreshEntryCount(libraryId);
    }

    public Map<String, Object> reExtractEntry(int entryId, double conf) {
        Map<String, Object> entry = entryRepository.findById(entryId)
                .orElseThrow(() -> new VideoBusinessException(400, "场景姿态条目不存在"));
        String imagePath = (String) entry.get("image_path");
        if (imagePath == null || imagePath.isBlank()) {
            throw new VideoBusinessException(400, "该条目无参考图片");
        }
        throw new VideoBusinessException(500, "提取失败: 图片存储不可用");
    }

    public Map<String, Object> extractPreview(byte[] imageBytes, double conf) {
        List<Map<String, Object>> persons = poseAnalysisService.extractPersons(imageBytes, conf);
        if (persons.isEmpty()) {
            return Map.of("count", 0, "persons", List.of());
        }
        List<Map<String, Object>> resultPersons = new ArrayList<>();
        for (Map<String, Object> person : persons) {
            Map<String, Object> row = new LinkedHashMap<>();
            @SuppressWarnings("unchecked")
            List<List<Object>> keypoints = (List<List<Object>>) person.get("keypoints");
            row.put("keypoints", person.get("keypoints"));
            if (keypoints != null) {
                row.put("feature_vector", PoseIntentMatcher.extractAngleFeatures(toKeypointArrays(keypoints)));
            } else {
                row.put("feature_vector", person.get("feature_vector"));
            }
            row.put("keypointCount", 17);
            row.put("poseType", "body17");
            resultPersons.add(row);
        }
        return Map.of("count", resultPersons.size(), "persons", resultPersons);
    }

    public List<Map<String, Object>> matchTest(int libraryId, byte[] imageBytes, double conf) {
        Map<String, Object> library = requireLibraryMap(libraryId);
        List<Map<String, Object>> persons = poseAnalysisService.extractPersons(imageBytes, conf);
        if (persons.isEmpty()) {
            return List.of();
        }
        List<Map<String, Object>> entries = entryRepository.listEnabledByLibrary(libraryId);
        double threshold = RequestParams.toDouble(library.get("similarity_threshold"), 0.72);
        String matchMode = library.get("match_mode") != null
                ? String.valueOf(library.get("match_mode"))
                : "angle";
        return PoseIntentMatcher.matchTest(persons, entries, matchMode, threshold);
    }

    public List<Map<String, Object>> listSceneTemplates() {
        List<Map<String, Object>> templates = new ArrayList<>();
        for (Map.Entry<String, Map<String, Object>> entry : SCENE_TEMPLATES.entrySet()) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("key", entry.getKey());
            row.putAll(entry.getValue());
            templates.add(row);
        }
        return templates;
    }

    public Map<String, Object> importSceneTemplate(int libraryId, String templateKey) {
        Map<String, Object> template = SCENE_TEMPLATES.get(templateKey);
        if (template == null) {
            throw new VideoBusinessException(400, "未知场景模板: " + templateKey);
        }
        requireLibrary(libraryId);
        Map<String, Object> fields = new LinkedHashMap<>();
        fields.put("scene_category", template.getOrDefault("scene_category", templateKey));
        fields.put("intent_event", template.get("intent_event"));
        fields.put("intent_object", template.get("intent_object"));
        fields.put("match_mode", template.getOrDefault("match_mode", "angle"));
        fields.put("similarity_threshold", template.getOrDefault("similarity_threshold", 0.72));
        libraryRepository.update(libraryId, fields);
        return addRuleEntry(
                libraryId,
                String.valueOf(template.getOrDefault("name", templateKey)),
                castMap((Map<?, ?>) template.get("extra_rules")),
                "内置模板 " + templateKey
        );
    }

    private Map<String, Object> addEntryFromImage(int libraryId, String name, byte[] imageBytes,
                                                  String remark, double conf) {
        List<Map<String, Object>> persons = poseAnalysisService.extractPersons(imageBytes, conf);
        if (persons.isEmpty()) {
            throw new VideoBusinessException(400, "未检测到人体姿态，请更换图片");
        }
        @SuppressWarnings("unchecked")
        List<List<Object>> keypoints = (List<List<Object>>) persons.get(0).get("keypoints");
        List<double[]> kpArrays = toKeypointArrays(keypoints);
        List<Double> feat = PoseIntentMatcher.extractAngleFeatures(kpArrays);
        String keypointsJson = keypoints != null ? writeJson(keypoints) : null;
        String featureVectorJson = feat != null ? writeJson(feat) : null;
        String objectName = libraryId + "/" + UUID.randomUUID().toString().replace("-", "") + ".jpg";
        String imageUrl = "/api/v1/buckets/" + POSE_BUCKET + "/objects/download?prefix=" + objectName;
        int id = entryRepository.insert(
                libraryId,
                name,
                "image",
                objectName,
                imageUrl,
                keypointsJson,
                featureVectorJson,
                null,
                remark,
                true
        );
        libraryRepository.refreshEntryCount(libraryId);
        return entryRepository.findById(id).orElseThrow();
    }

    private Map<String, Object> addRuleEntry(int libraryId, String name, Map<String, Object> extraRules, String remark) {
        int id = entryRepository.insert(
                libraryId,
                name != null && !name.isBlank() ? name.trim() : "规则模板",
                "rule",
                null,
                null,
                null,
                null,
                writeJson(extraRules),
                remark,
                true
        );
        libraryRepository.refreshEntryCount(libraryId);
        return entryRepository.findById(id).orElseThrow();
    }

    private void requireLibrary(int libraryId) {
        libraryRepository.findById(libraryId)
                .orElseThrow(() -> new VideoBusinessException(500, "查询失败: 场景姿态库不存在"));
    }

    private Map<String, Object> requireLibraryMap(int libraryId) {
        return libraryRepository.findById(libraryId)
                .orElseThrow(() -> new VideoBusinessException(500, "查询失败: 场景姿态库不存在"));
    }

    private static List<double[]> toKeypointArrays(List<List<Object>> keypoints) {
        List<double[]> out = new ArrayList<>();
        for (List<Object> kp : keypoints) {
            if (kp == null || kp.size() < 2) {
                continue;
            }
            double x = kp.get(0) instanceof Number n ? n.doubleValue() : Double.parseDouble(String.valueOf(kp.get(0)));
            double y = kp.get(1) instanceof Number n ? n.doubleValue() : Double.parseDouble(String.valueOf(kp.get(1)));
            double c = kp.size() >= 3 && kp.get(2) instanceof Number n ? n.doubleValue() : 1.0;
            out.add(new double[]{x, y, c});
        }
        return out;
    }

    private void deleteMinioObject(String objectName) {
        if (objectName == null || objectName.isBlank()) {
            return;
        }
        log.debug("skip MinIO delete for scenario pose object {}", objectName);
    }

    private String toJsonTags(Object tags) {
        try {
            return objectMapper.writeValueAsString(normalizeBusinessTags(tags));
        } catch (Exception ex) {
            return "[]";
        }
    }

    private String writeJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (Exception ex) {
            throw new VideoBusinessException(500, "JSON 序列化失败: " + ex.getMessage());
        }
    }

    private List<String> normalizeBusinessTags(Object tags) {
        if (tags == null) {
            return List.of();
        }
        List<String> items = new ArrayList<>();
        if (tags instanceof String text) {
            items.add(text);
        } else if (tags instanceof List<?> list) {
            for (Object item : list) {
                if (item != null) {
                    items.add(String.valueOf(item));
                }
            }
        } else {
            return List.of();
        }
        List<String> result = new ArrayList<>();
        for (String item : items) {
            String text = item.trim();
            if (text.isEmpty()) {
                continue;
            }
            for (String part : text.split(",")) {
                String tag = part.trim();
                if (!tag.isEmpty() && !result.contains(tag)) {
                    result.add(tag);
                }
            }
        }
        return result;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> castMap(Map<?, ?> map) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (Map.Entry<?, ?> entry : map.entrySet()) {
            result.put(String.valueOf(entry.getKey()), entry.getValue());
        }
        return result;
    }

    private static String orDefault(String value, String defaultValue) {
        return value == null || value.isBlank() ? defaultValue : value.trim();
    }

    private static Map<String, Object> template(String name, String sceneCategory, String intentEvent,
                                                String intentObject, String matchMode, double similarityThreshold,
                                                Map<String, Object> extraRules) {
        Map<String, Object> template = new LinkedHashMap<>();
        template.put("name", name);
        template.put("scene_category", sceneCategory);
        template.put("intent_event", intentEvent);
        template.put("intent_object", intentObject);
        template.put("match_mode", matchMode);
        template.put("similarity_threshold", similarityThreshold);
        template.put("extra_rules", extraRules);
        return template;
    }
}
