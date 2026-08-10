# FR-B38 Report — plate image_url MinIO + face entry 无模型诚实路径

**Status:** DONE (not COMPLETE)  
**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Python-first cites

| Topic | Python lines | Behavior |
|-------|--------------|----------|
| Plate image upload | `plate_library_service.py` `_upload_plate_image` **L103-109** | MinIO bucket `plate-library`; object `{library_id}/{uuid}.jpg`; `image_url` = `/api/v1/buckets/plate-library/objects/download?prefix=…` |
| Plate add entry | `plate_library_service.py` `add_entry` **L271-273** | When `image_bytes` provided → `_upload_plate_image`; no OCR gate |
| Face model missing | `face_library_service.py` `add_entry` **L319-326** | `extract_and_crop_largest_face` → `FileNotFoundError` → `ValueError('人脸特征模型 face_rec.onnx 未安装…')` |
| Face HTTP mapping | `face.py` `add_face_entry` **L282-283** | `ValueError` → `{"code": 400, "msg": …}` **HTTP 400** — **hard-fail, no soft-save** |
| No face detected | `face_library_service.py` **L327-328** | `ValueError('图片中未检测到人脸…')` → HTTP 400 |

## Evidence

Artifact: `logs/fr-b38-multipart-latest.json` / `.md`  
Fixture: `testdata/fr-b37/tiny.jpg`

| Probe | HTTP | code | ok | Notes |
|-------|------|------|-----|-------|
| `plate_entry_image_url` | 200 | 0 | **true** | `image_url` set: `/api/v1/buckets/plate-library/objects/download?prefix=…` |
| `face_entry_no_model_honest_400` | 200 | 400 | **true** | msg=`人脸特征模型 face_rec.onnx 未安装…`；Java envelope HTTP 200 (Python HTTP 400) |

**Summary:** **2/2** pass. Re-run B37: plate pass; face success still **EX** (code=400, not 500).

## Java fixes

1. **`PlateLibraryService.addEntry`** — `VideoMinioService.uploadBytes` to `plate-library` bucket; `buildDownloadUrl` for `image_url` (mirrors `_upload_plate_image` L103-109).
2. **`FaceRecognitionService.validateFaceEntryImage`** — entry path throws **400** + Python msg when engine absent (was 500 via `ensureFaceDetectable`).
3. **`FaceLibraryService.addEntry/updateEntry`** — use `validateFaceEntryImage` for entry paths.

## phase0

`python tools/video_java/certify.py --phase 0` → **5/5 PASS**  
Log: `logs/certify-frb38-phase0.log`

## Remaining / concerns

- **NOT COMPLETE** — face multipart **success** (code=0 + 12 keys) blocked until InsightFace worker + `face_rec.onnx` + Milvus.
- Java error envelope: HTTP **200** + `code=400` vs Python HTTP **400** (documented delta).
- Plate upload skipped when MinIO disabled (`image_url` null); Python always calls MinIO.
- `plate_entry` update with image not ported (out of B38 scope).

## Files touched (FR-B38 only)

- `DEVICE/iot-video/.../PlateLibraryService.java`, `FaceRecognitionService.java`, `FaceLibraryService.java`
- `tools/video_java/fr_b38_multipart.py`
- `logs/fr-b38-multipart-latest.*`, `logs/certify-frb38-phase0.log`
- `docs/video-java/FULL_REPLACEMENT_GAP.md`, `docs/video-java/HANDOFF.md`, `.superpowers/sdd/progress.md`
