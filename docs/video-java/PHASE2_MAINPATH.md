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

## Pack A3 — ViewForward / stream-forward ffmpeg lifecycle

| Field | Value |
|-------|-------|
| **Status** | **PASS** |
| **Date** | 2026-08-11 |
| **Evidence** | `logs/phase2-a3-forward.json` |

### Goal

Prove Java `video-server` under `profile=local` can start/stop device preview forward (ViewForward) and/or stream-forward tasks with a **real ffmpeg** subprocess alive, status reasonable, and clean stop — aligned with Python `camera.py` FFmpegDaemon and `stream_forward_daemon.py`.

### Oracle reference (Python)

| Item | Location |
|------|----------|
| ViewForward API | `VIDEO/app/blueprints/camera.py` → `/device/{id}/stream/start`, `/stop`, `/status` |
| ffmpeg launch | `camera.py` → `FFmpegDaemon` → `subprocess.Popen(ffmpeg_cmd)` |
| Stream-forward API | `VIDEO/app/blueprints/stream_forward.py` → `/task/{id}/start`, `/stop`, `/status` |
| Stream-forward daemon | `VIDEO/app/services/stream_forward_daemon.py` → `StreamForwardDaemon` |
| ffmpeg compat | `VIDEO/app/utils/ffmpeg_compat.py` |

### Java candidate

| Item | Location |
|------|-------|
| ViewForward | `CameraController` → `ViewForwardService` → `ViewForwardSupervisor` |
| Stream-forward | `StreamForwardController` → `StreamForwardService` → `StreamForwardSupervisor` |
| ffmpeg command | `ViewForwardService.buildFfmpegCommand()` + `FfmpegCompat` |

### Acceptance results

| # | Check | Result |
|---|-------|--------|
| 1 | Start → ffmpeg alive (Windows) | **PASS** — supervisor PID 25320, child `ffmpeg-win-x86_64-v7.1` |
| 2 | `stream/status` running | **PASS** — `status=running`, `enable_forward=true` |
| 3 | Stop → process gone | **PASS** — PID gone, `enable_forward=false` |
| 4 | Stream-forward task start/stop | **PASS** — task 63 `status=running`, ffmpeg log active |

### Fixture

- Device `frb26_device` (file `F:/acme/RUNTIME/testdata/sample.mp4` → SRS `rtmp://127.0.0.1/live/frb26_device`)
- Stream-forward task 63 (`vj_p2_device`, same file source)

### Code fixes (A3)

- `FfmpegCompat.java` — correct `rw_timeout` detection; remove broken global `-timeout` fallback for file inputs; `cmd.exe /c` wrapper for `.cmd` probes

---

## Pack A4 — Media DVR/Snap → Kafka → MinIO

| Field | Value |
|-------|-------|
| **Status** | **PASS** |
| **Date** | 2026-08-11 |
| **Evidence** | `logs/phase2-a4-media-minio.json` |

### Goal

Prove Java `video-server` under `profile=local` with `upload-mode=kafka` and MinIO enabled: media hook enqueue → Kafka consumer → MinIO object + explainable DB path — aligned with Python non-mini `media_hook_service` + upload workers.

### Oracle reference (Python)

| Item | Location |
|------|----------|
| Upload mode gate | `media_kafka_service.py` → `is_kafka_upload_mode()` |
| Snap hook | `media_hook.py` → `publish_snap_event` when kafka mode |
| DVR hook | `media_hook.py` → `enqueue_srs_dvr_hook` when kafka mode |
| DVR consumer | `services/media_upload_worker/run_worker.py` → `process_dvr_event` |
| Snap consumer | `services/media_upload_worker/run_snap_worker.py` → `process_snap_event` |
| MinIO + metadata | `dvr_upload_service.py` / `snap_upload_service.py` |

### Java candidate

| Item | Location |
|------|----------|
| Config | `application-local.yaml` → `video.media.upload-mode: kafka`, `video.minio.enabled: true` |
| Hook | `MediaHookController` → `MediaHookService` → `MediaKafkaProducer` |
| DVR consumer | `DvrUploadKafkaConsumerRunner` → `DvrUploadService` |
| Snap consumer | `SnapUploadKafkaConsumerRunner` → `SnapUploadService` |
| MinIO | `VideoMinioService` |

### Acceptance results

| # | Check | Result |
|---|-------|--------|
| 1 | `upload-mode=kafka` + `minio.enabled=true` (local) | **PASS** |
| 2 | Snap hook → `media.snap.completed` (not sync primary) | **PASS** |
| 3 | Snap consumer → MinIO object + `snap_image.url` | **PASS** — 115674 bytes |
| 4 | DVR hook → `media.dvr.completed` | **PASS** |
| 5 | DVR consumer → MinIO + `record_file` + `playback` | **PASS** — 748898 bytes |

### Fixture

- Device `frb26_device` (snap space 15 `snap-space`, record space 14 `record-space`, task 61 from A1)

### Code fixes (A4)

- None (evidence-only pack; consumers from FR-B15/B16, MinIO from FR-B2)

---

## Next pack

**A5** — Camera (`logs/phase2-a5-camera.json`).
