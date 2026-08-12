# Part2 W2 Gate-Fix — 巡检会话功能等价验收

> **发给主 Agent 的执行包。**  
> **背景：** W1 Pose ORT、W3 YAML 后处理主路径门控可过；**W2 仅接线 PASS，Done when 未齐（PARTIAL）**——证据多为手写 ini 直拉 RUNTIME 冒烟，缺少真实会话 start→进度/心跳→stop。  
> **SSOT 方案：** `docs/video-java/PART2_FINAL_PLAN.md` W2  
> **工作树：** `F:/acme/.worktrees/video-java`  
> **Oracle：** `F:/acme/VIDEO/` 只读  

---

## 0. 约束

1. **Leaf only**；禁止嵌套 Task。  
2. **禁止 COMPLETE / 禁止删 VIDEO / 禁止重写 RUNTIME 推理。**  
3. 只修 **W2 验收与缺口**；勿大改 W1/W3（除非回归坏了）。  
4. 证据必须行为级；禁止仅 compile；栈/设备不足标 **BLOCKED** 并写清缺什么。  
5. 交付：`logs/p2-final-w2-patrol.json`（覆盖旧冒烟或另存 `…-session.json` 并在报告标明 supersedes）；更新 `part2-final-w1-w3-report.md` 或新建 `part2-w2-gate-fix-report.md`；更新 `PART2_FINAL_PLAN.md` §7 看板。

---

## 1. 目标（Done when）

相对 `PART2_FINAL_PLAN` W2：

| # | 要求 |
|---|------|
| 1 | 经 **Java 巡检会话 API**（或等价 `PatrolSessionService`）完成 **create → start → 观测进度/心跳 → stop** |
| 2 | start 后子进程为 **RUNTIME**（非 `python` / 非 `run_deploy.py`） |
| 3 | 心跳到达 Java（DB 或日志可证）；进度可查（stats/SSE/DB progress） |
| 4 | ini 由 **`PatrolRuntimeIniService` / 会话路径** 生成，非仅手写冒烟 ini |
| 5 | **告警：** 至少开一条可解释路径，或书面 **Out**（本包不测告警）并在证据注明 |
| 6 | **rotate / hybrid：** 各至少静态 ini 或短跑一条，**或** 书面标 Out（仅保证 pool）——须在报告显式选择 |

通过后看板 W2 方可标 **PASS**。

---

## 2. 建议步骤

1. 读现有：`PatrolSupervisor`、`PatrolSessionService`、`PatrolRuntimeIniService`、旧证据 `p2-final-w2-patrol.json`（标 superseded 原因）。  
2. 准备最小 fixture：≥1 可解析源（文件源/测试 RTSP 即可）；模型路径与 RUNTIME 本机可用。  
3. 走会话 API 或同进程调用 `createSession` + `startSession`；记录 PID/命令行含 RUNTIME。  
4. 等 ≥1 次心跳或 progress 更新；再 `stopSession`；确认进程退出。  
5. 写证据 JSON：`evidence_type=session_behavioral`；含 session_id、时间线、heartbeat 摘录、进程命令行、ini 路径（须落在生成目录）。  
6. 更新报告与 `PART2_FINAL_PLAN.md` §7：W2 PASS 或 BLOCKED（诚实）。

---

## 3. 明确不做

- EDGE / 远程推流 / 真机联调 / 删 VIDEO / COMPLETE  
- 把检测重写进 Java  
- 为绿测伪造心跳日志  

---

## 4. 主 Agent 提示词（粘贴）

```text
执行 docs/video-java/PART2_W2_GATE_FIX.md（巡检会话功能等价验收）。

背景：门控判定 W2 PARTIAL——已改挂 RUNTIME，但证据是手写 ini 直拉冒烟，缺少会话 start→进度/心跳→stop。

强制：
- 工作树 F:/acme/.worktrees/video-java；Leaf only；禁止 COMPLETE；禁止删 VIDEO；禁止重写 RUNTIME 推理
- 用真实巡检会话路径（API 或 PatrolSessionService）验收；进程须为 RUNTIME
- 证据覆盖旧冒烟或另存并注明 supersedes；更新 PART2_FINAL_PLAN 看板
- rotate/hybrid 测或书面 Out；告警开或书面 Out

做完给出：PASS|BLOCKED|PARTIAL、证据路径、提交哈希。
```
