# Brief — CP-6: Patrol main-path code parity

## CRITICAL — NO NESTED SUBAGENTS
Leaf only when executed (另令).

## Goal
Patrol session create/start/stats/events/stop aligned with Python key semantics (code-level). No device farm required.

## Oracle / Java
- `VIDEO/app/blueprints/patrol.py`
- `PatrolController`, `PatrolSessionService`, `PatrolSupervisor`

## Done when
- Short dual-run evidence `logs/cp-6-patrol.json` + report
- Zero stub success

## Prereq
CP-1
