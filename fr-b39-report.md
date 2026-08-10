# FR-B39 Report — HTTP 400/404 中央映射 + plate update 带图

**Status:** DONE (not COMPLETE)  
**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Python-first cites

| Topic | Python lines | Behavior |
|-------|--------------|----------|
| ValueError → HTTP 400 | `face.py` `add_face_entry` **L282-283**; `plate.py` `add_plate_entry` **L183-184**; `update_plate_entry` **L200-201** | `jsonify({"code": 400, "msg": …}), 400` |
| HTTP 200 + code=500 (keep) | `camera.py` `capture_snapshot` **L1730-1732** | 前端 `isTransformResponse=false` 需读 msg；**有意 HTTP 200** |
| Plate update image | `plate.py` **L190-201** → `plate_library_service.update_entry` **L311-313** | `image_bytes` → delete old MinIO + `_upload_plate_image` → `image_url` |
| Plate image upload | `plate_library_service.py` `_upload_plate_image` **L103-109** | bucket `plate-library`; `image_url` = `/api/v1/buckets/plate-library/objects/download?prefix=…` |

## Evidence

Artifact: `logs/fr-b39-multipart-latest.json` / `.md`  
Fixture: `testdata/fr-b37/tiny.jpg`

| Probe | HTTP | code | ok | Notes |
|-------|------|------|-----|-------|
| `plate_entry_update_image_url` | 200 | 0 | **true** | PUT multipart → `image_url` set |
| `face_entry_no_model_http_400` | **400** | 400 | **true** | msg=`人脸特征模型 face_rec.onnx 未安装…` |

**Summary:** **2/2** pass.

Contract regression (`--probe-all`): **227 pass / 38 fail** (38×404 unmapped, pre-existing); HTTP 400 responses classify as pass.

## Java fixes

1. **`VideoApiResponseAdvice.businessCodeToHttpStatus`** — code 400→HTTP 400, 404→HTTP 404; default HTTP 200 (preserves `camera.py` L1730-1732 code=500 envelope).
2. **`PlateLibraryService.updateEntry`** — image upload via `uploadPlateImage`; delete old object (`objectNameFromImageUrl`); removed OCR `ensurePlateEngine` gate.
3. **`PlateController`** — split `PUT /entries/{id}` consumes: `application/json` vs `multipart/form-data` (mirrors B37 addEntry fix).

## phase0

`python tools/video_java/certify.py --phase 0` → **5/5 PASS**  
Log: `logs/certify-frb39-phase0.log`

## Remaining / concerns

- **NOT COMPLETE** — face multipart **success** (code=0 + 12 keys) blocked until InsightFace worker + `face_rec.onnx` + Milvus.
- Business code **500** still returns HTTP **200** envelope (intentional; `camera.py` snapshot pattern).
- code **503** not yet mapped to HTTP 503 (no probe coverage).
- Plate upload skipped when MinIO disabled (`image_url` null); Python always calls MinIO.

## Files touched (FR-B39 only)

- `DEVICE/iot-video/.../VideoApiResponseAdvice.java`, `PlateLibraryService.java`, `PlateController.java`
- `tools/video_java/fr_b39_multipart.py`
- `logs/fr-b39-multipart-latest.*`, `logs/certify-frb39-phase0.log`
- `docs/video-java/FULL_REPLACEMENT_GAP.md`, `docs/video-java/HANDOFF.md`, `.superpowers/sdd/progress.md`
