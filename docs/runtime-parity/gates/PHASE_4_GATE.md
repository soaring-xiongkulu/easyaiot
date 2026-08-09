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

## G-4.3 / G-4.4 — pending

- G-4.3 snap/patrol schedule P0 cases
- G-4.4 overlay/RTMP thresholds
- Phase 5 full certify / Python runtime removal
