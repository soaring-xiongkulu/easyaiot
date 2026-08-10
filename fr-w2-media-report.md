# FR-W2-MEDIA Report

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Summary

Ported **61** routes across `/video/snap` (38), `/video/record` (16), `/video/playback` (7) to Java controllers + `service/snap/*`, `service/record/*`, `PlaybackService`.  
`route_inventory.py` → **Py/Java diff 0** per prefix.  
`certify.py --phase 0` → **exit 0**.

## Commits

(see `git log -1` after commit)

## Python files read

| File | Scope |
|------|--------|
| `VIDEO/_retired_python_video/app/blueprints/snap.py` | 全部 38 routes |
| `VIDEO/_retired_python_video/app/blueprints/record.py` | 全部 16 routes |
| `VIDEO/_retired_python_video/app/blueprints/playback.py` | 全部 7 routes |
| `VIDEO/_retired_python_video/app/services/snap_space_service.py` | space CRUD/list/group/sync |
| `VIDEO/_retired_python_video/app/services/snap_task_service.py` | task CRUD/lifecycle/logs |
| `VIDEO/_retired_python_video/app/services/snap_image_service.py` | images list/get/delete/sync/cleanup |
| `VIDEO/_retired_python_video/app/services/snap_upload_service.py` | upload pipeline (referenced) |
| `VIDEO/_retired_python_video/app/services/record_space_service.py` | record space CRUD/list/sync |
| `VIDEO/_retired_python_video/app/services/record_video_service.py` | videos dates/day/object/alert-resolve |
| `VIDEO/_retired_python_video/app/services/algorithm_service.py` | task/region algorithm services |
| `VIDEO/_retired_python_video/app/services/storage_service.py` | device storage config |
| `VIDEO/_retired_python_video/app/services/space_group_save_time_service.py` | group-policy |
| `VIDEO/_retired_python_video/app/services/space_save_time_service.py` | save_time validation (referenced) |
| `VIDEO/_retired_python_video/run.py` | `url_prefix` `/video/snap|record|playback` |
| `VIDEO/_retired_python_video/models.py` | SnapTask/SnapImage/RecordFile/Playback/DetectionRegion |

## Inventory per prefix

```
prefix: /video/snap     python: 38  java: 38  diff: 0
prefix: /video/record   python: 16  java: 16  diff: 0
prefix: /video/playback python: 7   java: 7   diff: 0
```

## GAP §2.6

| 域 | 路由差 | 行为剩余 |
|----|--------|----------|
| snap | ✅ diff=0 | MinIO sync/cleanup、APScheduler 抓拍、真图片字节流 |
| record | ✅ diff=0 | MinIO 录像字节流、孤儿清理、告警片段精确匹配 |
| playback | ✅ diff=0 | `video_url` 真解析（现 file_path 直通） |

## Phase 0

`python tools/video_java/certify.py --phase 0` → **exit 0** (2026-08-10)

## Remaining

**无路由差**（inventory diff=0）。行为层见 GAP §2.6 ❌ 行。

## Concerns

1. **MinIO / 本地文件** — sync/cleanup/图片·录像 GET 在 mini 形态为 DB 桩或本地路径探测，无 MinIO SDK。
2. **抓拍调度** — start/stop/restart 仅更新 `snap_task.run_status`，无 APScheduler/cron 执行。
3. **空间目录树** — list 仍 root 直挂设备空间，未完整移植 `space_folder_tree_service` NVR/GB28181 层级。
4. **算法服务 task_id** — Python `algorithm_service` 绑 `algorithm_task`；snap 蓝图用 `snap_task` id，Java 按蓝图以 snap_task 存在性校验后写入 `algorithm_model_service`。
