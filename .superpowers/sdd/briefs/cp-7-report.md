# CP-7 Report — AudioTalk main-path code parity (handoff for CP-8 / CP-10)

**Status:** PASS  
**Pack:** CP-7 (W4)  
**Date:** 2026-08-11  
**Evidence:** `logs/cp-7-audiotalk.json`  
**nested_subagents:** none

## Prior reports

- [cp-1-report.md](./cp-1-report.md) — zero fallback on alert Kafka
- [cp-2-report.md](./cp-2-report.md) — matching consume chain via iot-sink
- [cp-3-report.md](./cp-3-report.md) — sink 15432 + enqueue_ok
- [cp-4-report.md](./cp-4-report.md) — snap scheduler init_all_tasks
- [cp-5-report.md](./cp-5-report.md) — honest services/status (no DB-only fake running)
- [cp-6-report.md](./cp-6-report.md) — patrol main-path semantics
- [cp-9-report.md](./cp-9-report.md) — FlightHub + directory (W4 parallel)

## What changed

| File | Change |
|------|--------|
| `AudioTalkController.java` | `@RequestParam(value=...)` explicit names (fixes capabilities binding); `fromServiceResult` maps service `status` → HTTP 400/404/500 (Python parity, not always 200) |
| `AudioTalkService.java` | Blank camera IP → honest 500 before ONVIF; `actionFailure` helper; health returns `onvif_available` / `audio_talk_available`; start checks service availability |
| `.scripts/cp-7-evidence.ps1` | Main-path evidence runner (capabilities/start/stop/health) |

**Not changed:** `AudioTalkSession` / `OnvifAudioBackchannelClient` — real ONVIF backchannel success = Part2 (needs camera fixture).

## Oracle vs Java

| Concern | Oracle (Python) | Java (CP-7) |
|---------|-----------------|-------------|
| Health keys | `status`, `onvif_available`, `audio_talk_available` | Same keys in `data` |
| Capabilities missing device | HTTP 400, `code=400` | Same via controller validation |
| Capabilities invalid device | HTTP 404, `code=404` | Same via service |
| Capabilities fixture (no IP) | `supported=false`, `code=0` | Honest probe fail → `supported=false` |
| Start missing device | HTTP 400 | Same |
| Start invalid device | HTTP 404 | Same |
| Start backchannel fail | HTTP 500, `data.success=false` | Same (blank IP or ONVIF fail) |
| Stop missing session | HTTP 400 | Same |
| Stop ok | HTTP 200, `success` + `session_id` | Same (idempotent even if session absent) |

## Evidence summary

| Scenario | Result |
|----------|--------|
| `GET /health` → `status=ok`, onvif/audio_talk flags | pass |
| `GET /capabilities` no device → HTTP 400 | pass |
| `GET /capabilities?device_id=invalid` → HTTP 404 | pass |
| `GET /capabilities?device_id=vj_p2_device` → `supported=false` | pass |
| `POST /start` no device → HTTP 400 | pass |
| `POST /start` invalid device → HTTP 404 | pass |
| `POST /start` fixture (no IP) → HTTP 500, `success=false` | pass |
| `POST /stop` no session → HTTP 400 | pass |
| `POST /stop` with session_id → `success=true` | pass |

Correlation: `cp-7-evidence-20260811233047` — fixture `vj_p2_device` on `:48096`, profile `local`.

## Notes for CP-8 / CP-10

1. **video-server** may be running from CP-7 evidence (`spring-boot:run` on `:48096`).
2. Gateway `:48080` was 503 during evidence — tests hit **direct** `:48096` (same as CP-6 pattern when Nacos stale).
3. ONVIF backchannel **success path** not green without real camera — expected Part2; CP-7 closes honest failure semantics only.
4. **CP-8** GB28181 code path is next W4 pack.

## Ready for W4 continue?

**Yes** — CP-7 closes G-07 AudioTalk main-path; CP-8 GB28181 remaining on W4 line.
