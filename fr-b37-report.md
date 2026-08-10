# FR-B37 Report — multipart 成功路径 + fixture bucket 名修复

**Status:** DONE (not COMPLETE)  
**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Python-first cites

| Route | Multipart fields | Success keys | Python oracle |
|-------|------------------|--------------|---------------|
| `POST /video/face/libraries/{id}/entries` | `person_name`, `file` | `FaceEntry.to_dict` 12 keys | `face.py` `add_face_entry` L262-281 |
| `POST /video/plate/libraries/{id}/entries` | `plate_no`, `file` (optional) | `PlateEntry.to_dict` 12 keys | `plate.py` `add_plate_entry` L166-182 |
| `POST /video/scenario-pose/entries/extract` | `file`, `conf?` | `count`, `persons` | `scenario_pose.py` L168-173 → `extract_preview` L339-353 |

MinIO bucket: `seed_p2_fixture._ensure_space` used `certify-{space_code}` → illegal `certify-vj_p2_*` (underscore). S3 allows hyphens only → `certify_bucket_name()` replaces `_` with `-`.

## Multipart evidence

Artifact: `logs/fr-b37-multipart-latest.json` / `.md`  
Fixture image: `testdata/fr-b37/tiny.jpg` (1×1 JPEG from FR-B25 `_MIN_JPEG`)

| Probe | HTTP | code | key_assert | ok | Notes |
|-------|------|------|------------|-----|-------|
| `plate_entry_multipart_success` | 200 | 0 | pass (12 keys) | **true** | After `PlateController` JSON/multipart split |
| `scenario_pose_extract_multipart_success` | 200 | 0 | pass (`count`,`persons`) | **true** | |
| `face_entry_multipart_success` | 200 | 500 | — | **false** | **EX** — `FaceRecognitionService.ensureFaceDetectable` → InsightFace worker absent (mini) |
| `snap_images_sync` | 200 | 0 | — | **true** | Was 500 with illegal bucket |
| `record_videos_sync` | 200 | 0 | — | **true** | Was 500 with illegal bucket |

**Summary:** multipart core **2/3** pass; bucket naming **fixed**; metadata sync **2/2** pass.

## Java / fixture fixes

1. **`certify_bucket_name()`** — `tools/video_java/bucket_naming.py`; `seed_p2_fixture.py` migrate existing rows; `record_python.py` create-space payload.
2. **`S3BucketNameSupport`** — 4xx on `_` in bucket before MinIO ops (`VideoMinioService`, `SpaceFileMetadataService`).
3. **`PlateController`** — split `consumes=application/json` vs `multipart/form-data` (was `@RequestBody` + multipart → 500 unsupported).
4. **`PlateLibraryService.addEntry`** — drop `ensurePlateEngine()` on image upload (Python `plate_library_service.add_entry` uploads without OCR gate).

## phase0

`python tools/video_java/certify.py --phase 0` → **5/5 PASS**  
Log: `logs/certify-frb37-phase0.log`

## Remaining / concerns

- **NOT COMPLETE** — face multipart success blocked until InsightFace Python worker + `face_rec.onnx` + Milvus available in target profile.
- Plate multipart does not yet upload image to MinIO (Java parity gap vs Python `_upload_plate_image`).
- Prod soak / real-device paths unchanged.

## Files touched (FR-B37 only)

- `tools/video_java/bucket_naming.py`, `fr_b37_multipart.py`, `seed_p2_fixture.py`, `record_python.py`
- `testdata/fr-b37/tiny.jpg`
- `DEVICE/iot-video/.../S3BucketNameSupport.java`, `VideoMinioService.java`, `SpaceFileMetadataService.java`, `PlateController.java`, `PlateLibraryService.java`
- `logs/fr-b37-multipart-latest.*`, `logs/certify-frb37-phase0.log`
- `docs/video-java/FULL_REPLACEMENT_GAP.md`, `.superpowers/sdd/progress.md`
