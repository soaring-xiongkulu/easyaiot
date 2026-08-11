# CP-6 Report — Patrol main-path code parity (handoff for CP-7 / CP-10)

**Status:** PASS  
**Pack:** CP-6 (W4)  
**Date:** 2026-08-11  
**Evidence:** `logs/cp-6-patrol.json`  
**nested_subagents:** none

## Prior reports

- [cp-1-report.md](./cp-1-report.md) — zero fallback on alert Kafka
- [cp-3-report.md](./cp-3-report.md) — sink `:48092` + PG 15432
- [cp-2-report.md](./cp-2-report.md) — matching consume chain via iot-sink
- [cp-4-report.md](./cp-4-report.md) — snap scheduler init_all_tasks
- [cp-5-report.md](./cp-5-report.md) — honest services/status (no DB-only fake running)
- [fr-w2-patrol-report.md](./fr-w2-patrol-report.md) — route inventory 9/9 baseline

## What changed

| File | Change |
|------|--------|
| `PatrolSupervisor.java` | `countAlive()` mirrors Python `_running_session_count` (alive processes, not DB); `VIDEO_CONTROL_URL` / `VIDEO_HEARTBEAT_URL` align gateway `{JAVA_BACKEND_URL}/admin-api/video` |
| `PatrolSessionService.java` | Session cap uses `supervisor.countAlive()`; non-blocking start lock (`巡检正在启动中`); heartbeat skips status flip when session already `stopped` |
| `PatrolController.java` | `POST .../stop` returns `code=0/400` + HTTP 200/400 like Python `stop_session` (was always `code=0`) |
| `.scripts/cp-6-evidence.ps1` | Main-path evidence runner |

**Not changed:** `PatrolProgressHub` SSE semantics (already aligned); patrol daemon still launches `run_deploy.py` — honest fail when script missing, not stub success.

## Oracle vs Java

| Concern | Oracle (Python) | Java (CP-6) |
|---------|-----------------|-------------|
| Create | `status=stopped`, `patrol_mode=pool`, 26-key `to_dict` | Same keys via `PatrolSessionRow.toMap()` |
| Start OK | `code=0`, HTTP 200, `status=running`, `service_log_path` set | Same; supervisor spawns daemon thread |
| Start cap | `_running_session_count()` = alive Popen only | `supervisor.countAlive()` — **fixed** (was DB `countRunning`) |
| Stats | `build_session_stats_payload` + `completed_devices/total_devices/completion_ratio` | `buildStatsPayload` identical shape |
| Events | SSE `event: progress` + initial stats JSON + `: keepalive` | `PatrolProgressHub` same |
| Heartbeat | Updates progress/totals; no status flip if `stopped` | **Fixed** — passes `status=null` when stopped |
| Stop | `code=0 if ok else 400`, `status=stopped` | **Fixed** — controller HTTP/code parity |
| Validation | empty `model_ids` → 400; missing session stats → 404 | Same via `VideoBusinessException` |

## Evidence summary

| Scenario | Result |
|----------|--------|
| `POST /session` → 26 keys, `status=stopped` | pass |
| `POST /session/{id}/start` → `status=running`, log path set | pass |
| `GET /session/{id}/stats` → stats keys + `total_devices=1` | pass |
| `GET /session/{id}/events` → SSE `progress` + `completed_devices` | pass |
| `POST /heartbeat` → `total_patrols=3`, `completed_devices=1` | pass |
| `POST /session/{id}/stop` → `status=stopped` | pass |
| empty `model_ids` → `code=400` | pass |
| missing session stats → `code=404` | pass |

Correlation: `cp-6-evidence-20260811232339` — session **50** on gateway `:48080`, profile `local`.

## Notes for CP-7 / CP-10

1. Session **50** left `stopped` after evidence.
2. Orphan sessions 48–49 may exist in DB from prior runs; preclean stops `status=running` rows.
3. Patrol worker process may exit quickly if `run_deploy.py` deps missing — DB still shows `running` until stop; **not** fake API success (start returns real supervisor + log path).
4. **CP-9** FlightHub/directory parallel pack may have landed separately.

## Ready for W4 continue?

**Yes** — CP-6 closes G-06 / D-09 patrol main-path; CP-7 AudioTalk next on W4 line.
