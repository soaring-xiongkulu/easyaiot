# FR-B45 Report — Plate matching→alert + Kafka 消费 + reExtract MinIO

**Status:** DONE (not COMPLETE)  
**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Python-first cites

| Topic | Source | Behavior |
|-------|--------|----------|
| Plate match process | `library_matching_service.py` L303-382 | `process_plate_matching_message` → `plate_library_match` |
| Alert create | `library_matching_service.py` L110-152 | `_create_match_alert` |
| Plate Kafka publish | `plate_matching_kafka_service.py` L23-88 | `build_plate_matching_message` + `send_plate_matching_to_kafka` |
| Plate matching API | `plate.py` L359-399 | `matching/publish` + `matching/process` |
| Pose re_extract | `scenario_pose.py` L155-159 | `POST /entries/{id}/re-extract` |
| Pose re_extract svc | `scenario_pose_library_service.py` L314-336 | MinIO `get_object` → YOLO re-extract |

## Evidence

### Plate direct alert (`logs/fr-b45-plate-matching-alert-latest.json`)

| Probe | HTTP | code | ok | Notes |
|-------|------|------|-----|-------|
| `plate_matching_hit_alert` | 200 | 0 | **true** | matched=true, alert_id set, event=`plate_library_match` via `/video/alert/correlation` |

**Summary:** **1/1** pass. Profile: `local,fr-b45-soak`.

### Plate Kafka consume (`logs/fr-b45-plate-kafka-alert-latest.json`)

| Probe | publish | ok | alert_id | Notes |
|-------|---------|-----|----------|-------|
| `plate_kafka_publish_consume_alert` | 0 | **true** | 4667 | `POST /video/plate/matching/publish` → `PlateMatchingKafkaConsumerRunner` → `plate_library_match` |

**Summary:** **1/1** pass. Consumer group: `video-plate-matching-frb45`. Java log: `Plate matching Kafka consumed ... matched=true alert_id=4667`.

### Pose re_extract (`logs/fr-b45-re-extract-latest.json`)

| Probe | ok | Notes |
|-------|-----|-------|
| `pose_re_extract_minio` | **honest_ex** | YOLO worker unavailable at probe time (`未检测到人体姿态`); MinIO load code wired in Java |

**Summary:** code fix landed; runtime E2E blocked by YOLO (same regression as `fr-b44-pose` at probe time).

## Java changes (FR-B45)

1. **`PlateMatchingKafkaConsumerRunner`** — in-process consumer when `use-direct-process=false` + `plate-matching-consumer-enabled=true`; calls `PlateMatchingService.process`.
2. **`ScenarioPoseLibraryService.reExtractEntry`** — MinIO `readBytes` + local file fallback; `addEntryFromImage` uploads to MinIO when enabled.
3. **`VideoMinioService`** — `readBytes`, `bucketExists`.
4. **`VideoProperties.Matching`** — consumer group/topic/poll config.
5. **`application-fr-b45-soak.yaml`** — MinIO + matching consumer overlay.

## Infrastructure (local)

- **Server:** `local,fr-b45-soak` + `-Dvideo.runtime.repo-root=F:/acme/.worktrees/video-java`
- **Kafka:** `127.0.0.1:9092`, topic `iot-plate-matching`, group `video-plate-matching-frb45`
- **Fixture:** `seed_fr_b45_fixture.py` → `frb45_device` task_id

## phase0

`python tools/video_java/certify.py --phase 0` → **5/5 PASS**  
Log: `logs/certify-frb45-phase0.log`

## Remaining / concerns

- **NOT COMPLETE** — prod plate matching Kafka + reExtract soak still open.
- reExtract runtime E2E needs YOLO worker + `yolo26n-pose.pt` (honest_ex at probe time).
- `/video/alert/page` filters alerts without `image_url`; plate match alerts verified via `/video/alert/correlation`.
- Shared topic `iot-plate-matching` may have backlog; dedicated consumer group mitigates for local E2E.

## Files touched (FR-B45 only)

- `PlateMatchingKafkaConsumerRunner.java`, `ScenarioPoseLibraryService.java`, `VideoMinioService.java`, `VideoProperties.java`
- `application-fr-b45-soak.yaml`
- `tools/video_java/seed_fr_b45_fixture.py`, `fr_b45_*_probe.py`
- `logs/fr-b45-*`, `logs/certify-frb45-phase0.log`
- `docs/video-java/PROD_SOAK_CHECKLIST.md`, `HANDOFF.md`, `.superpowers/sdd/progress.md`
- `fr-b45-report.md`
