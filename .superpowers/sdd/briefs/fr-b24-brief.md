# Brief — FR-B24: 打通本地 Kafka E2E + record_space 列缺口（Python-first）

## HARD RULE — NO NESTED SUBAGENTS
Do ALL work yourself. No Task/subagent tools.

## Python-first
1. Read `media_kafka_service.py` + DVR/snap upload workers again for E2E expectations.
2. Read Python `RecordSpace` / models for `is_custom_save_time` (and related columns) vs Java `RecordSpace` entity/DDL/migrations.
3. FR-B23 evidence: broker `advertised.listeners=Kafka:9092` blocks host clients; `record_space.is_custom_save_time` missing on some paths.

## Goal
1. **Kafka local E2E:** Make host Java/Python clients able to produce+consume `media.dvr.completed` / `media.snap.completed` against local Kafka. Prefer one of:
   - Document + apply hosts file / docker-compose advertised.listeners fix under `VIDEO/` or local compose override (do not break other stacks silently)
   - Or client bootstrap that works with current broker (if possible)
   Evidence in `logs/fr-b24-kafka-e2e.*` showing consume → `processDvrEvent`/`processSnapEvent` (file-missing honest retry/DLQ OK).
2. **Fix `is_custom_save_time`:** Align Java schema/mapping with Python so `on_dvr` / record paths don’t 500 on missing column (migration or nullable default).
3. Update soak checklist rows 1.2/1.3 with fuller local evidence if E2E works; still label local-only.
4. Restore mini-safe defaults; phase0 0; GAP/progress; commit; `fr-b24-report.md`.
5. Still **forbid COMPLETE**.

## Constraints
- Worktree: `F:/acme/.worktrees/video-java`
- Toolchain as prior
- Synthetic ids `frb24_*`
- Do not claim COMPLETE

## Done when
- Kafka E2E evidence OR documented hard blocker with attempted fix; column issue fixed; phase0 0; commit; report
