# FR-B42 Report — face entry update 带图 + soak checklist §6.1（local）

**Status:** DONE (not COMPLETE)  
**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Python-first cites

| Topic | Source | Behavior |
|-------|--------|----------|
| Update flow | `face_library_service.py` `update_entry` L428-482 | text fields → if `image_bytes`: extract_and_crop → `_delete_minio_object` → `_upload_face_image` → `delete_by_milvus_id` → `add_face_to_library` → `milvus_id` |
| Person sync | `face_library_service.py` L432-439 | when `cover_entry_id == entry.id`, sync `person_name`/`person_code` to person |
| MinIO delete | `face_library_service.py` `_delete_minio_object` L71-79 | best-effort `remove_object` on `image_path` |
| Milvus delete | `face_library_service.py` L463-467 | best-effort `store.delete_by_milvus_id` |
| HTTP route | `face.py` L345 | `update_entry(entry_id, image_bytes=..., **data)` |
| Entry create setup | `face_library_service.py` `add_entry` L303-380 | FR-B41 wiring reused for probe setup |
| HTTP response | `models.py` `FaceEntry.to_dict` L1327-1341 | 12 keys incl. `image_url`, `milvus_id` |

## Java alignment

| Component | Change |
|-----------|--------|
| `FaceLibraryService.updateEntry` | Full image path: `extractCropForEntry` → delete old MinIO → upload → `deleteFaceByMilvusId` → `addFaceToLibrary` → update `image_path`/`image_url`/`milvus_id`; person cover sync |
| `FaceRecognitionService.deleteFaceByMilvusId` | Best-effort Milvus delete via worker |
| `PythonInferenceWorker.faceDeleteByMilvusId` | Subprocess bridge |
| `face_inference_cli.py` | New `delete_by_milvus_id` command |

## Evidence

Artifact: `logs/fr-b42-face-update-latest.json` / `.md`  
Fixture: `testdata/fr-b41/face_sample.jpg` (reuse FR-B41)

| Probe | HTTP | code | ok | Notes |
|-------|------|------|-----|-------|
| `face_entry_update_multipart_success` | 200 | 0 | **true** | 12 keys; `image_url` changed; `milvus_id` re-upserted; `person_name` updated |

**Summary:** **1/1** pass.

Example from evidence:
- `original_milvus_id`: `468294075917271248` → `milvus_id`: `468294075917271251`
- `original_image_url`: `...ded81e8c...jpg` → `image_url`: `...940e37b8...jpg`

## Infrastructure (local)

- **Server:** `ACME_ROOT=F:\acme\.worktrees\video-java` + `VIDEO_PYTHON=F:\anaconda\python.exe` + profile `local,fr-b25-soak`
- **Milvus:** `milvusdb/milvus:v2.4.15` standalone on `:19530`
- **MinIO:** profile `fr-b25-soak` (`MINIO_ENABLED=true`)
- **Model:** `VIDEO/face_rec.onnx` (174,383,860 bytes)

## phase0

`python tools/video_java/certify.py --phase 0` → **5/5 PASS**  
Log: `logs/certify-frb42-phase0.log`

## Remaining / concerns

- **NOT COMPLETE** — prod Milvus/InsightFace soak still open; `/video/face/health` Java stub still returns `collection_exists=false` (real inference via worker subprocess).
- Server must have `ACME_ROOT` pointing at worktree (not `F:/acme` from `application-local.yaml` default).
- Cold-start worker ~35s first request after restart.
- `face_rec.onnx` must be present per machine.

## Files touched (FR-B42 only)

- `DEVICE/iot-video/.../FaceLibraryService.java`, `FaceRecognitionService.java`, `PythonInferenceWorker.java`
- `VIDEO/scripts/inference_workers/face_inference_cli.py`
- `tools/video_java/fr_b42_face_update_success.py`
- `logs/fr-b42-*`, `logs/certify-frb42-phase0.log`
- `docs/video-java/FULL_REPLACEMENT_GAP.md`, `docs/video-java/HANDOFF.md`, `docs/video-java/PROD_SOAK_CHECKLIST.md`, `.superpowers/sdd/progress.md`
- `fr-b42-report.md`
