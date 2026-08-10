# Brief — FR-B27: Matching Kafka 本地 produce 取证 + 字段矩阵自动扩面（Python-first）

## HARD RULE — NO NESTED SUBAGENTS
Do ALL work yourself. No Task/subagent tools.

## Python-first
1. Face/plate matching Kafka publish path in retired Python (`matching` services / blueprints)
2. Java matching produce when `use-direct-process=false`
3. Python `to_dict` patterns for expanding deep field samples OR a generator that extracts keys from Python models for list GET endpoints still missing from deep set

## Goal
1. **Matching Kafka produce:** soak window `use-direct-process=false`; trigger face and/or plate matching API that publishes to Kafka; evidence topic/key/offset in `logs/fr-b26`-style `logs/fr-b27-matching-kafka.*`. Worker consume optional EX if models absent — produce must be honest.
2. **Field matrix expansion:** add ≥10 more deep samples OR auto-generate key asserts from Python models for uncovered list/get endpoints; run deep+matrix; fix Java mismatches; `logs/fr-b27-field-*`.
3. Update checklist 1.4 local-only if produce works; restore mini-safe; phase0 0; GAP/HANDOFF/progress; commit; `fr-b27-report.md`.
4. Still **forbid COMPLETE**.

## Constraints
- Worktree: `F:/acme/.worktrees/video-java`
- JAVA_HOME=`F:\acme\.tools\jdk-21.0.2`
- Synthetic `frb27_*`
- Do not claim COMPLETE

## Done when
- Matching produce evidence OR EX with Python cite + attempt; field expansion landed; phase0 0; commit; report
