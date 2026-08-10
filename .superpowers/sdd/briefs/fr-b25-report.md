# FR-B25 Report — 真文件 DVR/Snap → MinIO+DB 成功链（Python-first）

**Status:** PARTIAL（local E2E ✅ / schema ✅ / mini-safe restored / phase0 PASS）— **禁止 COMPLETE**

**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

---

## Python-first 对照（已读）

| 源 | 要点 |
|----|------|
| `VIDEO/_retired_python_video/app/services/dvr_upload_service.py` | `wait_dvr_file_stable` → MinIO `fput_object` → `record_file`/`Playback` upsert → `record_path`=`/api/v1/buckets/{bucket}/objects/download?prefix=...` |
| `VIDEO/_retired_python_video/app/services/snap_upload_service.py` | `_wait_snap_file_stable` → MinIO put → `upsert_snap_image`；`SnapImage` 仅 `created_at`（无 `updated_at`） |
| `VIDEO/_retired_python_video/app/services/media_kafka_service.py` | topics `media.dvr.completed` / `media.snap.completed`；`_bootstrap_servers()` Kafka 主机名回退 |

## 1. 真文件 MinIO+DB E2E

**设备：** `frb25_device`（`seed_fr_b25_fixture.py`）  
**媒体：** `testdata/fr-b25/media/frb25_dvr_*.mp4`（146128B）+ `frb25_snap_*.jpg`（337B 最小 JPEG）  
**Profile：** `local,fr-b25-soak` — hybrid DVR（hook 同步 `processDvrEvent` + Kafka 入队）+ snap `kafka` consumer

**证据：** `logs/fr-b25-minio-upload-e2e-latest.json` — **11/11 steps OK**

| 验证项 | 结果 |
|--------|------|
| MinIO DVR | `record-space/frb25_device/2026/08/10/frb25_dvr_*.mp4` size=146128 |
| MinIO snap | `snap-space/frb25_device/frb25_snap_*.jpg` size=337 |
| DB `record_file` | url=`/api/v1/buckets/record-space/objects/download?prefix=...` |
| DB `snap_image` | url=`/api/v1/buckets/snap-space/objects/download?prefix=...` |
| DB `playback` | `file_path` 同上 record_path 形态 |
| Java log | `DVR 上传完成` + `抓拍上传完成` device=frb25_device |

**record_path 可播放形态示例：**
```
/api/v1/buckets/record-space/objects/download?prefix=frb25_device%2F2026%2F08%2F10%2Ffrb25_dvr_20260810T191456Z.mp4
```

## 2. Schema 修复 — `snap_image.updated_at`

**问题：** `SnapImageRepository.upsert` 引用 `updated_at`，Python `SnapImage` / DB 无此列 → snap 元数据写入 500。

**修复：** 移除 `updated_at` 列引用，对齐 Python 模型。

## 3. mini-safe 恢复

Soak 后 Java 重启为 `--spring.profiles.active=local`；`upload-mode=sync`，不经 broker。  
证据：`logs/fr-b25-restore-mini.log`（`DVR Kafka consumer not started: upload-mode=sync`）

## 4. Phase 0

`python tools/video_java/certify.py --phase 0` → **PASS 5/5** — `logs/fr-b25-phase0.log`

## 5. Checklist / GAP

- `PROD_SOAK_CHECKLIST.md` §2.4 + §0.4 更新为 FR-B25 local-only 证据
- `FULL_REPLACEMENT_GAP.md` §9 FR-B25 判定
- `HANDOFF.md` §8 摘要更新

## Remaining

- prod MinIO + Kafka `upload-mode=kafka` 全链路（无 hybrid hook 捷径）
- DVR Kafka consumer 积压时纯 kafka 路径延迟（需 prod broker 卫生或 DLQ 策略）
- 告警页浏览器实测可播（本地仅 DB/URL 形态验证）
- 全量 259 路由字段矩阵
- WVP / GB28181 / 远程 node prod 联调

## Concerns

- **hybrid 模式** 为本地 E2E 诚实绕过 DVR consumer 64 分区积压；prod 应验证纯 kafka 路径
- **date_dir** 取自文件 mtime（Asia/Shanghai），与 SRS 路径解析一致；跨日边界需回归
- shell `JAVA_HOME` 默认为 JDK 17；soak 脚本强制 `F:\acme\.tools\jdk-21.0.2`（jar class v65）
- 禁止对外宣称 COMPLETE / prod 绿
