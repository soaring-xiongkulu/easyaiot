# CP-5 Report — Algorithm services/status honesty (handoff for CP-6 / CP-10)

**Status:** PASS  
**Pack:** CP-5 (W3)  
**Date:** 2026-08-11  
**Evidence:** `logs/cp-5-services-status.json`  
**nested_subagents:** none

## Prior reports

- [cp-1-report.md](./cp-1-report.md) — zero fallback on alert Kafka
- [cp-2-report.md](./cp-2-report.md) — matching consume chain via iot-sink
- [cp-3-report.md](./cp-3-report.md) — sink 15432 + enqueue_ok
- [phase2-a2-report.md](./phase2-a2-report.md) — RUNTIME start/stop + services/status baseline

## What changed

| File | Change |
|------|--------|
| `AlgorithmTaskLifecycleService.java` | Removed `resolveServiceStatus` certify heuristic that returned `running` when `is_enabled=true` + `run_status=running` even if OS process dead |
| `.scripts/cp-5-evidence.ps1` | Evidence runner: start → running; orphan DB + kill PID → `status=stopped` |

**Not changed:** `extractor` / `sorter` / `pusher` remain `null` in `getServicesStatus` — **Python parity** (`algorithm_task.py` new architecture always null for these legacy fields).

## Oracle vs Java

| Concern | Oracle (Python) | Java (CP-5) |
|---------|-----------------|-------------|
| Running signal | `_running_daemons` poll **or** heartbeat &lt;60s | `supervisor.isAlive()` **or** remote healthy **or** heartbeat &lt;60s |
| DB-only running | **No** — stale heartbeat + dead daemon → `stopped` | **Fixed** — removed DB `is_enabled`+`run_status` heuristic |
| Legacy fields | `extractor`/`sorter`/`pusher` = `None` | Same `null` — not a gap |
| `run_status` field | Exposed from DB row | Exposed from DB row (may still say `running` while `status=stopped` after kill — honest split) |

## Evidence summary

| Scenario | Result |
|----------|--------|
| `POST /task/61/start` → `GET .../services/status` | `realtime_service.status=running`, PID alive |
| `extractor`/`sorter`/`pusher` | all `null` (Python parity) |
| Stop supervisor + SQL `is_enabled=true`, `run_status=running`, heartbeat 5m stale | `realtime_service.status=stopped` (not fake running from DB) |
| Start → `Stop-Process` RUNTIME → stale heartbeat | `realtime_service.status=stopped` while DB `run_status` may still be `running` |

Correlation: `cp-5-evidence-20260811224610` — task **61** `frb26_alert_e2e` on gateway `:48080`, profile `local`.

## Notes for CP-4 / CP-6

1. **Task 61** left stopped after evidence (`POST /stop` in script).
2. **video-server** may still be running from CP-5 evidence (`logs/cp-5-video-server.log`).
3. **Heartbeat &lt;60s** still reports `running` briefly after kill if heartbeat fresh — matches Python; CP-5 evidence ages heartbeat to 5m before asserting `stopped`.
4. **CP-4** snap scheduler files untouched by CP-5.

## Ready for W4?

**Yes** — CP-5 closes G-05 / D-05 fake running heuristic; W3 CP-4 may still be pending in parallel.
