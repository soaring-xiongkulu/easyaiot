# VIDEO Python → Java — HANDOFF

> 给后续 Agent / 开发者的编排说明。  
> **现行主线 = 完整功能替换（Phase FR）**，不是切片 certify COMPLETE。

## 1. 一句话目标

在**不重写 RUNTIME / ffmpeg / 流媒体 / AI**的前提下，把 Python VIDEO 编排层 **按功能面** 替换为 Java（`DEVICE/iot-video`），使 WEB/网关使用的 `/admin-api/video/**` 能力与 Python 一致，再退役 Python。

## 2. 完成定义（不可降级）

**不是：**

- Java 进程能起来 / 少数 API 200  
- Phase 0/1/2/3 CERTIFY 全绿  
- 15～30 分钟 observe  
- 服务改名 + Python 归档 + 话术 COMPLETE  
- `BLUEPRINT_GAP` 标 `migrated`（那只表示曾有切片 case）

**必须是：**

[`FULL_REPLACEMENT_GAP.md`](./FULL_REPLACEMENT_GAP.md) 中 **P0/P1（及产品未永久豁免的 P2）** 域行全部 ✅（路由 + 关键后台任务），路由差收敛；仅此时允许宣布「完整替换完成」并退役 Python。

执行方案：[`PLAN_FULL_REPLACEMENT.md`](./PLAN_FULL_REPLACEMENT.md)。

## 3. 门禁角色（换角色，不整锅端）

| 机制 | 角色 |
|------|------|
| 薄烟雾 `certify --phase 0` | **防回归**（health / 真 RUNTIME / hook success）；合入建议跑 |
| Phase 1/2/3 全绿 | **不作为进度**；历史档案 |
| 长观察 | **仅切流/预发 runbook**；开发期不算 PASS |
| 扩面验证 | 契约测试 + 路由清单 diff；**不为每个 API 录双边 golden** |

## 4. Oracle / Candidate

| | 路径 | 说明 |
|--|------|------|
| Oracle（只读对照） | `VIDEO/_retired_python_video/` | 按域读 blueprint/service；缺对照可临时恢复，**禁止再归档当完成** |
| 外部 oracle（可选） | `F:/acme/VIDEO` @ `video-java-oracle-baseline` | 录制/对照备用 |
| Candidate | `DEVICE/iot-video/` | `feat/video-java` @ worktree `F:/acme/.worktrees/video-java` |
| 文档 | `docs/video-java/` | 进度只看缺口表 |
| 工具 | `tools/video_java/` | 薄烟雾 +（待补）路由 diff / 契约抽检 |

**Oracle tip：** `bfbe7457ac65c90eb49d59247a1a2706d55c677d` — tag `video-java-oracle-baseline`。

## 5. 强制工作方式

1. **缺口表驱动：** 打开域缺口 → 读 Python → 补 Java 同前缀 → 短契约 → 勾选缺口表。  
2. **Oracle 只读：** 不为「图方便」改 Python 业务语义。  
3. **Candidate 按域扩面：** 禁止再用 CLOSE/EVID/长观察堆文档代替路由覆盖。  
4. **EX-\* = backlog**（完整替换下），除非产品书面永久豁免并改缺口表。  
5. **估时：** 按域路由数与服务复杂度；禁止用「certify 全绿」冒充燃尽。

## 6. 范围速查

**In：** 全部对外 `/video/**`（经网关 `/admin-api/video/**`）契约面；任务/设备/告警/媒体/巡检/对讲等 Python 已有能力；启动后台自愈与清理等关键守护。  

**Out：** C++ RUNTIME 改写成 Java；自研 ffmpeg/SRS/ZLM；自研 InsightFace/Paddle/Milvus；AI/SAM 训练并入。

## 7. 阅读清单（开工前）

1. [PLAN_FULL_REPLACEMENT.md](./PLAN_FULL_REPLACEMENT.md) — **现行方案**  
2. [FULL_REPLACEMENT_GAP.md](./FULL_REPLACEMENT_GAP.md) — **唯一进度表**  
3. [STACK.md](./STACK.md)  
4. [EXECUTION.md](./EXECUTION.md)  
5. `VIDEO/_retired_python_video/run.py` + `app/blueprints/` + services  
6. `DEVICE/iot-video/iot-video-biz/.../controller`  
7. 历史切片（只读）：[PLAN.md](./PLAN.md)、`gates/PHASE_*_GATE.md`

## 8. 现状摘要（2026-08-10 FR-W4）

- **HTTP 路由：** `route_inventory` 14 前缀 **Py≈259 / Java≈259 / diff=0**（`FR-W4` 全量核对）。
- **行为：** MinIO/ONVIF/YOLO/InsightFace/Milvus/SSE 真流等仍为 **mini 桩**；见 `FULL_REPLACEMENT_GAP.md` §2–§4。
- **脚手架：** Phase -1～0 骨架 + FR-W1～W3 路由/后台扩面已完成。
- **EVID：** 真 RUNTIME / alert success 等证据已抬升；**EVID 轮次结束**。
- **Phase 3/CLOSE：** 改名、归档、网关指向 = 运维动作，**≠ 功能完整替换**。
- **项目状态：** **FR HTTP 面已齐 / 行为桩仍存 — 禁止 COMPLETE**。
- **网关：** 现已指向 Java 名；行为桩未清前，**不得**认为生产功能已安全切完。

## 9. 你的下一步

按 [`PLAN_FULL_REPLACEMENT.md`](./PLAN_FULL_REPLACEMENT.md) §5 行为/后台 backlog：

1. MinIO 真同步/清理（snap/record/media）
2. ONVIF/NVR/扫描真连接（camera、audio_talk）
3. InsightFace/Paddle/Milvus 推理或产品旁路决策
4. snap_task 调度 `init_all_tasks`
5. post-process 真 sink；远程 node（EX-REMOTE-NODE）
6. 全量契约回归 + 回滚演练 → 才允许 COMPLETE

## 10. 历史审查决议（切片期，仍有效的工程约束）

栈、`{code,msg,data}`、共用 DB、不升 Boot 3、独立门禁目录等约束仍有效。  
**已作废的完成叙事：** CLOSE-S4 COMPLETE、整域 migrated、用 Phase 1/2/3 全绿当进度。
