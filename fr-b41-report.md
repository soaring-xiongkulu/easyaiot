# FR-B41 Report — face_rec.onnx + Face entry 成功路径（local）

**Status:** DONE (not COMPLETE)  
**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Python-first cites

| Topic | Source | Behavior |
|-------|--------|----------|
| Model path | `face_model_paths.py` L14-17 | `FACE_MATCH_MODEL_PATH` → `VIDEO/face_rec.onnx` (env override) |
| Model download | `VIDEO/scripts/download_face_rec_model.sh` L6-7 | buffalo_l.zip → `w600k_r50.onnx` → `VIDEO/face_rec.onnx` |
| Rec model gate | `face_recognition_service.py` L65-69 | `FileNotFoundError` if missing or &lt;10MB |
| Entry flow | `face_library_service.py` `add_entry` L303-380 | extract_and_crop → MinIO upload → DB entry → `add_face_to_library` → `milvus_id` |
| HTTP response | `models.py` `FaceEntry.to_dict` L1327-1341 | 12 keys incl. `image_url`, `milvus_id` |
| Java worker | `FaceRecognitionService.java` | subprocess `face_inference_cli.py` extract_crop + add_to_library |

## Model acquisition

- **Script:** `VIDEO/scripts/download_face_rec_model.sh` (InsightFace v0.7 `buffalo_l.zip`)
- **Local run:** Python urllib equivalent (Windows bash path issue); output `VIDEO/face_rec.onnx` **174,383,860 bytes**
- **Worker runtime:** copies/symlinks to `VIDEO/_retired_python_video/face_rec.onnx` + `face_det.onnx` (Python `chdir` to retired tree)
- **gitignore:** `VIDEO/.gitignore` — model not committed

## Evidence

Artifact: `logs/fr-b41-face-entry-success-latest.json` / `.md`  
Fixture: `testdata/fr-b41/face_sample.jpg` (InsightFace demo t1.jpg)

| Probe | HTTP | code | ok | Notes |
|-------|------|------|-----|-------|
| `face_entry_multipart_success` | 200 | 0 | **true** | 12 keys; `image_url` MinIO; `milvus_id` set |

**Summary:** **1/1** pass.

## Java / worker fixes (FR-B41)

1. **`face_inference_cli.py`** — `extract_crop` + `add_to_library` commands mirroring Python entry path.
2. **`FaceLibraryService.addEntry`** — full parity: worker crop → MinIO `face-library` → Milvus insert → `milvus_id`.
3. **`FaceRecognitionService`** — `extractCropForEntry`, `addFaceToLibrary`.
4. **`PythonInferenceWorker`** — temp-file image path (Windows cmdline 206); redirect output to file (pipe deadlock); parse last JSON line (ONNX warnings).

## Infrastructure (local)

- **Milvus:** `milvusdb/milvus:v2.4.15` standalone (v2.6.0 segfault on this host; compose `milvus_config/*.yaml` were directories)
- **Python:** `F:\anaconda\python.exe` via `VIDEO_PYTHON`
- **MinIO:** profile `fr-b25-soak` (`MINIO_ENABLED=true`)

## phase0

`python tools/video_java/certify.py --phase 0` → **5/5 PASS**  
Log: `logs/certify-frb41-phase0.log`

## Remaining / concerns

- **NOT COMPLETE** — prod Milvus/InsightFace soak still open; local-only evidence.
- `milvus_config/user.yaml` / `embedEtcd.yaml` in `.scripts/docker` are **directories** — breaks compose Milvus v2.6.0; use v2.4.15 or fix config files.
- Cold-start worker ~45s first entry (model load); subsequent faster.
- `face_rec.onnx` must be downloaded per machine (`download_face_rec_model.sh`).

## Files touched (FR-B41 only)

- `DEVICE/iot-video/.../PythonInferenceWorker.java`, `FaceRecognitionService.java`, `FaceLibraryService.java`
- `VIDEO/scripts/inference_workers/face_inference_cli.py`
- `tools/video_java/fr_b41_face_entry_success.py`
- `testdata/fr-b41/face_sample.jpg`
- `logs/fr-b41-*`, `logs/certify-frb41-phase0.log`
- `docs/video-java/FULL_REPLACEMENT_GAP.md`, `docs/video-java/HANDOFF.md`, `.superpowers/sdd/progress.md`
- `fr-b41-report.md`
