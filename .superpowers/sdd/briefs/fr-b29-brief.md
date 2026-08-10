# Brief — FR-B29: 收口 keys-matrix 59 envelope-only + 8 deferred（Python-first）

## HARD RULE — NO NESTED SUBAGENTS
Do ALL work yourself. No Task/subagent tools.

## Python-first
For every newly mapped GET path, cite Python `to_dict` / blueprint response keys BEFORE asserting. Prefer expanding `KEYS_MATRIX_MAP` (or equivalent) in `field_contract.py`.

## Goal
1. Reduce FR-B28 **59 envelope-only** GET routes by adding Python-first key mappings for as many as practical (target: map ≥30 more, or all remaining that have stable JSON shapes).
2. Clear FR-B28 **8 deferred** item-key skips via seed/setup (alert page, camera locations, matching records, etc.).
3. Fix Java missing keys found.
4. Re-run `--keys-matrix`; artifact `logs/fr-b29-keys-matrix-latest.*` with improved counts.
5. Update GAP/HANDOFF/progress; phase0 0; commit; `fr-b29-report.md`.
6. Still **forbid COMPLETE**.

## Constraints
- Worktree: `F:/acme/.worktrees/video-java`
- JAVA_HOME=`F:\acme\.tools\jdk-21.0.2`
- Do not invent keys; unmapped remain envelope-only honestly
- Do not claim COMPLETE

## Done when
- Mapped count meaningfully up; deferred cleared or EX cited; artifact; phase0 0; commit; report
