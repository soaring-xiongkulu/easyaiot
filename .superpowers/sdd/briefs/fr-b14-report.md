# FR-B14 Report — resolve 只读接线 + post_process 远程 worker

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Wired Python-parity read-path stream URL resolution into camera list/get (via `CameraService.toMap`) and inference-input; enhanced `StreamUrlSupport.resolveDeviceStreamUrls` with media-pool binding + stream-forward deployment host/tags fallback matching `stream_url_sync_service.resolve_device_stream_urls`. Ported `post_process_launcher_service.py` to `PostProcessLauncherService` with remote allocate/deploy/stop via `IotNodeClient` and local `run_worker.py` fallback; integrated into `AlgorithmTaskLifecycleService` start/stop.

**COMPLETE 未宣称** — prod 媒体池/iot-node/post-process worker 集群联调仍待。

## Python files read (oracle)

| Path | Purpose |
|------|---------|
| `VIDEO/_retired_python_video/app/services/stream_url_sync_service.py` | `resolve_device_stream_urls` (L69–107): media binding → stream-forward deployment → DB fallback; `build_stream_urls_for_host` |
| `VIDEO/_retired_python_video/app/services/camera_service.py` | `resolve_device_inference_input` (L1456–1488) calls `resolve_device_stream_urls`; list/get via `_to_dict` (DB fields; monitor-tree resolves in blueprint) |
| `VIDEO/_retired_python_video/app/services/post_process_launcher_service.py` | Full remote/local replica deploy/stop: `start_post_process_workers`, `stop_post_process_workers`, workload `pp_{task}_r{replica}`, spread replicas, `EASYAIOT_ENABLE_POST_PROCESS_WORKER` gate |
| `VIDEO/_retired_python_video/app/blueprints/camera.py` | `_device_monitor_tree_node` (L2557–2588) resolves streams on read |
| `VIDEO/_retired_python_video/app/services/algorithm_task_launcher_service.py` | `_start_post_process_cluster` / `_stop_post_process_cluster` on task start/stop/restart (L30–37, L777, L830, L1003) |

## Java changes (key)

| Component | Change |
|-----------|--------|
| `StreamUrlSupport` | `resolveDeviceStreamUrls` now: media pool `getDeviceMediaBinding` → stream-forward deployment lookup + node tags → DB fallback |
| `StreamForwardTaskRepository` | `findEnabled()` for deployment scan |
| `CameraService` | list/get/monitor-tree paths use resolved streams in `toMap` |
| `CameraAdminService` | `resolveInferenceInput` parity with Python fields |
| `PostProcessLauncherService` | New: remote `IotNodeClient` allocate/deploy/stop + local ProcessBuilder; replica spread; honest remote failure |
| `AlgorithmTaskLifecycleService` | Start/stop hooks for post-process workers; remote failure → `VideoBusinessException` |
| `RemoteScheduleSupport` | `WORKLOAD_POST_PROCESS` constant |
| `FULL_REPLACEMENT_GAP.md` / `progress.md` | FR-B14 ✅ deltas |

## GAP deltas

- §2.3 camera 行为：list/get/inference-input 只读 resolve → **FR-B14 ✅**
- §4 post-process worker 集群行新增 → **FR-B14 ✅**（prod 联调仍待）
- §8 行为桩：post-process worker 行关闭（prod 联调仍待）

## certify --phase 0

```
exit 0
```

Log: `logs/fr-b14-phase0.log`（oracle `:6000` 未运行 — stale golden warnings; all cases ok/exempt）

## Remaining

- Prod 媒体池 `getDeviceMediaBinding` + 推流分片集群真机验证
- `EASYAIOT_ENABLE_POST_PROCESS_WORKER=1` + 远程 iot-node + `VIDEO/services/post_process_worker/run_worker.py` 端到端
- 本机 worker 需 `VIDEO_ROOT` 可解析且脚本存在（否则 local path IOException）
- 全量 HTTP 契约回归（259 路由）

## Concerns

- Remote post-process enabled + iot-node down → `VideoBusinessException` on algorithm start（非静默，对齐 brief）
- Worker 全局默认关闭（`EASYAIOT_ENABLE_POST_PROCESS_WORKER` 未设 = 0），与 Python 一致
- Local post-process start failure 仅 warn（Python 新启动路径亦未检查返回值）；远程路径严格失败
- Pool enabled + binding API down：resolve 回退 DB 字段（只读，不写库）
