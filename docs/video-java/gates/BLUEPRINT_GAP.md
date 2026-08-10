# Blueprint gap inventory — retired Python vs Java `iot-video`

> **角色变更：** 本文件只做「域是否被切片碰到过」的台账。  
> **完整替换进度与完成定义：** 只看 [`../FULL_REPLACEMENT_GAP.md`](../FULL_REPLACEMENT_GAP.md)。  
> **禁止**把下表 `slice-only` 读成「该域已迁完 / migrated」。

**Audit date:** 2026-08-10  
**Oracle:** `VIDEO/_retired_python_video/app/blueprints/*.py`  
**Candidate:** `DEVICE/iot-video/iot-video-biz/.../controller/*`

Every retired blueprint row has a Java controller mapping, a certify case, or an EX id. **No silent omissions.** EX = Phase FR backlog（除非产品书面永久豁免）。

## Summary

| Status | Count | Blueprints |
|--------|------:|------------|
| Slice-only（曾有 certify case，域仍严重不足） | 11 | `algorithm_task`, `camera`, `device_detection_region`, `face`, `media_hook`, `patrol`, `plate`, `playback`, `record`, `snap`, `stream_forward` |
| Partial slice | 1 | `alert` |
| Missing（EX = 完整替换 backlog） | 1 | `scenario_pose` |

Heartbeat (`POST /video/algorithm/heartbeat/realtime`) is covered by `HeartbeatController` / `vj_p0_heartbeat`（切片，非完整）。

## Full table

| Blueprint | Python module | URL prefix | Java status | Java controller / surface | Certify case or EX id | Notes |
|-----------|---------------|------------|-------------|---------------------------|----------------------|-------|
| `algorithm_task` | `algorithm_task.py` | `/video/algorithm` | **slice-only** | `AlgorithmTaskController` | `vj_p0_task_start_stop`, `vj_p0_restart` | 无 CRUD；见缺口表 |
| `alert` | `alert.py` | `/video/alert` | **partial** | `AlertHookController`（仅 hook） | `vj_p0_alert_hook`；**EX-ALERT-ADMIN-API** | 管理面 = FR-W1-ALERT |
| `audio_talk` | `audio_talk.py` | `/video/camera/audio/talk` | **slice-only** | `AudioTalkController` | **FR-W3-TALK ✅ 路由 diff=0** | ONVIF back-channel 行为待真机 |
| `camera` | `camera.py` | `/video/camera` | **slice-only** | `CameraController` | `vj_p1_camera_*` | ~50+ 路由未迁；FR-W2-CAM |
| `device_detection_region` | `device_detection_region.py` | `/video/device-detection` | **slice-only** | `DeviceDetectionRegionController` | `vj_p2_detection_region_get`；**FR-W2-MATCH ✅ 路由 diff=0** | CRUD + cover/snapshot 路由已补 |
| `face` | `face.py` | `/video/face` | **slice-only** | `FaceController` + `FaceMatchingController` | `vj_p2_face_publish_process`；**FR-W2-MATCH ✅ 路由 diff=0** | 库/识别面路由已补；推理桩 |
| `media_hook` | `media_hook.py` | `/video/media` | **slice-only** | `MediaHookController` | `vj_p2_media_hook` | **FR-W2-HOOKS ✅ 路由 diff=0**；DVR MinIO 行为待 SDK |
| `patrol` | `patrol.py` | `/video/patrol` | **slice-only** | `PatrolController` | `vj_p2_patrol_task_list`；**FR-W2-PATROL ✅ 路由 diff=0** | 会话守护/SSE 行为 mini 桩 |
| `plate` | `plate.py` | `/video/plate` | **slice-only** | `PlateController` + `PlateMatchingController` | `vj_p2_plate_publish_process`；**FR-W2-MATCH ✅ 路由 diff=0** | 同 face |
| `playback` | `playback.py` | `/video/playback` | **slice-only** | `PlaybackController` | `vj_p2_playback_url` | 仅 list 级 |
| `record` | `record.py` | `/video/record` | **slice-only** | `RecordController` | `vj_p2_record_query` | 仅 space list |
| `scenario_pose` | `scenario_pose.py` | `/video/scenario-pose` | **missing** | — | **EX-SCENARIO-POSE** | FR-W3-POSE |
| `snap` | `snap.py` | `/video/snap` | **slice-only** | `SnapController` | `vj_p2_snap_list_or_create` | 任务/图片面缺 |
| `stream_forward` | `stream_forward.py` | `/video/stream-forward` | **slice-only** | `StreamForwardController` | `vj_p1_stream_forward_start_stop` | CRUD 缺 |

## Related controllers (not 1:1 blueprints)

| Controller | Prefix | Certify case |
|------------|--------|--------------|
| `HeartbeatController` | `/video/algorithm/heartbeat` | `vj_p0_heartbeat` |
| `VideoPingController` | `/video/ping` | (infra) |

Signed deferrals（现作 backlog）: `EXEMPTIONS.md`。真完成状态以 `FULL_REPLACEMENT_GAP.md` 为准。
