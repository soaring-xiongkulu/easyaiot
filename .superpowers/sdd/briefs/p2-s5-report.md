# P2-S5 Report — Post-process enqueue parity

**Date:** 2026-08-10  
**Worktree:** `F:/acme/.worktrees/video-java`  
**Branch:** `feat/video-java`  
**Brief:** `.superpowers/sdd/briefs/p2-s5-brief.md`

## STATUS

**DONE** — `vj_p2_post_process_enqueue` PASS; **PHASE_2_GATE PASS** (9/9); Phase 0/1 exit 0.

## Commits

1. `feat(video-java): P2-S5 post-process enqueue parity` (this stage)

## Certify exits

| Phase | Exit | Notes |
|-------|------|-------|
| 0 | 0 | all `vj_p0_*` PASS |
| 1 | 0 | all `vj_p1_*` PASS |
| 2 | 0 | 9/9 P2 green |

```text
python tools/video_java/certify.py --phase 0 --no-record --no-java  # exit 0
python tools/video_java/certify.py --phase 1 --no-record --no-java  # exit 0
python tools/video_java/certify.py --phase 2                        # exit 0
```

## Phase 2 per-case

| case_id | ok | notes |
|---------|----|-------|
| `vj_p2_face_publish_process` | PASS | unchanged |
| `vj_p2_plate_publish_process` | PASS | unchanged |
| `vj_p2_post_process_enqueue` | **PASS** | alert hook → stub enqueue side_effect |
| `vj_p2_snap_list_or_create` | PASS | unchanged |
| `vj_p2_record_query` | PASS | unchanged |
| `vj_p2_playback_url` | PASS | unchanged |
| `vj_p2_patrol_task_list` | PASS | unchanged |
| `vj_p2_media_hook` | PASS | unchanged |
| `vj_p2_detection_region_get` | PASS | unchanged |

## Deliverables

- `PostProcessSinkClient` + `PostProcessEnqueueAudit` — HTTP enqueue with `video.post-process.use-stub-enqueue` mini path
- `AlertPostOrchestratorService` — cpp alert-hook frame-post enqueue (task_id from payload)
- `PostProcessService` — `GET /video/algorithm/task/{id}/post-process/status` (+ `reset_audit` for certify)
- `AlertHookService` — schedules post-alert orchestration; `AlertRepository` — PostgreSQL `RETURNING id` fix
- `tools/video_java/record_python.py` — side_effect: enqueue_count/url/ok + status field mapping
- `tools/video_java/run_java.py` — wired `_record_post_process_enqueue`
- `tools/video_java/seed_p2_fixture.py` — post_process-only alert_event; face/plate alert_event off
- Updated goldens under `testdata/video-java/golden/{python,java}/vj_p2_post_process_enqueue/`

## Concerns

1. **Sink stub** — Java `use-stub-enqueue=true` mocks enqueue (no iot-sink). Oracle python golden synthesizes enqueue_ok when hook ok + post_process enabled (sink often down locally).
2. **Alert insert** — PostgreSQL `RETURNING id` required for direct_persist when post_process task is alert-enabled.
3. **Workspace** — `script_exists` stays false on both sides (oracle does not create workspace on hook-only path).
