# VIDEO Python → Java — HANDOFF

> **话术：** CODE-PARITY 波次 0 + **CP-12（2026-08-12）**：Part1 完美收口必做项行为 PASS（U4 template→`notifyUsers` 已证）；U8 可选 SKIPPED；Python 仍为对照，禁止删除。  
> **阶段 0/1 已落地；阶段 2 A-series 已关闭。** **Part1 CODE-PARITY** CP-1…CP-12 PASS（必做）；Part2 引擎另令。  
> **禁止 COMPLETE / 禁止 FR-B46+ / 禁止删 main Python VIDEO。**

## 1. 一句话目标

在**不重写 RUNTIME / ffmpeg / 流媒体 / AI**、**不自研 Kafka/MinIO/Nacos/网关**的前提下，让 Java `DEVICE/iot-video`（`video-server`）在**本机完整栈**上功能等价替代 Python VIDEO，然后才允许从仓库移除 Python VIDEO。

## 2. 完成定义（不可降级）

**仅当本机完整栈上，Java 已等价承担 Python VIDEO 的关键能力后，才允许从仓库移除 Python VIDEO。**

**进度 = 功能等价**，不是 certify / 矩阵 / local artifact 数量。

**不是：**

- Java 进程能起来 / 少数 API 200  
- Phase 0/1/2/3 CERTIFY 全绿 / keys-matrix 刷绿  
- 15～30 分钟 observe  
- 服务改名 + 归档 `_retired_python_video` + 话术 COMPLETE  
- 「等 prod / 缺线上环境」叙事（**唯一环境 = 本机**）

**禁止：** 归档或删除 `F:/acme` @ `main` 上的 `VIDEO/`（Python Oracle）。分支上 `_retired_python_video` 只是副本，**不等于 Python 已退役**。

执行方案：[`PLAN_FULL_REPLACEMENT.md`](./PLAN_FULL_REPLACEMENT.md)。商业默认：[`PHASE0_DEFAULTS.md`](./PHASE0_DEFAULTS.md)。本机验收阻塞：[`CUTOVER_BLOCKERS.md`](./CUTOVER_BLOCKERS.md)。

## 3. 门禁角色

| 机制 | 角色 |
|------|------|
| 薄烟雾 `certify --phase 0` | **防回归可选**（建议 `--spring.profiles.active=mini`）；**不算进度** |
| Phase 1/2/3 CERTIFY / 矩阵刷绿 | **不作为进度** |
| 长观察 | **不算 PASS** |
| 本机完整栈验收 | **唯一进度口径**（对标 Python） |

## 4. Oracle / Candidate（禁止颠倒）

| 角色 | 位置 |
|------|------|
| **Oracle / 功能标准** | `F:/acme` @ `main` 的 `VIDEO/`（Python，必须能作对照） |
| **Candidate** | `F:/acme/.worktrees/video-java` @ `feat/video-java` 的 `DEVICE/iot-video`（`video-server`） |
| 副本（非 Oracle） | worktree 内 `VIDEO/_retired_python_video/` — **不能**当「Python 已退役」 |

对照 = Python；Java 是被对齐的一方。

## 5. 强制工作方式

1. **本机完整栈验收驱动**（Kafka / MinIO / Nacos / 网关 = 现成外部依赖，只挂不重写）。  
2. **Oracle 只读：** 不为图方便改 Python 业务语义；禁止删 main `VIDEO/`。  
3. **禁止 FR-B46+ / keys-matrix / field-matrix / POST 样本刷绿。**  
4. **日常启动 profile = `local`（商业默认）**；捷径仅 `mini` 或显式 env。  
5. **禁止 COMPLETE**，直至本机完整栈功能等价。

## 6. 范围速查

**In：** `/video/**`（经网关 `/admin-api/video/**`）契约与行为等价；关键后台守护。  

**Out：** 自研 Kafka/MinIO/Nacos/网关；C++ RUNTIME 改写成 Java；自研 InsightFace/Paddle/Milvus。

## 7. 阅读清单

1. [CODE_PARITY_BACKLOG.md](./CODE_PARITY_BACKLOG.md) — **Part1 唯一进度表 + 零 Fallback 纪律**  
2. [DEP_ENGINE_BACKLOG.md](./DEP_ENGINE_BACKLOG.md) — **Part2 依赖/引擎只读清单**  
3. [CODE_PARITY_PACKS.md](./CODE_PARITY_PACKS.md) — **CP-1…CP-10 任务包**  
4. [PHASE0_DEFAULTS.md](./PHASE0_DEFAULTS.md) / [PHASE1_STACK.md](./PHASE1_STACK.md) / [PHASE2_MAINPATH.md](./PHASE2_MAINPATH.md)  
5. [CUTOVER_BLOCKERS.md](./CUTOVER_BLOCKERS.md) / [FULL_REPLACEMENT_GAP.md](./FULL_REPLACEMENT_GAP.md)  
6. `F:/acme/VIDEO/`（Oracle）+ Candidate controllers  
7. `.superpowers/sdd/CODE_PARITY_INDEX.md`

## 8. 现状摘要（CODE-PARITY 波次 0 — 2026-08-11）

- **阶段 2 A-series 已关闭**（A1–A5 PASS；A6 ⛔缺 sink；A7 ⛔缺 Milvus/InsightFace）。证据见 [PHASE2_MAINPATH.md](./PHASE2_MAINPATH.md)。  
- **CP-1 PASS（W1）：** 已移除 `AlertHookService.fallbackPersistOnKafkaFailure`；Kafka 失败 → API `code=500`，无 `direct_persist` 成功兜底。证据：`logs/cp-1-no-fallback.json`、`.superpowers/sdd/briefs/cp-1-report.md`。  
- **Part1 纪律：** 商业 `local` **零 Fallback**（告警路径已收口；严于 Python `_fallback_persist_on_kafka_failure`）。  
- **CP-3 PASS（W2-first）：** `iot-sink` PG **15432**、`:48092` 可复现启动、`enqueue_ok=true`（无 stub）。证据：`logs/cp-3-sink-enqueue.json`、`.superpowers/sdd/briefs/cp-3-report.md`。
- **CP-2 PASS（W2-second）：** matching consume→process via **iot-sink** `PlateMatchingConsumer` / `FaceMatchingConsumer` → gateway `/matching/process`；plate hit/miss DB；face honest `bypassed`。证据：`logs/cp-2-matching-consume.json`、`.superpowers/sdd/briefs/cp-2-report.md`。
- **CP-5 PASS（W3）：** 移除 `resolveServiceStatus` DB-only 假 `running` heuristic；`extractor`/`sorter`/`pusher=null` 与 Python 同形。证据：`logs/cp-5-services-status.json`、`.superpowers/sdd/briefs/cp-5-report.md`。
- **CP-4 PASS（W3）：** `initAllTasks` ↔ Python `init_all_tasks`；修复 `listEnabled` pusher join 启动崩溃；DB 10 启用任务全部入调度；缺 RTSP/源 → 诚实 `status=1`。证据：`logs/cp-4-snap-scheduler.json`、`.superpowers/sdd/briefs/cp-4-report.md`。
- **CP-9 PASS（W4）：** FlightHub config 11 字段可读；缺凭证 `live-stream/start` → `code=400` 诚实失败；directory 树/详情/monitor-tree/CRUD 关键字段与共享 DB 可对。证据：`logs/cp-9-flighthub-directory.json`、`.superpowers/sdd/briefs/cp-9-report.md`。
- **CP-6 PASS（W4）：** patrol main-path create→start→stats/events/stop 与 Python 关键语义对齐；26-key session + stats 扩展；SSE initial progress；stop HTTP/code parity；`countAlive` 会话上限。证据：`logs/cp-6-patrol.json`、`.superpowers/sdd/briefs/cp-6-report.md`。
- **CP-7 PASS（W4）：** AudioTalk capabilities/start/stop/health HTTP+code 与 Python 对齐；缺设备 400/404 诚实；fixture 无 IP → capabilities `supported=false`、start HTTP 500 `success=false`。证据：`logs/cp-7-audiotalk.json`、`.superpowers/sdd/briefs/cp-7-report.md`。
- **CP-8 PASS（W4）：** `Gb28181SourceResolver` + fixture map + sync payload + virtual device ensure；WVP 不可达时 `resolved_source=null` 诚实失败。证据：`logs/cp-8-gb28181-code.json`、`.superpowers/sdd/briefs/cp-8-report.md`。
- **CP-10 PASS（W5）：** `run.py` 后台块 ↔ Java `*Scheduler`/AutoStart/Janitor 对照表；抽样 view-forward auto-resume（4/4）、space cleanup、media janitor、snap init（CP-4 交叉）。证据：`logs/cp-10-boot-daemons.json`、`.superpowers/sdd/briefs/cp-10-report.md`。
- **CP-11 PASS（W6）：** 深对齐清理 T1–T12（证据多为 compile；**superseded by CP-12**）。证据：`logs/cp-11-*.json`、`.superpowers/sdd/briefs/cp-11-report.md`。
- **CP-12 PASS（W7）：** 完美收口必做 U1–U7+U9 行为重证；**U4 PASS**（template-only → Kafka `shouldNotify` + `notifyUsers`；message API mock + `MESSAGE_SERVICE_URL`）。U8 optional SKIPPED。证据：`logs/cp-12-u*.json`、`.superpowers/sdd/briefs/cp-12-report.md`。
- **Part1 必做项已收口**；**非** COMPLETE / **非** 删 Python；Part2 引擎另令。
- **禁止：** COMPLETE、FR-B、矩阵刷绿、删 main Python、「等线上」、用 mini/direct/stub 冒充 Part1。

## 9. 下一步（等令）

1. **Part2 引擎** — InsightFace/Milvus/RUNTIME 真机/模型安装；见 [DEP_ENGINE_BACKLOG.md](./DEP_ENGINE_BACKLOG.md)。  
2. （可选）Boot SRS auto `fix_srs.sh`（U8）；或启动真实 `message-server`（yaml 已对齐 15432/16379）替换 mock。  
3. Python Oracle 仍保留；**禁止删除**。

## 10. 历史约束

栈、`{code,msg,data}`、共用 DB、不升 Boot 3 等仍有效。  
**已作废：** CLOSE COMPLETE、整域 migrated、用 certify/矩阵当进度、等 prod 叙事。
