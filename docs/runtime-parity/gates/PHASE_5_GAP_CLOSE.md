# Phase 5 Gap Close Evidence

> Candidate: `F:/acme/.worktrees/runtime-parity` (`feat/runtime-parity`)  
> Date: **2026-08-10**  
> Goal: Close remaining HANDOFF §2.1 / CAP-BUSINESS-DECISIONS debt after prior gap-close ACCEPTED (`ac60e59`/`0f30d73`/`7b91413`).

## Verdict

**PASS (follow-up debt wave)** — doctor exit 0; `linux_full` 11/11; `win_cpp` 26/26; CAP-PLATE-MATCH / CAP-GB28181-SRC / CAP-NVENC-AUTO no longer deferred as unsupported.

### Follow-up wave (this commit set)

- Closed: `vid_p1_plate_match_chain`, `rt_p2_gb28181_relay`, `rt_p2_quality_nvenc`
- Remaining HANDOFF「要」product debt: **CAP-SAM-TASK only** (explicit veto)

## A. Cases added this wave

| Case | Layer(s) | Evidence |
|------|----------|----------|
| `vid_p1_plate_match_chain` | L_plate | VIDEO `alert_post_orchestrator` cpp path (mirror face chain) |
| `rt_p2_gb28181_relay` | L_lifecycle, L_detect | VIDEO resolve + `[stream_src]` → C++ consumes resolved URL; fixture map without WVP |
| `rt_p2_quality_nvenc` | L_lifecycle, L_stream | C++ `RTMPEncoder` NVENC try → software fallback + quality profile; encoder meta |

`linux_full` remains P0-only (11).  
`win_cpp` now 26 cases (prior 23 + 3).

## B. CAP placement

| CAP | Placement | Implementation |
|-----|-----------|----------------|
| CAP-PLATE-MATCH | VIDEO owned | `platform_sample.sample_vid_plate_match_chain` + L_plate diff |
| CAP-GB28181-SRC | VIDEO resolve → C++ consume | `resolve_gb28181_source` (+ `GB28181_FIXTURE_MAP`); ini `[stream_src]`; ConfigParser INFO; reject raw `gb28181://` |
| CAP-NVENC-AUTO | C++ `RTMPEncoder` | Prefer `h264_nvenc`, fallback `libx264`; quality high→medium→low; parity stream meta |

`runtime_config_service._contract_ini_block` no longer lists GB28181/NVENC as unsupported when enabled.  
Product-vetoed only: CAP-SAM-TASK.

## C. Certify hashes (2026-08-10 follow-up)

| Profile | Exit | Cases | SHA256 |
|---------|------|-------|--------|
| `linux_full` | 0 | 11 | `BC5205904DFA8B9AA54694655C5AF1822319B89801242F2770DC684C72F217CA` |
| `win_cpp` | 0 | 26 | `1ABB3A4B4CC2B8F4137A8F87F188BD7E19B098F454A4657A3976DF87725C4317` |

Archives: `logs/certify_linux_full.json`, `logs/certify_win_cpp.json` (gitignored; hashes authoritative).

## D. Debt remaining (explicit)

| CAP | Reason |
|-----|--------|
| CAP-SAM-TASK | Product veto (HANDOFF) |
| Dual-queue overlay 1:1 | Already non-blocking per G-4.4 |
| detect_conf 语义细对齐 | Open polish — not HANDOFF blocker |

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
