# FR-B22 Report — 深字段矩阵扩面 + HANDOFF/ops 收尾清单

**Date:** 2026-08-11  
**Branch:** `feat/video-java` @ `F:/acme/.worktrees/video-java`  
**Status:** DONE (≠ COMPLETE)

## Summary

- Added **9** new deep field samples (+16 → **25** endpoints) in `tools/video_java/field_contract.py`.
- Extended setup: GET prerequisite chain, `path_template` from setup `data.id`.
- **No Java code changes required** — all new asserts green on `:48096`.
- Refreshed `HANDOFF.md`; added `PROD_SOAK_CHECKLIST.md` (all ⬜, no fake green).
- Re-ran deep + matrix; artifacts under `logs/fr-b22-*`.
- `certify --phase 0` → **PASS** (5/5 cases).

## Deep assert counts

| Metric | FR-B20 | FR-B22 |
|--------|--------|--------|
| Endpoints | 16 | **25** |
| Asserts pass | 88 | **130** |
| Asserts fail | 0 | **0** |
| Asserts skip | 0 | **2** (empty list item-key deferred) |

Artifacts:
- `logs/fr-b22-field-contract-latest.json`
- `logs/fr-b22-field-matrix-latest.json`

## New samples (Python-first citations)

| id | path | Python source |
|----|------|---------------|
| `algorithm_task_get` | `/video/algorithm/task/{id}` | `models.py` `AlgorithmTask.to_dict` + `algorithm_task.py` `get_task` |
| `stream_forward_task_get` | `/video/stream-forward/task/{id}` | `models.py` `StreamForwardTask.to_dict` + `stream_forward.py` `get_task` |
| `face_libraries` | `/video/face/libraries` | `models.py` `FaceLibrary.to_dict` + `face.py` `list_face_libraries` |
| `plate_libraries` | `/video/plate/libraries` | `models.py` `PlateLibrary.to_dict` + `plate.py` `list_plate_libraries` |
| `alert_statistics` | `/video/alert/statistics` | `alert_service.py` `get_dashboard_statistics` L861-932 |
| `snap_task_list` | `/video/snap/task/list` | `models.py` `SnapTask.to_dict` + `snap.py` `list_tasks` |
| `record_space_by_device` | `/video/record/space/device/vj_p2_device` | `models.py` `RecordSpace.to_dict` + `record.py` `get_space_by_device` |
| `record_videos_list` | `/video/record/space/{id}/videos` | `models.py` `RecordFile.to_list_item` + `record.py` `list_videos` |
| `playback_statistics` | `/video/playback/statistics` | `playback.py` `get_playback_statistics` L292-300 |

## Matrix (envelope)

- 265 inventoried routes → **265 pass / 0 fail**
- 98 GET routes; 95 JSON envelope probes → **190 pass / 0 fail**
- 170 skip (167 non-GET + 3 non-JSON)

## Docs touched

- `tools/video_java/field_contract.py`
- `docs/video-java/HANDOFF.md`
- `docs/video-java/PROD_SOAK_CHECKLIST.md` (new)
- `docs/video-java/FULL_REPLACEMENT_GAP.md` (§5/§8/§9)
- `.superpowers/sdd/progress.md`
- `logs/fr-b22-field-contract-*.{json,md}`
- `logs/fr-b22-field-matrix-*.{json,md}`

## Phase 0

```
python tools/video_java/certify.py --phase 0
→ PASS (vj_p0_health, task_start_stop, heartbeat, alert_hook, restart)
```

Oracle `record_python` connection refused (expected when Python oracle not running); Java layers all pass/exempt.

## Remaining (honest)

1. **Prod soak** — all items in `PROD_SOAK_CHECKLIST.md` still ⬜
2. **Full 259-route field-key matrix** — not attempted
3. **Behavior stubs** — MinIO/ONVIF/inference/remote node prod paths
4. **COMPLETE forbidden** until P0/P1 backlog + soak evidence

## Concerns

- `snap_task_list` / `record_videos_list` skip item-key asserts when list empty (mini DB may lack files/tasks).
- Local mini defaults (`direct_persist`, `upload-mode=sync`, `minio.enabled=false`) do not validate prod integration paths.
- Checklist is actionable but unverified — must not be read as soak PASS.
