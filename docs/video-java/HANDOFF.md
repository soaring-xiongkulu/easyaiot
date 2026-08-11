# VIDEO Python → Java — HANDOFF

> **阶段 0 已落地：** 规矩与商业默认已切换；完整替换进行中；Python 仍为对照，禁止删除。  
> **禁止 COMPLETE / 禁止 FR-B46+ 本地取证流水线。**

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

1. [PHASE0_DEFAULTS.md](./PHASE0_DEFAULTS.md) — **商业默认**  
2. [CUTOVER_BLOCKERS.md](./CUTOVER_BLOCKERS.md) — **本机验收阻塞**  
3. [FULL_REPLACEMENT_GAP.md](./FULL_REPLACEMENT_GAP.md)  
4. [PLAN_FULL_REPLACEMENT.md](./PLAN_FULL_REPLACEMENT.md)  
5. `F:/acme/VIDEO/`（Oracle）+ Candidate controllers

## 8. 现状摘要（阶段 0）

- **话术：** 阶段 0：规矩与商业默认已切换；完整替换进行中；Python 仍为对照，禁止删除。  
- **HTTP 契约面：** 14 前缀 inventory diff≈0（历史）。  
- **默认配置：** `local` / `application.yaml` / `VideoProperties` 已切商业默认（Kafka / 真 enqueue / MinIO on）；捷径仅 `mini`。见 [PHASE0_DEFAULTS.md](./PHASE0_DEFAULTS.md)。  
- **禁止：** COMPLETE、FR-B46+、矩阵刷绿、删 main Python VIDEO、「等线上」叙事。

## 9. 下一步（阶段 1 — 须另令）

本机完整栈验收（起/挂 Nacos、Kafka、MinIO、网关），按 [CUTOVER_BLOCKERS.md](./CUTOVER_BLOCKERS.md) 逐项对标 Python。**未经下一令不要启动阶段 1。**

## 10. 历史约束

栈、`{code,msg,data}`、共用 DB、不升 Boot 3 等仍有效。  
**已作废：** CLOSE COMPLETE、整域 migrated、用 certify/矩阵当进度、等 prod 叙事。
