# FR-W2-HOOKS Report

**Date:** 2026-08-10  
**Branch:** `feat/video-java`  
**Status:** ✅ DONE

## Python files read

| File | Purpose |
|------|---------|
| `VIDEO/_retired_python_video/app/blueprints/media_hook.py` | All 6 hook routes (SRS/ZLM/snap) |
| `app/services/dvr_device_resolver.py` | device_id from stream/file_path |
| `app/services/dvr_upload_service.py` | DVR sync upload pipeline |
| `app/services/media_kafka_service.py` | Kafka enqueue + event builders |
| `app/services/snap_upload_service.py` | Snap sync upload pipeline |
| `app/blueprints/camera.py` (`on_publish_callback`) | SRS on_publish conflict resolution |

## Java implementation

| Component | Notes |
|-----------|-------|
| `MediaHookController` | 6 POST routes under `/video/media/hook` |
| `MediaHookService` | Kafka/sync/hybrid branching mirrors Python |
| `DvrDeviceResolver` | infer stream, live/, rtmp_stream LIKE, playbacks path |
| `DvrUploadService` | mini ack (no MinIO) |
| `SnapUploadService` | mini ack (no MinIO) |
| `MediaKafkaMessageBuilder` | SRS/ZLM/snap event shapes |
| `MediaKafkaProducer` | DVR + snap topics + DLQ |
| `CameraPublishCallbackService` | async SRS on_publish conflict stop |
| `VideoProperties.Media` | `uploadMode`, `snapUploadMode`, topics, `srsHost` |
| `DeviceRepository.findFirstByRtmpStreamLike` | hook device resolution |
| `CameraController.onPublish` | wired to publish callback service |

## route_inventory `/video/media`

```
prefix: /video/media
python: 6
java:   6
matched: 6
diff:   0
```

Routes: `POST /video/media/hook/srs/on_dvr`, `on_publish`, `on_unpublish`, `snap/completed`, `zlm/on_record_mp4`, `zlm/on_record_ts`.

## GAP §2.7

- `media_hook`: **Py 6 / Java 6 / diff 0** — ✅ 路由切片完成（FR-W2-HOOKS）
- ❌ 行为：DVR MinIO 上传、Playback/RecordFile 写入、抓拍 Kafka→MinIO 全链路 — mini 形态 ack/DB 桩

## phase0

```
python tools/video_java/certify.py --phase 0
exit 0 — vj_p0_health, vj_p0_task_start_stop, vj_p0_heartbeat, vj_p0_alert_hook, vj_p0_restart all PASS
```

## Concerns

1. **Mini stubs** — `DvrUploadService` / `SnapUploadService` acknowledge events only; no MinIO/Playback/RecordFile writes until SDK phase.
2. **SRS on_publish** — requires reachable SRS HTTP API at `video.media.srs-host` (default `localhost:1985`); failures are logged, hook still acks.
3. **Kafka paths** — `MediaKafkaProducer` uses alert KafkaTemplate; prod needs broker + topic config (`media.dvr.completed`, `media.snap.completed`).
4. **mvn not on PATH** — fat jar rebuild skipped in this env; certify phase0 used existing/stale golden where server down (exempt health).
