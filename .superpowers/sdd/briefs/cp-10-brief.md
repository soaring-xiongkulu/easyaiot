# Brief — CP-10: Boot daemons map (run.py ↔ Java schedulers)

## CRITICAL — NO NESTED SUBAGENTS
Leaf only when executed (另令).

## Goal
Map Python `run.py` background starts to Java schedulers/auto-start/janitor; sample ≥2 items with local evidence.

## Oracle / Java
- `VIDEO/run.py` background block
- `ViewForwardAutoResume*`, `StreamForwardAutoStart*`, `SpaceCleanupScheduler`, `MediaJanitorScheduler`, `AlgorithmTaskAutoStart*`, etc.

## Done when
- Mapping table in report; `logs/cp-10-boot-daemons.json`
- No fake success

## Prereq
CP-4, CP-5 recommended first
