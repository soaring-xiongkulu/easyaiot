# Runtime Parity Certify Status

> Candidate: `F:/acme/.worktrees/runtime-parity` (`feat/runtime-parity`)  
> Recorded: **2026-08-10** (Phase 5 / G-5.1 · G-5.2)

Environment:

- `ACME_ORACLE_ROOT=F:\acme`
- `ACME_CANDIDATE_ROOT=F:\acme\.worktrees\runtime-parity`
- Loaded `RUNTIME/scripts/deploy.env.ps1` before runs

Reports under `/logs/` are gitignored; SHA256 below is authoritative. Copies archived immediately after each profile to avoid overwrite.

## G-5.1 — `linux_full`

| Field | Value |
|-------|-------|
| Command | `python tools/runtime_parity_gate.py certify --profile linux_full` |
| Exit code | **0** |
| `ok` | `true` |
| Report archive | `logs/certify_linux_full.json` |
| SHA256 | `6A0D0A6C5BDC6AB6823C7882454A4000CF6D823C4956ED0BCAAB936F754F5B97` |
| Generated at | `2026-08-09T16:22:53` |
| Case count | **7** |
| Layer summary | pass=13, fail=0, not_sampled=0, warn=0 |

Cases (all `ok=true`):

1. `rt_p0_detect_single_onnx` — L_lifecycle, L_detect  
2. `rt_p0_heartbeat_lifecycle` — L_lifecycle  
3. `rt_p0_alert_hook_roi` — L_lifecycle, L_detect, L_alarm  
4. `snap_p0_cron_slot` — L_lifecycle, L_schedule  
5. `snap_p0_alert_payload` — L_lifecycle, L_alarm  
6. `patrol_p0_pool_interval` — L_lifecycle, L_schedule  
7. `patrol_p0_heartbeat_progress` — L_lifecycle  

## G-5.2 — `win_cpp`

| Field | Value |
|-------|-------|
| Command | `python tools/runtime_parity_gate.py certify --profile win_cpp` |
| Exit code | **0** |
| `ok` | `true` |
| Report archive | `logs/certify_win_cpp.json` |
| SHA256 | `83AE91D6A1E48E3185CE54A69EE3DCE43D5EE2B5789A8FE74D9EA0DE67510D55` |
| Generated at | (written immediately after linux_full archive) |
| Case count | **12** |
| Layer summary | pass=24, fail=0, not_sampled=0, warn=0 |

Cases (all `ok=true`):

1. `rt_p0_detect_single_onnx` — L_lifecycle, L_detect  
2. `rt_p0_heartbeat_lifecycle` — L_lifecycle  
3. `rt_p0_alert_hook_roi` — L_lifecycle, L_detect, L_alarm  
4. `rt_p1_motion_gate` — L_lifecycle, L_motion  
5. `rt_p1_tracking_stable` — L_lifecycle, L_track  
6. `snap_p0_cron_slot` — L_lifecycle, L_schedule  
7. `snap_p0_alert_payload` — L_lifecycle, L_alarm  
8. `patrol_p0_pool_interval` — L_lifecycle, L_schedule  
9. `patrol_p0_heartbeat_progress` — L_lifecycle  
10. `patrol_p1_hybrid_focus` — L_lifecycle, L_schedule  
11. `rt_p1_overlay_timing` — L_lifecycle, L_overlay, L_detect  
12. `rt_p1_rtmp_stream` — L_lifecycle, L_stream  

## Verdict (implementer)

Both planned certify profiles exit **0** with `ok=true`. No product exemption list required for `win_cpp`.

Deletion of Python algorithm services is **not** claimed here — see `gates/PHASE_5_GATE.md` G-5.3 (dry-run only).

## Post-quarantine re-verify (orchestrator, 2026-08-10)

After `safe_fsops` quarantine execute on candidate:

- `certify --profile win_cpp` → exit **0** (12/12)
- `certify --profile linux_full` → exit **0** (7/7)
- Oracle Python services left intact under `F:/acme/VIDEO/services/`
