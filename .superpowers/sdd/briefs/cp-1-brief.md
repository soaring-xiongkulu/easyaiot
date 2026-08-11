# Brief — CP-1: Clear commercial Fallback / silent success

## CRITICAL — NO NESTED SUBAGENTS
Leaf worker only when this pack is **executed** (另令). Wave 0 = docs only.

## Goal
On `profile=local`, alert Kafka send failure must **honest-fail**. Disable Part1 use of `fallbackPersistOnKafkaFailure` success path (stricter than Python `_fallback_persist_on_kafka_failure`). Audit other silent-success patterns.

## Oracle / Java
- `F:/acme/VIDEO/app/services/alert_hook_service.py`
- `AlertHookService.java` (`fallbackPersistOnKafkaFailure`)

## Done when
- Kafka failure → not `status=success` with `mode=direct_persist`
- Evidence `logs/cp-1-no-fallback.json`
- Report `.superpowers/sdd/briefs/cp-1-report.md`
- **Zero Fallback** on commercial local path

## Out
No engines, no FR-B, no COMPLETE, no delete Python, no mini-as-PASS.

## Prereq
None (Phase2 A1 success path already proven).
