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
| Blueprint / 域 | **14** | 有控制器触及约 **12** 域，其中 **2** 全缺、**多数仅切片** | ~15–25% 路由面 |
| HTTP `@route` / `@*Mapping` | **≈265** | **≈29** | **~11%** |
| `app/services` 量级 | **67** 个 py | **20** 个 Java service + 4 process + 2 scheduler | 编排核心有，周边大缺 |
| 独立 worker 目录 | `services/` 下 frame/sorter/pusher/media_*/post_process/stream_forward 等 | **无对等多进程 worker 包**（推流/RUNTIME 用 JVM 内 Supervisor） | 模型不同，能力未对齐 |
| 启动后台任务 | auto_start 算法/推流/观看、空间清理、janitor、磁盘守护、健康监控、抓拍调度… | FR-W1-BG：auto_start 算法/观看/stream_forward + 算法健康恢复；清理/janitor/抓拍调度仍缺 | 部分 |
| 门禁自称 | — | Phase -1～3 PASS + EVID | **切片证据 ≠ 完整替换** |

**结论一句话：**  
当前 Java VIDEO 是 **「certify 切片 + 可切网关名」的编排雏形**，距离 **完整替换 Python 全部功能** 仍缺 **约九成 HTTP 面** 以及大量设备/库/空间/媒体/巡检/对讲能力与后台任务。  
已签字的 `EX-*` / `BLUEPRINT_GAP.md` 只是把缺口记账，**不是已经实现。**

---

## 1. 域级总表（完整替换视角）

图例：

- **已有切片**：有部分 API，且有 certify case  
- **严重不足**：仅 list/get/hook 等，WEB 主流程会缺大量接口  
- **缺失**：无 Java Controller / 无对等实现  
- **豁免记账**：已有 EX-id，产品若接受「上线可缺」可不做；**完整替换则必须做**

| # | 域 | Python 前缀 | Py 路由数 | Java 现状 | Java 已有映射（摘要） | 完整替换判定 | 关联 EX / 备注 |
|---|----|-------------|----------:|-----------|----------------------|--------------|----------------|
| 1 | algorithm_task | `/video/algorithm` | 21 | 管理面 + lifecycle | list/get/CRUD/start/stop/restart/services/status/heartbeat/logs/streams/post-process | **本地切片** | route_inventory `/video/algorithm` Py=21 Java=21 diff=0；远程 node 仍 400（EX-REMOTE-NODE） |
| 2 | alert | `/video/alert` | 10 | 管理面 + hook | page/count/statistics/correlation/image/record/record/query/clear/clear/all + `POST /hook` | **本地切片** | route_inventory `/video/alert` Py=10 Java=10 diff=0；**EX-ALERT-ADMIN-API resolved**；**EX-KAFKA-HOOK resolved**（`use-direct-persist=false` → Kafka produce + fallback） |
| 3 | camera | `/video/camera` | **59** | 全量路由 | list/CRUD/stream/目录/NVR/… | **路由切片完成** | `route_inventory` Py=59 Java=59 diff=0；**FR-W2-CAM**；ONVIF/扫描/抓拍行为待 SDK |
| 4 | stream_forward | `/video/stream-forward` | 13 | 全量路由 | list/get/CRUD/start/stop/restart/status/heartbeat/logs/streams/ensure-task | **路由切片完成** | `route_inventory` Py=13 Java=13 diff=0；**FR-W2-SF**；远程 node/auto 调度仍 400 |
| 5 | face | `/video/face` | 35 | 切片 | matching/publish、matching/process | **严重不足** | 库/人像/entries/auto-enroll/normalize/recognize/model… 全缺 |
| 6 | plate | `/video/plate` | 26 | 切片 | matching/publish、matching/process | **严重不足** | 同 face，库与识别面缺 |
| 7 | snap | `/video/snap` | 38 | 全量路由 | space/task/region/service/images/storage | **路由切片完成** | `route_inventory` Py=38 Java=38 diff=0；**FR-W2-MEDIA**；MinIO/调度器待 SDK |
| 8 | record | `/video/record` | 16 | 全量路由 | space/videos/dates/day/resolve-alert | **路由切片完成** | `route_inventory` Py=16 Java=16 diff=0；**FR-W2-MEDIA** |
| 9 | playback | `/video/playback` | 7 | 全量路由 | list/CRUD/thumbnail/statistics | **路由切片完成** | `route_inventory` Py=7 Java=7 diff=0；**FR-W2-MEDIA** |
| 10 | media_hook | `/video/media` | 全量路由 | hook/srs + hook/zlm + snap/completed | **路由切片完成** | `route_inventory` Py=6 Java=6 diff=0；**FR-W2-HOOKS**；MinIO DVR 上传待 SDK |
| 11 | device_detection_region | `/video/device-detection` | 6 | 切片 | regions GET | **严重不足** | POST/PUT/DELETE、cover-image、snapshot 缺 |
| 12 | patrol | `/video/patrol` | 9 | 全量路由 | session CRUD/start/stop/stats/events/SSE/heartbeat/directory devices | **路由切片完成** | `route_inventory` Py=9 Java=9 diff=0；**FR-W2-PATROL**；守护进程/SSE 行为 mini 桩 |
| 13 | audio_talk | `/video/camera/audio/talk` | 5 | 无 | — | **缺失** | **EX-AUDIO-TALK** |
| 14 | scenario_pose | `/video/scenario-pose` | 14 | 无 | — | **缺失** | **EX-SCENARIO-POSE** |
| — | heartbeat（附属） | `/video/algorithm/heartbeat` | (含在 algorithm) | 切片 | realtime | **不足** | `heartbeat/patrol` 未见 Java 映射 |
| — | ping/actuator | `/video/ping`, `/actuator/*` | — | 有 | ping + Boot actuator | 基本可 | — |

**路由合计：Python ≈265 vs Java ≈29 → 缺口约 236 个 endpoint（数量级）。**

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
| ❌ 行为 | — | `schedule_policy!=local` 远程 node 部署（现 400，EX-REMOTE-NODE） |
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
| ❌ 行为 | ONVIF 真连接、NVR 通道枚举、hiktools 扫描、抓拍抽帧、司空 live、GB28181 全量同步 — 无硬件/SDK 时仅错误结构对齐 |

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
| ❌ 行为 | — | `schedule_policy!=local` 远程 node 部署（现 400，EX-REMOTE-NODE） |
| ✅ 路由差 | `/video/stream-forward`：**Py 13 / Java 13 / diff 0**（`route_inventory.py --prefix /video/stream-forward`） |

### 2.5 `face` / `plate`

| 已有 | 仍缺（完整替换） |
|------|------------------|
| `/matching/publish`, `/matching/process` | health、model download/status；libraries/entries/persons CRUD；auto-enroll；normalize；match；recognize；matching/records；旧 `/library` API 等 |

依赖层：Python 还有 InsightFace/ONNX、Milvus、PaddleOCR、Kafka matching consumer —— Java 现多为 **mini mock / stub**，完整替换需 ORT/SDK 或旁路策略产品拍板后落地。

### 2.6 `snap` / `record` / `playback` — FR-W2-MEDIA（路由面 diff=0）

| 域 | 路由差 | 状态 | 说明 |
|----|--------|------|------|
| snap | **Py 38 / Java 38 / diff 0** | ✅ 路由 | space CRUD/策略/sync；task CRUD/start/stop/restart/logs；region/service；images；device storage |
| record | **Py 16 / Java 16 / diff 0** | ✅ 路由 | space CRUD/策略/sync；videos dates/day/list/object/delete/sync/cleanup；resolve-alert |
| playback | **Py 7 / Java 7 / diff 0** | ✅ 路由 | list/get/create/update/delete；thumbnail；statistics |
| ❌ 行为 | — | MinIO 真同步/清理、抓拍 APScheduler、真 play URL 解析 — mini 形态桩/DB 为主 |

### 2.7 `media_hook` / `device_detection_region`

| 域 | 路由差 | 状态 | 说明 |
|----|--------|------|------|
| media_hook | **Py 6 / Java 6 / diff 0** | ✅ 路由 | SRS `on_dvr/on_publish/on_unpublish`；ZLM `on_record_mp4/ts`；`snap/completed` |
| ❌ 行为 | — | DVR MinIO 上传、Playback/RecordFile 写入、抓拍 Kafka→MinIO 全链路 — mini 形态 ack/DB 桩 |
| regions | GET regions | POST/PUT/DELETE；cover-image；snapshot |

### 2.8 整域缺失

| 域 | 全部路径 | 完整替换动作 |
|----|----------|--------------|
| `audio_talk` | capabilities/start/stop/send/health | ONVIF back-channel 服务（对齐 `onvif_audio_backchannel`） |
| `scenario_pose` | libraries/entries/extract/match-test/templates | 姿态库服务（对齐 `scenario_pose_library_service`） |

**已解决（FR-W2-PATROL）：** `patrol` — `PatrolController` + `PatrolSessionService` / `PatrolProgressHub`；`route_inventory /video/patrol` Py=9 Java=9 diff=0；**EX-PATROL-SESSION-API resolved**。

---

## 3. 后台守护 / 调度 / Worker（非 HTTP 但属于「全部功能」）

Python `run.py` 启动时拉起的能力 vs Java：

| Python 能力 | Java 现状 | 完整替换 |
|-------------|-----------|----------|
| `auto_start_streaming`（观看 ffmpeg） | ✅ `ViewForwardAutoResume*`（`enable_forward` + 离线/rtmp 跳过） | FR-W1-BG 已对齐本地语义 |
| `auto_start_all_tasks`（算法） | ✅ `AlgorithmTaskAutoStart*`（enabled + local + 模型/设备校验） | FR-W1-BG 已补 |
| `stream_forward` auto_start | ✅ `StreamForwardAutoStart*`（enabled + local） | FR-W1-BG 已补；远程分片仍 ❌ |
| 抓拍/录像空间定时清理（30min） | **缺** | 必须补 |
| playback disk guard | **缺** | 必须补 |
| media janitor | **缺** | 必须补或明确由独立 worker 承担 |
| stream_forward 集群健康迁移 | **缺** | 集群场景必须（`STREAM_FORWARD_HEALTH_*` 仅远程） |
| algorithm_task 健康监控（60s） | ✅ `AlgorithmTaskHealthRecovery*`（启动即恢复 + 定时；local 以 supervisor 为准） | FR-W1-BG 已对齐 P0 |
| snap_task 调度器 `init_all_tasks` | **缺** | snap 任务面补齐时必须 |
| `VIDEO/services/*` 独立进程（upload/janitor/post_process_worker…） | JVM 内或 stub | 完整替换需逐项定：迁入 Java / 保留外部进程 / 废弃 |

---

## 4. 下游集成与行为缺口

| 项 | Python | Java | 完整替换要求 |
|----|--------|------|--------------|
| Alert → Kafka | 可走 Kafka | `use-direct-persist=false` → Kafka produce（minimal 驼峰消息，deviceId key）；失败 fallback direct_persist；local/mini 默认仍 direct | **resolved by FR-W1-KAFKA**（prod 需 broker + iot-sink 联调） |
| Post-process → iot-sink | 真 enqueue | `use-stub-enqueue: true`（local） | 关闭 stub，接真 sink |
| Face/Plate matching | Kafka + 模型 | publish/process 切片；mini mock | 真 Kafka + 推理/旁路 |
| 远程 node / RUNTIME 分发 | node_client | EX-REMOTE-NODE 本地拒绝 | 对齐 iot-node API |
| ONVIF / NVR / GB28181 / FlightHub | camera 大面 | **无** | 随 camera 域补齐 |
| MinIO 空间同步/清理 | snap/record 多接口 | 基本无 | 随空间域补齐 |
| 鉴权（流票据、网关 token） | 有 | **FR-W1-AUTH ✅** mini gateway + `system-server` token check（invalid Bearer 401；valid Bearer 200）；流票据仍缺 | 生产全量路由 + 流票据待 W2 camera |
| 对外 JSON | `{code,msg,data}` | `VideoApiResponse` 已对齐方向 | 全接口字段级与 WEB 对表 |

---

## 5. 运维 / 切流 / 回滚（完整替换收尾）

| 项 | 现状 | 完整替换还要 |
|----|------|--------------|
| 网关 `lb://video-server` | 已改指向 Java 名 | 全量 API 可用前，**生产流量不应认为已安全切完** |
| Python 热路径归档 | `_retired_python_video/` | 保留直到 Java 全量绿 |
| 回滚演练 | 仅 3 文件进出台账级 | **全量** `app/`+`services/`+`run.py` 恢复 + 同名服务拉起 + 网关观察 |
| Nacos 双跑/切换 | 文档有漂移（仍见 video-server-java 旧述） | 与 CLOSE-S2 现实对齐并做一次真切换演练 |
| 证据门禁 | EVID 已抬真 RUNTIME/alert success 等 | 完整替换应另建 **全量契约回归**（按本文件域表），不能只靠现有 18 个 vj_* case |

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
| **P0** | auto_start / 健康恢复对等 | 进程重启后业务自愈 | **部分**（FR-W1-BG ✅ 本地；集群/stream_forward health ❌） |
| **P0** | Gateway + system-server 鉴权真通 | **✅ FR-W1-AUTH**（EX-GATEWAY-AUTH-LOCAL resolved） | ~~是~~ 本地已通；生产切流仍需 ops 演练 |
| **P0** | Alert Kafka 或产品书面确认永久 direct | **✅ FR-W1-KAFKA**（代码路径已实现；local/mini 默认 direct_persist=true） | ~~是~~ 代码已通；prod broker 联调待 ops |
| **P1** | Camera 主路径 | 注册/CRUD/目录/ONVIF/PTZ/snapshot/流票据 | **是**（设备台） |
| **P1** | Snap/Record/Playback 主路径 | 空间+文件+任务 | **是** |
| **P1** | Stream-forward CRUD + auto_start | 推流台 | 视产品 |
| **P1** | Media hooks SRS/ZLM 全套 | 录制闭环 | 视部署 |
| **P1** | Patrol session API | 去掉 EX-PATROL-SESSION-API | 视产品 |
| **P1** | Post-process 真 sink；face/plate 库+识别或旁路 | 去掉 stub/mock | 视产品 |
| **P2** | NVR/扫描/FlightHub/GB28181 目录同步 | camera 长尾 | 视现场 |
| **P2** | audio_talk | 去掉 EX-AUDIO-TALK | 视产品 |
| **P2** | scenario_pose | 去掉 EX-SCENARIO-POSE | 视产品 |
| **P2** | 空间清理/janitor/disk guard/远程 node | 运维完备 | 集群/长期运行 |
| **收尾** | 全量契约 certify + 全量回滚演练 + 退役 Python | 宣布 COMPLETE | — |

---

## 8. 数量摘要（给排期）

| 指标 | 数值 |
|------|------|
| Python HTTP 路由 | ≈ **265** |
| Java HTTP 映射 | ≈ **29** |
| 路由缺口（约） | ≈ **236** |
| 整域未实现 | **audio_talk, scenario_pose**（+ patrol 会话面实质未实现） |
| 标「已迁」但仍严重不足的域 | algorithm（管理面）、alert、camera、face、plate、snap、record、playback、media、stream_forward、regions |
| 现有 vj_* certify cases | ~18（远不够覆盖 265 路由） |

---

## 9. 最终判定

| 问题 | 答案 |
|------|------|
| 能否说「Java 已完整替换 Python VIDEO」？ | **不能** |
| 证据硬化（EVID）能否停？ | **可以停**，转本文件 backlog |
| 距完整替换还缺什么？ | **上表：~90% HTTP 面 + 大部门户后台任务 + 真 Kafka/库/设备栈 + 全量回滚/鉴权** |

**维护约定：** 每完成一个 FR 工作包，在本文件对应行改为 ✅，更新该域 Py vs Java 路由数，并保留短契约测；**不要**再开 Phase 门禁剧或 EVID/CLOSE 轮次。在全部 P0/P1（及产品未豁免的 P2）勾完前，禁止对外宣称「VIDEO Java 完整替换完成」。

**现行工作包顺序：** 见 [`PLAN_FULL_REPLACEMENT.md`](./PLAN_FULL_REPLACEMENT.md) §4–§5（Alert → Algorithm CRUD → auto_start → Camera…）。
