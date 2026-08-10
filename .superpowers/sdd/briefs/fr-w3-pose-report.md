# FR-W3-POSE Report

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Summary

Ported all **14** `/video/scenario-pose` Python routes to Java `ScenarioPoseController` + `ScenarioPoseLibraryService` / `PoseAnalysisService` + JDBC repositories.  
`route_inventory.py --prefix /video/scenario-pose` → **Py 14 / Java 14 / diff 0**.  
**EX-SCENARIO-POSE resolved.**  
`certify.py --phase 0` → **exit 0**.

## Commits

(see `git log -1` after commit)

## Python files read

| File | Scope |
|------|--------|
| `VIDEO/_retired_python_video/app/blueprints/scenario_pose.py` | **全部** 14 `@scenario_pose_bp.route` |
| `VIDEO/_retired_python_video/app/services/scenario_pose_library_service.py` | libraries/entries/extract/match/templates |
| `VIDEO/_retired_python_video/app/utils/pose_intent.py` | `SCENE_TEMPLATES` + angle features (stubbed in Java) |
| `VIDEO/_retired_python_video/models.py` | `ScenarioPoseLibrary` / `ScenarioPoseEntry` |
| `VIDEO/_retired_python_video/run.py` | `url_prefix='/video/scenario-pose'` |

## Inventory

```
prefix: /video/scenario-pose
python: 14
java:   14
matched: 14
diff: 0
```

## Py route ↔ Java mapping

| Method | Python path | Java |
|--------|-------------|------|
| GET | `/video/scenario-pose/libraries` | `ScenarioPoseController.listLibraries` |
| GET | `/video/scenario-pose/libraries/{id}` | `ScenarioPoseController.getLibrary` |
| POST | `/video/scenario-pose/libraries` | `ScenarioPoseController.createLibrary` |
| PUT | `/video/scenario-pose/libraries/{id}` | `ScenarioPoseController.updateLibrary` |
| DELETE | `/video/scenario-pose/libraries/{id}` | `ScenarioPoseController.deleteLibrary` |
| GET | `/video/scenario-pose/libraries/{id}/entries` | `ScenarioPoseController.listEntries` |
| POST | `/video/scenario-pose/libraries/{id}/entries` | `ScenarioPoseController.addEntry` |
| PUT | `/video/scenario-pose/entries/{id}` | `ScenarioPoseController.updateEntry` |
| DELETE | `/video/scenario-pose/entries/{id}` | `ScenarioPoseController.deleteEntry` |
| POST | `/video/scenario-pose/entries/{id}/re-extract` | `ScenarioPoseController.reExtractEntry` |
| POST | `/video/scenario-pose/entries/extract` | `ScenarioPoseController.extractPreview` |
| POST | `/video/scenario-pose/libraries/{id}/match-test` | `ScenarioPoseController.matchTest` |
| GET | `/video/scenario-pose/scene-templates` | `ScenarioPoseController.listSceneTemplates` |
| POST | `/video/scenario-pose/libraries/{id}/import-template` | `ScenarioPoseController.importTemplate` |

## EXEMPTIONS

`EX-SCENARIO-POSE` → **resolved by FR-W3-POSE**

## Phase 0

`python tools/video_java/certify.py --phase 0 --no-java --no-record` → **exit 0** (2026-08-10)

## Concerns

1. **YOLO pose / OpenCV** — `PoseAnalysisService` 为桩；图片录入/重提取/匹配返回空或 400「未检测到人体姿态」；规则条目 CRUD 与模板导入可用。
2. **MinIO 图片存储** — `scenario-pose-library` bucket 上传/删除为桩；`image_url` 路径已对齐 Python 格式。
3. **姿态相似度** — `match_test` / `extract_preview` 无 `pose_intent` 角度特征计算；有检测引擎前返回空结果。
4. **Maven 编译** — JDK 21 在 `F:\acme\.tools\jdk-21.0.2` 可用，但本机无 `mvn` PATH；`route_inventory` + `certify --phase 0` 已绿。

## Remaining routes

**无**（inventory diff=0）
