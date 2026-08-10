# EVID-S1 Report — Alert hook SUCCESS path (not skipped)

## STATUS
**DONE** — `vj_p0_alert_hook` alarm layer passes with `hook_status=success` on **both** oracle and Java; `alert_id_present=true`; certify `--phase 0` exit **0**.

## Commit
`fix(video-java): EVID-S1 alert hook success path + hook_status gate`

## Root cause
1. `task_start_stop` / `stop()` sets `algorithm_task.is_enabled=false` (oracle + Java parity).
2. Later P0 cases (`heartbeat`, `alert_hook`) ran with task 35 disabled → `findAlertEventTask` empty → `hook_status=skipped`.
3. `diff_layers` only compared bilateral snapshot fields; `skipped == skipped` falsely passed.

## Fixes
1. **`ensure_p0_alert_fixture()`** (`vj_common.py`) — before alert hook sampling, re-enable task (`is_enabled=true`, `alert_event_enabled=true`) and ensure device link.
2. **`record_python.py` / `run_java.py`** — call ensure + record `alert_id_present` in alarm snapshot.
3. **`thresholds.json` + `diff_layers.py`** — `vj_p0_alert_hook` requires `hook_status=success` on **each** side (skipped/suppressed now fail).
4. Re-seeded task 35, re-recorded both goldens.

## Verify
```text
python tools/video_java/seed_p0_fixture.py
python tools/video_java/record_python.py vj_p0_alert_hook
python tools/video_java/run_java.py vj_p0_alert_hook
python tools/video_java/certify.py --phase 0
```

| case_id | ok | alarm hook_status (py / java) |
|---------|----|------------------------------|
| **vj_p0_alert_hook** | **PASS** | **success / success** |

**alarm snapshot (both sides):** `hook_status=success`, `mode=direct_persist`, `alert_id_present=true`.

## Concerns
- `ensure_p0_alert_fixture` is test-only DB mutation; must run before each alert hook record (wired in samplers).
- Full certify re-record still times out on oracle `vj_p0_restart` start (pre-existing); diff uses stale python golden for that case.
- Health layer remains `exempt` (EX-ORACLE-HEALTH-DB) — Phase 0 gate not fully green on health.
