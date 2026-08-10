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
| SHA256 | `EF6500DB3701B5FE67E62475A63E8AD888E518106DDA424FC3CB8AEB1600AB6B` |
| Case count | **11** |

## detect_conf + POST /stop — `win_cpp`

| Field | Value |
|-------|-------|
| Command | `python tools/runtime_parity_gate.py certify --profile win_cpp` |
| Exit code | **0** |
| `ok` | `true` |
| Report archive | `logs/certify_win_cpp.json` |
| SHA256 | `A89A258DAAEECBAAA5E71CF9869E55A4E7E147A85DAF2CD3403386BA492C8FF7` |
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
Updated SHA256 above from orchestrator re-archive.  
**PROGRAM COMPLETE**（SAM 产品否决除外）。

### Effort retrospective（排期校正）

- **规划粗估（历史）：** `PLAN.md` / `HANDOFF.md` 曾写约 **2～4 人月**（易被读成两到三个月）——**高估，勿再引用为排期基准**。
- **本程序实际墙钟：** 约 **3 小时**量级（Phase 门禁推进至 certify 全绿 + quarantine；含后续业务栈冒烟验证）。
- 原因简述：能力面虽宽，但候选侧已有 RUNTIME/VIDEO/certify 资产，红清单驱动下收敛远快于「从零复刻」假设。
