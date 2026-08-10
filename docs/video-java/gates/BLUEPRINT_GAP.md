# Blueprint gap inventory — retired Python vs Java `iot-video`

**Audit date:** 2026-08-10  
**Oracle:** `VIDEO/_retired_python_video/app/blueprints/*.py`  
**Candidate:** `DEVICE/iot-video/iot-video-biz/.../controller/*`

Every retired blueprint row has a Java controller mapping, a certify case, or a signed exemption ID. **No silent omissions.**

## Summary

| Status | Count | Blueprints |
|--------|------:|------------|
| Migrated (certified) | 10 | `algorithm_task`, `camera`, `device_detection_region`, `face`, `media_hook`, `plate`, `playback`, `record`, `snap`, `stream_forward` |
| Partial (subset certified) | 2 | `alert`, `patrol` |
| Deferred (signed EX) | 2 | `audio_talk`, `scenario_pose` |

Heartbeat (`POST /video/algorithm/heartbeat/realtime`) is not a separate blueprint; it is covered by `HeartbeatController` and `vj_p0_heartbeat`.

## Full table

| Blueprint | Python module | URL prefix | Java status | Java controller / surface | Certify case or EX id | Notes |
|-----------|---------------|------------|-------------|---------------------------|----------------------|-------|
| `algorithm_task` | `algorithm_task.py` | `/video/algorithm` | **migrated** | `AlgorithmTaskController` | `vj_p0_task_start_stop`, `vj_p0_restart` | Task list/detail/start/stop (cpp) |
| `alert` | `alert.py` | `/video/alert` | **partial** | `AlertHookController` (`/hook` only) | `vj_p0_alert_hook` (hook); **EX-ALERT-ADMIN-API** (page/count/statistics/clear/image/record) | Hook path certified P0; admin/query UI deferred Phase 3+ |
| `audio_talk` | `audio_talk.py` | `/video/camera/audio/talk` | **deferred** | — | **EX-AUDIO-TALK** | ONVIF audio back-channel; out of Phase 0–2 |
| `camera` | `camera.py` | `/video/camera` | **migrated** | `CameraController` | `vj_p1_camera_list`, `vj_p1_camera_get`, `vj_p1_view_forward_start_stop` | View-forward ffmpeg under camera |
| `device_detection_region` | `device_detection_region.py` | `/video/device-detection` | **migrated** | `DeviceDetectionRegionController` | `vj_p2_detection_region_get` | |
| `face` | `face.py` | `/video/face` | **migrated** | `FaceMatchingController` | `vj_p2_face_publish_process` | publish + process |
| `media_hook` | `media_hook.py` | `/video/media` | **migrated** | `MediaHookController` | `vj_p2_media_hook` | snap completed hook |
| `patrol` | `patrol.py` | `/video/patrol` | **partial** | — (no `PatrolController`) | `vj_p2_patrol_task_list` (algorithm `task_type=patrol`); **EX-PATROL-SESSION-API** | Session CRUD/heartbeat/SSE deferred; P2 covers task list only |
| `plate` | `plate.py` | `/video/plate` | **migrated** | `PlateMatchingController` | `vj_p2_plate_publish_process` | publish + process |
| `playback` | `playback.py` | `/video/playback` | **migrated** | `PlaybackController` | `vj_p2_playback_url` | list substitute for play-url |
| `record` | `record.py` | `/video/record` | **migrated** | `RecordController` | `vj_p2_record_query` | space list |
| `scenario_pose` | `scenario_pose.py` | `/video/scenario-pose` | **deferred** | — | **EX-SCENARIO-POSE** | Pose library CRUD/match-test; out of Phase 0–2 |
| `snap` | `snap.py` | `/video/snap` | **migrated** | `SnapController` | `vj_p2_snap_list_or_create` | |
| `stream_forward` | `stream_forward.py` | `/video/stream-forward` | **migrated** | `StreamForwardController` | `vj_p1_stream_forward_start_stop` | |

## Related controllers (not 1:1 blueprints)

| Controller | Prefix | Certify case |
|------------|--------|--------------|
| `HeartbeatController` | `/video/algorithm/heartbeat` | `vj_p0_heartbeat` |
| `VideoPingController` | `/video/ping` | (infra; no blueprint) |

## Audit method

```text
# Python blueprints (exclude __init__.py)
ls VIDEO/_retired_python_video/app/blueprints/*.py

# Java iot-video controllers
ls DEVICE/iot-video/iot-video-biz/src/main/java/com/basiclab/iot/video/controller/*.java

# Blueprint URL prefixes
rg register_blueprint VIDEO/_retired_python_video/run.py
```

Signed deferrals: `gates/EXEMPTIONS.md`.
