# FR-W1-BG Report

**STATUS:** DONE  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Python files read (oracle)

1. `VIDEO/_retired_python_video/run.py` — startup order: `auto_start_streaming` → schedulers → `auto_start_all_tasks` (algorithm + stream_forward) → immediate health recovery
2. `VIDEO/_retired_python_video/app/blueprints/camera.py` — `auto_start_streaming()` (`enable_forward`, rtmp/offline skip)
3. `VIDEO/_retired_python_video/app/services/algorithm_task_launcher_service.py` — `auto_start_all_tasks`, `recover_unhealthy_algorithm_tasks`
4. `VIDEO/_retired_python_video/app/services/algorithm_task_health_service.py` — `run_algorithm_task_health_cycle`, `ALGORITHM_HEALTH_MONITOR_ENABLED`
5. `VIDEO/_retired_python_video/app/services/stream_forward_launcher_service.py` — `auto_start_all_tasks` (enabled + devices)
6. `VIDEO/_retired_python_video/app/services/stream_forward_health_service.py` — remote cluster migration only (`is_remote_deploy_enabled`)

## Python ↔ Java mapping (GAP §3 scope)

| Python | Java | Notes |
|--------|------|-------|
| `auto_start_streaming` | `ViewForwardAutoResumeScheduler` + `ViewForwardAutoResumeService` | `@Order(10)` on `ApplicationReadyEvent` |
| `auto_start_all_tasks` (algorithm) | `AlgorithmTaskAutoStartScheduler` + `AlgorithmTaskAutoStartService` | `@Order(20)`; validates model_ids / devices by task_type |
| `stream_forward` auto_start | `StreamForwardAutoStartScheduler` + `StreamForwardAutoStartService` | `@Order(30)`; `findEnabledLocal()` |
| `run_algorithm_task_health_cycle` | `AlgorithmTaskHealthRecoveryScheduler` + `AlgorithmTaskHealthRecoveryService` | `@Order(40)` startup + `video.health-monitor.interval-ms` (local 5s) |
| `stream_forward_health` (cluster) | — | ❌ deferred: Python gated on `is_remote_deploy_enabled` |

Startup order (`@Order`): view-forward resume → algorithm auto_start → stream_forward auto_start → algorithm health recovery.

## GAP §3

| Row | Status |
|-----|--------|
| `auto_start_streaming` | ✅ |
| `auto_start_all_tasks` (algorithm) | ✅ |
| `stream_forward` auto_start | ✅ (local only) |
| algorithm_task 健康监控 | ✅ |
| stream_forward 集群健康迁移 | ❌ (remote / W3+) |
| 空间清理 / janitor / disk guard | ❌ (W3-OPS, out of scope) |

## Evidence

- `application-local.yaml`: `skip-background-tasks: false`, `health-monitor.interval-ms: 5000`
- `certify.py --phase 0` → **exit 0** (`vj_p0_restart` lifecycle pass — crash stub + health recovery within 15s window)
- Startup schedulers gated by `video.skip-background-tasks=false` (mirrors `VIDEO_SKIP_BACKGROUND_TASKS`)

## Concerns

- **AUTH + KAFKA remain cutover hard gates** (EX-GATEWAY-AUTH-LOCAL, EX-KAFKA-HOOK).
- Snap-task auto_start does not auto-create snap spaces (Python `create_snap_space_for_device`); snap/patrol tasks without space may fail start until W2 snap path.
- Remote `schedule_policy=auto|node` still rejected (EX-REMOTE-NODE).
