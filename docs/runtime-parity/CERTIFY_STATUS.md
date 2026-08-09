# Runtime Parity Certify Status

> Candidate: `F:/acme/.worktrees/runtime-parity` (`feat/runtime-parity`)  
> Recorded: **2026-08-10** (detect_conf + POST /stop closure)

Environment:

- `ACME_ORACLE_ROOT=F:\acme`
- `ACME_CANDIDATE_ROOT=F:\acme\.worktrees\runtime-parity`
- Loaded `RUNTIME/scripts/deploy.env.ps1` before runs
- `PYTHONPATH=VIDEO` for platform samplers

Reports under `/logs/` are gitignored; SHA256 below is authoritative. Copies archived immediately after each profile to avoid overwrite.

## detect_conf + POST /stop — `linux_full`

| Field | Value |
|-------|-------|
| Command | `python tools/runtime_parity_gate.py certify --profile linux_full` |
| Exit code | **0** |
| `ok` | `true` |
| Report archive | `logs/certify_linux_full.json` |
| SHA256 | `AB7394CBBF844939F855E2C7076143598A7E09C077E8F1876BC673AD4385D0F0` |
| Case count | **11** |

## detect_conf + POST /stop — `win_cpp`

| Field | Value |
|-------|-------|
| Command | `python tools/runtime_parity_gate.py certify --profile win_cpp` |
| Exit code | **0** |
| `ok` | `true` |
| Report archive | `logs/certify_win_cpp.json` |
| SHA256 | `3A0CF8C4C6207DBC42288CFA5CB15B3A3C413327299945A1E970C9D847069F4D` |
| Case count | **27** |

New / newly green:

1. `rt_p1_control_stop` — L_lifecycle with live `POST /stop` → `process_exited`
2. CAP-INFER-THRESHOLD — C++ `score_threshold` = ini `confidence_threshold` / `detect_conf`

## Prior gap-close hashes (superseded)

| Profile | Old SHA256 | Cases |
|---------|------------|-------|
| linux_full | `543DD829…4537AE2` | 11 |
| win_cpp | `85BBB013…18423D0` | 26 |

See also [`gates/PHASE_5_GAP_CLOSE.md`](./gates/PHASE_5_GAP_CLOSE.md).

## Orchestrator re-verify (2026-08-10)

`doctor` + both profiles exit **0** after detect_conf / POST /stop wave.  
**C++ 必做债表项已闭环**（SAM 产品否决除外）。
