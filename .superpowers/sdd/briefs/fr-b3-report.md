# FR-B3 Report — snap_task 调度器 init_all_tasks

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Summary

Ported Python snap task scheduler startup (`init_all_tasks`) and per-task cron scheduling into Java. On `ApplicationReadyEvent`, enabled `snap_task` rows are registered with a `ThreadPoolTaskScheduler` + `CronTrigger` (Asia/Shanghai). CRUD/start/stop/restart on `SnapTaskService` now add/remove/reschedule jobs. Execution updates `total_captures` / status like Python `execute_snap_task`; RTSP/ONVIF capture remains a structural stub (camera SDK deferred to FR-B6).

`FULL_REPLACEMENT_GAP.md` §3 `snap_task` row updated.  
`certify.py --phase 0` → **exit 0**.

## Python files read

| File | Scope |
|------|--------|
| `VIDEO/_retired_python_video/run.py` | Startup calls `init_all_tasks()` after scheduler/space cleanup setup (~L1319–1327) |
| `VIDEO/_retired_python_video/app/services/snap_task_service.py` | `init_all_tasks`, `add_task_to_scheduler`, `remove_task_from_scheduler`, `execute_snap_task`, APScheduler `CronTrigger` |
| `VIDEO/_retired_python_video/app/utils/cron_utils.py` | 6-field cron normalization, min interval validation |

## Python ↔ Java mapping

| Python | Java | Notes |
|--------|------|-------|
| `init_all_tasks()` | `SnapTaskSchedulerService.initAllTasks()` | loads `is_enabled=true` rows |
| `add_task_to_scheduler` / `remove_task_from_scheduler` | same class + `SnapTaskService` hooks | create/update/start/stop/restart/delete |
| APScheduler `BackgroundScheduler` | `ThreadPoolTaskScheduler` + `CronTrigger` | zone `Asia/Shanghai` |
| `execute_snap_task` | `SnapTaskExecutionService` | night-mode skip, stats update |
| `capture_image` | `SnapTaskCaptureService` | structural stub; RTSP path returns false; ONVIF delegates to `CameraHardwareService` stub |

## GAP §3 snap_task row

| 项 | 状态 |
|----|------|
| `init_all_tasks` on startup | ✅ `SnapTaskScheduler` `@Order(55)` |
| Per-task cron scheduling | ✅ `SnapTaskSchedulerService` |
| Lifecycle hooks (start/stop/CRUD) | ✅ `SnapTaskService` |
| Capture/ffmpeg/MinIO upload | ❌ stub (FR-B6 / prod hardware) |

## Phase 0

`python tools/video_java/certify.py --phase 0` → **exit 0** (2026-08-10)

## Config keys

| Key / env | Purpose |
|-----------|---------|
| `video.snap-task-scheduler.enabled` | Master switch (default `true`) |
| `video.skip-background-tasks` | Disables all background timers including snap scheduler |

## New Java artifacts

- `scheduler/SnapTaskScheduler`
- `service/snap/SnapTaskSchedulerService`, `SnapTaskExecutionService`, `SnapTaskCaptureService`
- `support/SnapCronSupport`
- `VideoProperties.SnapTaskScheduler`
- Updated: `SnapTaskService`, `SnapTaskRepository`

## Concerns

1. **RTSP/RTMP frame capture** — Python uses ffmpeg/OpenCV; Java `SnapTaskCaptureService` logs and returns false for `capture_type=0`.
2. **Algorithm regions / alarm on snap** — Python `capture_image` full AI path not ported; scheduled runs only update task stats.
3. **Cron min-interval validation** — Python `validate_snap_cron_min_interval` not enforced on Java schedule path (invalid cron logs error, task skipped).
4. **Prod soak** — no live enabled snap tasks exercised in certify mini env.
