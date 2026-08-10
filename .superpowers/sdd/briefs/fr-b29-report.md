# FR-B29 Report — GET keys-matrix 扩面 + deferred 清除

**STATUS:** DONE (local `:48096`) — **禁止 COMPLETE**

**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Before / After (vs FR-B28 baseline)

| 指标 | FR-B28 (before) | FR-B29 (after) | Δ |
|------|-----------------|---------------|---|
| Routes probed | 265 | 265 | — |
| Routes pass | 247 | **265** | +18 |
| Mapping table paths | 41 | **94** | +53 |
| Key-assert routes | 39 | **92** | +53 |
| Envelope-only GET | 59 | **6** | −53 |
| Item-key asserts | 31 pass / 0 fail / **8 deferred** | **60 pass / 0 fail / 0 deferred** | deferred 清零 |
| Total asserts | 293 pass / 25 fail | **315 pass / 0 fail** | |

**Artifacts:** `logs/fr-b29-keys-matrix-latest.{json,md}`（映射表见 MD §「Python-first mapping table」）

## Mapping table（引用）

完整 94 路径映射见 `logs/fr-b29-keys-matrix-latest.md` 第 17–111 行。B29 新增模块：`tools/video_java/keys_matrix_b29_specs.py`（`B29_EXTRA_ROUTE_KEY_SPECS`，键均自 `VIDEO/_retired_python_video` blueprint / `to_dict` 读取，禁止发明键）。

代表性新增映射（节选）：

| path | python_source |
|------|---------------|
| `/video/algorithm/task/{param}/post-process/results` | `post_process_result_service.py list_post_process_results` |
| `/video/camera/directory/monitor-tree` | `camera.py get_directory_monitor_tree` → `{tree, unassigned_devices}` |
| `/video/stream-forward/task/{param}/streams` | `stream_forward.py get_task_streams` → `device_id, rtmp_stream, …` |
| `/video/snap/device/{param}/storage` | `snap.py get_device_storage` → `DeviceStorageConfig.to_dict` + `storage_service.get_device_storage_info` |
| `/video/scenario-pose/scene-templates` | `scenario_pose_library_service.list_scene_templates` → `key` + `SCENE_TEMPLATES` |

## Java fixes

| 组件 | 修复 |
|------|------|
| `PostProcessResultRepository` | 列名对齐 Python（`payload`/`counts`/…，非 `result_json`） |
| `AlgorithmTaskController.postProcessResults` | 返回 `VideoApiResponse.success(result)` |
| `FaceController.listPersons` | Python 顶栏分页 `{code,msg,data,total,page,page_size}` |
| `VideoApiResponseAdvice` | 透传已含 `{code,msg}` 的 Map（避免双层信封） |
| `SnapStorageService.getOrCreate` | 存储统计键 `snap_size`/`snap_count`/… 对齐 Python |

## B29 seed（`seed_fr_b29_keys_matrix.py`）

| step | 用途 |
|------|------|
| alert_hook_image | `alert/page` item-key |
| device_location | `camera/locations` |
| nvr_upsert | `camera/nvr/list` |
| track_session (DB) | `camera/tracks/sessions` |
| face/plate matching process | `face/plate/matching/records`（任务绑定 library_ids） |

**Seed 结果：** 6/6 OK（`run_b29_seed_setups` 集成于 `--keys-matrix`）

## phase0

`python tools/video_java/certify.py --phase 0` → **PASS 5/5**（`logs/certify-frb29-phase0.log`）

## Remaining envelope-only（6）

非 JSON / 流式 / 二进制，诚实保留 envelope-only：

1. `GET /video/alert/image`
2. `GET /video/alert/record`
3. `GET /video/patrol/session/{param}/events`（SSE）
4. `GET /video/playback/thumbnail/{param}`
5. `GET /video/record/space/{param}/video/{param}`
6. `GET /video/snap/space/{param}/image/{param}`

## Concerns

- keys-matrix 为 **抽样键断言**（首条 list item / data object），≠ 259 路由全字段 parity。
- `SnapStorageService` 存储用量仍为 0 占位（MinIO 桶统计未接线）。
- InsightFace/Milvus/ONVIF 等行为仍为 mini 桩；prod soak checklist 大部 open。
- **禁止对外宣称 COMPLETE / 整域 migrated。**
