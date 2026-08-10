# FR-B23 Report — 本地 Kafka + MinIO soak 取证（Python-first）

**Date:** 2026-08-11  
**Branch:** `feat/video-java` @ `F:/acme/.worktrees/video-java`  
**Status:** DONE (≠ COMPLETE)

## Summary

- Python-first 对照阅读：`media_kafka_service.py`、`run_worker.py`、`dvr_upload_service.py`、`snap_upload_service.py`；Java `DvrUploadKafkaConsumerRunner`、`SnapUploadKafkaConsumerRunner`、`VideoMinioService`、`MediaHookService`。
- 新增 soak 脚手架：`tools/video_java/fr_b23_soak.py`、`seed_fr_b23_fixture.py`、`application-fr-b23-soak.yaml`。
- **MinIO 本地证据：** put_object + sync API 200（凭据 `VIDEO/.env` `MINIO_SECRET_KEY`）。
- **Kafka 本地证据（部分）：** soak 窗口 consumer 线程启动 + hook 路径；**阻塞：** broker `advertised.listeners=Kafka:9092` 宿主机不可解析。
- **深字段：** FR-B22 的 2 skip 已清除 → **132 pass / 0 fail / 0 skip**（`logs/fr-b23-field-contract-latest.json`）。
- **phase0：** `certify --phase 0` PASS 5/5（`logs/fr-b23-phase0.log`）；已恢复 mini-safe `local` profile（`upload-mode=sync`，minio off）。

## Soak window vs restored defaults

| 项 | Soak 窗口 | 恢复后（mini-safe） |
|----|-----------|---------------------|
| Profile | `local` + CLI/`application-fr-b23-soak.yaml` | `local` only |
| `video.minio.enabled` | `true` + `MINIO_ENABLED=1` | `false`（默认） |
| `video.media.upload-mode` | `kafka` | `sync` |
| Consumer | DVR+Snap threads started | not started（日志确认） |

## Artifacts

| Artifact | Path |
|----------|------|
| Soak JSON/MD | `logs/fr-b23-soak-latest.{json,md}` |
| Java soak log | `logs/fr-b23-java-soak.log` |
| Deep field contract | `logs/fr-b23-field-contract-latest.json` |
| Phase 0 | `logs/fr-b23-phase0.log` |
| Seed fixture | `logs/fr-b23-seed-fixture.json` |

## PROD_SOAK_CHECKLIST rows touched (local-only)

- 0.4 Phase 0
- 1.2 DVR Kafka（部分 — broker 主机名）
- 1.3 Snap Kafka（部分）
- 2.1 MinIO 启用
- 2.2 Snap sync/minio
- 2.3 Record sync/minio

## Java fixes (field contract)

- `SnapTaskRepository`: `pusher_name` via `pusher.pusher_name` join
- `RecordFileRepository`: `size` / `last_modified` / `etag` aligned with Python `RecordFile.to_list_item`

## Phase 0

```
python tools/video_java/certify.py --phase 0
→ PASS (vj_p0_health, task_start_stop, heartbeat, alert_hook, restart)
```

## Remaining (honest)

1. **Prod soak** — checklist 大部仍 ⬜；本地 Kafka 需修 broker `advertised.listeners` 或 hosts 映射
2. **Full 259-route field-key matrix** — not attempted
3. **DVR 对象可播放 / hook→MinIO+DB 端到端** — 未在 soak 窗口验证
4. **COMPLETE forbidden**

## Concerns

- Docker Kafka 对宿主机客户端广播 `Kafka:9092` — Python `kafka-python` 与 Java consumer 均报错（诚实记录在 soak JSON）。
- Soak profile YAML 在 fat jar 内未重打包时需 CLI override（本次用 `--spring.config.additional-location` + env）。
- `on_dvr` hook 在部分 DB 行上曾触发 `record_space.is_custom_save_time` 列缺失（与 soak 设备/空间有关，非本包主路径）。
