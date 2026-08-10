# P2-S1 Report — Phase 2 certify scaffolding

**Date:** 2026-08-10  
**Worktree:** `F:/acme/.worktrees/video-java`  
**Branch:** `feat/video-java`  
**Brief:** `.superpowers/sdd/briefs/p2-s1-brief.md`

## STATUS

**DONE** — Phase 2 manifest + certify scaffold landed; `--phase 2` honest FAIL; Phase 0/1 remain exit 0.

## Commits

1. `feat(video-java): scaffold Phase 2 certify cases and honest FAIL gate`

## Certify exits

| Phase | Exit | Notes |
|-------|------|-------|
| 0 | 0 | all `vj_p0_*` PASS |
| 1 | 0 | all `vj_p1_*` PASS |
| 2 | 1 | all 9 `vj_p2_*` FAIL (expected scaffold) |

```text
python tools/video_java/certify.py --phase 0 --no-record --no-java  # exit 0
python tools/video_java/certify.py --phase 1 --no-record --no-java  # exit 0
python tools/video_java/certify.py --phase 2 --no-record --no-java  # exit 1
```

## Case list (manifest P2)

| case_id | layers | oracle endpoint(s) |
|---------|--------|-------------------|
| `vj_p2_face_publish_process` | api, side_effect | `/video/face/matching/publish` + `/matching/process` |
| `vj_p2_plate_publish_process` | api, side_effect | `/video/plate/matching/publish` + `/matching/process` |
| `vj_p2_post_process_enqueue` | side_effect | alert hook → post-process status delta |
| `vj_p2_snap_list_or_create` | api | GET `/video/snap/space/list` + POST `/video/snap/space` |
| `vj_p2_record_query` | api | GET `/video/record/space/list` |
| `vj_p2_playback_url` | api | **SUBSTITUTE** GET `/video/playback/list` (no stable play-url on oracle) |
| `vj_p2_patrol_task_list` | api | GET `/video/algorithm/task/list?task_type=patrol` |
| `vj_p2_media_hook` | api | POST `/video/media/hook/snap/completed` |
| `vj_p2_detection_region_get` | api | GET `/video/device-detection/device/{id}/regions` |

## Deliverables

- `testdata/video-java/manifest.json` — 9 P2 cases (`priority: P2`)
- `testdata/video-java/fixtures/vj_p2.json` + `tools/video_java/seed_p2_fixture.py`
- `tools/video_java/vj_common.py` — `side_effect` → `effects.json`, `phase2_case_ids`, `load_p2_fixture`
- `tools/video_java/diff_layers.py` — `side_effect` layer diff
- `tools/video_java/record_python.py` — oracle recorders for all P2 cases
- `tools/video_java/run_java.py` — `_run_p2_honest_fail` (no Java P2 surface yet)
- `tools/video_java/certify.py` — `--phase 2`, `PHASE_2_GATE.md`, `CERTIFY_STATUS` Phase 2 row
- `docs/video-java/gates/PHASE_2_GATE.md` — FAIL scaffold
- Python golden under `testdata/video-java/golden/python/vj_p2_*`
- Java fail golden under `testdata/video-java/golden/java/vj_p2_*`

## Concerns

1. **Face/plate publish** — oracle `matching/publish` can block on Kafka (8s timeout → `code:-1` in python golden); re-record when Kafka is healthy for stricter baseline.
2. **Playback** — no stable play-url contract on oracle; case uses `GET /video/playback/list` substitute (documented in manifest + gate).
3. **Patrol** — Java already exposes generic `task/list` from P0; P2 Java goldens use explicit honest-fail to avoid false partial parity.
4. **Next** — implement Java P2 controllers + flip `run_java` from `_run_p2_honest_fail` to real sampling.
