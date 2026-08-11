# Brief — CP-3: Post-process ↔ iot-sink reproducible wiring

## CRITICAL — NO NESTED SUBAGENTS
Leaf only when executed (另令).

## Goal
Align `iot-sink` local datasource to PG **15432**; document start runbook; achieve `enqueue_ok=true` without stub.

## Oracle / Java
- `post_process_sink_client.py`, `alert_post_orchestrator.py`
- `PostProcessSinkClient.java`
- `DEVICE/iot-sink/iot-sink-biz/src/main/resources/application-local.yaml` (today `:5432`)

## Done when
- sink listens (e.g. `:48092` or documented port)
- Alert/post-process path → `enqueue_ok=true`
- `logs/cp-3-sink-enqueue.json` + report
- Never flip `use-stub-enqueue=true`

## Prereq
CP-1; share stack with CP-2 (sink also hosts matching consumers)
