# Brief — CP-4: Snap scheduler ↔ init_all_tasks

## CRITICAL — NO NESTED SUBAGENTS
Leaf only when executed (另令).

## Goal
Prove Java `SnapTaskSchedulerService.initAllTasks()` matches Python `snap_task_service.init_all_tasks` on shared DB enabled tasks.

## Oracle / Java
- `VIDEO/app/services/snap_task_service.py` (`init_all_tasks`)
- `SnapTaskScheduler.java`, `SnapTaskSchedulerService.java`

## Done when
- Boot/init schedules enabled snap tasks; evidence vs Python set
- `logs/cp-4-snap-scheduler.json` + report
- Missing RTSP → honest fail, not fake snap success

## Prereq
CP-1
