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
| SHA256 | `543DD829C22466478C675C864E9A8AFF10A951D9CE14D332504CAC54B4537AE2` |
| Case count | **11** |

P0 set unchanged (plate/GB28181/NVENC are P1/P2 → win_cpp only).

## Follow-up gap-close — `win_cpp`

| Field | Value |
|-------|-------|
| Command | `python tools/runtime_parity_gate.py certify --profile win_cpp` |
| Exit code | **0** |
| `ok` | `true` |
| Report archive | `logs/certify_win_cpp.json` |
| SHA256 | `85BBB013FFD8FE94E488F25EFD5C3C5CD9FBE559BEE68B8C395D2480E18423D0` |
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

## Orchestrator final re-verify (2026-08-10)

Re-ran `doctor` + both profiles after follow-up wave; updated SHA256 above.  
**Program complete** relative to HANDOFF / CAP-BUSINESS-DECISIONS（SAM 产品否决除外）.
