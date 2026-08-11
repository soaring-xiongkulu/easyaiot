# Brief — CP-5: Algorithm services/status honesty

## CRITICAL — NO NESTED SUBAGENTS
Leaf only when executed (另令).

## Goal
Remove certify heuristic that reports `running` when OS process is dead but DB says running. Document extractor/sorter/pusher=null as Python-parity (not a gap).

## Oracle / Java
- `algorithm_task.py` `get_task_services_status`
- `AlgorithmTaskLifecycleService.resolveServiceStatus` (L153–158 heuristic)

## Done when
- Kill RUNTIME → status not fake-running solely from DB
- `logs/cp-5-services-status.json` + report

## Prereq
CP-1
