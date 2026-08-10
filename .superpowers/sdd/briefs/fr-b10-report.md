# FR-B10 Report — Patrol 守护/SSE + audio_talk 真路径 + 匹配告警 MinIO

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Closed FR-B9 remaining behavior gaps: patrol daemon env propagation aligned with Python `PatrolSessionDaemon`; ONVIF audio talk uses real G.711 companding + RTP port 5000; library-match alerts upload `image_path` to MinIO `alert-images` and set `image_url`; scenario-pose `match-test` returns per-person similarity scores via ported `pose_intent` logic.

## Python files read (oracle)

| Path | Purpose |
|------|---------|
| `VIDEO/_retired_python_video/app/services/patrol_session_service.py` | `PatrolSessionDaemon`, heartbeat, stats/SSE broadcast |
| `VIDEO/_retired_python_video/app/services/patrol_progress_hub.py` | SSE subscribe/publish queue semantics |
| `VIDEO/_retired_python_video/app/services/onvif_audio_backchannel.py` | RTSP DESCRIBE/SETUP/PLAY + G.711/RTP |
| `VIDEO/_retired_python_video/app/services/audio_talk_service_onvif.py` | session lifecycle + `AudioSender` |
| `VIDEO/_retired_python_video/app/services/library_matching_service.py` | `_create_match_alert` + MinIO upload |
| `VIDEO/_retired_python_video/app/services/alert_consumer_service.py` | `upload_image_to_minio` bucket/path contract |
| `VIDEO/_retired_python_video/app/services/scenario_pose_library_service.py` | `match_test` scoring loop |
| `VIDEO/_retired_python_video/app/utils/pose_intent.py` | angle/combined similarity + extra_rules |

## Java changes (key)

| Component | Change |
|-----------|--------|
| `PatrolSupervisor` | propagate DATABASE/KAFKA/MINIO/GB28181 env; log header on restart |
| `OnvifAudioBackchannelClient` | backchannel track selection strategy 3 (audio keyword) |
| `G711Codec` + `AudioTalkSession` | ITU-T A-law/μ-law encode; bind RTP UDP 5000 |
| `AlertImageUploadService` | `alert-images` upload + `AlertRepository.updateImageUrl` |
| `MatchAlertService` | post-insert MinIO link on match hits |
| `PoseIntentMatcher` | `extractAngleFeatures` / `matchTest` scoring |
| `ScenarioPoseLibraryService` | wired `matchTest` + extract preview features |
| `FULL_REPLACEMENT_GAP.md` | §2.8 patrol/audio_talk/pose behavior → FR-B10 ✅ |

## GAP

- §2.8 `patrol` / `audio_talk` / `scenario_pose` match-test → **FR-B10 ✅**
- §8 behavior stubs → patrol/audio_talk/match-image rows closed; cluster health / prod MinIO /真机仍待 ops
- Match alert MinIO → **FR-B10 ✅**（`MINIO_ENABLED` off 时 skip，与 Python 一致）

## certify --phase 0

```
exit 0
```

Log: `certify-frb10-phase0.log`（oracle `:6000` 未运行 — stale golden warnings; all cases ok/exempt）

## Concerns / remaining

1. **Patrol 真机** — 守护脚本 `EDGE/runtime/services/patrol_algorithm_service/run_deploy.py` 需本机 Python 依赖；默认目录 GB28181 同步仍 Java warning-only。
2. **Audio talk 真机** — RTSP back-channel 需摄像机 Profile T/Q；端口 5000 冲突时会话启动失败。
3. **MinIO prod** — `video.minio.enabled` / `MINIO_ENABLED` 默认 off；启用后需 broker/桶联调。
4. **Pose match-test** — 评分在 Java 侧；extract 仍依赖 Python YOLO worker（FR-B9 路径）。
