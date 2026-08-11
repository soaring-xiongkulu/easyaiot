# Phase 2 — Agent report index (shared across A1–A7)

All Phase 2 subagents **must** read prior pack reports before starting, and **must** write their own report before finishing.

| Pack | Status | Brief | Report | Evidence | Commit |
|------|--------|-------|--------|----------|--------|
| A1 Alert Kafka | PASS | [phase2-a1-brief.md](./briefs/phase2-a1-brief.md) | [phase2-a1-report.md](./briefs/phase2-a1-report.md) | `logs/phase2-a1-alert-kafka.json` | `2b3d483` |
| A2 RUNTIME lifecycle | PASS | [phase2-a2-brief.md](./briefs/phase2-a2-brief.md) | [phase2-a2-report.md](./briefs/phase2-a2-report.md) | `logs/phase2-a2-runtime-lifecycle.json` | `e214456` |
| A3 Forward/ffmpeg | PASS | [phase2-a3-brief.md](./briefs/phase2-a3-brief.md) | [phase2-a3-report.md](./briefs/phase2-a3-report.md) | `logs/phase2-a3-forward.json` | `50ce091` |
| A4 Media MinIO | PASS | [phase2-a4-brief.md](./briefs/phase2-a4-brief.md) | [phase2-a4-report.md](./briefs/phase2-a4-report.md) | `logs/phase2-a4-media-minio.json` | `2be5393` |
| A5 Camera | PASS | [phase2-a5-brief.md](./briefs/phase2-a5-brief.md) | [phase2-a5-report.md](./briefs/phase2-a5-report.md) | `logs/phase2-a5-camera.json` | `af3f3bd` |
| A6 Post-process | ⛔缺 sink | [phase2-a6-brief.md](./briefs/phase2-a6-brief.md) | [phase2-a6-report.md](./briefs/phase2-a6-report.md) | `logs/phase2-a6-postprocess.json` | `f7c3276` |
| A7 Matching | ⛔缺 Milvus | [phase2-a7-brief.md](./briefs/phase2-a7-brief.md) | [phase2-a7-report.md](./briefs/phase2-a7-report.md) | `logs/phase2-a7-matching.json` | (pending) |

**Phase 2 A-series closed** (2026-08-11). A1–A5 PASS; A6 ⛔缺 sink; A7 ⛔缺 Milvus/InsightFace. Python Oracle retained; no COMPLETE.

## Collaboration rules (binding)
1. One pack at a time; orchestrator dispatches; implementer does **all** work (no nested subagents). **Never call the Task tool. Leaf workers only.**
2. Before exit: write `.superpowers/sdd/briefs/phase2-aN-report.md` handover for the next agent.
3. Update this index row + `docs/video-java/PHASE2_MAINPATH.md` + `HANDOFF.md`.
4. Evidence JSON under `logs/`; small commit per pack; no secrets/models/conda-env.

