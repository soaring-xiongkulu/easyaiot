# FR-W3-OPS Report

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Summary

Aligned Java background ops schedulers with Python `run.py` janitor / disk-guard / space-cleanup tasks:

- `SpaceCleanupScheduler` — snap + record space cleanup every 30 min + startup boot cleanup
- `PlaybackDiskGuardScheduler` — SRS playback disk guard every 10 min + startup first run
- `MediaJanitorScheduler` — orphan DVR/snap requeue every 60s + disk emergency trigger

`FULL_REPLACEMENT_GAP.md` §3 updated (3 rows ✅).  
`certify.py --phase 0` → **exit 0**.

## Commits

(see `git log -1` after commit)

## Python files read

| File | Scope |
|------|--------|
| `VIDEO/_retired_python_video/run.py` | `auto_cleanup_snap_spaces` / `auto_cleanup_record_spaces` (30min), `playback_disk_guard`, `media_janitor` APScheduler jobs + startup boot |
| `VIDEO/_retired_python_video/app/services/snap_space_service.py` | `auto_cleanup_all_spaces` |
| `VIDEO/_retired_python_video/app/services/record_space_service.py` | `auto_cleanup_all_record_spaces` |
| `VIDEO/_retired_python_video/app/services/playback_disk_guard_service.py` | `run_playback_disk_guard` + disk/age/count/emergency helpers |
| `VIDEO/_retired_python_video/app/services/media_janitor_service.py` | `run_janitor_cycle`, orphan scan/requeue, `is_janitor_enabled` |

## GAP §3 progress

| Python 能力 | 状态 |
|-------------|------|
| 抓拍/录像空间定时清理（30min） | ✅ `SpaceCleanupScheduler` + `SnapSpaceCleanupService` / `RecordSpaceCleanupService` |
| playback disk guard | ✅ `PlaybackDiskGuardScheduler` + `PlaybackDiskGuardService` |
| media janitor | ✅ `MediaJanitorScheduler` + `MediaJanitorService` |
| stream_forward 集群健康迁移 | ❌ 仍缺（EX-REMOTE-NODE 范围外） |
| snap_task 调度器 `init_all_tasks` | ❌ 仍缺（非本包范围） |

## Phase 0

`python tools/video_java/certify.py --phase 0` → **exit 0** (2026-08-10)

## Concerns

1. **Mini 空间清理** — Java 定时清理走 DB 过期行删除（`snap_image` / `record_file`），未接 MinIO 真删/归档；与 Python mini 形态（MinIO 未启用时跳过）语义近似但非字节级对等。
2. **Playback 权限修复** — Python `ensure_playback_path_deletable` / sudo chmod 未移植；Windows/权限受限环境删除可能静默失败。
3. **Janitor 紧急清理** — 磁盘超阈值时复用 `PlaybackDiskGuardService.runGuard()` 全量策略，非 Python janitor 内仅 `emergency_free_disk` 的轻量路径。
4. **stream_forward 健康迁移 / snap_task 调度** — GAP §3 其余 ❌ 行未在本包处理。

## New Java artifacts

- `service/ops/SnapSpaceCleanupService`, `RecordSpaceCleanupService`, `PlaybackDiskGuardService`, `MediaJanitorService`
- `scheduler/SpaceCleanupScheduler`, `PlaybackDiskGuardScheduler`, `MediaJanitorScheduler`
- `support/MediaPathSupport`, `SpaceSaveTimeSupport`
- `VideoProperties`: `space-cleanup`, `playback-disk-guard`, `media-janitor`
