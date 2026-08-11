# CP-8 Report — GB28181 source resolve + sync API code parity (handoff for CP-10)

**Status:** PASS  
**Pack:** CP-8 (W4)  
**Date:** 2026-08-11  
**Evidence:** `logs/cp-8-gb28181-code.json`  
**nested_subagents:** none

## Prior reports

- [cp-1-report.md](./cp-1-report.md) — zero fallback on alert Kafka
- [cp-2-report.md](./cp-2-report.md) — matching consume chain via iot-sink
- [cp-3-report.md](./cp-3-report.md) — sink 15432 + enqueue_ok
- [cp-4-report.md](./cp-4-report.md) — snap scheduler init_all_tasks
- [cp-5-report.md](./cp-5-report.md) — honest services/status
- [cp-6-report.md](./cp-6-report.md) — patrol main-path
- [cp-7-report.md](./cp-7-report.md) — AudioTalk honest failures
- [cp-9-report.md](./cp-9-report.md) — FlightHub + directory (W4 parallel)

## What changed

| File | Change |
|------|--------|
| `Gb28181SourceResolver.java` | **New** — mirrors Python `gb28181_source.py`: parse, `GB28181_FIXTURE_MAP`, WVP play URL selection (`rtmp_first` / `hevc_rtsp_first`), candidate bases |
| `Gb28181SourceSupport.java` | `playReadTimeoutMs()` default 60s for play/start (sync stays 15s) |
| `CameraAdminService.java` | `resolveInferenceInput` calls resolver for `gb28181://` (was echoing virtual source) |
| `CameraHardwareService.java` | `captureSnapshot` resolves GB28181 before FFmpeg; honest 500 when play fails |
| `Gb28181SyncService.java` | `ensureGb28181VirtualDevice()` for on-demand `gb28181_*` rows (Python `ensure_gb28181_virtual_device`) |
| `CameraLocationService.java` | Location GET creates missing GB virtual device via sync service |
| `.scripts/cp-8-evidence.ps1` | Fixture sync + resolve + virtual ensure + WVP-unreachable honest null |

**Not changed:** Live SIP/NVR/WVP play success = Part2; `Gb28181SyncService.syncFromWvp` WVP pull path already existed.

## Oracle vs Java

| Concern | Oracle (Python) | Java (CP-8) |
|---------|-----------------|-------------|
| Parse `gb28181://dev/ch` | `parse_gb28181_source` | `Gb28181SourceResolver.parseGb28181Source` |
| Fixture offline resolve | `GB28181_FIXTURE_MAP` env | Same env + JSON/semicolon map |
| Play protocol order | `GB28181_PLAY_PROTOCOL`, `GB28181_HEVC_RTSP_FIRST` | Same env keys + branch meta |
| Inference input resolve | `resolve_gb28181_source` in `resolve_device_inference_input` | `gb28181SourceResolver.resolve` |
| Snapshot grab | `grab_frame_for_snapshot` → resolve first | `captureSnapshot` resolves before FFmpeg |
| Sync from payload | `sync_gb28181_channels_from_payload` | `syncFromPayload` (pre-existing) |
| Virtual device ensure | `ensure_gb28181_virtual_device` | `ensureGb28181VirtualDevice` |
| WVP down, no fixture | `resolve_gb28181_source` → `None` | `resolve` → `null`, API `resolved_source=null` |

## Evidence summary

| Scenario | Result |
|----------|--------|
| `POST /directory/sync-gb28181` with fixture channels | `created=1`, DB `source=gb28181://…/…` |
| `GET …/inference-input` with `GB28181_FIXTURE_MAP` | `resolved_source=rtsp://127.0.0.1:8554/cp8-fixture` |
| `GET …/location` for unknown `gb28181_*` | auto-creates device row |
| Valid GB source, no fixture, WVP down | `resolved_source=null` (honest) |

Correlation: `cp-8-evidence-20260811234758` — direct `:48096`, Nacos discovery disabled for evidence jar, profile `local`.

## Notes for CP-10

1. Evidence starts dedicated jar with `GB28181_FIXTURE_MAP`; production uses WVP or env fixture for offline cert.
2. Gateway `:48080` may 503 when Nacos stale — CP-8 evidence hits direct `:48096` (same as CP-6/CP-7).
3. **Part2:** real WVP play/SIP device matrix not required for Part1 PASS.

## Ready for W5 CP-10?

**Yes** — CP-8 closes G-08 / D-10 GB28181 code path; W4 complete except any parallel stragglers.
