# CP-1 Report — Disable alert Kafka fallback (handoff for CP-3 / CP-2)

**Status:** PASS  
**Pack:** CP-1 (W1)  
**Date:** 2026-08-11  
**Evidence:** `logs/cp-1-no-fallback.json`  
**nested_subagents:** none

## Prior reports
- [phase2-a1-report.md](./phase2-a1-report.md) — Kafka success path baseline (`mode=kafka`)
- [CODE_PARITY_INDEX.md](../CODE_PARITY_INDEX.md) W1 rules

## What changed
- `AlertHookService.sendViaKafka`: on Kafka send failure → `status=failed`, `mode=kafka`, error logged; **no** `fallbackPersistOnKafkaFailure`.
- Removed `fallbackPersistOnKafkaFailure` method entirely.
- `persistDirectly` unchanged — only when `video.alert.use-direct-persist=true` / `mini` (not Part1 commercial `local`).

## Evidence summary
| Scenario | Result |
|----------|--------|
| Kafka up → `POST /video/alert/hook` | `code=0`, `data.status=success`, `data.mode=kafka`, topic `iot-alert-notification` |
| Kafka unavailable / send fail | `code=500`, `data=null`, **not** `mode=direct_persist`; `silent_persist_rows=0` |
| Happy path regression | Same as A1 + `kafka_up_happy` in evidence (offset 1346) |

## Oracle vs Java (Part1 stricter)
- Python `_fallback_persist_on_kafka_failure` can return `status=success`, `mode=direct_persist`.
- **Part1 local:** Java must **not** — honest API failure only.

## Audit (same change set)
- No other alert-path silent-success found.
- `PostProcessSinkClient` enqueue failure already returns `false` (sink down → WARN); **CP-3** scope.
- `use-direct-persist` / `use-stub-enqueue` / `use-direct-process` remain **false** on `local` defaults.

## Leftover state
- `algorithm_task` id **61** `is_enabled=true` (was `false` before evidence).
- Kafka container was **recreated** after `docker stop` zombie on Windows Docker; may need `docker compose up -d Kafka` from `F:/acme/.scripts/docker` if broker slow.
- `video-server` may be running on `:48096` from CP-1 evidence run (`logs/cp-1-video-server.log`).

## Notes for CP-3 / CP-2
- **CP-3:** sink `:48092` still refused during alert post-orchestration (expected A6 gap); do not treat enqueue WARN as success.
- **CP-2:** matching consumers still default-off in video; face consume in `iot-sink` — CP-1 ensures Kafka alert failures won't mask matching/alert chain issues via direct_persist.

## Ready for W2?
**Yes** — CP-3 then CP-2 serial on sink/matching line.
