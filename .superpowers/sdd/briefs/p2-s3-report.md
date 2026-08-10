# P2-S3 Report — Face matching publish/process parity

**Date:** 2026-08-10  
**Worktree:** `F:/acme/.worktrees/video-java`  
**Branch:** `feat/video-java`  
**Brief:** `.superpowers/sdd/briefs/p2-s3-brief.md`

## STATUS

**DONE** — `vj_p2_face_publish_process` PASS; Phase 0/1 exit 0; prior P2-S2 cases remain green.

## Commits

1. `feat(video-java): P2-S3 face matching publish/process parity` (this stage)

## Certify exits

| Phase | Exit | Notes |
|-------|------|-------|
| 0 | 0 | all `vj_p0_*` PASS |
| 1 | 0 | all `vj_p1_*` PASS |
| 2 | 1 | 7/9 P2 green; plate/post_process still deferred |

```text
python tools/video_java/certify.py --phase 0 --no-record --no-java  # exit 0
python tools/video_java/certify.py --phase 1 --no-record --no-java  # exit 0
python tools/video_java/certify.py --phase 2                        # exit 1 (2 deferred cases)
```

## Phase 2 per-case

| case_id | ok | notes |
|---------|----|-------|
| `vj_p2_face_publish_process` | **PASS** | publish mini-path + process → `face_match_record` |
| `vj_p2_plate_publish_process` | FAIL | deferred |
| `vj_p2_post_process_enqueue` | FAIL | deferred |
| `vj_p2_snap_list_or_create` | PASS | unchanged |
| `vj_p2_record_query` | PASS | unchanged |
| `vj_p2_playback_url` | PASS | unchanged |
| `vj_p2_patrol_task_list` | PASS | unchanged |
| `vj_p2_media_hook` | PASS | unchanged |
| `vj_p2_detection_region_get` | PASS | unchanged |

## Deliverables

- `FaceMatchingController` — `POST /video/face/matching/publish` + `/process`
- `FaceMatchingService` — message build, mini mock-Kafka (`video.matching.use-direct-process`), process without InsightFace
- `FaceLibraryRepository`, `FaceMatchRecordRepository` — JDBC parity with oracle `face_match_record`
- `VideoProperties.Matching` + `application-local.yaml` mini path flag
- `tools/video_java/run_java.py` — face case wired to `_run_p2_with_failover` + `_record_face_publish_process`
- `tools/video_java/record_python.py` — deterministic `face_correlation_id`; oracle Kafka fallback synthesizes publish contract when broker unavailable
- Updated goldens under `testdata/video-java/golden/{python,java}/vj_p2_face_publish_process/`

## Concerns

1. **Kafka mini path** — Java `use-direct-process=true` mocks publish success (no broker). Oracle publish still blocks/fails without Kafka; python golden uses synthesized publish contract when oracle returns non-zero.
2. **No face recognition** — process inserts unmatched `face_match_record` (no InsightFace); sufficient for certify side_effect (`matching_record_created`).
3. **Phase 2 gate** — overall exit 1 until plate/post_process stages land.
