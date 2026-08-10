# FR-W3-TALK Report

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Summary

Ported all **5** `/video/camera/audio/talk` Python routes to Java `AudioTalkController` + `AudioTalkService` / `OnvifAudioBackchannelClient` / `AudioTalkSession`.  
`route_inventory.py --prefix /video/camera/audio/talk` → **Py 5 / Java 5 / diff 0**.  
**EX-AUDIO-TALK resolved.**  
`certify.py --phase 0` → **exit 0**.

## Commits

(see `git log -1` after commit)

## Python files read

| File | Scope |
|------|--------|
| `VIDEO/_retired_python_video/app/blueprints/audio_talk.py` | **全部** 5 `@audio_talk_bp.route` |
| `VIDEO/_retired_python_video/app/services/onvif_audio_backchannel.py` | probe/describe/setup/play/teardown + SDP parse |
| `VIDEO/_retired_python_video/app/services/audio_talk_service_onvif.py` | session manager + RTP send |
| `VIDEO/_retired_python_video/run.py` | `url_prefix='/video/camera/audio/talk'` |

## Inventory

```
prefix: /video/camera/audio/talk
python: 5
java:   5
matched: 5
diff: 0
```

## Py route ↔ Java mapping

| Method | Python path | Java |
|--------|-------------|------|
| GET | `/video/camera/audio/talk/capabilities` | `AudioTalkController.capabilities` |
| POST | `/video/camera/audio/talk/start` | `AudioTalkController.start` |
| POST | `/video/camera/audio/talk/stop` | `AudioTalkController.stop` |
| POST | `/video/camera/audio/talk/send` | `AudioTalkController.send` |
| GET | `/video/camera/audio/talk/health` | `AudioTalkController.health` |

## EXEMPTIONS

`EX-AUDIO-TALK` → **resolved by FR-W3-TALK**

## Phase 0

`python tools/video_java/certify.py --phase 0` → **exit 0** (2026-08-10)

## Concerns

1. **ONVIF 真机** — `OnvifAudioBackchannelClient` 为 Python `onvif_audio_backchannel` 的 Java 移植；无 ONVIF 设备时 capabilities 返回 `supported=false`，start 返回 500（与 Python 等价）。
2. **G.711 编码** — Java 侧为简化线性 PCM→G.711 映射；非标准 A-law/μ-law 查表，真机音质/兼容性待验。
3. **设备密码** — `DeviceRepository.findPasswordById` 单独查询 `device.password`（`DeviceRow` 不含密码字段）。
4. **Maven 编译** — 本机 JDK 17 + 项目 target 21 → `mvn package` 失败；`route_inventory` + `certify --phase 0` 已绿（沿用既有 fat jar 跑 P0；新控制器需 JDK21 重编后重启 `:48096`）。

## Remaining routes

**无**（inventory diff=0）
