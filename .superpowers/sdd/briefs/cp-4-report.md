# CP-4 Report — Snap scheduler ↔ init_all_tasks (handoff for CP-5 / CP-10)

**Status:** PASS  
**Pack:** CP-4 (W3)  
**Date:** 2026-08-11  
**Evidence:** `logs/cp-4-snap-scheduler.json`  
**nested_subagents:** none

## Prior reports

- [cp-1-report.md](./cp-1-report.md) — zero Fallback alert path
- [cp-3-report.md](./cp-3-report.md) — sink `:48092` + PG 15432
- [cp-2-report.md](./cp-2-report.md) — matching consume→process via iot-sink

## What changed

| File | Change |
|------|--------|
| `SnapTaskRepository.listEnabled()` | Add `LEFT JOIN pusher p` + `pusher_name` — same row shape as `findById`/`list`; **fixes boot crash** that blocked `initAllTasks` |
| `SnapTaskSchedulerService.initAllTasks()` | Log `scheduled_task_ids` on init; add `getScheduledTaskIds()` (Python `_running_tasks` parity) |

**Not changed:** `AlgorithmTaskLifecycleService` (CP-5 scope).

## Bug found & fixed

Pre-CP-4, `initAllTasks` **always failed at startup**:

```
ResultSet 中找不到栏位名称 pusher_name
  at SnapTaskRepository.listEnabled
  at SnapTaskSchedulerService.initAllTasks
  at SnapTaskScheduler.initOnStartup
```

Root cause: `listEnabled()` SELECT omitted `pusher` join while `taskRow()` reads `pusher_name`. API `list`/`findById` had the join; startup path did not.

Evidence pre-fix: `logs/cp-1-video-server.log` L805-839, `logs/phase2-a7-video-server.log` L1062-1097.

## Oracle vs Java

| Concern | Python (`init_all_tasks`) | Java (CP-4) |
|---------|---------------------------|-------------|
| Trigger | `run.py` after app ready | `SnapTaskScheduler` `@EventListener(ApplicationReadyEvent)` |
| Query | `SnapTask.query.filter_by(is_enabled=True).all()` | `SnapTaskRepository.listEnabled()` (`is_enabled=TRUE`) |
| Schedule | `add_task_to_scheduler(task.id)` per row | `addTaskToScheduler(taskId)` per row |
| Running set | `_running_tasks` dict | `runningTasks` ConcurrentHashMap |
| Missing RTSP | `capture_image` → `False`, `status=1`, `exception_reason` | `SnapTaskCaptureService` → `false`, DB `status=1`, `抓拍失败` |

## Evidence summary

| Check | Result |
|-------|--------|
| DB `is_enabled=true` count | **10** ids `[7…16]` |
| Java `initAllTasks` scheduled | **10** ids `[7…16]` — **exact match** |
| Boot log | `enabled=10, scheduled=10, scheduled_task_ids=[7, 8, 9, 10, 11, 12, 13, 14, 15, 16]` |
| Missing source honest fail | Task 16: `status=1`, `exception_reason=抓拍失败`, WARN in log (file/RTSP open fail) — **not** fake snap success |
| `video.skip-background-tasks` | **false** (local commercial) |
| `video.snap-task-scheduler.enabled` | **true** (default) |

## Runtime

```powershell
# After mvn package (see logs/cp-4-mvn-build.log)
$env:NACOS_PASSWORD = "<from F:/acme/VIDEO/.env>"
$env:MINIO_SECRET_KEY = "<from F:/acme/VIDEO/.env>"
java -jar DEVICE/iot-video/iot-video-biz/target/iot-video-biz.jar --spring.profiles.active=local
```

CP-4 evidence run: `logs/cp-4-video-server.log` (PID 43592 on `:48096`).

## Notes for CP-5 / CP-10

1. **video-server restarted** for CP-4 — re-check sink enqueue / matching if CP-5 needs warm stack.
2. **Task 16 cron restored** to `0 */5 * * * *` after fast-cron probe.
3. **CP-5** owns `AlgorithmTaskLifecycleService.resolveServiceStatus` fake-running heuristic — do not conflate with CP-4.
4. **CP-10** should include snap scheduler in `run.py` ↔ Java boot daemons对照表 (now proven).

## Ready for CP-5 (W3 parallel)?

**Yes** — snap `initAllTasks` code-complete with evidence-level DB set parity and honest capture fail on missing RTSP/file source.
