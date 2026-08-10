# FR-W4 Report — 全量路由核对 + 缺口表收口 + fat jar

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Summary

Ran `tools/video_java/route_inventory.py` for all 14 inventoried video prefixes.  
**Py≈259 / Java≈259 / prefix-level diff=0.**  
Updated `FULL_REPLACEMENT_GAP.md` §0/§8/§9, `progress.md`, `HANDOFF.md`.  
Rebuilt fat jar (`iot-video-biz.jar`), restarted `:48096`, `certify.py --phase 0` → **exit 0**.

## Commits

(see `git log -1` after commit)

## Full inventory table

| Prefix | Py | Java | diff | Notes |
|--------|---:|-----:|-----:|-------|
| `/video/alert` | 10 | 10 | 0 | |
| `/video/algorithm` | 21 | 21 | 0 | |
| `/video/camera` | 59 | 64 | 5† | †only-java = 5× `/audio/talk/*`（inventory 前缀重叠，非缺口） |
| `/video/camera/audio/talk` | 5 | 5 | 0 | FR-W3-TALK |
| `/video/stream-forward` | 13 | 13 | 0 | |
| `/video/face` | 35 | 35 | 0 | |
| `/video/plate` | 26 | 26 | 0 | |
| `/video/snap` | 38 | 38 | 0 | |
| `/video/record` | 16 | 16 | 0 | |
| `/video/playback` | 7 | 7 | 0 | |
| `/video/media` | 6 | 6 | 0 | |
| `/video/patrol` | 9 | 9 | 0 | |
| `/video/scenario-pose` | 14 | 14 | 0 | FR-W3-POSE |
| `/video/device-detection` | 6 | 6 | 0 | |
| **合计（去重）** | **≈259** | **≈259** | **0** | talk 路由只计一次 |

## Remaining behavior gaps (honest)

| 类别 | 缺口 |
|------|------|
| MinIO | snap/record 空间真同步/清理；media DVR 上传；抓拍 Kafka→MinIO 全链路 |
| ONVIF / 设备 | camera PTZ/预设/NVR 枚举/网段扫描/抓拍抽帧；audio_talk back-channel 真机 |
| 推理 / 库 | face InsightFace/ONNX + Milvus；plate PaddleOCR；scenario_pose extract/match-test |
| 远程 / 集群 | algorithm/stream_forward `schedule_policy!=local` → 400（EX-REMOTE-NODE） |
| 后台 | snap_task `init_all_tasks` 调度；stream_forward 集群健康迁移 |
| 集成 | post-process 真 sink（`use-stub-enqueue`）；prod Kafka 全链路联调 |
| patrol | SSE/守护进程 mini 桩 |

## Build & restart

```text
JAVA_HOME=F:\acme\.tools\jdk-21.0.2
mvn -f DEVICE/pom.xml -pl iot-video/iot-video-biz -am package -DskipTests
java -jar DEVICE/iot-video/iot-video-biz/target/iot-video-biz.jar --spring.profiles.active=local
# → http://127.0.0.1:48096/actuator/health
```

## Phase 0

`python tools/video_java/certify.py --phase 0` → **exit 0** (2026-08-10)

## COMPLETE allowed?

**NO** — HTTP 路由面已齐，但 MinIO/ONVIF/YOLO/推理/Milvus 等行为桩仍存；禁止 COMPLETE / 退役 Python。
