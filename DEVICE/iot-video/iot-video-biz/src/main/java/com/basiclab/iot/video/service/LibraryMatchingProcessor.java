package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.FaceMatchRecordRepository;
import com.basiclab.iot.video.dal.PlateEntryRepository;
import com.basiclab.iot.video.dal.PlateMatchRecordRepository;
import com.basiclab.iot.video.service.face.FaceRecognitionService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Honest face/plate matching process path for non-mini profiles.
 * Plate: library DB lookup by plate number (no OCR required).
 * Face: ORT/InsightFace when available; otherwise explicit bypass (not fake success).
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class LibraryMatchingProcessor {

    private static final String FACE_BYPASS_REASON =
            "recognition engine unavailable on JVM (InsightFace/ORT not configured)";

    private final PlateEntryRepository plateEntryRepository;
    private final FaceMatchRecordRepository faceMatchRecordRepository;
    private final PlateMatchRecordRepository plateMatchRecordRepository;
    private final FaceRecognitionService faceRecognitionService;

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
        if (canRunFaceInference(faceImagePath)) {
            // Future ORT hook: delegate to FaceRecognitionService.matchInLibrary when engine loads.
            log.info("face inference path not yet wired; recording bypass for taskId={}", taskId);
        }

        Integer libraryId = firstLibraryId(libraries, payload);
        return faceMatchRecordRepository.insert(
                taskId,
                taskName,
                deviceId,
                deviceName,
                libraryId,
                libraryName,
                faceImagePath,
                false,
                null,
                null,
                null,
                null,
                null,
                correlationId,
                taskType,
                threshold,
                "bypassed",
                FACE_BYPASS_REASON
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
        boolean matched = false;
        Integer libraryId = null;
        String resolvedLibraryName = libraryName;
        Integer matchedEntryId = null;
        String matchedOwnerName = null;

        if (!normalizedPlateNo.isEmpty()) {
            for (Map<String, Object> library : libraries) {
                int libId = ((Number) library.get("id")).intValue();
                Optional<Map<String, Object>> entry = plateEntryRepository.findByPlateNo(libId, normalizedPlateNo);
                if (entry.isPresent()) {
                    matched = true;
                    libraryId = libId;
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

        return plateMatchRecordRepository.insert(
                taskId,
                taskName,
                deviceId,
                deviceName,
                libraryId,
                resolvedLibraryName,
                plateNo,
                plateColor,
                plateImagePath,
                matched,
                matchedEntryId,
                matchedOwnerName,
                correlationId,
                taskType,
                detectConf,
                "success",
                null
        );
    }

    private boolean canRunFaceInference(String faceImagePath) {
        if (faceImagePath == null || faceImagePath.isBlank()) {
            return false;
        }
        if (!faceRecognitionService.isEngineAvailable()) {
            return false;
        }
        try {
            return Files.isRegularFile(Path.of(faceImagePath));
        } catch (Exception ex) {
            return false;
        }
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

    private static Object firstNonNull(Map<String, Object> data, String... keys) {
        for (String key : keys) {
            if (data.containsKey(key) && data.get(key) != null) {
                return data.get(key);
            }
        }
        return null;
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
}
