# Phase 5 Gap Close Evidence

> Candidate: `F:/acme/.worktrees/runtime-parity` (`feat/runtime-parity`)  
> Date: **2026-08-10**  
> Goal: Close remaining HANDOFF §2.1 / CAP-BUSINESS-DECISIONS debt after prior gap-close ACCEPTED.

## Verdict

**PASS (detect_conf + POST /stop wave)** — doctor exit 0; `linux_full` / `win_cpp` certify green after CAP-INFER-THRESHOLD + CAP-CONTROL-HTTP closure.

### This wave

- Closed: **detect_conf 语义**（C++ `score_threshold` ← ini `confidence_threshold` / `detect_conf`；告警同值）
- Closed: **`POST /stop`**（`rt_p1_control_stop`；保留 `/control/streaming/stop`）
- Remaining HANDOFF「要」product debt: **CAP-SAM-TASK only** (explicit veto)

### Prior follow-up (still accepted)

- Closed: `vid_p1_plate_match_chain`, `rt_p2_gb28181_relay`, `rt_p2_quality_nvenc`

## A. Cases added this wave

| Case | Layer(s) | Evidence |
|------|----------|----------|
| `rt_p1_control_stop` | L_lifecycle | Live `POST /stop` → JSON `{success,message,...}` → `process_exited` |

Prior wave:

| Case | Layer(s) | Evidence |
|------|----------|----------|
| `vid_p1_plate_match_chain` | L_plate | VIDEO `alert_post_orchestrator` cpp path (mirror face chain) |
| `rt_p2_gb28181_relay` | L_lifecycle, L_detect | VIDEO resolve + `[stream_src]` → C++ consumes resolved URL |
| `rt_p2_quality_nvenc` | L_lifecycle, L_stream | C++ `RTMPEncoder` NVENC try → software fallback |

## B. Implementation mapping

| CAP | Where | Behavior |
|-----|-------|----------|
| CAP-INFER-THRESHOLD | `Yolov11Engine::scoreThreshold_` + `Config.detectConfidenceThreshold` | VIDEO `task.detect_conf` → ini `confidence_threshold` → inference + alarm (Python `_get_detect_conf` / `conf=`) |
| CAP-CONTROL-HTTP | `Detech` `POST /stop` | Stop RTMP → respond JSON → `s_exit=1` → graceful process exit; `/health` until teardown |

`runtime_config_service` already writes `confidence_threshold={detect_conf}`.

## C. Certify hashes

| Profile | Exit | Cases | SHA256 |
|---------|------|-------|--------|
| `linux_full` | 0 | 11 | `AB7394CBBF844939F855E2C7076143598A7E09C077E8F1876BC673AD4385D0F0` |
| `win_cpp` | 0 | 27 | `3A0CF8C4C6207DBC42288CFA5CB15B3A3C413327299945A1E970C9D847069F4D` |

Archives: `logs/certify_linux_full.json`, `logs/certify_win_cpp.json` (gitignored; hashes authoritative).

## D. Debt remaining (explicit)

| CAP | Reason |
|-----|--------|
| CAP-SAM-TASK | Product veto (HANDOFF) |
| Dual-queue overlay 1:1 | Already non-blocking per G-4.4 |

## Commands

```powershell
cd F:\acme\.worktrees\runtime-parity
. .\RUNTIME\scripts\deploy.env.ps1
$env:ACME_ORACLE_ROOT='F:\acme'
$env:ACME_CANDIDATE_ROOT=(Get-Location).Path
$env:PYTHONPATH='VIDEO'
python tools/runtime_parity_gate.py doctor
python tools/runtime_parity_gate.py certify --profile linux_full
python tools/runtime_parity_gate.py certify --profile win_cpp
```
