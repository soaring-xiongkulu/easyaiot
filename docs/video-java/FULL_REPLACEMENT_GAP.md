# VIDEO：Python → Java **完整功能替换**缺口清单

> **本文件 = 唯一进度表与完成定义**（Phase FR）。方案见 [`PLAN_FULL_REPLACEMENT.md`](./PLAN_FULL_REPLACEMENT.md)。  
> **审计方式：** 人工对照代码 + 路由清单 diff（非 CERTIFY 自述）  
> **Oracle：** `VIDEO/_retired_python_video/`（原 Flask VIDEO；只读对照）  
> **Candidate：** `DEVICE/iot-video/`（`feat/video-java`）  
> **日期：** 2026-08-10  
> **目标定义：** Java 在 **HTTP 契约 + 关键后台守护/调度 + 下游集成** 上覆盖 Python VIDEO；WEB/网关可无功能豁免使用 Java 后，再退役 Python。  
> **勾选约定：** 某 API/后台项落地并有短契约证据后，将该行 `❌` 改为 `✅`，并更新本节「Py vs Java」计数。未勾完前禁止称 COMPLETE / 整域 migrated。

---

## 0. 总览（先看这个）

| 维度 | Python（oracle） | Java（candidate） | 完整替换进度（粗估） |
|------|------------------|-------------------|----------------------|
| Blueprint / 域 | **14** | **14** 域均有 Controller；`route_inventory` 14 前缀 **diff=0** | **HTTP 路由面 ~100%**（ inventoried 前缀） |
| HTTP `@route` / `@*Mapping` | **≈259**（14 前缀合计） | **≈259** | **diff 0**（`FR-W4` 全量核对） |
| `app/services` 量级 | **67** 个 py | **40+** Java service + 4 process + 8 scheduler | 编排面已扩；**行为桩仍多** |
| 独立 worker 目录 | `services/` 下 frame/sorter/pusher/media_*/post_process/stream_forward 等 | **无对等多进程 worker 包**（推流/RUNTIME 用 JVM 内 Supervisor） | 模型不同，能力未对齐 |
| 启动后台任务 | auto_start 算法/推流/观看、空间清理、janitor、磁盘守护、健康监控、抓拍调度… | FR-W1-BG + FR-W3-OPS + **FR-B3** + **FR-B6** snap cron + ffmpeg/ONVIF 抓拍 | 部分 |
| 门禁自称 | — | Phase 0 薄烟雾绿 + EVID 历史 | **HTTP 齐 ≠ 行为齐** |

**结论一句话（FR-W4）：**  
**14 个 inventoried 前缀 HTTP 路由已与 Python diff=0**；Java VIDEO **HTTP 契约面已齐**。  
距离 **完整替换** 仍缺：**MinIO/ONVIF/YOLO/InsightFace/Milvus 真行为**、远程 node、snap 任务调度、部分集群健康迁移等。  
**禁止称 COMPLETE**——行为桩与后台缺口见 §2/§3/§4。

---

## 1. 域级总表（完整替换视角）

图例：

- **已有切片**：有部分 API，且有 certify case  
- **严重不足**：仅 list/get/hook 等，WEB 主流程会缺大量接口  
- **缺失**：无 Java Controller / 无对等实现  
- **豁免记账**：已有 EX-id，产品若接受「上线可缺」可不做；**完整替换则必须做**

| # | 域 | Python 前缀 | Py 路由数 | Java 现状 | Java 已有映射（摘要） | 完整替换判定 | 关联 EX / 备注 |
|---|----|-------------|----------:|-----------|----------------------|--------------|----------------|
| 1 | algorithm_task | `/video/algorithm` | 21 | 管理面 + lifecycle | list/get/CRUD/start/stop/restart/services/status/heartbeat/logs/streams/post-process | **本地切片** | route_inventory `/video/algorithm` Py=21 Java=21 diff=0；**FR-B4 ✅** 远程 node 客户端（prod 需 iot-node + Agent 联调） |
| 2 | alert | `/video/alert` | 10 | 管理面 + hook | page/count/statistics/correlation/image/record/record/query/clear/clear/all + `POST /hook` | **本地切片** | route_inventory `/video/alert` Py=10 Java=10 diff=0；**EX-ALERT-ADMIN-API resolved**；**EX-KAFKA-HOOK resolved**（`use-direct-persist=false` → Kafka produce + fallback） |
| 3 | camera | `/video/camera` | **59** | 全量路由 | list/CRUD/stream/目录/NVR/… | **路由切片完成** | `route_inventory` Py=59 Java=59 diff=0；**FR-W2-CAM**；**FR-B6 ✅** ONVIF/扫描/NVR/ffmpeg 抓拍行为 |
| 4 | stream_forward | `/video/stream-forward` | 13 | 全量路由 | list/get/CRUD/start/stop/restart/status/heartbeat/logs/streams/ensure-task | **路由切片完成** | `route_inventory` Py=13 Java=13 diff=0；**FR-W2-SF**；**FR-B4 ✅** 远程 node 客户端（分片/SRS 健康迁移仍待集群联调） |
| 5 | face | `/video/face` | 35 | 全量路由 | health/model/libraries/persons/entries/auto-enroll/normalize/match/recognize/matching/* | **路由切片完成** | `route_inventory` Py=35 Java=35 diff=0；**FR-W2-MATCH**；InsightFace/Milvus 推理桩 |
| 6 | plate | `/video/plate` | 26 | 全量路由 | health/model/libraries/entries/auto-enroll/normalize/match/recognize/matching/* | **路由切片完成** | `route_inventory` Py=26 Java=26 diff=0；**FR-W2-MATCH**；PaddleOCR 推理桩 |
| 7 | snap | `/video/snap` | 38 | 全量路由 | space/task/region/service/images/storage | **路由切片完成** | `route_inventory` Py=38 Java=38 diff=0；**FR-W2-MEDIA**；MinIO/调度器待 SDK |
| 8 | record | `/video/record` | 16 | 全量路由 | space/videos/dates/day/resolve-alert | **路由切片完成** | `route_inventory` Py=16 Java=16 diff=0；**FR-W2-MEDIA** |
| 9 | playback | `/video/playback` | 7 | 全量路由 | list/CRUD/thumbnail/statistics | **路由切片完成** | `route_inventory` Py=7 Java=7 diff=0；**FR-W2-MEDIA** |
| 10 | media_hook | `/video/media` | 全量路由 | hook/srs + hook/zlm + snap/completed | **路由切片完成** | `route_inventory` Py=6 Java=6 diff=0；**FR-W2-HOOKS**；MinIO DVR 上传待 SDK |
| 11 | device_detection_region | `/video/device-detection` | 6 | 全量路由 | regions CRUD、cover-image、snapshot | **路由切片完成** | `route_inventory` Py=6 Java=6 diff=0；**FR-W2-MATCH**；抓拍/MinIO 行为桩 |
| 12 | patrol | `/video/patrol` | 9 | 全量路由 | session CRUD/start/stop/stats/events/SSE/heartbeat/directory devices | **路由切片完成** | `route_inventory` Py=9 Java=9 diff=0；**FR-W2-PATROL**；守护进程/SSE 行为 mini 桩 |
| 13 | audio_talk | `/video/camera/audio/talk` | 5 | 全量路由 | capabilities/start/stop/send/health | **路由切片完成** | `route_inventory` Py=5 Java=5 diff=0；**FR-W3-TALK**；ONVIF back-channel 真机待验 |
| 14 | scenario_pose | `/video/scenario-pose` | 14 | 全量路由 | libraries/entries/extract/match-test/templates | **路由切片完成** | `route_inventory` Py=14 Java=14 diff=0；**FR-W3-POSE**；姿态推理桩 |
| — | heartbeat（附属） | `/video/algorithm/heartbeat` | (含在 algorithm) | 切片 | realtime | **不足** | `heartbeat/patrol` 未见 Java 映射 |
| — | ping/actuator | `/video/ping`, `/actuator/*` | — | 有 | ping + Boot actuator | 基本可 | — |

**路由合计（FR-W4 `route_inventory` 14 前缀）：Python ≈259 vs Java ≈259 → diff 0。**  
注：`--prefix /video/camera` 扫描时 Java 计 **64**（含 5 条 `/audio/talk` 子路径，与 `/video/camera/audio/talk` 前缀重复计数，非真实缺口）。

---

## 2. 分域缺口明细（完整替换必须补的 API）

### 2.1 `algorithm_task` — 已有 vs 仍缺

| 状态 | 方法 | 路径 |
|------|------|------|
| ✅ | GET | `/video/algorithm/task/list` |
| ✅ | GET | `/video/algorithm/task/{id}` |
| ✅ | POST | `/video/algorithm/task`（创建） |
| ✅ | PUT/DELETE | `/video/algorithm/task/{id}` |
| ✅ | GET | `/video/algorithm/task/{id}/services/status` |
| ✅ | POST | `/video/algorithm/task/{id}/start\|stop\|restart` |
| ✅ | POST | `/video/algorithm/heartbeat/realtime` |
| ✅ | POST | `/video/algorithm/heartbeat/patrol` |
| ✅ | GET | `.../extractor\|sorter\|pusher\|realtime/logs` |
| ✅ | GET | `.../streams` |
| ✅ | GET/POST/PUT | post-process `status` / `init` / `toggle` / `ide-url` / `results` |
| ✅ 行为 | — | `schedule_policy=auto|node` 远程 iot-node 部署（**FR-B4 ✅** `IotNodeClient`；mini 默认本机回退） |
| ✅ 路由差 | `/video/algorithm`：**Py 21 / Java 21 / diff 0**（`route_inventory.py --prefix /video/algorithm`） |

### 2.2 `alert` — 管理面 + hook（FR-W1-ALERT）

| 状态 | 路径 |
|------|------|
| ✅ | `POST /video/alert/hook`（mini：`direct_persist`） |
| ✅ | `GET /page`, `/count`, `/statistics`, `/correlation`, `/image`, `/record`, `/record/query` |
| ✅ | `DELETE /clear`, `/clear/all` |
| ✅ 路由差 | `/video/alert`：**Py 10 / Java 10 / diff 0**（`tools/video_java/route_inventory.py --prefix /video/alert`） |
| ✅ 行为 | Kafka 告警路径（`use-direct-persist=false` → produce `iot-alert-notification` / `iot-snapshot-alert`；失败 fallback direct_persist；**resolved by FR-W1-KAFKA**） |

### 2.3 `camera` — FR-W2-CAM（路由面 diff=0）

| 状态 | 说明 |
|------|------|
| ✅ 路由差 | `/video/camera`：**Py 59 / Java 59 / diff 0**（`route_inventory.py --prefix /video/camera`） |
| ✅ | `/list`，`/device/{id}`，stream start/stop/status |
| ✅ | 流票据、位置/轨迹、注册、CRUD、batch-delete |
| ✅ | PTZ/ONVIF 预设/RTSP·ONVIF 任务、snapshot、NVR、scan/discovery/refresh |
| ✅ | SRS 回调、目录树、conflicts、inference-input、ensure-spaces、FlightHub 配置/登记 |
| ❌ 行为 | ONVIF 真连接、NVR 通道枚举、hiktools 扫描、抓拍抽帧、司空 live、GB28181 全量同步 — **FR-B6 ✅** ONVIF SOAP/WS-Discovery、ISAPI 扫描/NVR 枚举、ffmpeg 抓拍已落地；无设备时错误结构与 Python 对齐；**FR-B11 ✅** GB28181/WVP 目录同步客户端 + 默认分组 patrol/monitor-tree 接线；**FR-B12 ✅** 目录 JSON 同步 + FlightHub OpenAPI live/register + 大华 NVR CGI 通道枚举；**FR-B13 ✅** 媒体节点池客户端 + AI/流地址接线 + Ceph allocate gate（prod 媒体池/iot-node 联调仍待）；**FR-B14 ✅** list/get/monitor-tree/inference-input 只读 `resolveDeviceStreamUrls` 接线（媒体池绑定 + 推流分片 host/tags 回退） |

### 2.4 `stream_forward` — FR-W2-SF（路由面 diff=0）

| 状态 | 方法 | 路径 |
|------|------|------|
| ✅ | GET | `/video/stream-forward/task/list` |
| ✅ | GET | `/video/stream-forward/task/{id}` |
| ✅ | POST | `/video/stream-forward/task` |
| ✅ | PUT/DELETE | `/video/stream-forward/task/{id}` |
| ✅ | POST | `/video/stream-forward/task/{id}/start\|stop\|restart` |
| ✅ | GET | `/video/stream-forward/task/{id}/status` |
| ✅ | POST | `/video/stream-forward/heartbeat` |
| ✅ | GET | `/video/stream-forward/task/{id}/logs` |
| ✅ | GET | `/video/stream-forward/task/{id}/streams` |
| ✅ | POST | `/video/stream-forward/device/{device_id}/ensure-task` |
| ✅ 行为 | — | `schedule_policy=auto|node` 远程 iot-node 部署（**FR-B4 ✅** `IotNodeClient`；mini 默认本机回退） |
| ✅ 路由差 | `/video/stream-forward`：**Py 13 / Java 13 / diff 0**（`route_inventory.py --prefix /video/stream-forward`） |

### 2.5 `face` / `plate` — FR-W2-MATCH（路由面 diff=0）

| 域 | 路由差 | 状态 | 说明 |
|----|--------|------|------|
| face | **Py 35 / Java 35 / diff 0** | ✅ 路由 | health/model；libraries/entries/persons CRUD；auto-enroll；normalize；match；recognize；matching/records；legacy `/library` |
| plate | **Py 26 / Java 26 / diff 0** | ✅ 路由 | health/model；libraries/entries CRUD；auto-enroll；normalize；match；recognize；matching/records |
| ✅ 行为 | — | **FR-B9 ✅** Python worker 桥接（face InsightFace+Milvus / plate PaddleOCR / pose YOLO）；匹配命中 → `face_library_match` / `plate_library_match` 告警；无引擎时诚实 bypass/错误 |

依赖层：Python 还有 InsightFace/ONNX、Milvus、PaddleOCR、Kafka matching consumer —— Java 现多为 **mini mock / stub**，完整替换需 ORT/SDK 或旁路策略产品拍板后落地。

### 2.6 `snap` / `record` / `playback` — FR-W2-MEDIA（路由面 diff=0）

| 域 | 路由差 | 状态 | 说明 |
|----|--------|------|------|
| snap | **Py 38 / Java 38 / diff 0** | ✅ 路由 | space CRUD/策略/sync；task CRUD/start/stop/restart/logs；region/service；images；device storage |
| record | **Py 16 / Java 16 / diff 0** | ✅ 路由 | space CRUD/策略/sync；videos dates/day/list/object/delete/sync/cleanup；resolve-alert |
| playback | **Py 7 / Java 7 / diff 0** | ✅ 路由 | list/get/create/update/delete；thumbnail；statistics |
| ❌ 行为 | — | MinIO 真同步/清理、真 play URL 解析 — **FR-B2 ✅** MinIO 代码路径；**FR-B3 ✅** snap cron 调度（抓拍执行为桩）；**FR-B30 ✅** `SnapStorageService` 存储用量对齐 Python `get_bucket_size`（enabled 真统计 / disabled 诚实 0） |

### 2.7 `media_hook` / `device_detection_region`

| 域 | 路由差 | 状态 | 说明 |
|----|--------|------|------|
| media_hook | **Py 6 / Java 6 / diff 0** | ✅ 路由 | SRS `on_dvr/on_publish/on_unpublish`；ZLM `on_record_mp4/ts`；`snap/completed` |
| ❌ 行为 | — | DVR MinIO 上传、Playback/RecordFile 写入、抓拍 Kafka→MinIO 全链路 — **FR-B2 ✅** 代码路径已实现；**FR-B15 ✅** `media.dvr.completed` Kafka consumer + retry/DLQ（`upload-mode=kafka\|hybrid` 门控；默认 sync 不经 broker）；**FR-B16 ✅** `media.snap.completed` Kafka consumer + retry/DLQ（`snap-upload-mode` / `upload-mode` 门控）；mini 默认本地路径 |
| regions | **Py 6 / Java 6 / diff 0** | ✅ 路由 | GET/POST regions；PUT/DELETE region；cover-image；snapshot |
| ❌ 行为 | — | 抓拍 FFmpeg/GB28181、MinIO 上传 — mini 形态错误结构对齐 |

### 2.8 整域 HTTP 路由（FR-W4 收口）

| 域 | 路由差 | 状态 | 说明 |
|----|--------|------|------|
| `audio_talk` | **Py 5 / Java 5 / diff 0** | ✅ 路由 | **FR-W3-TALK** + **FR-B10 ✅** ONVIF RTSP DESCRIBE/SETUP/PLAY + G.711 RTP |
| `scenario_pose` | **Py 14 / Java 14 / diff 0** | ✅ 路由 | **FR-W3-POSE** + **FR-B9 ✅** extract；**FR-B10 ✅** match-test 相似度评分 |
| `patrol` | **Py 9 / Java 9 / diff 0** | ✅ 路由 | **FR-W2-PATROL** + **FR-B10 ✅** 守护进程 env 对齐 + SSE hub |

**14 inventoried 前缀无 HTTP 路由缺口**；剩余为 **行为 / 后台 / 集成**（§3–§4）。

---

## 3. 后台守护 / 调度 / Worker（非 HTTP 但属于「全部功能」）

Python `run.py` 启动时拉起的能力 vs Java：

| Python 能力 | Java 现状 | 完整替换 |
|-------------|-----------|----------|
| `auto_start_streaming`（观看 ffmpeg） | ✅ `ViewForwardAutoResume*`（`enable_forward` + 离线/rtmp 跳过） | FR-W1-BG 已对齐本地语义 |
| `auto_start_all_tasks`（算法） | ✅ `AlgorithmTaskAutoStart*`（enabled + local + 模型/设备校验） | FR-W1-BG 已补 |
| `stream_forward` auto_start | ✅ `StreamForwardAutoStart*`（enabled + local） | FR-W1-BG 已补；远程分片 **FR-B8 ✅** 健康迁移 |
| 抓拍/录像空间定时清理（30min） | ✅ `SpaceCleanupScheduler` + `SnapSpaceCleanupService` / `RecordSpaceCleanupService`（DB mini 清理 + 启动即清） | FR-W3-OPS 已补 |
| playback disk guard | ✅ `PlaybackDiskGuardScheduler` + `PlaybackDiskGuardService`（10min + 启动首次） | FR-W3-OPS 已补 |
| media janitor | ✅ `MediaJanitorScheduler` + `MediaJanitorService`（60s 孤儿重入队 + 磁盘紧急） | FR-W3-OPS 已补 |
| stream_forward 集群健康迁移 | ✅ `StreamForwardHealth*`（`STREAM_FORWARD_HEALTH_*` 仅远程；local no-op） | **FR-B8 ✅** |
| algorithm_task 健康监控（60s） | ✅ `AlgorithmTaskHealthRecovery*`（启动即恢复 + 定时；local 以 supervisor 为准） | FR-W1-BG 已对齐 P0 |
| snap_task 调度器 `init_all_tasks` | ✅ `SnapTaskScheduler` + `SnapTaskSchedulerService`（启动加载 enabled 任务 + cron；create/update/start/stop 联动） | FR-B3 + **FR-B6 ✅** 抓拍执行为 ffmpeg/ONVIF HTTP 真路径 |
| `VIDEO/services/*` 独立进程（upload/janitor/post_process_worker…） | JVM 内或 stub | 完整替换需逐项定：迁入 Java / 保留外部进程 / 废弃 |

### 3.1 `VIDEO/services/*` 处置表（FR-B15）

对照 Python `run.py` / launcher 与 Java `feat/video-java` 现状（证据见各 FR 报告与代码路径）：

| Worker 目录 | Python 角色 | Java 处置 | 证据 |
|-------------|-------------|-----------|------|
| `media_upload_worker` | 独立进程消费 `media.dvr.completed` → `process_dvr_event`；retry≤12 → DLQ | **迁入 Java** — **FR-B15 ✅** `DvrUploadKafkaConsumerRunner` 调用 `DvrUploadService.processDvrEvent`；`upload-mode=kafka\|hybrid` 门控；默认 `sync` 不启 broker | `run_worker.py` L21–79；`DvrUploadKafkaConsumerRunner.java` |
| `media_upload_worker` (snap) | 独立进程消费 `media.snap.completed` → `process_snap_event`；retry≤8 → DLQ | **迁入 Java** — **FR-B16 ✅** `SnapUploadKafkaConsumerRunner` 调用 `SnapUploadService.processSnapEvent`；`snap-upload-mode` / `upload-mode` 门控；默认 `sync` 不启 broker | `run_snap_worker.py` L19–69；`SnapUploadKafkaConsumerRunner.java` |
| `media_janitor` | 独立进程或 `run.py` APScheduler 周期 `run_janitor_cycle` | **迁入 Java** — **FR-W3-OPS ✅** `MediaJanitorScheduler` + `MediaJanitorService`（JVM 内 60s） | `run_janitor.py`；`MediaJanitorService.java` |
| `post_process_worker` | HTTP worker 执行用户脚本；由 `post_process_launcher_service` 远程/本机拉起 | **保留外部进程** — **FR-B14 ✅** `PostProcessLauncherService` 仍部署 `run_worker.py`（`EASYAIOT_ENABLE_POST_PROCESS_WORKER=1`） | `post_process_worker/run_worker.py` L1–4；`PostProcessLauncherService.java` |
| `frame_extractor_service` | 算法任务抽帧子进程（`algorithm_task_launcher_service` → `run_deploy.py`） | **已由 FR-* 覆盖（模型变更）** — Java 用 `AlgorithmRuntimeSupervisor` + RUNTIME 二进制替代 Python 三件套子进程 | `algorithm_task_launcher_service.py`；`AlgorithmRuntimeSupervisor.java` |
| `pusher_service` | 算法推送子进程 | **已由 FR-* 覆盖（模型变更）** — 同上 RUNTIME 内聚 | 同上 |
| `sorter_service` | 算法排序子进程 | **已由 FR-* 覆盖（模型变更）** — 同上 RUNTIME 内聚 | 同上 |
| `stream_forward_service` | 推流转发子进程（`stream_forward_launcher_service`） | **迁入 Java** — **FR-W1-BG / FR-B4 / FR-B8 ✅** `StreamForwardSupervisor` + 远程 `IotNodeClient` deploy `run_deploy.py` 可选 | `stream_forward_service/run_deploy.py`；`StreamForwardSupervisor.java` |

**说明：** `VIDEO/services/` 顶层目录为部署模板；oracle 源码在 `VIDEO/_retired_python_video/services/`。snap Kafka 消费 **FR-B16 ✅** `SnapUploadKafkaConsumerRunner`；DVR 路径 **FR-B15 ✅**。


## 4. 下游集成与行为缺口

| 项 | Python | Java | 完整替换要求 |
|----|--------|------|--------------|
| Alert → Kafka | 可走 Kafka | `use-direct-persist=false` → Kafka produce（minimal 驼峰消息，deviceId key）；失败 fallback direct_persist；local/mini 默认仍 direct | **resolved by FR-W1-KAFKA**（prod 需 broker + iot-sink 联调） |
| Post-process → iot-sink | 真 enqueue | `use-stub-enqueue: true`（local） | **resolved by FR-B1**（`use-stub-enqueue=false` → HTTP POST iot-sink；不可达时 `enqueue_ok=false` + warn 日志；local/mini 默认仍 stub） |
| Post-process worker 集群 | `post_process_launcher_service` 远程/本机副本 | **FR-B14 ✅** `PostProcessLauncherService` allocate/deploy/stop via `IotNodeClient`；`EASYAIOT_ENABLE_POST_PROCESS_WORKER=1` 门控；远程失败 `VideoBusinessException`（非静默） | prod 需 iot-node + `run_worker.py` 联调 |
| Face/Plate matching | Kafka + 模型 | **FR-B5 ✅** Kafka produce；**FR-B9 ✅** Python worker 推理 + 匹配命中告警链 | prod 需模型/Milvus + `use-direct-process=false` |
| 远程 node / RUNTIME 分发 | node_client | **FR-B4 ✅** `IotNodeClient` allocate/deploy/stop；**FR-B13 ✅** `requireCephMount` / `ceph_mount_ready` gate | prod 集群需 iot-node + Agent + SRS 联调 |
| ONVIF / NVR / GB28181 / FlightHub | camera 大面 | **FR-B6 ✅** ONVIF SOAP + WS-Discovery + ISAPI 扫描/NVR 枚举 + ffmpeg 抓拍；**FR-B11 ✅** `Gb28181SyncService` WVP 拉取/前端 payload 同步 + 默认目录 patrol 接线；**FR-B12 ✅** 目录 JSON 同步 + FlightHub OpenAPI live/register + 大华 NVR CGI 通道枚举 | prod 真机/NVR/WVP/司空联调仍待 |
| MinIO 空间同步/清理 | snap/record 多接口 | **✅ FR-B2** `VideoMinioService` + `SpaceFileMetadataService`；`video.minio.enabled` / `MINIO_ENABLED` 开关；DVR/snap 上传真路径；**FR-B30 ✅** `GET /video/snap/device/{id}/storage` 用量统计对齐 Python `get_device_storage_info` | mini 默认 `enabled=false`（DB/本地路径）；prod 需 MinIO 联调 |
| 鉴权（流票据、网关 token） | 有 | **FR-W1-AUTH ✅** mini gateway + `system-server` token check；**FR-B7 ✅** 流票据签发与 Python 对齐（JWT 自校验 + tenant-id；未登录 401） | 生产全量路由 + 网关切流 ops 演练 |
| 对外 JSON | `{code,msg,data}` | `VideoApiResponse` 已对齐方向 | 全接口字段级与 WEB 对表 |

---

## 5. 运维 / 切流 / 回滚（完整替换收尾）

| 项 | 现状 | 完整替换还要 |
|----|------|--------------|
| 网关 `lb://video-server` | 已改指向 Java 名 | 全量 API 可用前，**生产流量不应认为已安全切完** |
| Python 热路径归档 | `_retired_python_video/` | 保留直到 Java 全量绿 |
| 回滚演练 | **FR-B7 ✅** 全量 `app/`+`services/`+`run.py`+`models.py` safe_fsops 恢复→验证→再归档（见 `ROLLBACK_LOG.md` FR-B7）；**FR-B11 ✅** Nacos `video-server` 进程切换 dry-run 证据（见 `ROLLBACK_LOG.md` FR-B11） | 生产真切换 + 网关冒烟仍待 ops |
| Nacos 双跑/切换 | 文档有漂移（仍见 video-server-java 旧述） | **FR-B11 ✅** dry-run 记录；生产真切换仍待 ops |
| 证据门禁 | EVID 已抬真 RUNTIME/alert success 等 | 完整替换应另建 **全量契约回归**（按本文件域表），不能只靠现有 18 个 vj_* case；**FR-B16 ✅** `tools/video_java/contract_regression.py` 14 前缀 inventory + 可选薄烟雾；**FR-B17 ✅** 265 路由 method-aware 薄探针执行；**FR-B18 ✅** 6 条 fail 收口 → **265 pass / 0 fail**（见 `logs/fr-b17-contract-latest.json`；mapped ≠ COMPLETE）；**FR-B19 ✅** P0/P1 字段级抽样（`tools/video_java/field_contract.py`；12 端点 / 67 assert；artifact `logs/fr-b19-field-contract-latest.json`；≠ 全量 259 字段矩阵）；**FR-B20 ✅** 14 前缀字段抽样扩面 + 空列表 item-key 实测（16 端点 / 88 assert / 0 skip；artifact `logs/fr-b20-field-contract-latest.json`；仍 ≠ 全量矩阵）；**FR-B21 ✅** GET 信封自动矩阵（`field_contract.py --matrix`；98 GET / 95 JSON 信封探针 + 3 非 JSON skip；265 路由 inventoried / 190 pass / 0 fail；artifact `logs/fr-b21-field-matrix-latest.json`；信封 ≠ 字段键矩阵）；**FR-B22 ✅** 深字段扩面 +9 端点（25 端点 / 130 pass / 2 skip 空列表 item-key；artifact `logs/fr-b22-field-contract-latest.json`）+ `PROD_SOAK_CHECKLIST.md`（全部 ⬜ 待 ops）；**FR-B28 ✅** GET 字段键自动矩阵（`field_contract.py --keys-matrix`；265 路由 / **41** Python-first 映射 / **39** key-assert + **59** envelope-only；**31** item-key pass / **0** fail；artifact `logs/fr-b28-keys-matrix-latest.json`；**59** 未映射路由仍 envelope-only；prod soak 仍 open） |

---

## 6. 与门禁 / `BLUEPRINT_GAP` 的关系（避免误读）

| 文件说法 | 本文件立场 |
|----------|------------|
| `BLUEPRINT_GAP` **slice-only**（旧称 migrated） | 仅表示 **曾有 certify 切片**，**不是** 该域已迁完；真进度只看本表 |
| EX-AUDIO-TALK 等 | 完整替换目标下 = **待实现 backlog**，不是「不用做」 |
| Phase 0/1/2/3 CERTIFY PASS | 历史切片 / 薄烟雾来源；**≠** 功能完整替换完成 |
| 15～30min observe | 切流运维可选；**≠** 开发期 PASS |
| 薄烟雾 `certify --phase 0` | 防 RUNTIME/hook 回归；**≠** 域完成 |

---

## 7. 完整替换工作量切片建议（执行用 backlog）

按依赖排序（完成定义：对应域路由+关键后台任务+WEB 冒烟）：

| 优先级 | 工作包 | 内容 | 阻塞切流？ |
|--------|--------|------|------------|
| **P0** | Alert 管理面 | page/count/statistics/image/record/clear | **是**（告警台） |
| **P0** | Algorithm CRUD + patrol heartbeat + logs | 任务可配可管 | **是** |
| **P0** | auto_start / 健康恢复对等 | 进程重启后业务自愈 | **部分**（FR-W1-BG ✅ 本地；**FR-B8 ✅** stream_forward 集群健康） |
| **P0** | Gateway + system-server 鉴权真通 | **✅ FR-W1-AUTH**（EX-GATEWAY-AUTH-LOCAL resolved） | ~~是~~ 本地已通；生产切流仍需 ops 演练 |
| **P0** | Alert Kafka 或产品书面确认永久 direct | **✅ FR-W1-KAFKA**（代码路径已实现；local/mini 默认 direct_persist=true） | ~~是~~ 代码已通；prod broker 联调待 ops |
| **P1** | Camera 主路径 | 注册/CRUD/目录/ONVIF/PTZ/snapshot/流票据 | **是**（设备台） |
| **P1** | Snap/Record/Playback 主路径 | 空间+文件+任务 | **是** |
| **P1** | Stream-forward CRUD + auto_start | 推流台 | 视产品 |
| **P1** | Media hooks SRS/ZLM 全套 | 录制闭环 | 视部署 |
| **P1** | Patrol session API | 去掉 EX-PATROL-SESSION-API | 视产品 |
| **P1** | Post-process 真 sink；face/plate 库+识别或旁路 | **✅ FR-B1** post-process sink；**✅ FR-B5** Kafka + 诚实 process（plate DB 匹配；face bypass 待 ORT） | 视产品 |
| **P2** | NVR/扫描/FlightHub/GB28181 目录同步 | **✅ FR-B11** GB28181/WVP 同步；**✅ FR-B12** 目录 JSON 同步 + FlightHub live/register + 大华 NVR CGI 枚举（prod 联调仍待） | 视现场 |
| **P2** | audio_talk | 去掉 EX-AUDIO-TALK | 视产品 |
| **P2** | scenario_pose | 去掉 EX-SCENARIO-POSE | 视产品 |
| **P2** | 空间清理/janitor/disk guard/远程 node | 运维完备 | 集群/长期运行 |
| **收尾** | 全量契约 certify + 全量回滚演练 + 退役 Python | 宣布 COMPLETE | — |

---

## 8. 数量摘要（给排期）— FR-W4 更新

| 指标 | 数值 |
|------|------|
| Python HTTP 路由（14 前缀） | ≈ **259** |
| Java HTTP 映射（14 前缀） | ≈ **259** |
| 路由缺口（prefix-level） | **0** |
| inventory 扫描 artifact | `/video/camera` 前缀 Java **+5**（talk 子路径重复计入） |
| 整域 HTTP 未实现 | **无**（14 前缀均已 diff=0） |
| 行为桩仍存的域 | algorithm/stream_forward（远程 node 集群健康 prod 联调）；face/plate/pose **FR-B9 ✅** Python worker（prod 需模型运行时）；patrol/audio_talk/match-image **FR-B10 ✅**（真机/MinIO 联调待 ops）；GB28181 **FR-B11 ✅**（prod WVP 联调待）；媒体节点池 **FR-B13 ✅**（prod iot-node 媒体 API 联调待）；post-process worker **FR-B14 ✅**（prod 远程副本联调待）；DVR Kafka consumer **FR-B15 ✅**（prod broker + `upload-mode=kafka` 联调待）；snap Kafka consumer **FR-B16 ✅**（prod broker + `snap-upload-mode=kafka` 联调待） |
| **FR-B17/FR-B18 契约探针**（`:48096` live） | **265** probed → **265 pass** / **0 fail** / **0 skip**（FR-B18 收口 patrol session HTTP 404×3、playback POST 尾斜杠、record/snap `/**` AntPathMatcher、device-detection smoke 路径；artifact `logs/fr-b17-contract-latest.json`） |
| **FR-B19 字段级抽样**（`:48096` live） | **12** P0/P1 GET 端点 → **67 pass** / **0 fail** / **2 skip**（空列表 item-key 延后；artifact `logs/fr-b19-field-contract-latest.json`；patrol 无 oracle `GET /session/list`，抽样 `directory/{id}/devices`） |
| **FR-B20 字段级抽样**（`:48096` live） | **16** 端点覆盖 **14 inventoried 前缀** → **88 pass** / **0 fail** / **0 skip**（`alert_page`/`playback_list` POST seed + item keys；新增 media `/video/ping`、device-detection、audio/talk health、scenario-pose libraries；artifact `logs/fr-b20-field-contract-latest.json`；仍 ≠ 259 字段矩阵） |
| **FR-B21 GET 信封矩阵**（`:48096` live） | **265** inventoried 路由（**98 GET**）→ **265 pass** / **0 fail** / **170 skip**（167 非 GET 自动 skip + 3 非 JSON：`alert/image`、`alert/record`、patrol SSE `/events`）；**95** JSON GET 信封探针 **190 pass** / **0 fail**；保留 FR-B20 深采样 **16** 端点 / **88** assert；artifact `logs/fr-b21-field-matrix-latest.json`；信封 presence ≠ 字段键矩阵） |
| **FR-B22 深字段扩面**（`:48096` live） | **25** 端点（+9：algorithm/stream-forward get-by-id、face/plate libraries、alert statistics、snap task list、record space-by-device、record videos list、playback statistics）→ **130 pass** / **0 fail** / **2 skip**（空列表 item-key）；artifact `logs/fr-b22-field-contract-latest.json`；**≠ 全量 259 字段矩阵**；`PROD_SOAK_CHECKLIST.md` 已建（全部 ⬜） |
| **FR-B22 GET 信封矩阵**（`:48096` live，复跑） | **265** pass / **0 fail**；artifact `logs/fr-b22-field-matrix-latest.json` |
| **FR-B28 GET 字段键矩阵**（`:48096` live） | **265** inventoried → **265 pass** / **0 fail**；**98 GET**（**95** JSON + **3** 非 JSON skip）；**41** Python-first 路径映射 → **39** key-assert / **59** envelope-only；item-key **31 pass** / **0 fail** / **8 deferred**（空 data/列表）；全局 seed **15/15**；artifact `logs/fr-b28-keys-matrix-latest.json`；**≠ 259 路由全键覆盖**；`SnapTaskRepository.insert` 修复 |
| **FR-B29 GET 字段键矩阵**（`:48096` live） | **265** inventoried → **265 pass** / **0 fail**；**98 GET**（**95** JSON + **3** 非 JSON skip）；**94** Python-first 路径映射 → **92** key-assert / **6** envelope-only；item-key **60 pass** / **0 fail** / **0 deferred**（B29 seed 清除 8 条）；artifact `logs/fr-b29-keys-matrix-latest.json`；**≠ 259 路由全键覆盖** |
| **FR-B30 存储用量统计**（`:9000` local） | `SnapStorageService` + `VideoMinioService.getBucketUsage` 对齐 Python `get_bucket_size`；disabled 诚实 0；enabled 真 list+stat；artifact `logs/fr-b30-storage-stats-latest.json` |
| **FR-B31 POST/PUT mutating-matrix**（`:48096` live） | **265** inventoried → **265 pass** / **0 fail**；**140** POST+PUT 探针（**112 POST** / **28 PUT**）；**4** skip（3 destructive cleanup + 1 multipart）；**272** assert pass；artifact `logs/fr-b31-mutating-matrix-latest.json`；**≠ POST 字段键矩阵** |
| **FR-B31 storage cleanup**（`:48096` local） | `SnapStorageService.cleanup` 对齐 Python `check_and_cleanup_storage` + `cleanup_old_files`；MinIO disabled 诚实 no-op；artifact `logs/fr-b31-storage-cleanup-latest.json` |
| **FR-B32 cleanup 真删除 E2E**（`:9000` local） | 超配额 `frb32_device` 种子 + MinIO enabled → `POST /storage/cleanup` 真 `remove_object`；before/after object count；artifact `logs/fr-b32-cleanup-e2e-latest.json` |
| **FR-B32 6 非 JSON GET 探针**（`:48096` local） | content-type pass（非 envelope）：alert/image、alert/record、patrol SSE、playback/thumbnail、record video、snap image；artifact `logs/fr-b32-binary-get-latest.json` |
| **FR-B33 POST keys-matrix**（`:48096` local） | **16** curated POST 样本 → **16/16 pass** / **0 fail**；**11** success-key（Python to_dict）+ **5** envelope-only 4xx；**67** assert pass；artifact `logs/fr-b33-post-keys-matrix-latest.json`；**≠ 全量 POST 字段键矩阵** |
| **FR-B34 POST keys-matrix**（`:48096` local） | **42** curated POST 样本 → **42/42 pass** / **0 fail**；**25** success-key + **17** envelope/envelope_success；**13/14** 前缀覆盖；**169** assert pass；artifact `logs/fr-b34-post-keys-matrix-latest.json`；**≠ 全量 POST 字段键矩阵** |
| **FR-B35 POST keys-matrix**（`:48096` local） | **63** curated POST 样本 → **63/63 pass** / **0 fail**；**32** success-key + **31** envelope/envelope_success；**14/14** 前缀（含 `audio_talk` POST start/stop/send）；**242** assert pass；artifact `logs/fr-b35-post-keys-matrix-latest.json`；**≠ 全量 POST 字段键矩阵** |
| **FR-B36 POST keys-matrix**（`:48096` local） | **131** curated POST 样本 → **131/131 pass** / **0 fail**；**40** success-key + **91** envelope/envelope_success；**inventoried POST 112 = 109 sampled + 3 destructive skip**；**457** assert pass；coverage 表见 artifact `logs/fr-b36-post-keys-matrix-latest.json`；**≠ 逐字段 POST 全量 parity** |
| **FR-B37 multipart 成功探针**（`:48096` local） | **2/3** multipart core pass（plate entry + scenario-pose extract）；face entry **EX** InsightFace worker；fixture `testdata/fr-b37/tiny.jpg`；artifact `logs/fr-b37-multipart-latest.json` |
| **FR-B37 bucket 命名**（vj_p2 fixture） | `certify-vj_p2_*` → `certify-vj-p2-*`；`snap/record` metadata sync **0** not **500**；`S3BucketNameSupport` 4xx on illegal bucket |
| **FR-B38 plate image_url**（`:48096` local, MinIO on） | plate entry multipart → `image_url` populated `/api/v1/buckets/plate-library/objects/download?prefix=…`；artifact `logs/fr-b38-multipart-latest.json` |
| **FR-B38 face entry 无模型**（`:48096` local） | **code=400** + Python msg（非 500）；**不 soft-save**；artifact `logs/fr-b38-multipart-latest.json` |
| **FR-B39 HTTP 400 对齐**（`:48096` local） | `VideoApiResponseAdvice.businessCodeToHttpStatus`：code 400/404 → HTTP 400/404；code 500 仍 HTTP 200（`camera.py` L1730-1732）；face no-model **HTTP 400**；artifact `logs/fr-b39-multipart-latest.json` |
| **FR-B39 plate update image**（`:48096` local, MinIO on） | `PUT /video/plate/entries/{id}` multipart → `image_url`（`plate_library_service.update_entry` L311-313）；`PlateController` JSON/multipart consumes 拆分；artifact `logs/fr-b39-multipart-latest.json` |
| **FR-B40 契约探针 404 假阳性**（`:48096` live） | FR-B39 业务 code=404→HTTP 404 后 39 条探针误报 unmapped；`contract_regression.py` 区分 envelope 404 vs Spring 404 → **265 pass / 0 fail**；artifact `logs/fr-b40-contract-latest.json` |
| 现有 vj_* certify cases | ~18（**远不够**覆盖 265 路由；仅防回归） |

---

## 9. 最终判定 — FR-B40

| 问题 | 答案 |
|------|------|
| contract_regression 38×404 根因？ | **假阳性** — 路由已映射；FR-B39 `businessCodeToHttpStatus(404)` + probe `id=1` 不存在资源 → envelope HTTP 404（`patrol.py` L45；`face_library_service.py` L184） |
| contract_regression pass/fail？ | **265 / 0** — `is_video_api_envelope` + `classify_http_status` 修正；artifact `logs/fr-b40-contract-latest.json` |
| phase0？ | **PASS 5/5** — `logs/certify-frb40-phase0.log` |
| 能否称 COMPLETE？ | **禁止** — 探针仅验证路径可达；行为 parity / prod soak 仍 open |

## 10. 历史判定归档（只读）

<details>
<summary>FR-B38 / FR-B37 / FR-B36 … 历史判定（点击展开）</summary>

### FR-B38

| 问题 | 答案 |
|------|------|
| Plate `image_url` multipart 证据？ | **是（local, MinIO on）** — `plate_entry_image_url` pass；`_upload_plate_image` parity；artifact `logs/fr-b38-multipart-latest.json` |
| Face entry 无模型路径？ | **是（local）** — `code=400` + `face_rec.onnx` msg；**不 soft-save** |
| phase0？ | **PASS 5/5** — `logs/certify-frb38-phase0.log` |
| 备注 | HTTP 400 信封差在 **FR-B39** 已修 |

### FR-B37

| 问题 | 答案 |
|------|------|
| Multipart 成功证据？ | **部分（local）** — plate entry + pose extract **pass**；face entry **EX**（推理引擎）；artifact `logs/fr-b37-multipart-latest.json` |
| Fixture bucket S3 非法名？ | **已修复** — `seed_p2_fixture` migrate + `certify_bucket_name()`；sync **200 code=0** |
| Java multipart / MinIO 修复？ | **是** — `PlateController` consumes 拆分；`PlateLibraryService` 去 OCR gate；`S3BucketNameSupport` |
| phase0？ | **PASS 5/5** — `logs/certify-frb37-phase0.log` |
| 能否称 COMPLETE？ | **禁止** — face multipart 成功路径待 InsightFace worker；plate 图片 MinIO 上传 parity 未齐（**FR-B38 已修 plate image_url**） |

### FR-B36

| 问题 | 答案 |
|------|------|
| POST inventoried 路由覆盖？ | **是（local）** — **112** inventoried POST → **109** sampled + **3** documented destructive skip；coverage 表 `logs/fr-b36-post-keys-matrix-latest.md` |
| POST success body 键矩阵？ | **是（local）** — **131** 样本 **131/131**；**40** key-assert pass；artifact `logs/fr-b36-post-keys-matrix-latest.json` |
| Java 缺键/5xx 修复？ | **是** — face/plate multipart 缺文件 → 400；`persons/batch-delete` 空列表 → 400；scenario-pose re-extract 不存在 → 400 |
| phase0？ | **PASS 5/5** — `logs/certify-frb36-phase0.log` |
| 能否称 COMPLETE？ | **禁止** — prod soak open；multipart 成功路径 / 真机 ONVIF 未绿；fixture bucket 名 S3 非法致 sync 诚实 500 |

### FR-B35

| 问题 | 答案 |
|------|------|
| POST keys-matrix ≥60？ | **是（local）** — **63** 样本 **63/63**；artifact `logs/fr-b35-post-keys-matrix-latest.json` |
| audio_talk POST 覆盖？ | **是** — start/stop/send + 4xx/500；Python `audio_talk.py` L87-176 |
| Java audio_talk 修复？ | **是** — 无 IP 诚实 500 + `data.success=false`；HTTP 200 信封 |
| phase0 回归？ | **是** — `logs/certify-frb35-phase0.log` **5/5** |
| 能否称 COMPLETE？ | **禁止** |

### FR-B33

| 问题 | 答案 |
|------|------|
| POST success body 键矩阵？ | **是（local）** — 16 样本；artifact `logs/fr-b33-post-keys-matrix-latest.json` |
| Java 缺键修复？ | **是** — `DeviceRepository.insert` 补 `auto_snap_enabled=false` |
| 能否称 COMPLETE？ | **禁止** |

### FR-B31

| 问题 | 答案 |
|------|------|
| POST/PUT mutating-matrix？ | **是（local）** — artifact `logs/fr-b31-mutating-matrix-latest.json` |
| `check_and_cleanup_storage` MinIO 对齐？ | **是（local）** — artifact `logs/fr-b31-storage-cleanup-latest.json` |
| 能否称 COMPLETE？ | **禁止** |

### FR-B30

| 问题 | 答案 |
|------|------|
| Snap/record 存储用量真 MinIO？ | **是（local）** — artifact `logs/fr-b30-storage-stats-latest.json` |
| 能否称 COMPLETE？ | **禁止** |

### FR-B29

| 问题 | 答案 |
|------|------|
| 全量 GET 字段键自动矩阵？ | **部分** — **94** 映射 / **92** key-assert / **6** envelope-only；artifact `logs/fr-b29-keys-matrix-latest.json` |
| FR-B28 8 deferred 清除？ | **是** |
| 能否称 COMPLETE？ | **禁止** |

### FR-B28

| 问题 | 答案 |
|------|------|
| 全量 GET 字段键自动矩阵？ | **部分** — **41** 映射 / **39** key-assert / **59** envelope-only |
| 能否称 COMPLETE？ | **禁止** |

### FR-B27

| 问题 | 答案 |
|------|------|
| Matching Kafka produce？ | **是（local-only）** |
| 能否称 COMPLETE？ | **禁止** |

</details>

## 10. 最终判定 — FR-B26

| 问题 | 答案 |
|------|------|
| 纯 `upload-mode=kafka` DVR 真文件成功？ | **是（local-only）** — `frb26_device` hook 仅入队（对齐 Python `media_hook.py` kafka-only）；专用 topic `media.dvr.completed.frb26` + consumer group `upload-worker-dvr-frb26`；consumer `DVR 上传完成` → MinIO 146128B + DB `record_path` `/api/v1/buckets/...`；`logs/fr-b26-pure-kafka-dvr-latest.json` **8/8** |
| Alert `use-direct-persist=false` produce？ | **是（local-only）** — `POST /video/alert/hook` → `mode=kafka` topic=`iot-alert-notification` key=`frb26_device`；`logs/fr-b26-alert-kafka-latest.json`；iot-sink 消费 **EX** |
| 能否称 COMPLETE？ | **禁止** |

## 10. 最终判定 — FR-B25

| 问题 | 答案 |
|------|------|
| 真文件 DVR+snap → MinIO+DB？ | **是（local-only）** — `frb25_device` 真 mp4/jpg；hybrid DVR hook + snap Kafka consumer；MinIO object + `record_file`/`snap_image`/`playback` URL `/api/v1/buckets/...`；`logs/fr-b25-minio-upload-e2e-latest.json` **11/11** |
| `snap_image.updated_at` 列错位？ | **已修** — Java `SnapImageRepository` 对齐 Python `SnapImage`（仅 `created_at`） |
| 能否称 COMPLETE？ | **禁止** |

## 10. 最终判定 — FR-B24

| 问题 | 答案 |
|------|------|
| 本地 Kafka 宿主机 E2E？ | **是（local-only）** — `127.0.0.1 Kafka` hosts + `fr_b24_kafka_e2e.py`；consumer → `DVR 文件未就绪` / `抓拍文件未就绪`（`logs/fr-b24-kafka-e2e-latest.json`） |
| `is_custom_save_time` 列错位？ | **已修** — Java `DeviceSpaceRepository` 对齐 Python `RecordSpace.save_time_custom` |
| 能否称 COMPLETE？ | **禁止** |

## 11. 最终判定 — FR-B23

| 问题 | 答案 |
|------|------|
| HTTP 路由是否与 Python 对齐？ | **是**（14 inventoried 前缀 `route_inventory` diff=0） |
| 能否说「Java 已完整替换 Python VIDEO」？ | **不能** — prod 联调与**全量**字段级契约仍 open；**HTTP 薄探针 265/265 已绿**（FR-B18）；**深字段抽样 39 端点已执行**（FR-B27：**192 pass / 0 fail**）；**GET 信封矩阵 265/265**；**GET 字段键矩阵 265/265**（FR-B29：**92** mapped key-assert / **6** envelope-only） |
| 本地 MinIO/Kafka soak？ | **部分** — MinIO put + sync API（`logs/fr-b23-soak-*`）；**FR-B24 ✅** Kafka 宿主机 E2E；**FR-B25 ✅** 真文件 MinIO+DB（hybrid DVR）；**FR-B26 ✅** 纯 kafka DVR + Alert Kafka produce（`logs/fr-b26-*`）；**FR-B27 ✅** matching Kafka produce + 深字段 39 端点（`logs/fr-b27-*`）；**FR-B28 ✅** keys-matrix 基线（`logs/fr-b28-*`）；**FR-B29 ✅** keys-matrix 扩面 + deferred 清除（`logs/fr-b29-*`）；**FR-B30 ✅** 存储用量统计（`logs/fr-b30-storage-stats-*`）；`snap_image.updated_at` schema 错位已修 |
| 能否称 COMPLETE / 退役 Python？ | **禁止** |
| 证据硬化（EVID）能否停？ | **可以停**，转本文件 backlog + [`PROD_SOAK_CHECKLIST.md`](./PROD_SOAK_CHECKLIST.md) |
| 距完整替换还缺什么？ | **prod 联调 soak**（checklist 大部仍 ⬜）+ **6 GET 路由 Python 键矩阵** + prod 场景回放 + 回滚演练 |

**维护约定：** 每完成一个 FR 工作包，在本文件对应行改为 ✅，更新该域 Py vs Java 路由数，并保留短契约测；**不要**再开 Phase 门禁剧或 EVID/CLOSE 轮次。在全部 P0/P1（及产品未豁免的 P2）勾完前，禁止对外宣称「VIDEO Java 完整替换完成」。

**现行工作包顺序：** 见 [`PLAN_FULL_REPLACEMENT.md`](./PLAN_FULL_REPLACEMENT.md) §4–§5（Alert → Algorithm CRUD → auto_start → Camera…）。
