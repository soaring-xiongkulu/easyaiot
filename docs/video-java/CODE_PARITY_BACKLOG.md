# CODE-PARITY — Part 1 Backlog（代码可完美复刻）

> **话术：** CODE-PARITY 波次 0：Part1/Part2 清单与任务包已建立；功能实现另令；Python 仍为对照，禁止删除。  
> **进度表角色：** 本文件是 **Part 1 唯一进度表**。Part 2 见 [DEP_ENGINE_BACKLOG.md](./DEP_ENGINE_BACKLOG.md)。任务包见 [CODE_PARITY_PACKS.md](./CODE_PARITY_PACKS.md)。  
> **唯一环境：** 本机完整栈（PG `127.0.0.1:15432` / Kafka / MinIO / Nacos / 网关 / `video-server` `local`）。**禁止「等线上」叙事。**

---

## 1. 分类规则

| 类 | 定义 | 本表 |
|----|------|------|
| **Part 1 — 代码可完美复刻** | 逻辑写在 Python `VIDEO/` 或仓库内已有 Java 兄弟模块（如 `DEVICE/iot-sink`）里，用 Java **等价实现/对齐**即可 | **本文件跟踪** |
| **Part 2 — 依赖/引擎** | InsightFace、Milvus、模型文件、真机 ONVIF/NVR、远程 Ceph/node 等 | **只列清单，不开工** → [DEP_ENGINE_BACKLOG.md](./DEP_ENGINE_BACKLOG.md) |

**边界举例**

- Kafka publish → consume → 调用 `matching/process` 的 **代码路径** = Part1；InsightFace/Milvus 是否装好 = Part2。  
- `iot-sink` 对齐 `15432` + 可复现启动 + `enqueue_ok=true` = Part1；装模型 = Part2。  
- FlightHub/GB **API 与源解析代码** = Part1；真机 SIP/无人机联调 = Part2。

---

## 2. Part1 零 Fallback 纪律（强制）

商业路径 `profile=local` 上：

1. **Kafka / 入队 / 匹配失败必须诚实失败** — 不得 silent 落库、不得把 bypass/stub 当成功。  
2. **Part1 禁用告警 Kafka 失败兜底：** Python 存在 `_fallback_persist_on_kafka_failure`（`alert_hook_service.py`）；Java 存在对等的 `AlertHookService.fallbackPersistOnKafkaFailure`。  
   - **本项目 Part1 标准严于该 Python 兜底：商业 `local` 路径必须禁用该兜底**（Kafka 失败 → `status=failed` / 非 success，不得 `mode=direct_persist` + success）。  
   - `mini` / 显式 env 捷径不计入 Part1 PASS。  
3. **禁止**把 `use-direct-persist=true` / `use-stub-enqueue=true` / `use-direct-process=true` / `mini` 当作 Part1 完成方案。  
4. **禁止** `services/status` 在进程已死时仅凭 DB `run_status=running` 报假 `running`（见缺口 G-05）。  
5. 引擎缺失时允许 **诚实** `status=bypassed` / ⛔ — **不得**记为匹配成功；引擎本身归 Part2。

---

## 3. 已读路径（波次 0 核对）

### Python Oracle（`F:/acme/VIDEO/`）

| 路径 | 用途 |
|------|------|
| `app/services/alert_hook_service.py` | `_should_use_direct_alert_persist` / Kafka send / `_fallback_persist_on_kafka_failure` |
| `app/services/library_matching_service.py` | `process_face_matching_message` / `process_plate_matching_message` |
| `app/services/face_matching_kafka_service.py` / `plate_matching_kafka_service.py` | publish topics |
| `app/services/snap_task_service.py` | `init_all_tasks()`（启用任务装入调度器） |
| `app/services/post_process_sink_client.py` | HTTP → iot-sink `/post-process/enqueue` |
| `app/services/alert_post_orchestrator.py` | 告警后触发后处理入队 |
| `app/blueprints/patrol.py` / `audio_talk.py` | 巡检 / 对讲 HTTP 面 |
| `app/blueprints/camera.py` | FlightHub / GB28181 / directory 相关路由 |
| `app/services/gb28181_sync_service.py` / `app/utils/gb28181_source.py` / `app/utils/flighthub_source.py` | 国标同步 / 源解析 / 司空 |
| `app/blueprints/algorithm_task.py` | `services/status`（`extractor`/`sorter`/`pusher` 常为 `None`） |
| `run.py` | 后台：auto_start streaming、snap/record cleanup、algorithm/stream-forward daemons 等 |

### Java Candidate

| 路径 | 用途 |
|------|------|
| `…/service/AlertHookService.java` | `fallbackPersistOnKafkaFailure`（**违约降级**） |
| `…/config/VideoProperties.java` | `plateMatchingConsumerEnabled=false` 默认；商业捷径默认已关 |
| `…/kafka/PlateMatchingKafkaConsumerRunner.java` | 板牌消费 runner（默认不启） |
| **无** `FaceMatchingKafkaConsumerRunner` in `iot-video` | Face 消费在 **`iot-sink`** `FaceMatchingConsumer` |
| `DEVICE/iot-sink/…/FaceMatchingConsumer.java` / `PlateMatchingConsumer.java` | sink 消费 → HTTP 调 video `/face|plate/matching/process` |
| `…/service/LibraryMatchingProcessor.java` | face 引擎不可用 → `status=bypassed` |
| `…/service/PostProcessSinkClient.java` | 真 HTTP / mini stub |
| `…/service/snap/SnapTaskSchedulerService.java` + `scheduler/SnapTaskScheduler.java` | `initAllTasks()` |
| `…/service/AlgorithmTaskLifecycleService.java` | `getServicesStatus`；**certify heuristic 假 running** |
| `DEVICE/iot-sink/…/application-local.yaml` | PG 仍 **`localhost:5432`**（未对齐 15432） |
| 阶段 2：`logs/phase2-a*.json`、`PHASE2_MAINPATH.md`、`.superpowers/sdd/briefs/phase2-a*-report.md` | A1–A5 PASS；A6 ⛔缺 sink；A7 ⛔缺 Milvus |

---

## 4. 已存在但违约的降级 / 缺口（审查已知 + 读码增补）

| ID | 违约/缺口 | 证据锚点 | 归类 |
|----|-----------|----------|------|
| **D-01** | ~~告警 Kafka 失败 → `direct_persist` fallback 仍可 success~~ **CP-1 PASS** — fallback removed; honest `code=500` | `AlertHookService.java`；证据 `logs/cp-1-no-fallback.json` | Part1 → **CP-1** ✓ |
| **D-02** | ~~`plateMatchingConsumerEnabled=false`：publish 通但 video 内 consume 默认关~~ **CP-2 PASS** — sink `PlateMatchingConsumer` consume→process proven; video runner intentionally off | `VideoProperties.Matching` L74；证据 `logs/cp-2-matching-consume.json` | Part1 → **CP-2** ✓ |
| **D-03** | ~~`iot-video` 无 Face consumer；sink 未接线~~ **CP-2 PASS** — `FaceMatchingConsumer` → HTTP `/face/matching/process` (honest bypass) | sink consumers；证据 `logs/cp-2-matching-consume.json` | Part1 **CP-2** ✓；引擎 **Part2** |
| **D-04** | ~~`iot-sink` local 库端口未对齐 **15432** / 未纳入可复现启动~~ **CP-3 PASS** — PG 15432 + sink `:48092` runbook | `application-local.yaml`；证据 `logs/cp-3-sink-enqueue.json` | Part1 → **CP-3** ✓ |
| **D-05** | ~~`services/status`：进程已死仍可因 DB `is_enabled`+`run_status=running` 报 running（certify heuristic）~~ **CP-5 PASS** — heuristic removed; alive process or heartbeat&lt;60s only | `AlgorithmTaskLifecycleService.resolveServiceStatus`；证据 `logs/cp-5-services-status.json` | Part1 → **CP-5** ✓（`extractor`/`sorter`/`pusher` 为 null **与 Python 同形**，非缺口） |
| **D-06** | ~~Snap 调度与 Python `init_all_tasks` **缺证据级对齐**~~ **CP-4 PASS** — boot schedules all `is_enabled` tasks; set parity + honest RTSP fail | Python `snap_task_service.init_all_tasks`；证据 `logs/cp-4-snap-scheduler.json` | Part1 → **CP-4** ✓ |
| **D-07** | ~~Post-process：代码路径已有，缺 sink 进程 → A6 `enqueue_ok=false`~~ **CP-3 PASS** — sink UP, `enqueue_ok=true` | `logs/cp-3-sink-enqueue.json` | Part1 → **CP-3** ✓ |
| **D-08** | ~~Matching：缺 consume→process 本机闭环证据~~ **CP-2 PASS** — sink consumers → process; plate hit/miss; face honest bypass | `logs/cp-2-matching-consume.json` | Part1 **CP-2** ✓；InsightFace/Milvus **Part2** |
| **D-09** | Patrol / AudioTalk：**控制器已有**，相对 Python 行为/SSE/进程语义需证据级收口 | ~~Patrol~~ **CP-6 PASS** — main-path create/start/stats/events/stop; AudioTalk → CP-7 | Part1 → **CP-6** ✓ / **CP-7** |
| **D-10** | GB28181 / FlightHub / directory：**Java 支持类已有**，缺与 Python 关键路径的代码证据（真机归 Part2） | `Gb28181*` / `CameraFlighthubService` / `camera.py` routes | Part1 → **CP-8 / CP-9** |
| **D-10a** | ~~FlightHub + directory 代码证据~~ **CP-9 PASS** — config shape + missing-creds honest fail + directory fields on shared DB | 证据 `logs/cp-9-flighthub-directory.json` | Part1 → **CP-9** ✓ |
| **D-11** | `run.py` 后台项 vs Java schedulers：多项已移植，缺总表证据 | Python `run.py`；Java `*Scheduler` / AutoStart / Janitor | Part1 → **CP-10** |

**相对门卡审查增删说明**

- **保留并升格为 Part1：** D-01 fallback、D-02 plate consumer 默认关、D-04 sink 15432、D-07 A6 sink、假 running heuristic（D-05）。  
- **澄清：** 「缺 Face consumer in video」≠完全没消费代码——在 **iot-sink**；Part1 要的是可复现 **consume→process** 链，不是把 InsightFace 塞进 video。  
- **降级为「非缺口」：** `services/status` 的 `extractor`/`sorter`/`pusher` 常 null — **Python 亦如此**（`algorithm_task.py`）。  
- **划入 Part2：** InsightFace/Milvus/`face_rec.onnx`、真机 ONVIF/NVR/SIP、远程 Ceph/node、YOLO pose 模型文件。

---

## 5. 缺口表（Part1）

| ID | 域 | Python 锚点 | Java 现状 | 差距 | 建议包 | 优先级 |
|----|----|-------------|-----------|------|--------|--------|
| G-01 | Alert | `_fallback_persist_on_kafka_failure` | ~~`fallbackPersistOnKafkaFailure`~~ **已移除（CP-1 PASS）** | Part1 禁用兜底；Kafka 失败诚实失败 | CP-1 | P0 ✓ |
| G-02 | Matching consume | sink/VIDEO process 链路 | **CP-2 PASS** — sink consumers → gateway process; plate hit/miss; face bypass | **CP-2 PASS** | CP-2 | P0 ✓ |
| G-03 | Post-process / sink | `post_process_sink_client.py` | Client 已有；sink **15432 + :48092** + `enqueue_ok=true` | **CP-3 PASS** | CP-3 | P0 ✓ |
| G-04 | Snap schedule | `init_all_tasks` | **CP-4 PASS** — `listEnabled` fix + boot schedules 10/10 enabled ids | **CP-4 PASS** | CP-4 | P1 ✓ |
| G-05 | Algo status | `services/status` + 真进程 | **CP-5 PASS** — no DB-only fake running; legacy null fields documented | **CP-5 PASS** | CP-5 | P1 ✓ |
| G-06 | Patrol | `patrol.py` | **CP-6 PASS** — main-path semantics + SSE + honest validation | **CP-6 PASS** | CP-6 | P2 ✓ |
| G-07 | AudioTalk | `audio_talk.py` | `AudioTalkService` | 启停/capabilities 证据 | CP-7 | P2 |
| G-08 | GB28181 code | `gb28181_*` / camera | `Gb28181SourceSupport` / Sync | 源解析+同步 API 代码证据（无真机要求） | CP-8 | P2 |
| G-09 | FlightHub + directory | `flighthub_*` / directory routes | **CP-9 PASS** — config/live honest fail + directory key fields | **CP-9 PASS** | CP-9 | P2 ✓ |
| G-10 | Boot daemons | `run.py` 后台块 | 多个 `*Scheduler` | 对照表 + 抽样证据 | CP-10 | P2 |

---

## 6. 进度（波次 0）

| 项 | 状态 |
|----|------|
| Part1/Part2 分类 + 零 Fallback 纪律 | **已文档化** |
| CP 任务包索引 + briefs | **已建立** |
| **CP-1** 告警 Kafka fallback 清除 | **PASS** — `logs/cp-1-no-fallback.json` |
| **CP-3** iot-sink 15432 + enqueue | **PASS** — `logs/cp-3-sink-enqueue.json` |
| **CP-2** matching consume→process | **PASS** — `logs/cp-2-matching-consume.json` |
| **CP-4** snap scheduler init_all_tasks | **PASS** — `logs/cp-4-snap-scheduler.json` |
| **CP-5** services/status honesty | **PASS** — `logs/cp-5-services-status.json` |
| **CP-9** FlightHub + directory | **PASS** — `logs/cp-9-flighthub-directory.json` |
| CP-6…CP-8, CP-10 | **待 W4/W5**（W3 complete；CP-9 ✓） |
| 功能实现 / 长联调 / FR-B / COMPLETE / 删 Python | **禁止** |
