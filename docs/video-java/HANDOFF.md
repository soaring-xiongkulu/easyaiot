# VIDEO Python → Java — HANDOFF

> **话术：** CODE-PARITY 波次 0：Part1/Part2 清单与任务包已建立；功能实现另令；Python 仍为对照，禁止删除。  
> **阶段 0/1 已落地；阶段 2 A-series 已关闭。** **CODE-PARITY W1 CP-1 PASS**；**W2 CP-3 + CP-2 PASS**；**W3 CP-4 + CP-5 PASS**；下一步 **W4 CP-6…CP-9**。  
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
- **禁止：** COMPLETE、FR-B、矩阵刷绿、删 main Python、「等线上」、用 mini/direct/stub 冒充 Part1。

## 9. 下一步（等令）

1. **W4：CP-6 ∥ CP-7 ∥ CP-8 ∥ CP-9** — 见 [CODE_PARITY_PACKS.md](./CODE_PARITY_PACKS.md)。**W3 complete**（CP-4 + CP-5 ✓）。  
2. Part2 引擎（InsightFace/Milvus/真机）**不开工直至 Part1 代码路径收口**。  
3. Python Oracle 仍保留；**禁止删除**。

## 10. 历史约束

栈、`{code,msg,data}`、共用 DB、不升 Boot 3 等仍有效。  
**已作废：** CLOSE COMPLETE、整域 migrated、用 certify/矩阵当进度、等 prod 叙事。
