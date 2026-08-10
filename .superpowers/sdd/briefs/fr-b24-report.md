# FR-B24 Report — 本地 Kafka E2E + `save_time_custom` schema 修复

**Status:** PARTIAL（local E2E ✅ / schema ✅ / mini-safe restored / phase0 PASS）— **禁止 COMPLETE**

**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

---

## Python-first 对照（已读）

| 源 | 要点 |
|----|------|
| `VIDEO/_retired_python_video/app/services/media_kafka_service.py` | topics `media.dvr.completed` / `media.snap.completed`；`_bootstrap_servers()` 在 `Kafka` 主机名时回退 `localhost:9092` |
| `services/media_upload_worker/run_worker.py` | 消费 DVR topic → `process_dvr_event`；失败 retry → DLQ |
| `services/media_upload_worker/run_snap_worker.py` | 消费 snap topic → `process_snap_event` |
| `models.py` `RecordSpace` / `SnapSpace` | 列名 **`save_time_custom`**（非 `is_custom_save_time`）；必填 `space_code` / `bucket_name` |

## 1. Kafka 本地 E2E

**根因（FR-B23）：** Docker `kafka-server` 配置 `KAFKA_ADVERTISED_LISTENERS=INTERNAL://Kafka:9092`；宿主机连 `127.0.0.1:9092` 后元数据指向不可解析的 `Kafka:9092`。

**修复：**

1. 文档 `VIDEO/KAFKA_HOST_CLIENTS.md` — 宿主机 `hosts` 增加 `127.0.0.1 Kafka`
2. 示例 override `VIDEO/docker-compose.kafka-host.override.example.yaml`（新栈可选，不自动改 prod stack）
3. Soak profile `application-fr-b24-soak.yaml`（`upload-mode=kafka` + MinIO）
4. 取证脚本 `tools/video_java/fr_b24_kafka_e2e.py`

**证据：**

- `logs/fr-b24-kafka-e2e-latest.json` — **7/7 steps OK**
- `logs/fr-b24-java-soak.log` — consumer 订阅 + `DVR 文件未就绪` + `抓拍文件未就绪`（缺失文件诚实 retry，无 `is_custom_save_time` SQL 错误）

## 2. Schema 修复 — `is_custom_save_time`

**问题：** `DeviceSpaceRepository` INSERT/SELECT 使用 `is_custom_save_time` + `status`，与 Python/其余 Java DAL（`save_time_custom`）不一致 → `on_dvr` / `processDvrEvent` 路径 500。

**修复：** `DeviceSpaceRepository.java` — 对齐 Python `create_record_space` / `create_snap_space` 列集（`space_code`, `bucket_name`, `save_time_custom`）。

## 3. mini-safe 恢复

Soak 后 Java 已重启为 `--spring.profiles.active=local`（无 `fr-b24-soak`）；`upload-mode=sync`，不经 broker。

## 4. Phase 0

`python tools/video_java/certify.py --phase 0` → **PASS 5/5** — `logs/fr-b24-phase0.log`

## 5. Checklist / GAP

- `PROD_SOAK_CHECKLIST.md` 行 1.2 / 1.3 / 0.4 更新为 FR-B24 local-only 证据
- `FULL_REPLACEMENT_GAP.md` §9 FR-B24 判定 + Kafka soak 行更新
- `HANDOFF.md` §8 摘要更新

## Remaining

- prod broker + `upload-mode=kafka` 联调（非本地 hosts 方案）
- DVR 真文件 → MinIO + DB 播放链（checklist 2.4）
- 全量 259 路由字段矩阵
- WVP / GB28181 / 远程 node prod 联调

## Concerns

- **hosts 方案** 需管理员权限；团队需文档化（已写入 `KAFKA_HOST_CLIENTS.md`）
- 现有 `kafka-server` 容器未改 advertised.listeners（避免破坏 Docker 内 `Kafka:9092` 别名）
- E2E 使用缺失文件路径，验证的是 **消费 + process* + retry**，非完整 MinIO 上传成功路径
