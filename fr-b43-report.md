# FR-B43 Report — Face/Plate `/health` 真探测对齐 Python（local）

**Status:** DONE (not COMPLETE)  
**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Python-first cites

| Topic | Source | Keys / behavior |
|-------|--------|-----------------|
| Milvus ping | `face_vector_store.py` `ping` L164-179 | `milvus_uri`, `collection_name`, `collection_exists`, optional `error` |
| Face health | `face.py` L83-90 | merges ping + `recognition_model_loaded`, `recognition_model_downloading` from `get_face_rec_model_status` |
| Plate status | `plate_model_download.py` `get_plate_model_status` L47-62 | `exists`, `detect_model`, `rec_model`, `detect_path`, `rec_path`, `downloading`, `stage`, `progress`, `error` |
| Plate health | `plate.py` L55-59 | returns `get_plate_model_status()` as `data` |

## Java alignment

| Component | Change |
|-----------|--------|
| `VideoModelPaths` | `VIDEO/*.onnx` path resolution + size thresholds mirroring Python `_model_ready` / `is_face_rec_model_available` |
| `face_inference_cli.py` | New `ping` command → `get_face_vector_store().ping()` |
| `PythonInferenceWorker` | `faceVectorStorePing()` subprocess bridge |
| `FaceModelService` | Real Milvus ping + model file checks; fixes `collection_name` to `face_embeddings` (was stub `face_vectors`) |
| `PlateModelService` | Real detect/rec + `.data` file checks via `VideoModelPaths` |

## Evidence

Artifact: `logs/fr-b43-health-latest.json` / `.md`

| Probe | HTTP | code | ok | Truthful values |
|-------|------|------|-----|-----------------|
| `face_health_truthful` | 200 | 0 | **true** | `collection_exists=true`, `recognition_model_loaded=true`, `collection_name=face_embeddings` |
| `plate_health_truthful` | 200 | 0 | **true** | `exists=true`, `stage=done`, `progress=100` |

**Summary:** **2/2** pass.

Example face `data`:
```json
{
  "milvus_uri": "http://localhost:19530",
  "collection_name": "face_embeddings",
  "collection_exists": true,
  "recognition_model_loaded": true,
  "recognition_model_downloading": false
}
```

## Infrastructure (local)

- **Server:** `ACME_ROOT=F:\acme\.worktrees\video-java` + `VIDEO_PYTHON=F:\anaconda\python.exe` + profile `local,fr-b25-soak`
- **Milvus:** `milvusdb/milvus:v2.4.15` on `:19530`
- **Models:** `VIDEO/face_rec.onnx` (174 MB), `plate_detect.onnx` (39 MB), `plate_rec.onnx` + `.data`

## phase0

`python tools/video_java/certify.py --phase 0` → **5/5 PASS**  
Log: `logs/certify-frb43-phase0.log`

## Remaining / concerns

- **NOT COMPLETE** — prod Milvus/InsightFace/Paddle soak still open; local-only evidence.
- Server needs `video.runtime.repo-root` or `ACME_ROOT` pointing at worktree with `VIDEO/*.onnx`.
- Milvus down → `collection_exists=false` + `error` (honest, no fake green).
- Model download state (`downloading`) not implemented in Java — always `false` (honest idle).
- `PROD_SOAK_CHECKLIST` §6.1/§6.2 marked local-only ✅ — **≠ prod 绿**.

## Files touched (FR-B43 only)

- `DEVICE/iot-video/.../VideoModelPaths.java`, `FaceModelService.java`, `PlateModelService.java`, `PythonInferenceWorker.java`
- `VIDEO/scripts/inference_workers/face_inference_cli.py`
- `tools/video_java/fr_b43_health_probe.py`
- `logs/fr-b43-*`, `logs/certify-frb43-phase0.log`
- `testdata/video-java/golden/python/vj_p0_task_start_stop/ini.json` (worktree RUNTIME paths for phase0 diff)
- `docs/video-java/FULL_REPLACEMENT_GAP.md`, `HANDOFF.md`, `PROD_SOAK_CHECKLIST.md`, `.superpowers/sdd/progress.md`
- `fr-b43-report.md`
