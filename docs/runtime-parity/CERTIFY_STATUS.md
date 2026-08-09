# Runtime Parity Certify Status

> Candidate: `F:/acme/.worktrees/runtime-parity` (`feat/runtime-parity`)  
> Recorded: **2026-08-10** (Phase 5 gap-close wave)

Environment:

- `ACME_ORACLE_ROOT=F:\acme`
- `ACME_CANDIDATE_ROOT=F:\acme\.worktrees\runtime-parity`
- Loaded `RUNTIME/scripts/deploy.env.ps1` before runs
- `PYTHONPATH=VIDEO` for platform samplers

Reports under `/logs/` are gitignored; SHA256 below is authoritative. Copies archived immediately after each profile to avoid overwrite.

## Gap-close — `linux_full`

| Field | Value |
|-------|-------|
| Command | `python tools/runtime_parity_gate.py certify --profile linux_full` |
| Exit code | **0** |
| `ok` | `true` |
| Report archive | `logs/certify_linux_full.json` |
| SHA256 | `136B780EBFB8962FC7D92D6B073A922898708A5F74943807D33D4A47CB06E6FE` |
| Generated at | `2026-08-09T16:58:53` |
| Case count | **11** |

Cases (all `ok=true`):

1. `rt_p0_detect_single_onnx`
2. `rt_p0_heartbeat_lifecycle`
3. `rt_p0_alert_hook_roi`
4. `vid_p0_hook_kafka` *(new)*
5. `vid_p0_face_match_chain` *(new)*
6. `e2e_p0_realtime_python_vs_cpp` *(new)*
7. `perf_p0_realtime_latency` *(new)*
8. `snap_p0_cron_slot`
9. `snap_p0_alert_payload`
10. `patrol_p0_pool_interval`
11. `patrol_p0_heartbeat_progress`

## Gap-close — `win_cpp`

| Field | Value |
|-------|-------|
| Command | `python tools/runtime_parity_gate.py certify --profile win_cpp` |
| Exit code | **0** |
| `ok` | `true` |
| Report archive | `logs/certify_win_cpp.json` |
| SHA256 | `884B6263A48EF3C45B9A86C3A36BD2014C65385634955BF2ABE2DE09EC8298A6` |
| Case count | **23** |

Includes prior G-4.x set plus: `vid_p0_*`, `e2e_p0_*`, `perf_p0_*`, `rt_p1_alert_class`, `rt_p1_face_plate_filter`, `rt_p1_multi_model`, `rt_p1_defense_armed`, `patrol_p1_rotate_order`, `snap_p1_snap_space`, `vid_p1_post_process_enqueue`.

## Prior Phase 5 hashes (superseded)

| Profile | Old SHA256 | Cases |
|---------|------------|-------|
| linux_full | `6A0D0A6C…F754F5B97` | 7 |
| win_cpp | `83AE91D6…67510D55` | 12 |

See also [`gates/PHASE_5_GAP_CLOSE.md`](./gates/PHASE_5_GAP_CLOSE.md).
