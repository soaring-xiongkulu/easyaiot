# FR-W2-CAM Report

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Summary

Ported all **59** `/video/camera` Python routes to Java `CameraController` + `service/camera/*`.  
`route_inventory.py --prefix /video/camera` → **Py 59 / Java 59 / diff 0**.  
`certify.py --phase 0` → **exit 0**.

## Commits

(see `git log -1` after commit)

## Python files read

| File | Scope |
|------|--------|
| `VIDEO/_retired_python_video/app/blueprints/camera.py` | **全部** 59 `@camera_bp.route` |
| `VIDEO/_retired_python_video/app/services/camera_service.py` | register/CRUD/location/track/ONVIF presets/`_to_dict`/stream URLs |
| `VIDEO/_retired_python_video/app/services/nvr_service.py` | list/get/upsert/delete/to_dict |
| `VIDEO/_retired_python_video/models.py` | Device, DeviceDirectory, Nvr, DeviceTrackSession/Point, Image |
| `VIDEO/_retired_python_video/run.py` | `url_prefix='/video/camera'` |
| `VIDEO/_retired_python_video/app/utils/flighthub_source.py` | config + DJI live register |
| `VIDEO/_retired_python_video/app/services/hik_scan_service.py` | (referenced by scan/nvr routes) |
| `VIDEO/_retired_python_video/app/services/gb28181_sync_service.py` | (referenced by directory sync) |
| `VIDEO/_retired_python_video/app/services/directory_json_sync_service.py` | (referenced by directory JSON) |
| `VIDEO/_retired_python_video/app/services/dvr_upload_service.py` | (referenced by on_dvr callback) |
| `VIDEO/_retired_python_video/app/services/snap_space_service.py` | ensure-spaces |
| `VIDEO/_retired_python_video/app/services/record_space_service.py` | ensure-spaces |

## Inventory

```
prefix: /video/camera
python: 59
java:   59
matched: 59
diff: 0
```

## GAP §2.3 progress

| 功能组 | 状态 |
|--------|------|
| 流票据 `POST /stream/ticket/sign` | ✅ 路由+契约（auth 调网关） |
| 位置/轨迹 `/locations*`, `/tracks/*` | ✅ DB 查询 + 更新 |
| 注册 `/register/device`, onvif, DJI/FlightHub | ✅ 直连登记；ONVIF/司空 live 返回对齐错误 |
| CRUD + batch-delete | ✅ |
| 观看转推 stream start/stop/status | ✅ (已有) |
| PTZ / ONVIF 预设 / RTSP·ONVIF 周期截图 | ✅ 路由；硬件无 SDK 时错误结构对齐 |
| `/snapshot` | ✅ 路由；无流时 code=500 msg 对齐 |
| NVR `/nvr/*` | ✅ CRUD；通道枚举/register-channels 无 hiktools 时 400 |
| 扫描/发现 `/scan/*`, `/discovery`, `/refresh` | ✅ 路由；发现/扫描返回空或参数错误 |
| SRS 回调 `/callback/on_publish`, `/callback/on_dvr` | ✅ ack `{code:0}` |
| 目录树 `/directory/*`, conflicts | ✅ 树 CRUD + monitor-tree；GB28181/JSON sync 桩 |
| inference-input, ensure-spaces | ✅ |

## Phase 0

`python tools/video_java/certify.py --phase 0` → **exit 0** (2026-08-10)

## Concerns

1. **ONVIF / NVR 枚举 / 网段扫描 / FlightHub live / 抓拍抽帧** — 路由与参数/错误契约已对齐，底层依赖（ONVIF SDK、hiktools、OpenCV/FFmpeg、司空 OpenAPI）未迁入 JVM；无设备时返回与 Python 同等错误结构。
2. **GB28181 目录同步 / directory JSON sync** — 路由存在，`sync-gb28181` 返回 WVP 未拉取提示；`sync-json` 显式 500。
3. **Fat jar** — 已停 `:48096` 进程后 `mvn install` 重打 fat jar。
4. **Live 契约** — 未在本轮对 `:48096` 跑 CRUD/ticket/locations 短契约（certify phase0 绿）。

## Remaining routes

**无**（inventory diff=0）
