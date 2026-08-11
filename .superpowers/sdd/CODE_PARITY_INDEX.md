# CODE-PARITY — Agent / pack index (Part1)

> Wave 0 docs established 2026-08-11. **Implementation = 另令 (start at CP-1).**  
> Phase 2 closed: see [PHASE2_AGENT_INDEX.md](./PHASE2_AGENT_INDEX.md).

## Collaboration rules (binding)

1. One CP pack at a time; implementer does **all** work.  
2. **Never call the Task tool. No nested subagents. Leaf workers only.**  
3. Before exit: write `.superpowers/sdd/briefs/cp-N-report.md`.  
4. Update this index + `docs/video-java/CODE_PARITY_BACKLOG.md` + `HANDOFF.md`.  
5. Evidence under `logs/cp-N-*.json`. **Zero Fallback** on `local`.  
6. No FR-B, no COMPLETE, no delete Python, no mini/direct/stub as PASS.

## Prior Phase 2 reports (read before CP work)

| Pack | Report |
|------|--------|
| A1–A7 | [PHASE2_AGENT_INDEX.md](./PHASE2_AGENT_INDEX.md) |

## Part1 packs

| Pack | Status | Brief | Report | Evidence | Commit |
|------|--------|-------|--------|----------|--------|
| CP-1 No Fallback | pending | [cp-1-brief.md](./briefs/cp-1-brief.md) | — | `logs/cp-1-no-fallback.json` | — |
| CP-2 Matching consume | pending | [cp-2-brief.md](./briefs/cp-2-brief.md) | — | `logs/cp-2-matching-consume.json` | — |
| CP-3 iot-sink enqueue | pending | [cp-3-brief.md](./briefs/cp-3-brief.md) | — | `logs/cp-3-sink-enqueue.json` | — |
| CP-4 Snap scheduler | pending | [cp-4-brief.md](./briefs/cp-4-brief.md) | — | `logs/cp-4-snap-scheduler.json` | — |
| CP-5 services/status | pending | [cp-5-brief.md](./briefs/cp-5-brief.md) | — | `logs/cp-5-services-status.json` | — |
| CP-6 Patrol | pending | [cp-6-brief.md](./briefs/cp-6-brief.md) | — | `logs/cp-6-patrol.json` | — |
| CP-7 AudioTalk | pending | [cp-7-brief.md](./briefs/cp-7-brief.md) | — | `logs/cp-7-audiotalk.json` | — |
| CP-8 GB28181 code | pending | [cp-8-brief.md](./briefs/cp-8-brief.md) | — | `logs/cp-8-gb28181-code.json` | — |
| CP-9 FlightHub+directory | pending | [cp-9-brief.md](./briefs/cp-9-brief.md) | — | `logs/cp-9-flighthub-directory.json` | — |
| CP-10 Boot daemons | pending | [cp-10-brief.md](./briefs/cp-10-brief.md) | — | `logs/cp-10-boot-daemons.json` | — |

## Master docs

| Doc | Role |
|-----|------|
| [CODE_PARITY_BACKLOG.md](../../docs/video-java/CODE_PARITY_BACKLOG.md) | Part1 progress + 零 Fallback |
| [DEP_ENGINE_BACKLOG.md](../../docs/video-java/DEP_ENGINE_BACKLOG.md) | Part2 read-only |
| [CODE_PARITY_PACKS.md](../../docs/video-java/CODE_PARITY_PACKS.md) | Pack definitions |
| [HANDOFF.md](../../docs/video-java/HANDOFF.md) | Current status / next |
