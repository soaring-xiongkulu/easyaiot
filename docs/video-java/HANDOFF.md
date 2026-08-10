# VIDEO Python → Java — HANDOFF

> 给后续 Agent / 开发者的编排说明。**先计划审查，再 Phase 0。** 禁止未过门禁就切网关默认流量。

## 1. 一句话目标

在**不重写 RUNTIME / ffmpeg / 流媒体 / AI**的前提下，用与 **runtime-parity 同构**的 oracle/candidate/红清单/certify 方法，把 Python VIDEO 编排层替换为 Java（`DEVICE/iot-video`），等价全绿后再切流并退役 Python VIDEO。

## 2. 完成定义（不可降级）

**不是**「Java 进程能起来 / 几个 API 200」。  
**必须是：** 在 `docs/video-java/testbed/` 标准等价场上，Java VIDEO 与 Python VIDEO **分层 diff 全绿**（或**显式豁免清单清空**），才允许：

1. 网关默认指向 Java `video-server`
2. 停止注册 Python VIDEO
3. 归档/删除 Python `VIDEO/` 热路径（另波次，safe_fsops 纪律）

## 3. Oracle / Candidate

| | 路径 | 分支 / Tag |
|--|------|------------|
| Oracle | `F:/acme/VIDEO`（Python Flask） | `main`；Phase 0 打 tag `video-java-oracle-baseline` |
| Candidate | `DEVICE/iot-video`（待建） | `feat/video-java` + worktree `F:/acme/.worktrees/video-java` |
| 文档 / 门禁 | `docs/video-java/` | 不与 `docs/runtime-parity/gates` 混用 |
| 工具 | `tools/video_java/`（待建） | 对标 `tools/runtime_parity/` 思想，代码独立 |

**当前 oracle tip（Phase -1 tag）：** `bfbe7457ac65c90eb49d59247a1a2706d55c677d` — tag `video-java-oracle-baseline`。

## 4. 强制工作方式

1. **先测后改：** 每个能力域先有 failing case / 红项，再实现，再双边对比。
2. **Oracle 只读：** 除录制工具与测试场夹具外，不改 Python VIDEO 业务行为「图方便」。
3. **Candidate 窄改：** Java VIDEO + 必要网关双跑路由 + 部署脚本；禁止借机大改 RUNTIME/sink/node。
4. **红清单驱动：** 只修当前红项；不做无关重构。
5. **估时：** 按 case 面与模块切片；**禁止**用 runtime-parity「约 3 小时」类推；**禁止**空喊数人月却不挂钩门禁（见 runtime-parity 工作量 retrospective）。

## 5. 范围速查

**In：** 对外 `/admin-api/video/**` 契约；任务生命周期与 ini；心跳/告警 hook；设备与媒体编排（调 ffmpeg）；人脸/车牌等平台 API 与 sink 协作；等价测试场。  

**Out：** C++ RUNTIME 改写成 Java；自研 ffmpeg/SRS/ZLM；自研 InsightFace/Paddle/Milvus 引擎；AI/SAM 训练服务并入；先大重构 Python 再迁移。

细节与栈：见 [STACK.md](./STACK.md)、[PLAN.md](./PLAN.md)。

## 6. 阅读清单（开工前）

1. [STACK.md](./STACK.md) — 技术栈与模块结构（**有条件通过，含 §9.1 约束**）
2. [PLAN.md](./PLAN.md) — 分期与门禁
3. [EXECUTION.md](./EXECUTION.md) — 纪律
4. [testbed/README.md](./testbed/README.md) — 等价场
5. `F:/acme/VIDEO/run.py` — 蓝图注册、actuator、后台任务
6. `VIDEO/app/services/algorithm_task_daemon.py` / `algorithm_task_launcher_service.py` / `runtime_config_service.py` / `alert_hook_service.py`
7. `docs/runtime-parity/reports/04-video-absorb-surface.md` — VIDEO vs RUNTIME 吸收面
8. `DEVICE/iot-gateway/.../application.yaml` — `video-admin-api` → `lb://video-server`
9. `DEVICE/iot-sink` — face/plate/post-process 回调与 Kafka 主题
10. `docs/runtime-parity/EXECUTION.md` + `HANDOFF.md` — 方法论参照（**勿复用其门禁目录**）

## 7. 现状摘要（2026-08-10 P3-S3 终态）

- **Java `iot-video`**：`DEVICE/iot-video`，Nacos `video-server`，`:48096`，Phase 0/1/2 certify PASS。
- **网关默认流量**：`video-admin-api` → `lb://video-server`（CLOSE-S2；原 P3-S1 用 `video-server-java`）。
- **Python VIDEO 热路径**：已归档至 `VIDEO/_retired_python_video/`（P3-S3，safe_fsops）；不再从 `VIDEO/run.py` 对外服务。
- **外部 oracle**：`F:/acme/VIDEO`（tag `video-java-oracle-baseline`）仍可作 parity 录制；certify 默认 `--no-record` 用 frozen golden。
- **Phase 3 门禁**：`PHASE_3_GATE` PASS；`CERTIFY_STATUS` Phase 3 PASS。

## 8. 你的下一步

**项目 video-java 迁移主线已完成（Phase 3 PASS）。** 后续仅运维项：

1. 生产/预发执行 gateway auth smoke（`PHASE_3_GATE` 项 4）与 15–30 min 观察（项 5）。
2. ~~视需要将 Java `spring.application.name` 改为 `video-server`~~ — **done (CLOSE-S2)**。
3. 新 parity 需求：用 archived oracle 或 Java-only smoke；勿恢复 in-repo `VIDEO/app` 热路径除非 rollback runbook。

## 9. 决议（审查填写）

> **审查轮次：** 2026-08-10（side-chat 审 STACK → PLAN → HANDOFF）  
> **总评：** **有条件通过** — 方法论与边界正确；与 DEVICE BOM 对齐值得肯定。按下列决议修订/执行，即可开 Phase -1。

| 项 | 状态 |
|----|------|
| 栈与模块布局 | ✅ **通过** — Java 21 + Boot 2.7.18 + Cloud 2021.0.5 + 新建 `DEVICE/iot-video`（api+biz）；不升 Boot 3；ProcessBuilder 编排 RUNTIME/ffmpeg |
| P0 范围 | ✅ **通过** — health + 任务启停/ini/心跳/alert hook + 进程监督；camera/ffmpeg 转推放 P1；远程 node P0 可豁免并登记 |
| 双跑服务名 / 切流 | ✅ **通过（附约束）** — 双跑名 `video-server-java` / 端口 `48096`；见下方硬约束 |
| Oracle tag SHA | ⬜ Phase -1/0 打 tag 时写回（勿沿用写稿时的 `4f93baf` 口头值） |
| 独立门禁 | ✅ **通过** — `docs/video-java` + `tools/video_java`；禁止混进 runtime-parity gates |
| 估时 | ✅ **通过** — case 燃尽；禁止「3 小时」类推与空人月 |

### 9.1 硬约束（必须写进 STACK/PLAN 或 Phase -1 门禁，否则易翻车）

1. **对外响应外壳：** 锁定 **兼容 Python `{code,msg,data}`**（STACK §4 已写）。Phase -1 须落地「与 `CommonResult` 冲突时的适配层」设计一句（Filter/Advice/显式 VO），避免第一天就被 iot-common-web 习惯带偏。
2. **P0 certify 基址：** **默认真连** `http://127.0.0.1:48096`（及 Python `:6000`）；**不依赖**先改 WEB 代理。网关 `/admin-api/video-java/**` 仅作可选联通，不作 P0 阻塞。
3. **切流与生产名：** CLOSE-S2 完成 — Java `spring.application.name` 为 `video-server`，网关 `lb://video-server`；Python 已归档，无 Nacos 抢名风险。
4. **共用 `iot-video20`：** 同意首期共用；certify **必须**专用 `task_id` / 关一侧 `auto_start` / `VIDEO_SKIP_BACKGROUND_TASKS`（PLAN 已有）。Alarm 层禁止 Python/Java **并行**对同一 hook 夹具双写同一告警行——录制与回放串行或分 case 隔离。
5. **本地 mini / 无 Nacos：** DEVICE 栈默认 Nacos；Phase -1 须提供 **`local`/`mini` profile**（可关 discovery 或 soft-fail），对齐现网 VIDEO 无 Nacos 仍可跑的开发形态。
6. **鉴权：** P0 对内直连可暂宽；若走网关必须与现网 token/`tenant-id` 行为对齐。流票据等 P1 再钉，但不得在切流后出现「Java 裸奔、Python 校验」的不一致而不进门禁。

### 9.2 赞同一并保留的设计

- 与 `iot-parent` BOM / `iot-common-*` / sink·node·file 模式对齐（本审查最重要加分项）
- Oracle/candidate + 红清单 + 独立 certify（同构 runtime-parity）
- 下游不动：RUNTIME、ffmpeg、SRS/ZLM、AI、匹配算法不进 VIDEO 重写
- 人脸/车牌：ORT Java 或阶段性旁路，且必须进 video-java 门禁

### 9.3 下一步

**Phase 3 PASS（2026-08-10）。** Python VIDEO 热路径已归档；网关在 Java。运维 smoke/观察见 `gates/PHASE_3_GATE.md` 项 4–5。
