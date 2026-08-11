# CODE-PARITY — Agent / pack index (Part1)

> Wave 0 docs: `decb37e`. **Implementation authorized under W1→W5 waves (2026-08-11).**  
> Phase 2 closed: see [PHASE2_AGENT_INDEX.md](./PHASE2_AGENT_INDEX.md).

## Collaboration rules (binding) — UPDATED for full Part1 run

1. **Wave order mandatory:** W1 → W2 → W3 → W4 → W5. Never open all ten packs at once.  
2. **W1:** CP-1 alone; must merge before W2.  
3. **W2:** CP-3 then CP-2 **serial** on one line (same sink files/process). **Forbidden:** two agents editing `iot-sink` in parallel.  
4. **W3:** CP-4 ∥ CP-5 allowed (different files).  
5. **W4:** CP-6 ∥ CP-7 ∥ CP-8 ∥ CP-9 allowed; Done when = **Python key semantics**, not “Controller 200”.  
6. **W5:** CP-10 after CP-4/CP-5.  
7. Each pack = **leaf subagent**: implementer does **all** work. **Never call the Task tool. No nested subagents.**  
8. Before exit: write `.superpowers/sdd/briefs/cp-N-report.md` (handoff for next).  
9. Next pack prompt **must link prior reports** in the same CODE-PARITY task.  
10. Update this index + `docs/video-java/CODE_PARITY_BACKLOG.md` + `HANDOFF.md`.  
11. Evidence `logs/cp-N-*.json`. **Zero Fallback** on `local`.  
12. No FR-B, no COMPLETE, no delete Python, no mini/direct/stub as PASS. No Part2 engine install as Part1 complete.

## Prior Phase 2 reports (read before CP work)

| Pack | Report |
|------|--------|
| A1–A7 | [PHASE2_AGENT_INDEX.md](./PHASE2_AGENT_INDEX.md) |

## Part1 packs

| Pack | Wave | Status | Brief | Report | Evidence | Commit |
|------|------|--------|-------|--------|----------|--------|
| CP-1 No Fallback | W1 | **PASS** | [cp-1-brief.md](./briefs/cp-1-brief.md) | [cp-1-report.md](./briefs/cp-1-report.md) | `logs/cp-1-no-fallback.json` | `e7ee0c9` |
| CP-3 iot-sink enqueue | W2-first | pending | [cp-3-brief.md](./briefs/cp-3-brief.md) | — | `logs/cp-3-sink-enqueue.json` | — |
| CP-2 Matching consume | W2-second | pending | [cp-2-brief.md](./briefs/cp-2-brief.md) | — | `logs/cp-2-matching-consume.json` | — |
| CP-4 Snap scheduler | W3 | pending | [cp-4-brief.md](./briefs/cp-4-brief.md) | — | `logs/cp-4-snap-scheduler.json` | — |
| CP-5 services/status | W3 | pending | [cp-5-brief.md](./briefs/cp-5-brief.md) | — | `logs/cp-5-services-status.json` | — |
| CP-6 Patrol | W4 | pending | [cp-6-brief.md](./briefs/cp-6-brief.md) | — | `logs/cp-6-patrol.json` | — |
| CP-7 AudioTalk | W4 | pending | [cp-7-brief.md](./briefs/cp-7-brief.md) | — | `logs/cp-7-audiotalk.json` | — |
| CP-8 GB28181 code | W4 | pending | [cp-8-brief.md](./briefs/cp-8-brief.md) | — | `logs/cp-8-gb28181-code.json` | — |
| CP-9 FlightHub+directory | W4 | pending | [cp-9-brief.md](./briefs/cp-9-brief.md) | — | `logs/cp-9-flighthub-directory.json` | — |
| CP-10 Boot daemons | W5 | pending | [cp-10-brief.md](./briefs/cp-10-brief.md) | — | `logs/cp-10-boot-daemons.json` | — |

## Master docs

| Doc | Role |
|-----|------|
| [CODE_PARITY_BACKLOG.md](../../docs/video-java/CODE_PARITY_BACKLOG.md) | Part1 progress + 零 Fallback |
| [DEP_ENGINE_BACKLOG.md](../../docs/video-java/DEP_ENGINE_BACKLOG.md) | Part2 read-only |
| [CODE_PARITY_PACKS.md](../../docs/video-java/CODE_PARITY_PACKS.md) | Pack definitions |
| [HANDOFF.md](../../docs/video-java/HANDOFF.md) | Current status / next |
