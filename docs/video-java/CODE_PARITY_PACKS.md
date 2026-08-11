# CODE-PARITY — Part1 任务包总表（CP-1 … CP-10）

> 实现 **另令**。波次 0 只建包。纪律：见 [CODE_PARITY_BACKLOG.md](./CODE_PARITY_BACKLOG.md) **零 Fallback**。  
> Briefs：`.superpowers/sdd/briefs/cp-N-brief.md` · 索引：`.superpowers/sdd/CODE_PARITY_INDEX.md`

**依赖序：** CP-1 → CP-2 → CP-3（可与 CP-2 紧耦合）→ CP-4 / CP-5 → CP-6…CP-10。

---

## CP-1 — 清除商业路径 Fallback / 降级

| 字段 | 内容 |
|------|------|
| **目标** | `local` 上告警 Kafka 失败 **诚实失败**；审计并清除其它 silent-success |
| **In** | 禁用/切断 `fallbackPersistOnKafkaFailure` 成功路径；扫描同类降级 |
| **Out** | 不装引擎；不改 mini 行为（可保留 mini 捷径但不计入 Part1） |
| **Oracle** | `VIDEO/app/services/alert_hook_service.py`（`_fallback_persist_on_kafka_failure` — **Part1 禁用**） |
| **Java** | `AlertHookService.java`；相关配置 |
| **Done when** | Kafka 不可达或 send 失败时响应 **非 success**（不得 `mode=direct_persist` 当成功）；证据证明未 silent 落库；**零 Fallback** |
| **前置** | 无（Phase2 A1 已证成功路径） |
| **证据** | `logs/cp-1-no-fallback.json` |

---

## CP-2 — Matching 消费链代码完备

| 字段 | 内容 |
|------|------|
| **目标** | plate consumer 商业默认可用；face 消费链（**iot-sink → process** 或对等）可测到调用 process / 诚实缺引擎 |
| **In** | `plate-matching-consumer-enabled` local 默认 true（或文档化并以 sink consumer 为唯一商业路径且本机启用）；确保 face consume→`/face/matching/process` 代码路径可触发 |
| **Out** | **不要求** InsightFace/Milvus 命中（属 Part2）；不得 `use-direct-process=true` |
| **Oracle** | `library_matching_service.py`；face/plate kafka services；sink 职责（Python 经 HTTP process） |
| **Java** | `PlateMatchingKafkaConsumerRunner`；`VideoProperties.Matching`；`iot-sink` `FaceMatchingConsumer` / `PlateMatchingConsumer` → `*MatchingServiceImpl` |
| **Done when** | publish 后消费侧调用到 process（日志/审计）；引擎缺失时 **诚实 bypass/失败** 且非 matched success；plate 可用 DB hit/miss 作消费链旁证 |
| **前置** | CP-1（避免失败被 fallback 掩盖） |
| **证据** | `logs/cp-2-matching-consume.json` |

---

## CP-3 — Post-process ↔ iot-sink 可复现接线

| 字段 | 内容 |
|------|------|
| **目标** | 仓库内 `iot-sink` 对齐 PG **15432**；runbook；`enqueue_ok=true` |
| **In** | 改 sink `application-local.yaml`（或等价）端口；启动文档；网关/直连 enqueue 绿证 |
| **Out** | 不改回 `use-stub-enqueue=true`；不自研 Kafka |
| **Oracle** | `post_process_sink_client.py`；`alert_post_orchestrator.py` |
| **Java** | `PostProcessSinkClient`；`DEVICE/iot-sink/**`；`PHASE1_STACK` 扩展 |
| **Done when** | sink UP；`POST` 后处理路径 `enqueue_ok=true`；DB/日志可解释；**零 stub** |
| **前置** | CP-1；建议与 CP-2 同栈（sink 亦承载 matching consume） |
| **证据** | `logs/cp-3-sink-enqueue.json` |

---

## CP-4 — Snap 调度 ↔ `init_all_tasks`

| 字段 | 内容 |
|------|------|
| **目标** | 启动后 snap 启用任务进入调度，行为证据对齐 Python `init_all_tasks` |
| **In** | 对照 `SnapTaskSchedulerService.initAllTasks`；短验启用任务被 schedule |
| **Out** | 不要求真 RTSP 抓拍成功（源缺失诚实失败） |
| **Oracle** | `snap_task_service.py` `init_all_tasks` |
| **Java** | `SnapTaskScheduler` / `SnapTaskSchedulerService` |
| **Done when** | 证据显示 init 调用与调度条目；与 Python 同库启用集一致或可解释 diff |
| **前置** | CP-1 |
| **证据** | `logs/cp-4-snap-scheduler.json` |

---

## CP-5 — Algorithm `services/status` 诚实字段模型

| 字段 | 内容 |
|------|------|
| **目标** | 去掉假 running；`realtime_service` 等与 Python 关键语义一致；**无假 running** |
| **In** | 修订 `resolveServiceStatus` certify heuristic；文档化 extractor/sorter/pusher=null（Python 同形） |
| **Out** | 不重写整套旧架构 extractor/sorter/pusher 进程（Python 亦常 null） |
| **Oracle** | `algorithm_task.py` `get_task_services_status` |
| **Java** | `AlgorithmTaskLifecycleService.getServicesStatus` |
| **Done when** | 进程杀掉后 status **不得**仅凭 DB 报 running；证据 JSON |
| **前置** | CP-1 |
| **证据** | `logs/cp-5-services-status.json` |

---

## CP-6 — Patrol 代码主路径

| 字段 | 内容 |
|------|------|
| **目标** | 巡检 session 启停/状态/事件与 Python 关键语义对齐（代码级） |
| **In** | `PatrolController` / `PatrolSessionService` / SSE 或 events |
| **Out** | 不要求真机摄像头矩阵；Part2 真机 |
| **Oracle** | `app/blueprints/patrol.py`；`patrol_session_service.py` |
| **Java** | `PatrolController`；`PatrolSessionService`；`PatrolSupervisor` |
| **Done when** | 创建→start→stats/events→stop 短验；零 stub success |
| **前置** | CP-1 |
| **证据** | `logs/cp-6-patrol.json` |

---

## CP-7 — AudioTalk 代码主路径

| 字段 | 内容 |
|------|------|
| **目标** | capabilities / start / stop / health 对齐 Python 关键面 |
| **In** | `AudioTalkController` / `AudioTalkService` |
| **Out** | 真 SIP 话机设备（Part2） |
| **Oracle** | `app/blueprints/audio_talk.py` |
| **Java** | `…/talk/AudioTalkService.java` |
| **Done when** | 无设备时诚实失败；有 fixture 时启停可解释 |
| **前置** | CP-1 |
| **证据** | `logs/cp-7-audiotalk.json` |

---

## CP-8 — GB28181 代码路径（无真机强制）

| 字段 | 内容 |
|------|------|
| **目标** | `gb28181://` 源解析 + sync API 代码与 Python 对齐 |
| **In** | `Gb28181SourceSupport` / `Gb28181SyncService`；camera 相关路由 |
| **Out** | 真 SIP/NVR 设备联调（Part2 E-07） |
| **Oracle** | `gb28181_source.py`；`gb28181_sync_service.py`；camera 引用 |
| **Java** | `service/camera/Gb28181*.java` |
| **Done when** | 合成/fixture 源解析与 sync 接口行为证据；失败诚实 |
| **前置** | CP-1 |
| **证据** | `logs/cp-8-gb28181-code.json` |

---

## CP-9 — FlightHub + 目录同步代码路径

| 字段 | 内容 |
|------|------|
| **目标** | FlightHub config/live 与 directory 关键 API 代码对齐 |
| **In** | `CameraFlighthubService`；directory list/关联 |
| **Out** | 真 FlightHub token/无人机（Part2 E-08） |
| **Oracle** | `flighthub_source.py`；`camera.py` flighthub/directory 路由 |
| **Java** | `CameraFlighthubService`；`CameraController` directory |
| **Done when** | 配置读取 + 无凭证时诚实失败；directory 关键字段同库可对 |
| **前置** | CP-1 |
| **证据** | `logs/cp-9-flighthub-directory.json` |

---

## CP-10 — Boot 后台项对照（`run.py` ↔ Java schedulers）

| 字段 | 内容 |
|------|------|
| **目标** | `run.py` 后台启动项与 Java `*Scheduler`/AutoStart/Janitor **对照表 + 抽样证据** |
| **In** | ViewForward auto-resume、stream-forward auto-start、space cleanup、media janitor、algo auto-start/health 等 |
| **Out** | 不重做已 PART 的 Kafka/MinIO 主路径 |
| **Oracle** | `VIDEO/run.py` 后台块 |
| **Java** | `scheduler/*`；`ViewForwardAutoResume*`；`AlgorithmTaskAutoStart*` 等 |
| **Done when** | 文档化映射表；至少 2 项本机抽样证明启用且非假成功 |
| **前置** | CP-4、CP-5 建议先完成 |
| **证据** | `logs/cp-10-boot-daemons.json` |

---

## 包数量说明

共 **10** 包（≥6 ≤12）。未把 Part2 引擎攻坚塞入 Part1。CP-8/9 Done when **明确排除真机**。
