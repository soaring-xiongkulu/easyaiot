# Phase 2 — Main-path parity (local full stack)

> Worktree: `feat/video-java` · Profile: **`local`** (commercial defaults) · Oracle: `F:/acme/VIDEO/`

Phase 1 stack wiring is documented in [PHASE1_STACK.md](./PHASE1_STACK.md). This file tracks **main-path** parity packs (A-series) against Python Oracle on the local full stack.

---

## Pack A1 — Alert hook Kafka path

| Field | Value |
|-------|-------|
| **Status** | **PASS** |
| **Date** | 2026-08-11 |
| **Evidence** | `logs/phase2-a1-alert-kafka.json` |

### Goal

Prove Java `video-server` under `profile=local` sends alert hooks via **real Kafka** (`use-direct-persist=false`), aligned with Python non-mini `alert_hook_service.process_alert_hook`.

### Oracle reference (Python)

| Item | Location |
|------|----------|
| Direct-persist gate | `VIDEO/app/services/alert_hook_service.py` → `_should_use_direct_alert_persist()` — false when env unset and not mini |
| Kafka path | `get_kafka_producer()` → `producer.send(topic, key=device_id)` → returns `topic` / `partition` / `offset` |
| Fallback | `_fallback_persist_on_kafka_failure` only on Kafka failure (not primary local path) |

### Java candidate

| Item | Location |
|------|----------|
| Config | `application-local.yaml` → `video.alert.use-direct-persist: false` |
| Service | `AlertHookService.processHook()` → `sendViaKafka()` when `useDirectPersist` false |
| Response | `mode=kafka`, `topic`, `partition`, `offset` |

### Acceptance results

| # | Check | Result |
|---|-------|--------|
| 1 | `video.alert.use-direct-persist=false` (committed local + effective) | **PASS** |
| 2 | `POST /admin-api/video/alert/hook` (gateway) | **PASS** — `mode=kafka` |
| 3 | `POST /video/alert/hook` (direct :48096) | **PASS** — `mode=kafka` |
| 4 | Broker message on `iot-alert-notification` | **PASS** — consumed at partition 48 |
| 5 | No direct_persist fallback on success path | **PASS** |

### Fixture

- Device: `frb26_device` (task 61 `frb26_alert_e2e`, `alert_event_enabled=true`)

---

## Pack A2 — Algo task RUNTIME lifecycle

| Field | Value |
|-------|-------|
| **Status** | **PASS** |
| **Date** | 2026-08-11 |
| **Evidence** | `logs/phase2-a2-runtime-lifecycle.json` |

### Goal

Prove Java `video-server` under `profile=local` can start/stop an algo task with a **real C++ RUNTIME** subprocess alive, `services/status` reasonable, and clean stop — aligned with Python `start_algorithm_task` / `stop_algorithm_task`.

### Oracle reference (Python)

| Item | Location |
|------|----------|
| Start/stop | `VIDEO/app/services/algorithm_task_service.py` → `start_algorithm_task` / `stop_algorithm_task` |
| RUNTIME launch | `VIDEO/app/services/algorithm_task_daemon.py` → `Popen(runtime_bin, ini, env+PATH)` |
| Binary resolve | `VIDEO/app/services/runtime_config_service.py` → `resolve_runtime_bin` / `ensure_runtime_bin_ready` |
| DLL PATH | `runtime_config_service.runtime_library_path_env()` |
| API routes | `VIDEO/app/blueprints/algorithm_task.py` → `/task/{id}/start`, `/stop`, `/services/status` |

### Java candidate

| Item | Location |
|------|-------|
| Controller | `AlgorithmTaskController` → `POST /task/{id}/start`, `/stop`; `GET /services/status` |
| Lifecycle | `AlgorithmTaskLifecycleService.start()` / `.stop()` |
| Supervisor | `AlgorithmRuntimeSupervisor` + `RuntimeLibraryPath` (PATH for vendor DLLs) |
| Ini | `RuntimeIniGenerator` (Windows `file://` → plain path) |

### Acceptance results

| # | Check | Result |
|---|-------|--------|
| 1 | `executor_bin` real RUNTIME.exe (not stub) | **PASS** — 650240 bytes |
| 2 | Start → PID alive on Windows | **PASS** — PID 42616 |
| 3 | `services/status` running | **PASS** — `status=running`, `run_status=running` |
| 4 | Stop → process gone, DB stopped | **PASS** — PID gone, `is_enabled=false` |

### Fixture

- Task 61 `frb26_alert_e2e` (device `frb26_device`, from A1); `runtime_bin_path` → worktree `RUNTIME/build-win/Release/RUNTIME.exe`

### Code fixes (A2)

- `RuntimeLibraryPath.java` — PATH parity with Python `runtime_library_path_env()`
- `AlgorithmRuntimeSupervisor` — inject PATH before spawn
- `RuntimeIniGenerator` — strip `file://` for Windows ffmpeg

---

## Next pack

**A3** — Forward/ffmpeg path (`logs/phase2-a3-forward.json`).
