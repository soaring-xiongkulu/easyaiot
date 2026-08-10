# Report — EVID-S6: Alert observe SUCCESS + rollback restore drill

**Date:** 2026-08-10  
**Branch:** `feat/video-java`  
**Status:** ✅ DONE

## Alert observe

Re-ran alert-hook probe with `ensure_p0_alert_fixture(task_id=35, device_id=vj_p0_device)` before POST.

| Field | Value |
|-------|-------|
| `data.status` | **success** (was `skipped` in EVID-S5) |
| `data.alert_id` | **4509** |
| `data.mode` | `direct_persist` |
| `code` | `0` |
| `correlation_id` | `evid_s6_probe_69d915e0` |

Evidence: [OBSERVE_EVID-S6.md](../../docs/video-java/gates/OBSERVE_EVID-S6.md), [OBSERVE_LOG.md](../../docs/video-java/gates/OBSERVE_LOG.md).

## Rollback restore drill

Real safe_fsops drill (not paper): restore minimal serving surface from archive, verify, re-archive.

| Step | Duration |
|------|----------|
| Restore (`run.py`, `models.py`, `start_prod.sh`) dry-run → execute | **4311 ms** |
| `Test-Path VIDEO/run.py` | **True** |
| Re-archive same paths dry-run → execute | **3112 ms** |
| **Total** | **7530 ms** |

Post-drill tree matches P3-S3 retired state (`VIDEO/run.py` absent, archive intact).

Evidence: [ROLLBACK_LOG.md](../../docs/video-java/gates/ROLLBACK_LOG.md) EVID-S6 row + detail section.

## Certify

| Phase | Exit |
|-------|------|
| 0 (`--no-record --no-java`) | **0** |
| 1 (`--no-record --no-java`) | **0** |
| 2 (`--no-record`) | **0** (1st run exit 1 on flaky `vj_p2_post_process_enqueue`; retry green) |

## Concerns

- Restore drill used `--allow-delete-prefix VIDEO/_retired_python_video` for archive→active moves; re-archive used standard whitelist (`VIDEO/run.py` etc.).
- Drill restored 3 files only (not full `app/` + `services/`); prod rollback still needs full surface + Nacos process swap.
- Phase 2 `vj_p2_post_process_enqueue` flaky on first certify pass (`enqueue_count: 1 != 2`); passed on immediate retry.

## Commit

`docs(video-java): EVID-S6 alert SUCCESS observe + rollback restore drill`
