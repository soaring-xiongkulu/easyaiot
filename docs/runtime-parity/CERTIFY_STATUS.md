# Runtime Parity Certify Status

> Candidate: `F:/acme/.worktrees/runtime-parity` (`feat/runtime-parity`)  
> Recorded: **2026-08-10** (Phase 5 gap-close follow-up: plate / GB28181 / NVENC)

Environment:

- `ACME_ORACLE_ROOT=F:\acme`
- `ACME_CANDIDATE_ROOT=F:\acme\.worktrees\runtime-parity`
- Loaded `RUNTIME/scripts/deploy.env.ps1` before runs
- `PYTHONPATH=VIDEO` for platform samplers

Reports under `/logs/` are gitignored; SHA256 below is authoritative. Copies archived immediately after each profile to avoid overwrite.

## Follow-up gap-close — `linux_full`

| Field | Value |
|-------|-------|
| Command | `python tools/runtime_parity_gate.py certify --profile linux_full` |
| Exit code | **0** |
| `ok` | `true` |
| Report archive | `logs/certify_linux_full.json` |
| SHA256 | `BC5205904DFA8B9AA54694655C5AF1822319B89801242F2770DC684C72F217CA` |
| Case count | **11** |

P0 set unchanged (plate/GB28181/NVENC are P1/P2 → win_cpp only).

## Follow-up gap-close — `win_cpp`

| Field | Value |
|-------|-------|
| Command | `python tools/runtime_parity_gate.py certify --profile win_cpp` |
| Exit code | **0** |
| `ok` | `true` |
| Report archive | `logs/certify_win_cpp.json` |
| SHA256 | `1ABB3A4B4CC2B8F4137A8F87F188BD7E19B098F454A4657A3976DF87725C4317` |
| Case count | **26** |

New / newly green:

1. `vid_p1_plate_match_chain` — L_plate (CAP-PLATE-MATCH)
2. `rt_p2_gb28181_relay` — L_lifecycle + L_detect (CAP-GB28181-SRC)
3. `rt_p2_quality_nvenc` — L_lifecycle + L_stream (CAP-NVENC-AUTO)

## Prior gap-close hashes (superseded)

| Profile | Old SHA256 | Cases |
|---------|------------|-------|
| linux_full | `136B780E…D33D4A47CB06E6FE` | 11 |
| win_cpp | `884B6263…EC8298A6` | 23 |

See also [`gates/PHASE_5_GAP_CLOSE.md`](./gates/PHASE_5_GAP_CLOSE.md).
