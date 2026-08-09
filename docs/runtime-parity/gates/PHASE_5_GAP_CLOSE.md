# Phase 5 Gap Close Evidence

> Candidate: `F:/acme/.worktrees/runtime-parity` (`feat/runtime-parity`)  
> Date: **2026-08-10**  
> Goal: Close HANDOFF §2.1 / CAP-BUSINESS-DECISIONS / reports/06 gaps that remained after G-5.* ACCEPTED.

## Verdict

**PASS (implementation wave)** — doctor exit 0; `linux_full` 11/11; `win_cpp` 23/23; implemented CAPs no longer land in `unsupportedCaps`.

### Orchestrator acceptance (2026-08-10)

- Re-verify: `doctor` / `certify --profile linux_full` / `certify --profile win_cpp` all exit **0**
- Commits: `ac60e59`, `0f30d73`, `7b91413`
- **GAP-CLOSE WAVE ACCEPTED**
- Remaining HANDOFF「要」debt (GB28181 / NVENC-AUTO / plate-match e2e) continues in follow-up wave — not silently closed.

## A. Missing P0 (reports/06, non-SAM)

| Case | Layer(s) | Evidence |
|------|----------|----------|
| `vid_p0_hook_kafka` | L_kafka, L_alarm | platform mock: publish + suppress; golden keys include device_name/region |
| `vid_p0_face_match_chain` | L_face | `alert_post_orchestrator` cpp path under mocks |
| `e2e_p0_realtime_python_vs_cpp` | L_lifecycle, L_detect, L_alarm, L_e2e_alarm | frozen python golden vs live cpp RUNTIME |
| `perf_p0_realtime_latency` | L_perf | relative to `thresholds.json` (p95 ratio/slack, fps, rss) |

`linux_full` case_filter=P0 now includes the above (11 cases).  
`win_cpp` includes the P0 gap-close set plus P1 CAP cases.

## B. Frame CAPs previously marked unsupported

| CAP | Placement | Implementation |
|-----|-----------|----------------|
| CAP-ALERT-CLASS-FILTER | C++ `AlertFilters` | whitelist `alert_class_names` |
| CAP-FACE-FILTER / CAP-PLATE-FILTER | C++ `AlertFilters` | drop face/plate classes when flag false |
| CAP-MULTI-MODEL | C++ `Yolov11ThreadPool::loadExtraModels` | serial merge after primary |
| CAP-DEFENSE | C++ `isDefenseArmed` | `active` / windows schedule; skip alerts when disarmed |
| CAP-SNAP-SPACE | VIDEO platform sample | ingest count (no MinIO required in C++) |
| CAP-PATROL-ROTATE | already in `PatrolScheduler` | case `patrol_p1_rotate_order` green |
| CAP-POST-PROCESS / CAP-POSE | VIDEO owned | `vid_p1_post_process_enqueue`; **not** cpp unsupported |
| CAP-FACE-MATCH / CAP-PLATE-MATCH | VIDEO owned | `vid_p0_face_match_chain`; **not** cpp unsupported |
| CAP-TRACKING / CAP-MOTION-GATE / CAP-PATROL-HYBRID | already C++ | removed from VIDEO `[unsupported]` emit |

`ConfigParser` ignores stale `[unsupported]` listings for implemented/VIDEO-owned CAP IDs.  
`runtime_config_service._contract_ini_block` only keeps product-vetoed/P2 deferred (SAM / GB28181 / NVENC-AUTO).

## C. Certify hashes (2026-08-10)

| Profile | Exit | Cases | SHA256 |
|---------|------|-------|--------|
| `linux_full` | 0 | 11 | `136B780EBFB8962FC7D92D6B073A922898708A5F74943807D33D4A47CB06E6FE` |
| `win_cpp` | 0 | 23 | `884B6263A48EF3C45B9A86C3A36BD2014C65385634955BF2ABE2DE09EC8298A6` |

Archives: `logs/certify_linux_full.json`, `logs/certify_win_cpp.json` (gitignored; hashes authoritative).

## D. Debt still deferred (explicit, not silent)

| CAP | Reason |
|-----|--------|
| CAP-SAM-TASK | Product veto (HANDOFF) |
| CAP-GB28181-SRC | P2 — parse/flag → WARNING unsupported; no silent success |
| CAP-NVENC-AUTO | P2 — same |
| CAP-PLATE-MATCH e2e case `vid_p1_plate_match_chain` | Not in this wave; face chain covers orchestrator pattern |
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
