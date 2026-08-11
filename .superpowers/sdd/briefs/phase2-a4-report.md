# Phase 2 A4 Report — Media DVR/Snap → Kafka → MinIO (handoff for A5)

**Status:** PASS  
**Pack:** P2-A4  
**Date:** 2026-08-11  
**Commit:** `a00af3d` — `feat(video-java): phase2 A4 media minio kafka parity`  
**Evidence:** `logs/phase2-a4-media-minio.json`  
**nested_subagents:** none

## Prior packs

- A1 PASS (`2b3d483`) — alert Kafka; fixture device `frb26_device`, task 61
- A2 PASS (`e214456`) — algo RUNTIME lifecycle
- A3 PASS (`50ce091`) — ViewForward / stream-forward ffmpeg lifecycle
- Phase 1 stack PASS — profile `local`, PG 15432, MinIO 9000

## What was proven

On local full stack (`profile=local`, `upload-mode=kafka`, `minio.enabled=true`):

1. **Snap** — `POST /admin-api/video/media/hook/snap/completed` → Kafka `media.snap.completed` → `SnapUploadKafkaConsumerRunner` → MinIO `snap-space/frb26_device/frb26_snap_20260811183253.jpg` + `snap_image` row with explainable `/api/v1/buckets/...` URL
2. **DVR** — `POST /admin-api/video/media/hook/srs/on_dvr` → Kafka `media.dvr.completed` → `DvrUploadKafkaConsumerRunner` → MinIO `record-space/frb26_device/2026/08/11/20260811183345.mp4` + `record_file` + `playback` rows
3. Local source files deleted after successful upload (consumer path, not sync hook upload)
4. `upload-mode` not flipped to sync; MinIO not disabled

## Oracle vs Java

| Concern | Oracle (Python) | Java candidate |
|---------|-----------------|----------------|
| Upload mode gate | `MEDIA_UPLOAD_MODE=kafka` → `is_kafka_upload_mode()` | `video.media.upload-mode: kafka` → `MediaHookService.isKafkaUploadMode()` |
| Snap hook | `media_hook.py` → `publish_snap_event` | `MediaHookController` → `MediaHookService.snapCompleted()` → `MediaKafkaProducer.publishSnapEvent` |
| DVR hook | `media_hook.py` → `enqueue_srs_dvr_hook` | `MediaHookController` → `MediaHookService.srsOnDvr()` → `MediaKafkaProducer.publishDvrEvent` |
| DVR consumer | `run_worker.py` → `process_dvr_event` | `DvrUploadKafkaConsumerRunner` → `DvrUploadService.processDvrEvent` |
| Snap consumer | `run_snap_worker.py` → `process_snap_event` | `SnapUploadKafkaConsumerRunner` → `SnapUploadService.processSnapEvent` |
| MinIO + DB | `dvr_upload_service` / `snap_upload_service` | `DvrUploadService` / `SnapUploadService` + `VideoMinioService` |

## Code changes (this pack)

None — FR-B15/B16 consumer + FR-B2 MinIO paths already implemented; this pack is **local full-stack evidence** under commercial `local` profile (`upload-mode=kafka`, MinIO enabled).

## Fixture left in DB / MinIO

- `snap_image` id 12 — `frb26_device/frb26_snap_20260811183253.jpg` (115674 bytes)
- `record_file` id 14 + `playback` id 52 — `frb26_device/2026/08/11/20260811183345.mp4` (748898 bytes)
- MinIO objects in `snap-space` and `record-space` buckets (not cleaned up)

## Constraints for A5

- Do NOT flip shortcuts / mini / stub executor / sync upload / disable MinIO
- Do NOT claim COMPLETE / delete Python
- Stack unchanged: PG 15432, Kafka 9092, Nacos 8848, MinIO 9000, GW 48080, video 48096 **local**
- Device `frb26_device` has prior A1–A4 fixture rows; scope checks explicitly

## Next pack

**P2-A5** — Camera (`logs/phase2-a5-camera.json`)
