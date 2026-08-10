# Brief — FR-B15: DVR Kafka upload consumer + VIDEO/services 处置表（Python-first）

## HARD RULE — NO NESTED SUBAGENTS
Do ALL work yourself. No Task/subagent tools.

## Python-first (mandatory before Java)
Read and cite from `VIDEO/_retired_python_video/` (and sibling `services/` if present):
1. `services/media_upload_worker/run_worker.py` — Kafka consume `media.dvr.completed`, retry, DLQ
2. `app/services/dvr_upload_service.py` — `process_dvr_event`
3. `app/services/media_kafka_service.py` — upload modes sync/kafka/hybrid, publish/DLQ
4. `app/blueprints/media_hook.py` + camera DVR path comments
5. Inventory other `services/*`: `frame_extractor_service`, `sorter_service`, `pusher_service`, `stream_forward_service`, `media_janitor`, `post_process_worker` — how Python `run.py` / launchers use them vs Java today

## Goal
1. **Implement** Java Kafka consumer for `media.dvr.completed` that calls existing `DvrUploadService.processDvrEvent`, with retry/DLQ parity to Python upload worker. Gate so mini/local default sync mode does not require broker. When mode=kafka/hybrid and consumer enabled but broker down: honest logs, no silent drop forever without DLQ path.
2. **Write disposition** in `FULL_REPLACEMENT_GAP.md` §3 for each `VIDEO/services/*` worker: 迁入 Java / 保留外部进程 / 已由 FR-* 覆盖 / 废弃 — with evidence.
3. Update §8/§9 honesty (remove stale “大量行为桩” where closed; still **forbid COMPLETE** while prod联调/契约回归 open).
4. `python tools/video_java/certify.py --phase 0` exit 0.
5. Commit + `.superpowers/sdd/briefs/fr-b15-report.md` + progress.md.

## Constraints
- Worktree: `F:/acme/.worktrees/video-java`
- `JAVA_HOME=F:\acme\.tools\jdk-21.0.2`
- Maven: `F:\acme\.tools\apache-maven-3.9.16\bin\mvn`
- Do **not** announce COMPLETE
- Prefer Spring Kafka listener or dedicated consumer thread matching existing MediaKafkaProducer patterns

## Done when
- DVR Kafka consumer path exists + config gated; services disposition table in GAP; phase0 0; commit; report with Python cites
