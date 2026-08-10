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

**当前 oracle tip（写稿时）：** `4f93baf` — 以 Phase 0 打 tag 时的 SHA 为准并写回本文件。

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

1. [STACK.md](./STACK.md) — 技术栈与模块结构（**已锁定草案，待审**）
2. [PLAN.md](./PLAN.md) — 分期与门禁
3. [EXECUTION.md](./EXECUTION.md) — 纪律
4. [testbed/README.md](./testbed/README.md) — 等价场
5. `F:/acme/VIDEO/run.py` — 蓝图注册、actuator、后台任务
6. `VIDEO/app/services/algorithm_task_daemon.py` / `algorithm_task_launcher_service.py` / `runtime_config_service.py` / `alert_hook_service.py`
7. `docs/runtime-parity/reports/04-video-absorb-surface.md` — VIDEO vs RUNTIME 吸收面
8. `DEVICE/iot-gateway/.../application.yaml` — `video-admin-api` → `lb://video-server`
9. `DEVICE/iot-sink` — face/plate/post-process 回调与 Kafka 主题
10. `docs/runtime-parity/EXECUTION.md` + `HANDOFF.md` — 方法论参照（**勿复用其门禁目录**）

## 7. 现状摘要

- Python VIDEO：`app/` 约 4–5 万 LOC；14 Blueprint；多 Process 守护。
- 帧内推理已 cpp-only；Python 算法三服务已从主线删除。
- 网关已转发 video；**无**现成 `iot-video` Java 模块。
- Java 侧已有：Boot 2.7.18 / Java 21 / Nacos / Kafka / MinIO / iot-node 部署 RUNTIME·ffmpeg / iot-sink 匹配链。

## 8. 你的下一步（审查通过前）

1. 审 [STACK.md](./STACK.md) 选型与模块布局。  
2. 审 [PLAN.md](./PLAN.md) P0 门禁与双跑切流。  
3. **批准前不建业务代码骨架以外的大规模实现**（Phase 0 仅允许：打 oracle tag、空模块+health、测试场目录与 doctor 脚本草案）。  
4. 审查意见回写本 HANDOFF「决议」节。

## 9. 决议（审查填写）

| 项 | 状态 |
|----|------|
| 栈与模块布局 | ⬜ 待审 |
| P0 范围 | ⬜ 待审 |
| 双跑服务名 / 切流 | ⬜ 待审 |
| Oracle tag SHA | ⬜ Phase 0 填写 |
