# P2-S2 Report — Snap/Record/Playback/Patrol/Region/MediaHook API parity

**Date:** 2026-08-10  
**Worktree:** `F:/acme/.worktrees/video-java`  
**Branch:** `feat/video-java`  
**Brief:** `.superpowers/sdd/briefs/p2-s2-brief.md`

## STATUS

**DONE** — Six P2-S2 cases green; face/plate/post_process remain honest FAIL; Phase 0/1 exit 0.

## Commits

1. `feat(video-java): P2-S2 snap/record/playback/patrol/region/media-hook parity` (this stage)

## Certify exits

| Phase | Exit | Notes |
|-------|------|-------|
| 0 | 0 | all `vj_p0_*` PASS |
| 1 | 0 | all `vj_p1_*` PASS |
| 2 | 1 | 6/9 P2 green; face/plate/post_process expected FAIL |

```text
python tools/video_java/certify.py --phase 0 --no-record --no-java  # exit 0
python tools/video_java/certify.py --phase 1 --no-record --no-java  # exit 0
python tools/video_java/certify.py --phase 2                        # exit 1 (3 deferred cases)
```

## Phase 2 per-case

| case_id | ok | notes |
|---------|----|-------|
| `vj_p2_snap_list_or_create` | **PASS** | GET list + POST create 403 |
| `vj_p2_record_query` | **PASS** | GET `/video/record/space/list` |
| `vj_p2_playback_url` | **PASS** | GET `/video/playback/list` substitute |
| `vj_p2_patrol_task_list` | **PASS** | GET task list `task_type=patrol` |
| `vj_p2_media_hook` | **PASS** | POST `/video/media/hook/snap/completed` |
| `vj_p2_detection_region_get` | **PASS** | GET device regions |
| `vj_p2_face_publish_process` | FAIL | deferred (honest fail) |
| `vj_p2_plate_publish_process` | FAIL | deferred (honest fail) |
| `vj_p2_post_process_enqueue` | FAIL | deferred (honest fail) |

## Deliverables

- Java controllers/services/dal: Snap, Record, Playback, MediaHook, DeviceDetectionRegion; `task_type` filter on algorithm task list
- `SpaceListApiResponse` for snap/record list envelope (`parent_key`, `breadcrumbs`, `is_search`, `scope`)
- Extended `AlgorithmTaskRow.toMap()` for patrol task oracle parity
- `tools/video_java/run_java.py` — `_run_p2_with_failover` for six S2 cases
- Updated java goldens under `testdata/video-java/golden/java/vj_p2_*`

## Concerns

1. **Space list filter** — Java mirrors Python `device_id IS NOT NULL` + excludes NVR/GB28181 grouped devices; orphan spaces (no device) omitted like oracle.
2. **Patrol task payload** — full `to_dict()` parity via extended row mapper; library name resolution still empty (certify fixture uses empty `model_ids`).
3. **Media hook** — acknowledge-only stub; no MinIO/Kafka upload in P2-S2.
4. **Phase 2 gate** — overall exit 1 until face/plate/post_process stages land.
