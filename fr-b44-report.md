# FR-B44 Report — Pose 提取成功路径 + Matching 命中告警链（local）

**Status:** DONE (not COMPLETE)  
**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Python-first cites

| Topic | Source | Behavior |
|-------|--------|----------|
| Pose extract | `scenario_pose.py` L168-179 | `POST /entries/extract` multipart → `extract_preview` |
| Pose extract svc | `scenario_pose_library_service.py` L339-353 | YOLO keypoints + `extract_angle_features` |
| Pose model | `pose_analysis.py` L51-79, L96-106 | `yolo26n-pose.pt` resolve VIDEO/AI root |
| Match-test | `scenario_pose.py` L182-193 | `POST /libraries/{id}/match-test` |
| Match-test svc | `scenario_pose_library_service.py` L356-391 | `match_person_to_entry` per entry |
| Face match process | `library_matching_service.py` L215-300 | `process_face_matching_message` |
| Alert create | `library_matching_service.py` L110-152 | `_create_match_alert` → `face_library_match` |
| Kafka message | `face_matching_kafka_service.py` L25-62 | `build_face_matching_message` |
| Java worker | `pose_inference_cli.py` | subprocess `extract` / `health` |
| Java matching | `LibraryMatchingProcessor.java` | `processFace` → `MatchAlertService` |

## Evidence

### Pose (`logs/fr-b44-pose-latest.json`)

| Probe | HTTP | code | ok | Notes |
|-------|------|------|-----|-------|
| `pose_extract_real_keypoints` | 200 | 0 | **true** | count=6, 17 kps, max_conf=0.9985, feature_vector len=11 |
| `pose_match_test_real_similarity` | 200 | 0 | **true** | similarity≥0.5, matched=true |

**Summary:** **2/2** pass. YOLO weights: `VIDEO/yolo26n-pose.pt`, `AI/yolo26n-pose.pt`.

### Matching alert (`logs/fr-b44-matching-alert-latest.json`)

| Probe | HTTP | code | ok | Notes |
|-------|------|------|-----|-------|
| `face_matching_hit_alert` | 200 | 0 | **true** | matched=true, similarity=1.0, alert_id set, event=`face_library_match` |

**Summary:** **1/1** pass. Profile: `local,fr-b44-soak` (`use-direct-process=false`).

Example process `data`:
```json
{
  "matched": true,
  "similarity": 1.0,
  "alert_id": 4659,
  "event": "face_library_match",
  "matched_person_name": "frb44_person_..."
}
```

## Java fixes (FR-B44)

1. **`ScenarioPoseLibraryService.addEntryFromImage`** — persist `keypoints` + `feature_vector` after YOLO extract (Python `_build_entry_from_keypoints` parity).
2. **`ScenarioPoseController`** — split multipart vs JSON `addEntry` handlers (fix multipart 405/content-type).
3. **`FaceMatchRecordRepository`** — serialize `candidates` with Jackson (fix jsonb insert).
4. **`application-fr-b44-soak.yaml`** — MinIO + `use-direct-process=false` for matching processor.

## Infrastructure (local)

- **Server:** `local,fr-b44-soak` + `-Dvideo.runtime.repo-root=F:/acme/.worktrees/video-java`
- **Models:** `VIDEO/yolo26n-pose.pt`, `VIDEO/face_rec.onnx`, Milvus v2.4.15
- **Fixture:** `testdata/fr-b41/face_sample.jpg`; seed `frb44_device` task_id via `seed_fr_b44_fixture.py`

## phase0

`python tools/video_java/certify.py --phase 0` → **5/5 PASS**  
Log: `logs/certify-frb44-phase0.log`

## Remaining / concerns

- **NOT COMPLETE** — prod YOLO pose soak + prod matching-alert Kafka consumer chain still open.
- Pose `reExtractEntry` still stub (MinIO read) — out of FR-B44 scope.
- phase0 ini golden uses `F:/acme/RUNTIME/models/*` paths (Java ini generator + `application-local.yaml` repo-root); worktree runtime bin path separate.
- Matching probe uses direct `/process` API (not Kafka publish→consumer); honest local path per `LibraryMatchingProcessor`.
- `VIDEO/yolo26n-pose.pt` copied locally; not committed (gitignore).

## Files touched (FR-B44 only)

- `DEVICE/iot-video/.../ScenarioPoseLibraryService.java`, `ScenarioPoseController.java`, `FaceMatchRecordRepository.java`
- `application-fr-b44-soak.yaml`
- `tools/video_java/fr_b44_pose_probe.py`, `fr_b44_matching_alert_probe.py`, `seed_fr_b44_fixture.py`
- `logs/fr-b44-*`, `logs/certify-frb44-phase0.log`
- `testdata/video-java/golden/python/vj_p0_task_start_stop/ini.json`
- `docs/video-java/PROD_SOAK_CHECKLIST.md`, `FULL_REPLACEMENT_GAP.md`, `HANDOFF.md`, `.superpowers/sdd/progress.md`
- `fr-b44-report.md`
