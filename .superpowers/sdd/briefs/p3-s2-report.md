# P3-S2 Report — Rollback drill + auth smoke notes

**Date:** 2026-08-10  
**Worktree:** `F:/acme/.worktrees/video-java`  
**Branch:** `feat/video-java`  
**Brief:** `.superpowers/sdd/briefs/p3-s2-brief.md`

## STATUS

**DONE** — Rollback drill documented in `ROLLBACK_LOG.md`; gateway restored to `lb://video-server-java`; `PHASE_3_GATE` updated with drill ✅ and provisional auth smoke; Phase 0/1/2 certify exit 0.

## Commits

1. `feat(video-java): P3-S2 rollback drill + gateway auth smoke notes` (this stage)

## Rollback duration

| Segment | Duration |
|---------|----------|
| YAML revert + restore (local) | **40 ms** |
| Prod budget (config + gateway reload) | ~2–5 min (not measured here) |

## Final gateway URI

```yaml
# DEVICE/iot-gateway/.../application.yaml — video-admin-api
uri: lb://video-server-java
```

## Certify exits

| Phase | Exit |
|-------|------|
| 0 | 0 |
| 1 | 0 |
| 2 | 0 |

## Deliverables

| Item | Path |
|------|------|
| Rollback drill log | `docs/video-java/gates/ROLLBACK_LOG.md` |
| Phase 3 gate update | `docs/video-java/gates/PHASE_3_GATE.md` |

## Concerns

1. **Auth smoke provisional** — no local `iot-gateway` on `:48080` and no prod token; ops must run gateway curl in staging/prod to clear checklist item 4.
2. **Drill scope** — local drill timed config edits only; prod rollback still needs gateway restart + Java/Python task ownership steps.
3. **Observe window** — 15–30 min post-cutover monitoring (item 5) not executed in dev.
