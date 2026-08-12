# CP-10 Report — Boot daemons map (run.py ↔ Java schedulers)

**Status:** PASS  
**Pack:** CP-10 (W5 final)  
**Date:** 2026-08-12  
**Evidence:** `logs/cp-10-boot-daemons.json`  
**nested_subagents:** none

## Prior reports

- [cp-1-report.md](./cp-1-report.md) — zero Fallback alert path
- [cp-2-report.md](./cp-2-report.md) — matching consume via iot-sink
- [cp-3-report.md](./cp-3-report.md) — sink 15432 + enqueue_ok
- [cp-4-report.md](./cp-4-report.md) — snap `init_all_tasks` boot parity
- [cp-5-report.md](./cp-5-report.md) — services/status honesty
- [cp-6-report.md](./cp-6-report.md) — patrol main-path
- [cp-7-report.md](./cp-7-report.md) — AudioTalk
- [cp-8-report.md](./cp-8-report.md) — GB28181 code
- [cp-9-report.md](./cp-9-report.md) — FlightHub + directory

## What changed

| File | Change |
|------|--------|
| `logs/cp-10-boot-daemons.json` | Mapping table + 4 sampled boot daemons with log/DB evidence |
| `logs/cp-10-video-server.log` | Fresh `local` boot capture (PID 2784) |
| `.scripts/cp-10-evidence.ps1` | Reproducible boot log harvester |
| `CODE_PARITY_INDEX.md` / `CODE_PARITY_BACKLOG.md` / `HANDOFF.md` | CP-10 PASS; Part1 A-series CP closed |

**No Java scheduler code changes** — mapping + evidence pack only.

## Python `run.py` ↔ Java mapping

| ID | Python (`run.py`) | Java | Parity |
|----|-------------------|------|--------|
| M-01 | `VIDEO_SKIP_BACKGROUND_TASKS` gate | `video.skip-background-tasks` + `@ConditionalOnProperty` | ✓ |
| M-02 | Nacos register + heartbeat thread | Spring Cloud Nacos (`bootstrap-local.yaml`) | ✓ (framework) |
| M-03 | `maybe_fix_srs_on_startup` | — | **gap** |
| M-04 | `_start_search` → `_init_all_cameras` + `repair_nvr_channel_links` + IP monitor | `NvrRepairBootScheduler` + `IpReachabilityBootScheduler` | **CP-11 closed** (was mislabeled ONVIF search) |
| M-05 | `auto_start_streaming()` | `ViewForwardAutoResumeScheduler` | ✓ **sample-1** |
| M-06 | `auto_cleanup_snap_spaces` 30m + boot | `SpaceCleanupScheduler` → `SnapSpaceCleanupService` | ✓ **sample-2** |
| M-07 | `auto_cleanup_record_spaces` 30m + boot | `SpaceCleanupScheduler` → `RecordSpaceCleanupService` | ✓ **sample-2** |
| M-08 | `playback_disk_guard` | `PlaybackDiskGuardScheduler` | ✓ |
| M-09 | `media_janitor` | `MediaJanitorScheduler` | ✓ **sample-3** |
| M-10 | `stream_forward_health` + boot recovery | `StreamForwardHealthScheduler` | ✓ (0 enabled tasks in DB) |
| M-11 | `algorithm_task_health` + boot recovery | `AlgorithmTaskHealthRecoveryScheduler` | ✓ (honest RUNTIME fail) |
| M-12 | `init_all_tasks()` | `SnapTaskScheduler` | ✓ **sample-4** (CP-4) |
| M-13 | `start_auto_frame_extraction` (commented) | — | n/a (both disabled) |
| M-14 | `check_heartbeat_timeout` 1m | — | **gap** (legacy extractor/sorter/pusher) |
| M-15 | Reset face/plate auto-enroll `is_running` | — | **gap** (API-only reset in Java) |
| M-16 | `auto_start_all_tasks` (algorithm) | `AlgorithmTaskAutoStartScheduler` | ✓ (honest 0/4 skip) |
| M-17 | `auto_start_all_tasks` (stream_forward) | `StreamForwardAutoStartScheduler` | ✓ (0 enabled) |
| M-18 | `safe_shutdown_daemons` atexit | Supervisor `@PreDestroy` | partial |
| M-19 | `sync_unassigned_devices_to_default_directory` | `Gb28181SyncService` on GB/API | different trigger |

## Evidence summary (local, no fake success)

| Sample | Oracle | Java evidence | Result |
|--------|--------|---------------|--------|
| **1 View-forward** | `enable_forward=true` devices auto-stream | DB **4** ids; log `resumed=4` matching ids | **PASS** |
| **2 Space cleanup** | Boot snap + record cleanup | `startup 抓拍空间清理完成`; record `deleted=1` on space vj_p2 | **PASS** (real delete) |
| **3 Media janitor** | `media_janitor` 60s job | `Janitor 周期完成: dvr_orphans=0 … disk=92.11%` | **PASS** |
| **4 Snap init** | `init_all_tasks` all enabled | `scheduled=10` ids `[7…16]` = DB `is_enabled` count | **PASS** (CP-4 cross-ref) |
| Algo auto-start | Start enabled local tasks | **0/4** — WARN missing `model_ids`, not fake start | **honest** |
| Health recovery | Recover dead daemons | ERROR `RUNTIME 二进制不存在` when binary missing | **honest** |

Correlation: `cp-10-evidence-20260812001608` — profile `local`, boot log `logs/cp-10-video-server.log`.

## Gaps (documented, not Part1 blockers for CP-10)

1. ~~**ONVIF camera search thread**~~ — **Corrected:** Python `_start_search` is NVR repair + IP monitor, not ONVIF discovery (CP-11).  
2. ~~**SRS startup self-check**~~ — **CP-11:** `SrsStartupGuardScheduler` (honest log, no fake healthy).  
3. **Legacy heartbeat timeout job** — Python updates FrameExtractor/Sorter/Pusher + AlgorithmTask every 1m; Java relies on supervisor + per-request heartbeat semantics (CP-5).  
4. ~~**Auto-enroll boot reset**~~ — **CP-11:** `AutoEnrollBootResetScheduler` clears stale `is_running`.

## Part1 closure

**CP-1 … CP-10 all PASS.** Part1 code-path packs complete. Part2 engines (InsightFace/Milvus/RUNTIME binary on host) remain. **No COMPLETE. No delete Python.**

## Ready for Part2?

**Yes** — boot daemon map documented with evidence; engine gaps explicitly Part2.
