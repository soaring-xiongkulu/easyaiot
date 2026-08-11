# Phase 2 A7 Report — Face/plate matching Kafka path (final A-series pack)

**Status:** ⛔ (缺 Milvus/InsightFace)  
**Pack:** P2-A7  
**Date:** 2026-08-11  
**Commit:** (pending) — `feat(video-java): phase2 A7 matching kafka path parity`  
**Evidence:** `logs/phase2-a7-matching.json`  
**nested_subagents:** none

## Prior packs

- A1 PASS (`2b3d483`) — alert Kafka
- A2 PASS (`e214456`) — algo RUNTIME lifecycle
- A3 PASS (`50ce091`) — ViewForward / stream-forward ffmpeg
- A4 PASS (`2be5393`) — media DVR/Snap → Kafka → MinIO
- A5 PASS (`af3f3bd`) — camera list/get/register/update
- A6 ⛔缺 sink (`f7c3276`) — post-process real HTTP enqueue (sink down)
- Phase 1 stack PASS — profile `local`, PG 15432

## What was proven

On local full stack (`profile=local`, `use-direct-process=false`):

1. **Config** — `video.matching.use-direct-process=false` in committed `application-local.yaml` + `application.yaml` default; mini mock Kafka path not used
2. **Face publish** — `POST /admin-api/video/face/matching/publish` → `MatchingKafkaProducer.publishFace` → topic `iot-face-matching` partition 48 offset 1; broker message verified
3. **Plate publish** — gateway + direct `:48096` → topic `iot-plate-matching` offsets 0/1; broker messages verified
4. **Plate process hit** — `POST .../plate/matching/process` plate `P2A7HIT01` → `matched=true`, `library_id=79`, `alert_id=4669`
5. **Plate process miss** — plate `P2A7MISS99` → `matched=false`, `status=success`
6. **Face process (honest ⛔)** — `status=bypassed`, `error_message=recognition engine unavailable (Python worker / InsightFace / Milvus not configured)`; `matched=false` — bypass not treated as success

## Oracle vs Java

| Concern | Oracle (Python) | Java candidate |
|---------|-----------------|----------------|
| Publish gate | Non-mini: real Kafka | `useDirectProcess=false` → `MatchingKafkaProducer` |
| Face topic | `iot-face-matching` | `faceMatchingTopic` default aligned |
| Plate topic | `iot-plate-matching` | `plateMatchingTopic` default aligned |
| Face process | InsightFace + Milvus | `LibraryMatchingProcessor` → `FaceRecognitionService` → `PythonInferenceWorker` |
| Plate process | `plate_entry` DB lookup | `PlateEntryRepository.findByPlateNo` aligned |
| Engine absent | Honest failure / bypass | `status=bypassed` + `error_message` (not fake match) |

## Code changes (this pack)

- `LibraryMatchingProcessor.java` — null-safe `bestMatch` when inserting `face_match_record` on unmatched/bypassed path (fixed HTTP 500 NPE blocking process evidence)

## Fixture left in DB

- Task 48 `vj_p2_face_match` (face library 6), task 49 `vj_p2_plate_match` (plate library 79)
- `plate_entry` id 21 `P2A7HIT01` in library 79 (hit test)
- `face_match_record` id 43 (bypassed), `plate_match_record` ids 38/39 (hit/miss)
- Alert id 4669 (`plate_library_match`)

## Phase 2 A-series closure

| Pack | Status |
|------|--------|
| A1 Alert Kafka | PASS |
| A2 RUNTIME | PASS |
| A3 Forward/ffmpeg | PASS |
| A4 Media MinIO | PASS |
| A5 Camera | PASS |
| A6 Post-process | ⛔缺 sink |
| A7 Matching | ⛔缺 Milvus/InsightFace |

**A-series closed.** Python Oracle retained. No COMPLETE. A1–A5 hard gate holds.

## Concerns

1. **Face engine not on Phase 1 stack** — `face_inference_cli.py` / `face_rec.onnx` / Milvus required for face hit/miss; starting inference stack would unblock re-run to PASS without code changes
2. **Plate Kafka consumer** — `plate-matching-consumer-enabled=false` by default; process API exercised directly (same `PlateMatchingService.process` as consumer)
3. **A6 + A7 blocked deps** — iot-sink `:48092` and face Milvus stack are external to current local wiring

## A1–A5 hard gate

**Still holds.** No `use-direct-process`, `use-direct-persist`, `use-stub-enqueue`, or `mini` shortcuts flipped. Profile `local` unchanged.
