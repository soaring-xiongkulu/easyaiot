# FR-W2-MATCH Report

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Summary

Ported all **35** `/video/face`, **26** `/video/plate`, and **6** `/video/device-detection` Python routes to Java.  
`FaceMatchingController` / `PlateMatchingController` **matching publish/process preserved**.  
`route_inventory.py` → **face Py=35/Java=35**, **plate Py=26/Java=26**, **device-detection Py=6/Java=6**, all **diff=0**.  
`certify.py --phase 0` → **exit 0** (cached golden diff; `--no-java --no-record`).

## Commits

- `4e01ae2` feat(video-java): FR-W2-MATCH port face/plate/device-detection routes (67/67)

## Python files read

| File | Scope |
|------|--------|
| `VIDEO/_retired_python_video/app/blueprints/face.py` | **全部** 35 `@face_bp.route` |
| `VIDEO/_retired_python_video/app/blueprints/plate.py` | **全部** 26 `@plate_bp.route` |
| `VIDEO/_retired_python_video/app/blueprints/device_detection_region.py` | **全部** 6 routes |
| `VIDEO/_retired_python_video/app/services/face_library_service.py` | libraries/entries/persons/normalize/match |
| `VIDEO/_retired_python_video/app/services/face_auto_enroll_service.py` | auto-enroll config/start/stop |
| `VIDEO/_retired_python_video/app/services/face_recognition_service.py` | recognize/legacy library/Milvus |
| `VIDEO/_retired_python_video/app/services/plate_library_service.py` | libraries/entries/normalize/match |
| `VIDEO/_retired_python_video/app/services/plate_auto_enroll_service.py` | auto-enroll |
| `VIDEO/_retired_python_video/app/services/device_detection_region_service.py` | regions CRUD + cover |
| `VIDEO/_retired_python_video/models.py` | FaceLibrary/Entry/Person, PlateLibrary/Entry, DeviceDetectionRegion |
| `VIDEO/_retired_python_video/run.py` | url_prefix registration |

## Inventory

```
prefix: /video/face
python: 35
java:   35
matched: 35
diff: 0

prefix: /video/plate
python: 26
java:   26
matched: 26
diff: 0

prefix: /video/device-detection
python: 6
java:   6
matched: 6
diff: 0
```

## GAP §2.5 / §2.7 progress

| 功能组 | 状态 |
|--------|------|
| face health/model/libraries/persons/entries | ✅ 路由+DB CRUD |
| face auto-enroll/normalize/match/recognize | ✅ 路由；推理/Milvus 桩 |
| face matching/publish+process | ✅ 保留既有 `FaceMatchingController` |
| face matching/records + legacy `/library` | ✅ 路由 |
| plate 全路由面 | ✅ 同 face 模式 |
| device-detection POST/PUT/DELETE regions | ✅ |
| device-detection cover-image/snapshot | ✅ 路由；抓拍/MinIO 桩 |

## Phase 0

`python tools/video_java/certify.py --phase 0 --no-java --no-record` → **exit 0** (2026-08-10)

## Concerns

1. **InsightFace / Milvus / PaddleOCR** — 录入/识别/匹配返回 Python 等价错误结构；无 JVM 推理引擎。
2. **Auto-enroll 守护** — DB 配置/start/stop 已对齐；无后台抓帧循环。
3. **Normalize merge** — 预览返回空组；合并为 no-op 桩（需向量相似度）。
4. **Maven / fat jar** — 本机无 `mvn` PATH；未重打 jar；phase0 依赖既有 golden diff。
5. **device-detection snapshot** — 复用 `CameraHardwareService.captureSnapshot` 错误路径；无 GB28181/MinIO 真链路。

## Remaining routes

**无**（三个 prefix inventory diff 均 = 0）
