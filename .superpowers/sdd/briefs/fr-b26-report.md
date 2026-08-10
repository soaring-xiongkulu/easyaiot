# FR-B26 Report — 纯 Kafka DVR 路径 + Alert Kafka 本地取证（Python-first）

**Status:** PARTIAL（local E2E ✅ / mini-safe restored / phase0 PASS）— **禁止 COMPLETE**

**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

---

## Python-first 对照（已读）

| 源 | 要点 |
|----|------|
| `VIDEO/_retired_python_video/app/services/media_kafka_service.py` | `is_kafka_upload_mode()` → `publish_dvr_event` 入队 `media.dvr.completed`；`is_hybrid_upload_mode()` 区分 hybrid |
| `VIDEO/_retired_python_video/app/blueprints/media_hook.py` | `upload-mode=kafka` 且非 hybrid 时 `enqueue_srs_dvr_hook` 后直接 `return`（**不同步** `process_dvr_event`） |
| `VIDEO/_retired_python_video/app/services/alert_hook_service.py` | `use_direct_persist=false` → `_build_minimal_alert_kafka_message` + `get_kafka_producer().send(topic, key=device_id)` |

## 1. 纯 Kafka DVR 真文件成功链

**设备：** `frb26_device`（`seed_fr_b26_fixture.py`）  
**媒体：** `testdata/fr-b26/media/frb26_dvr_*.mp4`（146128B）  
**Profile：** `local,fr-b26-soak` — `upload-mode=kafka`（**非 hybrid**）

**避积压策略：** 专用 topic `media.dvr.completed.frb26`（1 partition）+ consumer group `upload-worker-dvr-frb26`

**证据：** `logs/fr-b26-pure-kafka-dvr-latest.json` — **8/8 steps OK**

| 验证项 | 结果 |
|--------|------|
| Hook 仅入队 | HTTP 200，`data=null`（无同步 `processDvrEvent`） |
| Consumer 订阅 | `DVR Kafka consumer subscribed topic=media.dvr.completed.frb26` |
| Consumer 成功 | Java log `DVR 上传完成` device=frb26_device |
| MinIO | `record-space/frb26_device/2026/08/10/frb26_dvr_*.mp4` size=146128 |
| DB `record_file` | url=`/api/v1/buckets/record-space/objects/download?prefix=...` |

**record_path 形态：**
```
/api/v1/buckets/record-space/objects/download?prefix=frb26_device%2F2026%2F08%2F10%2Ffrb26_dvr_20260810T192818Z.mp4
```

## 2. Alert Kafka produce（use-direct-persist=false）

**配置：** `video.alert.use-direct-persist=false`（soak profile）

**证据：** `logs/fr-b26-alert-kafka-latest.json`

| 验证项 | 结果 |
|--------|------|
| Hook 响应 | `mode=kafka` `status=success` |
| Topic | `iot-alert-notification` |
| Key | `frb26_device` |
| Metadata | partition=48 offset=0（示例 run） |
| iot-sink 消费 | **EX** — produce-only 取证；brief 允许 |

## 3. mini-safe 恢复

Soak 后 Java 重启为 `--spring.profiles.active=local`；`upload-mode=sync`，`use-direct-persist=true`。  
证据：`logs/fr-b26-restore-mini.log`（`DVR Kafka consumer not started: upload-mode=sync`）

## 4. Phase 0

`python tools/video_java/certify.py --phase 0` → **PASS 5/5** — `logs/fr-b26-phase0.log`

## 5. Checklist / GAP

- `PROD_SOAK_CHECKLIST.md` §1.1 + §1.2 更新为 FR-B26 local-only 证据
- `FULL_REPLACEMENT_GAP.md` §9 FR-B26 判定
- `HANDOFF.md` §8 摘要更新

## Remaining

- prod broker 上默认 topic `media.dvr.completed` 64 分区积压卫生 / DLQ 策略
- iot-sink Alert 消费端到端（本地 EX）
- 告警页浏览器实测可播
- 全量 259 路由字段矩阵
- WVP / GB28181 / 远程 node prod 联调

## Concerns

- **专用 topic** 为本地 E2E 诚实绕过默认 consumer group 积压；prod 应验证标准 topic + 正常 group lag
- **Java golden** `vj_p0_alert_hook` 曾遭 soak 污染为 `mode=kafka`；已恢复 mini-safe `direct_persist` 以通过 phase0
- shell `JAVA_HOME` 默认为 JDK 17；soak 脚本强制 `F:\acme\.tools\jdk-21.0.2`
- 禁止对外宣称 COMPLETE / prod 绿
