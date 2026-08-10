# FR-B28 Report — 全量 GET 字段键自动矩阵（Python-first）

**Status:** PARTIAL（keys-matrix 265/265 pass / phase0 PASS 5/5）— **禁止 COMPLETE**

**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

---

## 1. 工具：`field_contract.py --keys-matrix`

| 指标 | 值 |
|------|-----|
| Inventoried 路由 | **265** |
| 端点 pass/fail | **265 / 0** |
| GET 路由 | **98**（JSON **95** + 非 JSON skip **3**） |
| Python-first 映射表 | **41** 路径 |
| Key-assert 路由 | **39** |
| Envelope-only 路由 | **59** |
| Item/object key asserts | **31 pass / 0 fail / 8 deferred** |
| 全局 seed setups | **15/15 OK** |
| Asserts 总计 | pass=255 fail=0 skip=178 |

**证据：** `logs/fr-b28-keys-matrix-latest.{json,md}`  
**phase0：** `certify-frb28-phase0.log` → **PASS 5/5**

---

## 2. Python-first 映射表（41 路径）

键来源：`SAMPLE_CASES` + `EXTRA_ROUTE_KEY_SPECS`（均引用 Python `models.py` `to_dict` 或 blueprint handler；**未发明键**）。

| path | id | python_source |
|------|----|---------------|
| `/video/alert/count` | alert_count | `alert_service.py get_alert_count` |
| `/video/alert/page` | alert_page | `alert_service.py get_alert_list` + item keys `Alert.to_dict` |
| `/video/alert/statistics` | alert_statistics | `alert_service.py get_dashboard_statistics` |
| `/video/algorithm/task/list` | algorithm_task_list | `models.py AlgorithmTask.to_dict` |
| `/video/algorithm/task/{param}` | algorithm_task_get | `models.py AlgorithmTask.to_dict` |
| `/video/camera/list` | camera_list | `camera_service.py _to_dict` |
| `/video/camera/device/{param}` | camera_get | `camera_service.py _to_dict` |
| `/video/camera/locations` | camera_locations | `camera.py list_device_locations` |
| `/video/camera/directory/list` | camera_directory_list | `camera.py list_directories` |
| `/video/camera/nvr/list` | camera_nvr_list | `nvr_service.py list_nvrs` |
| `/video/camera/tracks/sessions` | camera_tracks_sessions | `models.py DeviceTrackSession.to_dict` |
| `/video/camera/audio/talk/health` | audio_talk_health | `audio_talk.py health()` |
| `/video/device-detection/device/{param}/regions` | device_detection_regions | `models.py DeviceDetectionRegion.to_dict` |
| `/video/face/health` | face_health | `face.py face_health` |
| `/video/face/libraries` | face_libraries | `models.py FaceLibrary.to_dict` |
| `/video/face/libraries/{param}` | face_library_get | `models.py FaceLibrary.to_dict` |
| `/video/face/matching/records` | face_matching_records | `models.py FaceMatchRecord.to_dict` |
| `/video/face/model/status` | face_model_status | `face_model_download.py get_face_rec_model_status` |
| `/video/plate/health` | plate_health | `plate_model_download.py get_plate_model_status` |
| `/video/plate/libraries` | plate_libraries | `models.py PlateLibrary.to_dict` |
| `/video/plate/libraries/{param}` | plate_library_get | `models.py PlateLibrary.to_dict` |
| `/video/plate/matching/records` | plate_matching_records | `models.py PlateMatchRecord.to_dict` |
| `/video/plate/model/status` | plate_model_status | `plate_model_download.py` |
| `/video/playback/list` | playback_list | `models.py Playback.to_dict` |
| `/video/playback/{param}` | playback_get | `models.py Playback.to_dict` |
| `/video/playback/statistics` | playback_statistics | `playback.py get_playback_statistics` |
| `/video/record/space/list` | record_space_list | `models.py RecordSpace.to_dict` |
| `/video/record/space/device/{param}` | record_space_by_device | `models.py RecordSpace.to_dict` |
| `/video/record/space/{param}` | record_space_get | `models.py RecordSpace.to_dict` |
| `/video/record/space/{param}/videos` | record_videos_list | `models.py RecordFile.to_list_item` |
| `/video/scenario-pose/libraries` | scenario_pose_libraries | `models.py ScenarioPoseLibrary.to_dict` |
| `/video/scenario-pose/libraries/{param}` | scenario_pose_library_get | `models.py ScenarioPoseLibrary.to_dict` |
| `/video/snap/space/list` | snap_space_list | `models.py SnapSpace.to_dict` |
| `/video/snap/space/{param}` | snap_space_get | `models.py SnapSpace.to_dict` |
| `/video/snap/task/list` | snap_task_list | `models.py SnapTask.to_dict` |
| `/video/snap/task/{param}` | snap_task_get | `models.py SnapTask.to_dict` |
| `/video/stream-forward/task/list` | stream_forward_task_list | `models.py StreamForwardTask.to_dict` |
| `/video/stream-forward/task/{param}` | stream_forward_task_get | `models.py StreamForwardTask.to_dict` |
| `/video/stream-forward/task/{param}/status` | stream_forward_task_status | `stream_forward.py get_task_status` |
| `/video/patrol/directory/{param}/devices` | patrol_directory_devices | `patrol.py directory_patrol_devices` |
| `/video/ping` | media_ping | Java `VideoPingController`（非 inventoried；保留深采样） |

**未映射（59 GET）：** envelope-only（不 fail），含 algorithm task 子路径、face/plate library entries、snap region、patrol session 等 — 待后续从 Python blueprint 补映射。

---

## 3. Java 修复

| 文件 | 问题 | 修复 |
|------|------|------|
| `SnapTaskRepository.insert` | INSERT 25 `?` vs 24 列；`run_status` 未 `i++`；缺 `total_captures`；PostgreSQL `getKey()` 多列 | 对齐 25 列/占位符；`total_captures=0`；`new String[]{"id"}` |

修复后 `POST /video/snap/task` 成功；`GET /video/snap/task/list` item-key **36 keys pass**。

---

## 4. 8 deferred item-key（空 data/列表，非 fail）

- `GET /video/alert/page` — alert_list 空（filter 需 image_url 种子）
- `GET /video/camera/locations` / `nvr/list` / `tracks/sessions` — 空列表
- `GET /video/face/matching/records` / `plate/matching/records` — 无匹配记录
- `GET /video/record/space/{param}` / `snap/task/{param}` — probe id 未绑定 setup 创建 id

---

## Remaining

- 补 **59** envelope-only 路由的 Python-first 映射
- deferred 端点种子（alert_page、matching records、locations 等）
- prod soak checklist 大部仍 ⬜
- matching worker 推理链

## Concerns

- keys-matrix 绿 ≠ 259 路由全键 parity
- 未映射路由静默 envelope-only — 需持续扩映射表
- 禁止对外宣称 COMPLETE
