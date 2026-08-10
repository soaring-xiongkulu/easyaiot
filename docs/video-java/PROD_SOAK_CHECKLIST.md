# VIDEO Java — 生产联调 / Soak Checklist

> **用途：** 切流前 ops 逐项验证；**全部 ⬜ = 未做**，禁止在无证据时标 ✅。  
> **不等于 COMPLETE** — 见 [`FULL_REPLACEMENT_GAP.md`](./FULL_REPLACEMENT_GAP.md)。  
> **本地已绿 ≠ prod 已绿：** mini 默认 `direct_persist` / `upload-mode=sync` / `video.minio.enabled=false` 等。

图例：⬜ 未验证 | 🔄 进行中 | ✅ 有证据（附链接/日志） | ⛔ 阻塞

---

## 0. 前置

| # | 项 | 配置 / 门控 | 期望证据 | 状态 |
|---|-----|-------------|----------|------|
| 0.1 | Java `video-server` 健康 | Nacos 注册 + `/actuator/health` UP | 截图或 `curl` JSON `status:UP` | ⬜ |
| 0.2 | 网关路由 | `lb://video-server`（非 Python 遗留名） | `gateway` 路由表导出 | ⬜ |
| 0.3 | 共享 DB | Java 与 WEB 同库只读冒烟 | 告警/设备 list 200 + 有数据 | ⬜ |
| 0.4 | Phase 0 薄烟雾 | `python tools/video_java/certify.py --phase 0` | `gates/PHASE_0_GATE.md` PASS | ✅ local-only evidence — FR-B25 复跑 PASS 5/5（mini-safe 恢复后）；`logs/fr-b25-phase0.log` |

---

## 1. Kafka — 告警 / DVR / Snap

| # | 项 | 配置标志 | 期望证据 | 状态 |
|---|-----|----------|----------|------|
| 1.1 | 告警 Kafka 路径 | `video.alert.use-direct-persist=false` | hook → topic `iot-alert-notification` / `iot-snapshot-alert`；iot-sink 消费 | ⬜ |
| 1.2 | DVR 上传 Kafka | `video.media.upload-mode=kafka` 或 `hybrid` | SRS/ZLM `on_dvr` → `media.dvr.completed` → MinIO + DB | ✅ local-only evidence — FR-B24：`hosts` 加 `127.0.0.1 Kafka`（`VIDEO/KAFKA_HOST_CLIENTS.md`）+ `application-fr-b24-soak.yaml`；`fr_b24_kafka_e2e.py` 发布缺失文件事件 → `DvrUploadService` 日志 `DVR 文件未就绪`（诚实 retry，非 schema 500）；`logs/fr-b24-kafka-e2e-latest.json` + `logs/fr-b24-java-soak.log` |
| 1.3 | Snap 上传 Kafka | `video.media.snap-upload-mode=kafka` 或 `upload-mode` 含 kafka | `media.snap.completed` consumer；retry/DLQ 日志 | ✅ local-only evidence — 同上 FR-B24；`SnapUploadService` 日志 `抓拍文件未就绪`；DLQ topic 已创建；**非 prod 绿** |
| 1.4 | Face/plate matching Kafka | `video.matching.use-direct-process=false` | matching topic produce + worker 推理 + 命中告警 | ⬜ |

**mini 默认：** direct_persist / sync 不经 broker — **本地绿不覆盖上表**。

---

## 2. MinIO

| # | 项 | 配置标志 | 期望证据 | 状态 |
|---|-----|----------|----------|------|
| 2.1 | MinIO 启用 | `video.minio.enabled=true` / `MINIO_ENABLED=1` | bucket 存在；health 无 5xx | ✅ local-only evidence — `fr_b23_soak.py` put_object `fr-b23-soak/fr-b23/probe-*`；凭据 `VIDEO/.env` `MINIO_SECRET_KEY`；`logs/fr-b23-soak-latest.json` |
| 2.2 | Snap 空间同步 | `POST /video/snap/space/sync/minio` | 新设备空间 bucket 前缀创建 | ✅ local-only evidence — soak 窗口 `POST` 200 `code=0`（8 spaces, 0 errors）；`logs/fr-b23-soak-latest.json` |
| 2.3 | Record 空间同步 | `POST /video/record/space/sync/minio` | 同上 | ✅ local-only evidence — 同上 record sync 行 |
| 2.4 | DVR 对象可播放 | hook 后 `record_path` 为 `/api/v1/buckets/...` | 告警页录像可播 | ✅ local-only evidence — FR-B25：`frb25_device` 真 mp4+jpg → MinIO `record-space`/`snap-space` + DB `record_file`/`snap_image`/`playback`；`record_path` 形如 `/api/v1/buckets/record-space/objects/download?prefix=frb25_device%2F...`；`application-fr-b25-soak.yaml`（hybrid DVR + snap kafka）；`fr_b25_minio_upload_e2e.py` **11/11 OK**；`logs/fr-b25-minio-upload-e2e-latest.json`；**非 prod 绿** |
| 2.5 | 空间清理 cron | 磁盘超阈 | janitor / space cleanup 日志 + 对象减少 | ⬜ |

---

## 3. WVP / GB28181 / 目录

| # | 项 | 配置 / 依赖 | 期望证据 | 状态 |
|---|-----|-------------|----------|------|
| 3.1 | WVP 目录同步 | `Gb28181SyncService` + WVP 可达 | `POST` 同步后设备树与 WVP 一致 | ⬜ |
| 3.2 | 国标通道在线 | 真 SIP 注册 | `channel_online` / 流地址可拉 | ⬜ |
| 3.3 | 目录 JSON 同步 | patrol/monitor-tree | WEB 目录与后端一致 | ⬜ |

---

## 4. FlightHub / 真机 / ONVIF

| # | 项 | 配置 / 依赖 | 期望证据 | 状态 |
|---|-----|-------------|----------|------|
| 4.1 | ONVIF 扫描 | 局域网摄像机 | `scan/discovery` 返回真实 MAC/IP | ⬜ |
| 4.2 | NVR 通道枚举 | 海康/大华 CGI | 通道列表与 NVR 一致 | ⬜ |
| 4.3 | FlightHub live/register | `skylink_token` + OpenAPI | live 地址可播；登记回写 | ⬜ |
| 4.4 | audio_talk 真机 | ONVIF back-channel | `start` → RTP 双向；`health` onvif_available=true | ⬜ |
| 4.5 | ffmpeg 抓拍 | 真 RTSP/RTMP | snap task 执行日志 + 图片入库 | ⬜ |

---

## 5. iot-node / Ceph / 远程 node

| # | 项 | 配置标志 | 期望证据 | 状态 |
|---|-----|----------|----------|------|
| 5.1 | 算法远程部署 | `schedule_policy=auto|node` | `IotNodeClient` allocate/deploy；RUNTIME 进程在节点 | ⬜ |
| 5.2 | 推流转发远程 | 同上 + `STREAM_FORWARD_HEALTH_*` | 分片健康迁移日志 | ⬜ |
| 5.3 | Ceph mount gate | `requireCephMount` / `ceph_mount_ready` | 未挂载时诚实失败（非静默） | ⬜ |
| 5.4 | 媒体节点池 | iot-node 媒体 API | `resolveDeviceStreamUrls` 返回池化地址 | ⬜ |
| 5.5 | post_process worker 远程 | `EASYAIOT_ENABLE_POST_PROCESS_WORKER=1` | `run_worker.py` 副本在节点；enqueue 真通 | ⬜ |

---

## 6. 推理运行时（Face / Plate / Pose）

| # | 项 | 配置 / 依赖 | 期望证据 | 状态 |
|---|-----|-------------|----------|------|
| 6.1 | InsightFace + Milvus | 模型文件 + Milvus URI | `/video/face/health` collection_exists=true | ⬜ |
| 6.2 | PaddleOCR plate | 模型下载完成 | `/video/plate/health` exists=true | ⬜ |
| 6.3 | YOLO pose | Python worker 或 ORT | extract/match-test 非 bypass | ⬜ |
| 6.4 | 匹配命中告警链 | Kafka + 库配置 | `face_library_match` / `plate_library_match` 入库 | ⬜ |

---

## 7. Nacos 切换 / 网关冒烟

| # | 项 | 步骤 | 期望证据 | 状态 |
|---|-----|------|----------|------|
| 7.1 | 双跑观察 | Java + Python 均注册（仅预发） | 流量镜像对比无 5xx 尖刺 | ⬜ |
| 7.2 | Nacos 权重切换 | `video-server` 100% Java | `ROLLBACK_LOG.md` 式 dry-run 已升级为真切换记录 | ⬜ |
| 7.3 | 网关全前缀冒烟 | `/admin-api/video/**` P0 页面 | 告警台/设备台/抓拍台手工走通 | ⬜ |
| 7.4 | 回滚演练 | 切回 Python 或降权 | 5 分钟内恢复；无数据损坏 | ⬜ |

---

## 8. 契约回归（prod 环境）

| # | 项 | 命令 / artifact | 期望 | 状态 |
|---|-----|-----------------|------|------|
| 8.1 | 薄探针 | `contract_regression.py` @ prod URL | 265 pass / 0 fail | ⬜ |
| 8.2 | 深字段抽样 | `field_contract.py --deep` @ prod | 25 端点 / 0 fail | ⬜ |
| 8.3 | GET 信封矩阵 | `field_contract.py --matrix` @ prod | 95 JSON GET 信封 0 fail | ⬜ |
| 8.4 | 全量字段矩阵 | **未实现** | 259 路由字段键 — open backlog | ⬜ |

---

## 9. 签署

| 角色 | 姓名 | 日期 | 备注 |
|------|------|------|------|
| 开发 | | 2026-08-11 | FR-B23 本地 MinIO/Kafka soak 取证 ≠ prod 绿 |
| 运维 | | | |
| 产品 | | | 永久豁免项须书面确认 |

**维护：** 每项 ✅ 必须附 artifact（日志路径、ticket、截图 URL）。禁止批量勾选。
