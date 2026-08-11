# CP-9 Report — FlightHub + directory code path (handoff for CP-10)

**Status:** PASS  
**Pack:** CP-9 (W4)  
**Date:** 2026-08-11  
**Evidence:** `logs/cp-9-flighthub-directory.json`  
**nested_subagents:** none

## Prior reports

- [cp-1-report.md](./cp-1-report.md) — zero fallback on alert Kafka
- [cp-5-report.md](./cp-5-report.md) — services/status honesty
- [cp-4-report.md](./cp-4-report.md) — snap scheduler init_all_tasks

## What changed

| File | Change |
|------|--------|
| `CameraFlighthubService.java` | Fix env fallback: `coalesce(data field, FLIGHTHUB_* env)` — prior code passed env **value** as map key to `firstNonBlank` |
| `.scripts/cp-9-evidence.ps1` | Evidence runner: config shape, missing-creds honest fail, directory tree/detail/monitor-tree/CRUD |

**Not changed:** `FlighthubSourceSupport` / `CameraDirectoryService` / `CameraController` routes — already aligned with Python oracle; no Part2 FlightHub token/drone required.

## Oracle vs Java

| Concern | Oracle (Python) | Java (CP-9) |
|---------|-----------------|-------------|
| Public config keys | `get_flighthub_public_config()` 11 fields | `FlighthubSourceSupport.publicConfig()` — same keys |
| Live start missing creds | `code=400`, msg lists required fields | `VideoApiResponse.error(400, …)` — honest fail |
| DJI register no source | HTTP 400 `source is required` | `VideoBusinessException(400, …)` |
| Directory tree | `id/name/parent_id/sort_order/is_default/device_count/children` + save times | `CameraDirectoryService.listTree()` — same |
| Monitor tree | `type=directory|device`, stream fields, `unassigned_devices=[]` | `monitorTree(skip_sync=1)` — same shape |
| Default dir DB | `默认分组` root id | API default id **matches** PG `device_directory` row |

## Evidence summary

| Scenario | Result |
|----------|--------|
| `GET …/flighthub/config` | `code=0`, 11 config keys, `live_start_path=/openapi/v0.1/live-stream/start` |
| `POST …/flighthub/live-stream/start` {} | `code=400`, honest required-fields msg |
| `POST …/flighthub/live-stream/start` partial | `code=400` (no token) |
| `POST …/register/device/dji-live` no source | `code=400` |
| `GET …/directory/list` | tree keys OK; default id=1 matches DB |
| `GET …/directory/1` | `device_count`, `children_count`, timestamps present |
| `GET …/directory/monitor-tree?skip_sync=1` | `tree` + device node stream fields |
| Directory CRUD round-trip | create → update sort → delete |

Correlation: `cp-9-evidence-20260811231920` — gateway `:48080`, profile `local`.

## Explainable diffs

1. **Default directory `device_count`:** Python `list_directory_devices` on default may trigger GB sync before count; Java `listTree` uses direct `COUNT(*)`. Evidence: API 15 vs raw PG 17 — fields explainable, not fake success.
2. **Real FlightHub live / drone:** Part2 (E-08) — CP-9 only proves config + honest missing-creds + directory semantics on shared DB.

## Notes for CP-10

- `video-server` restarted for CP-9 evidence (`logs/cp-9-video-server.log`); may coexist with prior CP-5/CP-4 runs.
- Env fallback fix requires rebuilt jar (clean `target` after corrupted partial repackage).

## Ready for W5?

**Yes** — CP-9 closes G-09 / D-10 FlightHub+directory code evidence; CP-10 boot daemons remains.
