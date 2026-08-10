# FR-B2 Report — MinIO 空间同步/清理 + media DVR 上传

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Summary

Implemented real MinIO client operations in Java (replacing ack-only stubs) for snap/record space sync/cleanup, metadata sync, DVR upload, and snap upload pipelines. Config follows `video.minio.*` + `MINIO_*` env overrides; mini/certify default keeps `enabled=false` with explicit skip/fail semantics (no fake success when enabled).

`FULL_REPLACEMENT_GAP.md` §4 MinIO row updated.  
`certify.py --phase 0` → **exit 0**.

## Python files read

| File | Scope |
|------|--------|
| `VIDEO/_retired_python_video/app/services/snap_space_service.py` | `sync_spaces_to_minio`, `delete_snap_space`, `auto_cleanup_all_spaces`, MinIO bucket/device dir |
| `VIDEO/_retired_python_video/app/services/record_space_service.py` | `sync_spaces_to_minio`, `delete_record_space`, `auto_cleanup_all_record_spaces`, public bucket policy |
| `VIDEO/_retired_python_video/app/services/dvr_upload_service.py` | DVR MinIO upload, Playback/RecordFile upsert, alert `record_path` patch, local cleanup |
| `VIDEO/_retired_python_video/app/services/snap_upload_service.py` | Snap MinIO upload + metadata + local cleanup |
| `VIDEO/_retired_python_video/app/services/space_file_metadata_service.py` | `upsert_*`, `sync_*_from_minio`, metadata delete on cleanup |
| `VIDEO/_retired_python_video/app/services/snap_image_service.py` | `cleanup_old_images_by_save_time`, `sync_snap_images_metadata` |
| `VIDEO/_retired_python_video/app/services/record_video_service.py` | `cleanup_old_videos_by_save_time`, `sync_record_videos_metadata` |
| `VIDEO/_retired_python_video/app/utils/minio_bucket_policy.py` | Public read/write bucket policy |
| `VIDEO/_retired_python_video/app/utils/service_urls.py` | `minio_storage_enabled()` mini vs prod |
| `VIDEO/_retired_python_video/app/services/media_dvr_utils.py` | DVR path resolve, file stable wait, date parsing |

## GAP §4 MinIO row

| 项 | 状态 |
|----|------|
| MinIO 空间同步/清理 | ✅ `VideoMinioService.syncDeviceDirectories` + space admin delete prefix |
| DVR MinIO 上传 | ✅ `DvrUploadService.processDvrEvent` |
| Snap MinIO 上传 | ✅ `SnapUploadService.processSnapEvent` |
| 元数据 sync/cleanup | ✅ `SpaceFileMetadataService` + `SnapImageService` / `RecordVideoService` |
| 配置开关 | ✅ `video.minio.enabled` (default false) / `MINIO_ENABLED` |

## Phase 0

`python tools/video_java/certify.py --phase 0` → **exit 0** (2026-08-10)

## Config keys

| Key / env | Purpose |
|-----------|---------|
| `video.minio.enabled` | Master switch (default `false` for mini/certify) |
| `MINIO_ENABLED` | Env override for enabled |
| `video.minio.endpoint` / `MINIO_ENDPOINT` | MinIO endpoint |
| `video.minio.access-key` / `MINIO_ACCESS_KEY` | Access key |
| `video.minio.secret-key` / `MINIO_SECRET_KEY` | Secret key |
| `video.minio.snap-bucket` | Default `snap-space` |
| `video.minio.record-bucket` | Default `record-space` |
| `SRS_DVR_MIN_FILE_BYTES` | Minimum DVR segment size |

## New Java artifacts

- `service/minio/VideoMinioService`, `SpaceFileMetadataService`
- `support/VideoMinioBucketPolicy`, `MediaDvrPathSupport`
- `VideoProperties.Minio` nested config
- Updated: `SnapSpaceAdminService`, `RecordSpaceAdminService`, `SnapImageService`, `RecordVideoService`, `SnapStorageService`, `SnapSpaceCleanupService`, `RecordSpaceCleanupService`, `DvrUploadService`, `SnapUploadService`, `CameraAdminService`
- Repository upserts: `RecordFileRepository`, `SnapImageRepository`, `PlaybackRepository`, `AlertRepository.patchAlertsRecord`

## Concerns

1. **Archive save_mode=1** — Python zips to archive bucket; Java FR-B2 implements standard delete (save_mode=0) only.
2. **DVR thumbnail / ffprobe duration** — Python extracts JPEG thumbnail + ffprobe duration; Java uses duration=1 stub and skips thumbnail upload.
3. **Orphan MinIO object cleanup** — Python `cleanup_orphan_minio_record_objects` not ported; scheduled cleanup is DB-driven + MinIO delete for known rows.
4. **Prod MinIO not exercised here** — code paths fail clearly when `enabled=true` but broker unreachable; no live MinIO integration test in this env.
5. **Snap scheduling (FR-B3)** — still out of scope; Kafka→snap worker parity not part of B2.
