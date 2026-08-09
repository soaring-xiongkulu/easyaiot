# Phase 4 Gate Evidence

> Candidate: `F:/acme/.worktrees/runtime-parity` (`feat/runtime-parity`)  
> Updated: 2026-08-09

## G-4.1 — P0 detect/alarm/lifecycle (prior)

| Case | Layers | Status |
|------|--------|--------|
| `rt_p0_detect_single_onnx` | L_lifecycle, L_detect | PASS |
| `rt_p0_heartbeat_lifecycle` | L_lifecycle | PASS |
| `rt_p0_alert_hook_roi` | L_lifecycle, L_detect, L_alarm | PASS |

Evidence: `python tools/runtime_parity_gate.py certify --profile win_cpp` (P0 subset) exit 0.

## G-4.2 — P1 motion_gate + tracking

| Case | Layers | CAP | Status |
|------|--------|-----|--------|
| `rt_p1_motion_gate` | L_lifecycle, L_motion | CAP-MOTION-GATE | **PASS** |
| `rt_p1_tracking_stable` | L_lifecycle, L_track | CAP-TRACKING | **PASS** |

### Implementation summary

- **C++** `MotionGate` (`RUNTIME/src/motion/`) — frame-diff gate aligned with `VIDEO/app/utils/motion_gate.py`; skips infer on below-threshold sample frames; logs on failure.
- **C++** `SimpleTracker` (`RUNTIME/src/tracking/`) — IoU/center/shape similarity tracker; `track_id` on `DetectObject` and alert hook JSON.
- **Pipeline** integrates gate + tracker; `ParityRecorder` writes `logs/cpp_sample/<case>/parity_sample.json` for testbed sampling.
- **Testbed** manifest P1 cases, fixtures, `L_motion`/`L_track` diff layers, `win_cpp` profile `case_ids` includes P1.

### Certify commands (2026-08-09)

```bat
cd F:\acme\.worktrees\runtime-parity
python tools\runtime_parity_gate.py record-oracle-smoke --case rt_p1_motion_gate --engine onnx
python tools\runtime_parity_gate.py record-oracle-smoke --case rt_p1_tracking_stable --engine onnx
python tools\runtime_parity_gate.py run --executor cpp --case rt_p1_motion_gate
python tools\runtime_parity_gate.py run --executor cpp --case rt_p1_tracking_stable
python tools\runtime_parity_gate.py certify --profile win_cpp
```

Exit code: **0** (all five `win_cpp` cases green).

Report: `logs/runtime_parity_report.json`

### UI note

`WEB/AlgorithmTaskModal.vue` not present in candidate worktree; cpp tracking/motion remain configurable via ini (`[tracking]` / `[motion_gate]`) from `runtime_config_service`. UI re-enable deferred to when WEB subtree is available.

### Orchestrator acceptance (2026-08-09)

- Commit: `3a76bb3`
- Re-verify: `certify --profile win_cpp` exit **0** (5 cases: 3×P0 + `rt_p1_motion_gate` + `rt_p1_tracking_stable`)
- **G-4.2 ACCEPTED**

## G-4.3 — snap/patrol schedule P0

| Case | Layers | CAP | Status |
|------|--------|-----|--------|
| `snap_p0_cron_slot` | L_lifecycle, L_schedule | CAP-CRON-SNAP | **PASS** |
| `snap_p0_alert_payload` | L_lifecycle, L_alarm | CAP-ALERT-HOOK (snapshot) | **PASS** |
| `patrol_p0_pool_interval` | L_lifecycle, L_schedule | CAP-PATROL-POOL | **PASS** |
| `patrol_p0_heartbeat_progress` | L_lifecycle | CAP-PATROL-PROGRESS | **PASS** |
| `patrol_p1_hybrid_focus` | L_lifecycle, L_schedule | CAP-PATROL-HYBRID | **PASS** |

### Implementation summary

- **C++** `cron/CronUtils` — Asia/Shanghai (UTC+8) 5/6-field cron matching aligned with `VIDEO/app/utils/cron_utils.py` (match window + slot key).
- **C++** `SnapScheduler` — per-device slot dedupe; parity `schedule` events for L_schedule.
- **C++** `PatrolScheduler` — **hybrid** (focus `interval/2` + background `pool_size-1`); warmup 3 frames; parallel batch; `total_patrols`/`total_detections`/`progress` on heartbeat.
- **Hook** snap alerts emit `task_type=snapshot` (Python-aligned).
- **Testbed** P0/P1 cases in manifest `win_cpp`; `L_schedule` diff; oracle smoke + cpp sample.

### Certify commands (2026-08-09)

```bat
cd F:\acme\.worktrees\runtime-parity
. .\RUNTIME\scripts\deploy.env.ps1
set ACME_ORACLE_ROOT=F:\acme
set ACME_CANDIDATE_ROOT=%CD%
python tools\runtime_parity_gate.py record-oracle-smoke --case snap_p0_cron_slot --engine onnx
python tools\runtime_parity_gate.py record-oracle-smoke --case snap_p0_alert_payload --engine onnx
python tools\runtime_parity_gate.py record-oracle-smoke --case patrol_p0_pool_interval --engine onnx
python tools\runtime_parity_gate.py record-oracle-smoke --case patrol_p0_heartbeat_progress --engine onnx
python tools\runtime_parity_gate.py record-oracle-smoke --case patrol_p1_hybrid_focus --engine onnx
python tools\runtime_parity_gate.py run --executor cpp --case snap_p0_cron_slot
python tools\runtime_parity_gate.py run --executor cpp --case snap_p0_alert_payload
python tools\runtime_parity_gate.py run --executor cpp --case patrol_p0_pool_interval
python tools\runtime_parity_gate.py run --executor cpp --case patrol_p0_heartbeat_progress
python tools\runtime_parity_gate.py run --executor cpp --case patrol_p1_hybrid_focus
python tools\runtime_parity_gate.py certify --profile win_cpp
```

Exit code: **0** (10 `win_cpp` cases green: 5 prior realtime + 5 snap/patrol).

Report: `logs/runtime_parity_report.json`

### Orchestrator acceptance (2026-08-10)

- Commits: `88be2ea` (feat), `d57637f` (docs checkbox)
- Re-verify: `certify --profile win_cpp` exit **0** (10/10: prior 5 realtime + snap/patrol P0/P1)
- **G-4.3 ACCEPTED**

## G-4.4 — overlay / RTMP thresholds

| Case | Layers | CAP | Status |
|------|--------|-----|--------|
| `rt_p1_overlay_timing` | L_lifecycle, L_overlay, L_detect | CAP-OVERLAY-*, CAP-DRAW-OVERLAY | **PASS** |
| `rt_p1_rtmp_stream` | L_lifecycle, L_stream | CAP-RTMP-PUSH, CAP-FIXED-RATE-PUSH | **PASS** |

### Implementation summary

- **C++** `ParityRecorder` samples overlay draw latency (capture→draw) and RTMP push meta/counters; `Pipeline` records on draw + `encodeAndPush`; `RTMPEncoder` exposes push/bitrate getters.
- **Gate** `L_overlay` / `L_stream` diffs in `diff_layers.py`; `run_cpp` enables `enable_draw` / `enable_rtmp` and mid-run ffprobe against SRS HTTP-FLV (`http://127.0.0.1:8080/live/...flv`).
- **Thresholds** `overlay.p95_latency_ms_slack=200`; `stream` width/height/fps/bitrate bands + `min_pushed_ok`.
- **Dual-queue 1:1 not required** — P1 gate is overlay P95 slack + ffprobe profile.
- **win_cpp** retains prior 10 cases and adds the two G-4.4 cases (12 total).

### Certify commands (2026-08-10)

```bat
cd F:\acme\.worktrees\runtime-parity
. .\RUNTIME\scripts\deploy.env.ps1
set ACME_ORACLE_ROOT=F:\acme
set ACME_CANDIDATE_ROOT=%CD%
python tools\runtime_parity_gate.py record-oracle-smoke --case rt_p1_overlay_timing --engine onnx
python tools\runtime_parity_gate.py record-oracle-smoke --case rt_p1_rtmp_stream --engine onnx
python tools\runtime_parity_gate.py run --executor cpp --case rt_p1_overlay_timing
python tools\runtime_parity_gate.py run --executor cpp --case rt_p1_rtmp_stream
python tools\runtime_parity_gate.py certify --profile win_cpp
```

Exit code: **0** (12 `win_cpp` cases green: prior 10 + overlay + rtmp).

Report: `logs/runtime_parity_report.json`

### RTMP receive endpoint

Local Docker `srs-server` on `1935` / HTTP-FLV `8080` (shared middleware). Stream name: `parity_rt_p1_rtmp_stream`.

### Orchestrator acceptance

- Pending orchestrator review (implementer does not self-ACCEPT).
