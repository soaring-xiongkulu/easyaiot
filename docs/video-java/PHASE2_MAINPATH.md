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

## Pack A5 — Camera list/get/register key-path

| Field | Value |
|-------|-------|
| **Status** | **PASS** |
| **Date** | 2026-08-11 |
| **Evidence** | `logs/phase2-a5-camera.json` |

### Goal

Prove Java `video-server` under `profile=local` list/get/register/update camera key fields align with Python Oracle semantics on shared `iot-video20` DB — prefer gateway `/admin-api/video/camera/**`.

### Oracle reference (Python)

| Item | Location |
|------|----------|
| List | `VIDEO/app/blueprints/camera.py` → `GET /list` → `get_device_list` |
| Get | `camera.py` → `GET /device/{id}` → `get_camera_info` → `_to_dict` |
| Register | `camera.py` → `POST /register/device` → `register_camera` |
| Update | `camera.py` → `PUT /device/{id}` → `update_camera` |
| Key fields | `camera_service.py` → `_to_dict` (streams, online, location, nvr, device_kind) |

### Java candidate

| Item | Location |
|------|-------|
| Controller | `CameraController` → `/list`, `/device/{id}`, `/register/device`, `PUT /device/{id}` |
| List/Get | `CameraService` → `listDevices` / `getDevice` → `toMap` |
| Register/Update | `CameraAdminService` → `registerDevice` / `updateDevice` |
| Spaces | `ensureSpacesQuiet` on register (mirrors Python `ensure_device_spaces`) |

### Acceptance results

| # | Check | Result |
|---|-------|--------|
| 1 | List returns devices with `total` (gateway + direct agree) | **PASS** — 17 devices |
| 2 | Get key fields match Python `_to_dict` on same DB (`frb26_device`) | **PASS** |
| 3 | List item == GET for same device | **PASS** |
| 4 | Register with `source` + `cameraType=custom` | **PASS** — `p2a5_cam_20260811184235` |
| 5 | Register creates snap_space + record_space | **PASS** — ids 33/32 |
| 6 | Update name/model persisted | **PASS** |

### Fixture

- Existing: `frb26_device` (A1–A4 fixture)
- New: `p2a5_cam_20260811184235` — snap_space 33, record_space 32

### Code fixes (A5)

- None (evidence-only pack; routes from FR-W2-CAM)

---

## Pack A6 — Post-process real enqueue (no stub)

| Field | Value |
|-------|-------|
| **Status** | **⛔缺 sink** |
| **Date** | 2026-08-11 |
| **Evidence** | `logs/phase2-a6-postprocess.json` |

### Goal

Prove Java `video-server` under `profile=local` with `use-stub-enqueue=false` performs **real HTTP enqueue** to iot-sink when post-process is enabled — aligned with Python `post_process_sink_client.publish_post_process_request()`.

### Oracle reference (Python)

| Item | Location |
|------|----------|
| Enqueue gate | Non-mini: real HTTP, no stub |
| Sink URL | `post_process_sink_client.py` → `http://127.0.0.1:48092/post-process/enqueue` |
| Trigger | `post_process_runner.enqueue_post_process_request()` via alert orchestration |
| Message | `build_post_process_request_message(ctx)` camelCase fields |

### Java candidate

| Item | Location |
|------|-------|
| Config | `application-local.yaml` → `video.post-process.use-stub-enqueue: false` |
| Sink client | `PostProcessSinkClient.publishPostProcessRequest()` → `RestTemplate` POST |
| Orchestrator | `AlertPostOrchestratorService` → async enqueue on alert hook |
| Audit | `PostProcessEnqueueAudit` via `GET /task/{id}/post-process/status` |

### Acceptance results

| # | Check | Result |
|---|-------|--------|
| 1 | `use-stub-enqueue=false` (committed local + default) | **PASS** |
| 2 | Post-process workspace init + enabled on task 61 | **PASS** |
| 3 | Alert hook + detections triggers enqueue orchestration | **PASS** — `enqueue_count=1` |
| 4 | Real HTTP attempted (not stub) | **PASS** — `enqueue_ok=false` (stub would be `true`) |
| 5 | iot-sink UP + HTTP 2xx on enqueue | **⛔** — `127.0.0.1:48092` connection refused; GW sink 503 |

### Fixture

- Task 61 `frb26_alert_e2e` (device `frb26_device`, from A1); workspace `~/.video-java/post-process-workspaces/task_61/`

### Code fixes (A6)

- None (evidence-only pack; sink client from prior FR-B work)

---

## Next pack

**A7** — Matching (`logs/phase2-a7-matching.json`).
