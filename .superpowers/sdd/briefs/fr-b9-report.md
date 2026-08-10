# FR-B9 Report — 推理引擎与匹配告警链去桩

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Wired Java face/plate/pose inference to callable Python CLI workers under `VIDEO/scripts/inference_workers/` (subprocess bridge). Prod matching path (`use-direct-process=false`) runs real face Milvus match / plate OCR + library DB match via workers when models/runtime exist; otherwise honest bypass/errors (not fake success). Match hits now create `face_library_match` / `plate_library_match` alerts and link `alert_id` on match records.

## Python files read (oracle)

| Path | Purpose |
|------|---------|
| `VIDEO/_retired_python_video/app/services/face_recognition_service.py` | InsightFace ONNX + Milvus match/recognize |
| `VIDEO/_retired_python_video/app/services/library_matching_service.py` | match orchestration + `face_library_match` / `plate_library_match` alerts |
| `VIDEO/_retired_python_video/app/services/face_vector_store.py` | Milvus vector search contract |
| `VIDEO/_retired_python_video/app/utils/plate_capture_service.py` | PaddleOCR plate pipeline |
| `VIDEO/_retired_python_video/app/services/scenario_pose_library_service.py` | `extract_keypoints_from_image_bytes` |
| `VIDEO/_retired_python_video/app/utils/pose_analysis.py` | YOLO pose model load |
| `VIDEO/_retired_python_video/app/services/pose_intent_matching_service.py` | pose intent alert reference |
| `VIDEO/_retired_python_video/app/services/alert_service.py` | `LIBRARY_MATCH_EVENTS` |

## Engines wired

| Domain | Java | Python worker | When unavailable |
|--------|------|---------------|------------------|
| Face | `PythonInferenceWorker` → `face_inference_cli.py` | InsightFace + Milvus `match_image_file_in_library` | `status=bypassed` + error_message |
| Plate OCR | `plate_inference_cli.py` | `detect_and_recognize_plates` | `PlateRecognitionService` throws / empty |
| Pose | `pose_inference_cli.py` | YOLO `extract_keypoints_from_image_bytes` | empty persons list |
| Match→alert | `MatchAlertService` | mirrors `_create_match_alert` | log error, record without alert_id |

## Java changes (key)

| Component | Change |
|-----------|--------|
| `PythonInferenceWorker` | subprocess JSON CLI bridge |
| `MatchAlertService` | `face_library_match` / `plate_library_match` direct persist |
| `LibraryMatchingProcessor` | face multi-library match + alert; plate OCR pre-step |
| `FaceRecognitionService` / `PlateRecognitionService` / `PoseAnalysisService` | delegate to workers |
| `FaceMatchRecordRepository` / `PlateMatchRecordRepository` | persist `alert_id` |
| `VideoProperties.Inference` | `enabled`, `pythonExecutable`, `workersDir`, `timeoutSeconds` |
| `FULL_REPLACEMENT_GAP.md` | §2.5 / §2.8 / §4 updated |
| `OnvifSoapClient.java` | fix extra `)` blocking compile (pre-existing) |

## GAP

- §2.5 face/plate behavior → **FR-B9 ✅**
- §2.8 scenario_pose extract → **FR-B9 ✅** (Python worker)
- §4 Face/Plate matching → **FR-B5 + FR-B9 ✅**
- §8 behavior stubs → patrol SSE/daemon, audio_talk ONVIF 真机 remain

## certify --phase 0

```
exit 0
```

Log: `certify-frb9-phase0.log` (oracle `:6000` not running — stale golden warnings; all cases ok/exempt)

## Concerns / remaining

1. **Prod runtime:** workers need Python env (insightface, pymilvus, paddle/onnx, ultralytics), model files (`face_rec.onnx`, plate ONNX, `yolo26n-pose.pt`), Milvus.
2. **Mini default:** `use-direct-process=true` still mock Kafka + lightweight process (certify-safe).
3. **Patrol SSE/daemon:** not in FR-B9 scope; still mini stub.
4. **Match alert MinIO image upload:** Python uploads after alert; Java direct persist stores `image_path` only (FR-B2 path).
5. **Pose match-test:** extract wired; full library similarity scoring still minimal when worker returns persons.
