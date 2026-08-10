# FR-B5 Report — Face/Plate 真 Kafka + 诚实 process

**STATUS:** DONE  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Implemented real Kafka publish path for face/plate matching when `video.matching.use-direct-process=false`, aligned with retired Python topics and message shape. Process path is honest: plate matching performs real library DB lookup by plate number; face matching records explicit `status=bypassed` with reason when JVM ORT/InsightFace is unavailable (not fake `success` without work). Mini/local profile keeps mock Kafka + lightweight process for certify safety.

## Python files read (oracle)

| Path | Purpose |
|------|---------|
| `VIDEO/_retired_python_video/app/services/face_matching_kafka_service.py` | topic `iot-face-matching`, message build, producer send |
| `VIDEO/_retired_python_video/app/services/plate_matching_kafka_service.py` | topic `iot-plate-matching`, message build, producer send |
| `VIDEO/_retired_python_video/app/services/face_recognition_service.py` | InsightFace/ArcFace ONNX + Milvus inference contract |
| `VIDEO/_retired_python_video/app/services/library_matching_service.py` | `process_face_matching_message` / `process_plate_matching_message` |
| `VIDEO/_retired_python_video/app/blueprints/face.py` | publish/process HTTP surface |
| `VIDEO/_retired_python_video/app/blueprints/plate.py` | publish/process HTTP surface |

## Java changes

| Component | Change |
|-----------|--------|
| `MatchingKafkaProducer` | Kafka produce to `iot-face-matching` / `iot-plate-matching` (reuses alert `KafkaTemplate`) |
| `LibraryMatchingProcessor` | prod process: plate DB match; face explicit bypass |
| `FaceMatchingService` / `PlateMatchingService` | wire Kafka producer; branch mini vs prod process |
| `FaceMatchRecordRepository` / `PlateMatchRecordRepository` | status + error_message + match detail columns |
| `VideoProperties.Matching` | `faceMatchingTopic`, `plateMatchingTopic` |
| `FaceRecognitionService.isEngineAvailable()` | ORT hook point (currently false) |
| `application-mini.yaml` | topic defaults documented |
| `FULL_REPLACEMENT_GAP.md` | §4 Face/Plate row ✅ |

## Inference choice

**Explicit bypass (documented):** JVM stack has no ONNX Runtime / InsightFace / Milvus integration yet. Face process records `status=bypassed` + `error_message` instead of pretending recognition ran. Plate uses **library DB lookup** (honest match without OCR). Future ORT wiring should set `FaceRecognitionService.isEngineAvailable()` and delegate from `LibraryMatchingProcessor`.

## Short contract

| Config | publish | process |
|--------|---------|---------|
| `use-direct-process=true` (mini default) | mock kafka success | mini stub record (`matched=false`, `status=success`) |
| `use-direct-process=false` + broker up | real Kafka produce | plate: DB library match; face: `status=bypassed` |
| `use-direct-process=false` + broker down | HTTP 500 Kafka 投递失败 | n/a |

## GAP §4

`Face/Plate matching` → **resolved by FR-B5** (code paths exist; local/mini default mock; prod needs broker + `use-direct-process=false`)

## certify --phase 0

```
exit 0
```

## Concerns / follow-ups

1. **Prod:** needs Kafka broker + iot-sink consumers on `iot-face-matching` / `iot-plate-matching`.
2. **Face ORT:** Milvus vector search + `face_rec.onnx` not ported; bypass is intentional until ORT dependency added.
3. **Plate OCR:** `recognize/image` still throws; matching-by-plateNo works when plate number is already known (Kafka path).
4. **Match alerts:** Python creates `face_library_match` / `plate_library_match` alerts on hit; Java prod path not yet chaining alert creation.
