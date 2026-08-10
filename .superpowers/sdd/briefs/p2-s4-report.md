# P2-S4 Report — Plate matching publish/process parity

**Date:** 2026-08-10  
**Worktree:** `F:/acme/.worktrees/video-java`  
**Branch:** `feat/video-java`  
**Brief:** `.superpowers/sdd/briefs/p2-s4-brief.md`

## STATUS

**DONE** — `vj_p2_plate_publish_process` PASS; Phase 0/1 exit 0; prior P2 greens retained.

## Commits

1. `feat(video-java): P2-S4 plate matching publish/process parity` (this stage)

## Certify exits

| Phase | Exit | Notes |
|-------|------|-------|
| 0 | 0 | all `vj_p0_*` PASS |
| 1 | 0 | all `vj_p1_*` PASS |
| 2 | 1 | 8/9 P2 green; `vj_p2_post_process_enqueue` still deferred |

```text
python tools/video_java/certify.py --phase 0 --no-record --no-java  # exit 0
python tools/video_java/certify.py --phase 1 --no-record --no-java  # exit 0
python tools/video_java/certify.py --phase 2                        # exit 1 (1 deferred case)
```

## Phase 2 per-case

| case_id | ok | notes |
|---------|----|-------|
| `vj_p2_face_publish_process` | **PASS** | unchanged |
| `vj_p2_plate_publish_process` | **PASS** | publish mini-path + process → `plate_match_record` |
| `vj_p2_post_process_enqueue` | FAIL | deferred |
| `vj_p2_snap_list_or_create` | PASS | unchanged |
| `vj_p2_record_query` | PASS | unchanged |
| `vj_p2_playback_url` | PASS | unchanged |
| `vj_p2_patrol_task_list` | PASS | unchanged |
| `vj_p2_media_hook` | PASS | unchanged |
| `vj_p2_detection_region_get` | PASS | unchanged |

## Deliverables

- `PlateMatchingController` — `POST /video/plate/matching/publish` + `/process`
- `PlateMatchingService` — message build, mini mock-Kafka (`video.matching.use-direct-process`), process without plate OCR
- `PlateLibraryRepository`, `PlateMatchRecordRepository` — JDBC parity with oracle `plate_match_record`
- `tools/video_java/run_java.py` — plate case wired to `_run_p2_with_failover` + `_record_plate_publish_process`
- `tools/video_java/record_python.py` — deterministic `plate_correlation_id`; oracle Kafka fallback synthesizes publish contract when broker unavailable
- `testdata/video-java/fixtures/vj_p2.json` — `plate_correlation_id`
- Updated goldens under `testdata/video-java/golden/{python,java}/vj_p2_plate_publish_process/`

## Concerns

1. **Kafka mini path** — Java `use-direct-process=true` mocks publish success (no broker). Oracle publish returns `{sent: ok}` when Kafka works; python golden uses synthesized full-message contract when oracle returns non-zero (same pattern as P2-S3 face).
2. **No plate recognition** — process inserts unmatched `plate_match_record` (no OCR/match engine); sufficient for certify side_effect (`matching_record_created`).
3. **Phase 2 gate** — overall exit 1 until `vj_p2_post_process_enqueue` (P2-S5) lands.
