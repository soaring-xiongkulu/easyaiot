# Phase 2 A6 Report — Post-process real enqueue (handoff for A7)

**Status:** ⛔ (缺 sink)  
**Pack:** P2-A6  
**Date:** 2026-08-11  
**Commit:** `a28f9b8` — `feat(video-java): phase2 A6 postprocess enqueue parity`  
**Evidence:** `logs/phase2-a6-postprocess.json`  
**nested_subagents:** none

## Prior packs

- A1 PASS (`2b3d483`) — alert Kafka; fixture device `frb26_device`, task 61
- A2 PASS (`e214456`) — algo RUNTIME lifecycle
- A3 PASS (`50ce091`) — ViewForward / stream-forward ffmpeg lifecycle
- A4 PASS (`2be5393`) — media DVR/Snap → Kafka → MinIO
- A5 PASS (`af3f3bd`) — camera list/get/register/update key-field parity
- Phase 1 stack PASS — profile `local`, PG 15432

## What was proven

On local full stack (`profile=local`, `use-stub-enqueue=false`):

1. **Config** — `video.post-process.use-stub-enqueue=false` in committed `application-local.yaml` + `application.yaml` default; stub path not used
2. **Workspace** — `POST /admin-api/video/algorithm/task/61/post-process/init` → workspace + `post_process.py` created; `post_process_enabled=true`
3. **Trigger** — `POST /admin-api/video/alert/hook` with explicit `task_id=61` + `information.detections` → `AlertPostOrchestratorService` schedules enqueue (even when alert hook itself returns `skipped/alert_event_disabled`)
4. **Real HTTP attempt** — `GET .../post-process/status` shows `enqueue_count=1`, `enqueue_url=post-process/enqueue`, **`enqueue_ok=false`** (stub would record `enqueue_ok=true`)
5. **Sink down (honest ⛔)** — `127.0.0.1:48092` connection refused; gateway `POST /admin-api/sink/post-process/enqueue` → 503. Stub **not** restored.

## Oracle vs Java

| Concern | Oracle (Python) | Java candidate |
|---------|-----------------|----------------|
| Enqueue gate | Non-mini: real HTTP, no stub | `PostProcessSinkClient` → `useStubEnqueue=false` → `RestTemplate.postForEntity` |
| Sink URL | `post_process_sink_client._sink_enqueue_url()` → `http://127.0.0.1:48092/post-process/enqueue` | `PostProcessSinkClient.sinkEnqueueUrl()` same default |
| Message shape | `build_post_process_request_message(ctx)` camelCase fields | `buildPostProcessRequestMessage(ctx)` aligned |
| Trigger path | Alert hook → `alert_post_orchestrator` → `enqueue_post_process_request` | `AlertHookService` → `AlertPostOrchestratorService` → `publishPostProcessRequestAsync` |
| Audit | N/A (Python logs only) | `PostProcessEnqueueAudit` exposed via `/post-process/status` |

## Code changes (this pack)

None — FR-B post-process sink client already implemented; this pack is **local full-stack evidence** under commercial `local` profile (`use-stub-enqueue=false`).

## Fixture left in DB / filesystem

- Task 61 `frb26_alert_e2e`: `post_process_enabled=true`, workspace `~/.video-java/post-process-workspaces/task_61/`
- No sink-side Kafka/DB artifacts (sink not running)

## Constraints for A7

- Do NOT flip shortcuts / mini / stub enqueue / sync upload / disable MinIO
- Do NOT claim COMPLETE / delete Python
- Stack unchanged: PG 15432, Kafka 9092, Nacos 8848, MinIO 9000, GW 48080, video 48096 **local**
- **A6 ⛔ is sink availability, not Java wiring** — starting `iot-sink` on `:48092` would unblock a re-run to PASS without code changes

## Concerns

1. **iot-sink not in Phase 1 stack** — video-server correctly attempts real HTTP; local stack lacks running `iot-sink-biz` on 48092
2. **iot-sink PG config** uses `localhost:5432` in its own `application-local.yaml` (device DB), not the 15432 docker map used by video-server
3. Alert hook returns `skipped` for task 61 (`alert_event_disabled`); enqueue still fires via explicit `task_id` orchestration — matches Java/Python design

## Next pack

**P2-A7** — Matching (`logs/phase2-a7-matching.json`)
