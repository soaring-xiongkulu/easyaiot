# Phase 2 A5 Report — Camera list/get/register key-path (handoff for A6)

**Status:** PASS  
**Pack:** P2-A5  
**Date:** 2026-08-11  
**Commit:** (see index after commit) — `feat(video-java): phase2 A5 camera mainpath parity`  
**Evidence:** `logs/phase2-a5-camera.json`  
**nested_subagents:** none

## Prior packs

- A1 PASS (`2b3d483`) — alert Kafka; fixture device `frb26_device`, task 61
- A2 PASS (`e214456`) — algo RUNTIME lifecycle
- A3 PASS (`50ce091`) — ViewForward / stream-forward ffmpeg lifecycle
- A4 PASS (`2be5393`) — media DVR/Snap → Kafka → MinIO
- Phase 1 stack PASS — profile `local`, PG 15432

## What was proven

On local full stack (`profile=local`):

1. **List** — `GET /admin-api/video/camera/list` → 17 devices, `total` matches direct `:48096`
2. **Get** — `GET /admin-api/video/camera/device/frb26_device` → key fields (`id`, `name`, `source`, streams, `manufacturer`, `model`, `online`, `device_kind`, `directory_id`) match Python `camera_service._to_dict()` on same DB row
3. **List/get consistency** — list item for `frb26_device` identical to dedicated GET
4. **Register** — `POST /admin-api/video/camera/register/device` with `source` + `cameraType=custom` → device row + `snap_space` (id 33) + `record_space` (id 32) created
5. **Update** — `PUT /admin-api/video/camera/device/p2a5_cam_20260811184235` → `name` / `model` persisted; GET reflects changes; Python `_to_dict` agrees

## Oracle vs Java

| Concern | Oracle (Python) | Java candidate |
|---------|-----------------|----------------|
| List | `camera.py` → `GET /list` → `get_device_list` / paginated search | `CameraController.list` → `CameraService.listDevices` |
| Get | `camera.py` → `GET /device/{id}` → `get_camera_info` → `_to_dict` | `CameraController.get` → `CameraService.getDevice` → `toMap` |
| Register | `camera.py` → `POST /register/device` → `register_camera` | `CameraController.registerDevice` → `CameraAdminService.registerDevice` |
| Update | `camera.py` → `PUT /device/{id}` → `update_camera` | `CameraController.updateDevice` → `CameraAdminService.updateDevice` |
| Key payload | `_to_dict` — streams, online, location, nvr, device_kind | `CameraService.toMap` — same field set |
| Ensure spaces | `ensure_device_spaces` on register/get | `CameraAdminService.ensureSpacesQuiet` on register |

## Code changes (this pack)

None — FR-W2-CAM already ported 59 `/video/camera` routes; this pack is **local full-stack evidence** for list/get/register/update key-field parity on shared `iot-video20`.

## Fixture left in DB

- Existing: `frb26_device` (unchanged; prior A1–A4 fixture)
- New: `p2a5_cam_20260811184235` — `Phase2 A5 Updated Name`, snap_space 33, record_space 32 (not cleaned up)

## Constraints for A6

- Do NOT flip shortcuts / mini / stub executor / sync upload / disable MinIO
- Do NOT claim COMPLETE / delete Python
- Stack unchanged: PG 15432, Kafka 9092, Nacos 8848, MinIO 9000, GW 48080, video 48096 **local**
- Device `frb26_device` + `p2a5_cam_20260811184235` have prior rows; scope checks explicitly

## Concerns

1. ONVIF register not exercised (no hardware sweep per brief)
2. Oracle comparison via `_to_dict` on shared DB (Python HTTP not running)
3. New device stream URLs use config default host `10.0.0.1`; `frb26_device` has custom `127.0.0.1` stored values — both explainable

## Next pack

**P2-A6** — Post-process (`logs/phase2-a6-postprocess.json`)
