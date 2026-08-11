package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.FaceMatchRecordRepository;
import com.basiclab.iot.video.dal.PlateEntryRepository;
import com.basiclab.iot.video.dal.PlateMatchRecordRepository;
import com.basiclab.iot.video.service.face.FaceRecognitionService;
import com.basiclab.iot.video.service.plate.PlateRecognitionService;
import com.basiclab.iot.video.support.JsonFields;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Honest face/plate matching process path for non-mini profiles.
 * Face: Python worker (InsightFace + Milvus) when available; explicit bypass otherwise.
 * Plate: library DB lookup; OCR via Python worker when plate_no missing.
 * Match hits emit {@code face_library_match} / {@code plate_library_match} alerts.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class LibraryMatchingProcessor {

    private static final String FACE_BYPASS_REASON =
            "recognition engine unavailable (Python worker / InsightFace / Milvus not configured)";

    private final PlateEntryRepository plateEntryRepository;
    private final FaceMatchRecordRepository faceMatchRecordRepository;
    private final PlateMatchRecordRepository plateMatchRecordRepository;
    private final FaceRecognitionService faceRecognitionService;
    private final PlateRecognitionService plateRecognitionService;
    private final MatchAlertService matchAlertService;

    public Map<String, Object> processFace(
            List<Map<String, Object>> libraries,
            Map<String, Object> payload,
            long taskId,
            String faceImagePath,
            String deviceId,
            String deviceName,
            String taskName,
            String taskType,
            String correlationId,
            Float threshold,
            String libraryName
    ) {
        boolean matched = false;
        Map<String, Object> bestMatch = null;
        Map<String, Object> matchedLibrary = null;
        double bestSimilarity = -1.0;
        Object candidatesJson = null;
        Long alertId = null;
        String status = "success";
        String errorMessage = null;

        if (faceImagePath != null && !faceImagePath.isBlank() && libraries != null && !libraries.isEmpty()) {
            if (faceRecognitionService.isEngineAvailable()) {
                for (Map<String, Object> library : libraries) {
                    int libId = ((Number) library.get("id")).intValue();
                    double useThreshold = resolveFaceThreshold(threshold, library);
                    Map<String, Object> matchResult =
                            faceRecognitionService.matchImageFileInLibrary(libId, faceImagePath, useThreshold);
                    if (!Boolean.TRUE.equals(matchResult.get("matched"))) {
                        continue;
                    }
                    Map<String, Object> candidateBest = castMap(matchResult.get("best_match"));
                    double sim = toDouble(candidateBest.get("similarity"));
                    if (sim > bestSimilarity) {
                        bestSimilarity = sim;
                        bestMatch = candidateBest;
                        matchedLibrary = library;
                        candidatesJson = matchResult.get("candidates");
                    }
                }
                matched = matchedLibrary != null && bestMatch != null;
            } else {
                status = "bypassed";
                errorMessage = FACE_BYPASS_REASON;
                log.info("face inference bypass taskId={} path={}", taskId, faceImagePath);
            }
        } else if (!faceRecognitionService.isEngineAvailable()) {
            status = "bypassed";
            errorMessage = FACE_BYPASS_REASON;
        }

        if (matched && matchedLibrary != null && bestMatch != null) {
            List<String> businessTags = parseBusinessTags(matchedLibrary.get("business_tags"));
            String personName = stringOrNull(firstNonNull(bestMatch, "person_name", "label"));
            Map<String, Object> information = new LinkedHashMap<>();
            information.put("match_type", "face");
            information.put("source_event", stringOrNull(firstNonNull(payload, "sourceEvent", "source_event")));
            information.put("library_id", matchedLibrary.get("id"));
            information.put("library_name", matchedLibrary.get("name"));
            information.put("library_code", matchedLibrary.get("code"));
            information.put("matched_person_name", personName);
            information.put("matched_person_code", bestMatch.get("person_code"));
            information.put("matched_face_entry_id", bestMatch.get("face_entry_id"));
            information.put("similarity", bestMatch.get("similarity"));
            information.put("threshold", threshold);
            information.put("face_image_path", faceImagePath);
            alertId = matchAlertService.createFaceLibraryMatchAlert(
                    personName,
                    deviceId,
                    deviceName,
                    faceImagePath,
                    taskId,
                    taskName,
                    taskType,
                    businessTags,
                    correlationId,
                    information
            );
        }

        Integer libraryId = matchedLibrary != null
                ? ((Number) matchedLibrary.get("id")).intValue()
                : firstLibraryId(libraries, payload);

        return faceMatchRecordRepository.insert(
                taskId,
                taskName,
                deviceId,
                deviceName,
                libraryId,
                matchedLibrary != null ? stringOrNull(matchedLibrary.get("name")) : libraryName,
                faceImagePath,
                matched,
                bestMatch != null ? stringOrNull(firstNonNull(bestMatch, "person_name", "label")) : null,
                bestMatch != null ? stringOrNull(bestMatch.get("person_code")) : null,
                parseInteger(bestMatch != null ? bestMatch.get("face_entry_id") : null),
                bestMatch != null ? parseFloat(bestMatch.get("similarity")) : null,
                candidatesJson,
                correlationId,
                taskType,
                threshold,
                status,
                errorMessage,
                alertId
        );
    }

    public Map<String, Object> processPlate(
            List<Map<String, Object>> libraries,
            Map<String, Object> payload,
            long taskId,
            String plateNo,
            String plateColor,
            String plateImagePath,
            String deviceId,
            String deviceName,
            String taskName,
            String taskType,
            String correlationId,
            String libraryName,
            Float detectConf
    ) {
        String normalizedPlateNo = normalizePlateNo(plateNo);
        Float resolvedDetectConf = detectConf;

        if (normalizedPlateNo.isEmpty() && plateImagePath != null && !plateImagePath.isBlank()
                && plateRecognitionService.isEngineAvailable()) {
            List<Map<String, Object>> plates = plateRecognitionService.recognizePlatesFromPath(plateImagePath);
            if (!plates.isEmpty()) {
                Map<String, Object> top = plates.get(0);
                normalizedPlateNo = normalizePlateNo(stringOrNull(top.get("plate_no")));
                if (plateColor == null || plateColor.isBlank()) {
                    plateColor = stringOrNull(top.get("plate_color"));
                }
                if (resolvedDetectConf == null && top.get("detect_conf") != null) {
                    resolvedDetectConf = parseFloat(top.get("detect_conf"));
                }
            }
        }

        boolean matched = false;
        Integer libraryId = null;
        String resolvedLibraryName = libraryName;
        Integer matchedEntryId = null;
        String matchedOwnerName = null;
        Map<String, Object> matchedLibrary = null;
        Long alertId = null;

        if (!normalizedPlateNo.isEmpty()) {
            for (Map<String, Object> library : libraries) {
                int libId = ((Number) library.get("id")).intValue();
                Optional<Map<String, Object>> entry = plateEntryRepository.findByPlateNo(libId, normalizedPlateNo);
                if (entry.isPresent()) {
                    matched = true;
                    libraryId = libId;
                    matchedLibrary = library;
                    resolvedLibraryName = stringOrNull(library.get("name"));
                    matchedEntryId = ((Number) entry.get().get("id")).intValue();
                    matchedOwnerName = stringOrNull(entry.get().get("owner_name"));
                    break;
                }
            }
        }

        Integer payloadLibraryId = parseInteger(firstNonNull(payload, "libraryId", "library_id"));
        if (libraryId == null) {
            libraryId = payloadLibraryId;
        }

        if (matched && matchedLibrary != null) {
            List<String> businessTags = parseBusinessTags(matchedLibrary.get("business_tags"));
            String ownerName = matchedOwnerName != null ? matchedOwnerName : normalizedPlateNo;
            Map<String, Object> information = new LinkedHashMap<>();
            information.put("match_type", "plate");
            information.put("library_id", matchedLibrary.get("id"));
            information.put("library_name", matchedLibrary.get("name"));
            information.put("library_code", matchedLibrary.get("code"));
            information.put("plate_no", normalizedPlateNo);
            information.put("plate_color", plateColor);
            information.put("matched_owner_name", ownerName);
            information.put("matched_plate_entry_id", matchedEntryId);
            information.put("detect_conf", resolvedDetectConf);
            information.put("plate_image_path", plateImagePath);
            alertId = matchAlertService.createPlateLibraryMatchAlert(
                    normalizedPlateNo,
                    deviceId,
                    deviceName,
                    plateImagePath,
                    taskId,
                    taskName,
                    taskType,
                    businessTags,
                    correlationId,
                    information
            );
        }

        return plateMatchRecordRepository.insert(
                taskId,
                taskName,
                deviceId,
                deviceName,
                libraryId,
                resolvedLibraryName,
                plateNo != null && !plateNo.isBlank() ? plateNo : normalizedPlateNo,
                plateColor,
                plateImagePath,
                matched,
                matchedEntryId,
                matchedOwnerName,
                correlationId,
                taskType,
                resolvedDetectConf,
                "success",
                null,
                alertId
        );
    }

    private static double resolveFaceThreshold(Float threshold, Map<String, Object> library) {
        if (threshold != null) {
            return threshold.doubleValue();
        }
        Object libThreshold = library.get("similarity_threshold");
        if (libThreshold instanceof Number number) {
            return number.doubleValue();
        }
        return 0.55;
    }

    private static List<String> parseBusinessTags(Object raw) {
        List<Object> parsed = JsonFields.parseJsonList(raw != null ? String.valueOf(raw) : null);
        if (parsed.isEmpty() && raw instanceof String s && !s.isBlank()) {
            String[] parts = s.split(",");
            List<String> tags = new ArrayList<>();
            for (String part : parts) {
                String t = part.trim();
                if (!t.isEmpty()) {
                    tags.add(t);
                }
            }
            return tags;
        }
        List<String> tags = new ArrayList<>();
        for (Object item : parsed) {
            if (item != null && !String.valueOf(item).isBlank()) {
                tags.add(String.valueOf(item).trim());
            }
        }
        return tags;
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> castMap(Object value) {
        if (value instanceof Map<?, ?> map) {
            Map<String, Object> out = new LinkedHashMap<>();
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                out.put(String.valueOf(entry.getKey()), entry.getValue());
            }
            return out;
        }
        return Map.of();
    }

    private static double toDouble(Object value) {
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        try {
            return Double.parseDouble(String.valueOf(value));
        } catch (Exception ex) {
            return 0.0;
        }
    }

    private static Object firstNonNull(Map<String, Object> data, String... keys) {
        for (String key : keys) {
            if (data.containsKey(key) && data.get(key) != null) {
                return data.get(key);
            }
        }
        return null;
    }

    private static Integer firstLibraryId(List<Map<String, Object>> libraries, Map<String, Object> payload) {
        Integer fromPayload = parseInteger(firstNonNull(payload, "libraryId", "library_id"));
        if (fromPayload != null) {
            return fromPayload;
        }
        if (libraries == null || libraries.isEmpty()) {
            return null;
        }
        Object id = libraries.get(0).get("id");
        return id instanceof Number number ? number.intValue() : null;
    }

    private static String normalizePlateNo(String plateNo) {
        if (plateNo == null) {
            return "";
        }
        return plateNo.trim().toUpperCase().replace(" ", "");
    }

    private static String stringOrNull(Object value) {
        if (value == null) {
            return null;
        }
        String text = String.valueOf(value).trim();
        return text.isEmpty() ? null : text;
    }

    private static Integer parseInteger(Object value) {
        if (value == null || String.valueOf(value).isBlank()) {
            return null;
        }
        try {
            return Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException ex) {
            return null;
        }
    }

    private static Float parseFloat(Object value) {
        if (value == null || String.valueOf(value).isBlank()) {
            return null;
        }
        try {
            return Float.parseFloat(String.valueOf(value));
        } catch (NumberFormatException ex) {
            return null;
        }
    }
}
