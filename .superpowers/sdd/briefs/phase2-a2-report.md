# Phase 2 A2 Report — Algo task RUNTIME lifecycle (handoff for A3)

**Status:** PASS  
**Pack:** P2-A2  
**Date:** 2026-08-11  
**Commit:** `7511dd2` — `feat(video-java): phase2 A2 runtime lifecycle parity`  
**Evidence:** `logs/phase2-a2-runtime-lifecycle.json`

## Prior packs

- A1 PASS (`2b3d483`) — alert Kafka; fixture device `frb26_device`, task 61 `frb26_alert_e2e`
- Phase 1 stack PASS — profile `local`, PG 15432

## What was proven

On local full stack (`profile=local`):

1. `POST /admin-api/video/algorithm/task/61/start` → real **RUNTIME.exe** subprocess (PID 42616 alive)
2. `GET /admin-api/video/algorithm/task/61/services/status` → `realtime_service.status=running`, `run_status=running`
3. `POST /admin-api/video/algorithm/task/61/stop` → PID gone, DB `is_enabled=false`, `run_status=stopped`
4. `executor_bin` is real C++ binary (650240 bytes), **not** stub

## Oracle vs Java

| Concern | Oracle (Python) | Java candidate |
|---------|-----------------|----------------|
| Start/stop API | `algorithm_task.py` → `start_algorithm_task` / `stop_algorithm_task` | `AlgorithmTaskController` → `AlgorithmTaskLifecycleService` |
| RUNTIME launch | `algorithm_task_daemon.py` → `Popen(runtime_bin, ini, env+PATH)` | `AlgorithmRuntimeSupervisor` → `ProcessBuilder` + `RuntimeLibraryPath` |
| Binary resolve | `runtime_config_service.resolve_runtime_bin()` | `RuntimeIniGenerator.resolveRuntimeBin()` |
| DLL PATH | `runtime_library_path_env()` | `RuntimeLibraryPath.pathForProcess()` (new) |
| Ini generation | `runtime_config_service.write_runtime_ini()` | `RuntimeIniGenerator.generate()` |

## Code changes (this pack)

1. **`RuntimeLibraryPath.java`** — mirrors Python `runtime_library_path_env()`; prepends `build-win/Release` + `vendor/conda-env/Library/bin` (+ conda-pkgs fallbacks) to PATH before spawning RUNTIME
2. **`AlgorithmRuntimeSupervisor.java`** — calls `applyRuntimeLibraryPath()` on every start (fixes immediate exit 0xC0000135 DLL-not-found on Windows)
3. **`RuntimeIniGenerator.java`** — `normalizeRtspUrl()` strips `file://` for Windows ffmpeg (`avformat_open_input` rejects `file://` URIs)

## Fixture left in DB

- Task 61 `frb26_alert_e2e`: `runtime_bin_path` set to worktree `RUNTIME/build-win/Release/RUNTIME.exe`; stopped after evidence run (`is_enabled=false`)

## Constraints for A3

- Do NOT flip shortcuts / mini / stub executor
- Do NOT claim COMPLETE / delete Python
- `F:/acme/RUNTIME/build-win/Release/RUNTIME.exe` missing on host — use worktree binary or set `task.runtime_bin_path` / `RUNTIME_BIN`
- Other tasks (50, 62) may have stale RUNTIME children; scope lifecycle checks to explicit task PID
- Stack unchanged: PG 15432, Kafka 9092, Nacos 8848, MinIO 9000, GW 48080, video 48096 **local**

## Next pack

**P2-A3** — Forward/ffmpeg path (`logs/phase2-a3-forward.json`)
