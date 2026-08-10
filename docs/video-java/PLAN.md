# VIDEO Python → Java — PLAN

> **For reviewers / agentic workers:** 本文件是分期与门禁计划，不是编码许可证。审查通过前不进入大规模业务搬迁。  
> **REQUIRED 阅读:** [STACK.md](./STACK.md)、[HANDOFF.md](./HANDOFF.md)、[testbed/README.md](./testbed/README.md)。

**Goal:** Java `iot-video` 与 Python VIDEO 在标准等价场上行为一致后，切网关并退役 Python VIDEO。

**Architecture:** Oracle=Python VIDEO；Candidate=`DEVICE/iot-video`；ProcessBuilder 编排既有 RUNTIME/ffmpeg；帧后走 Kafka/HTTP 与 iot-sink 既有契约。

**Tech Stack:** 见 [STACK.md](./STACK.md)（Java 21、Boot 2.7.18、Maven、Nacos、MyBatis-Plus、Kafka、MinIO、ProcessSupervisor）。

---

## 0. 仓库与基线

| 项 | 决定 |
|----|------|
| 分支 | `feat/video-java` |
| Worktree | `F:/acme/.worktrees/video-java`（创建于审查通过后） |
| 模块 | `DEVICE/iot-video/{iot-video-api,iot-video-biz}` |
| Oracle tag | `video-java-oracle-baseline` @ Phase 0 的 `main` tip |
| 文档根 | `docs/video-java/` |
| 工具根 | `tools/video_java/` |

---

## 1. 等价方法论（PASS 定义）

### 1.1 流程（同构 runtime-parity）

```text
固定夹具/用例 → 录 Python golden → 启 Java 回放同一夹具
→ 分层 diff → 红清单 → 只修 candidate → 再比 → certify
```

### 1.2 建议 diff 层（可机器判定）

| 层 ID | 内容 | 典型工件 |
|-------|------|----------|
| `api` | HTTP 状态、code/msg、关键字段 | `api.json` |
| `lifecycle` | 任务 start/stop、进程存活、DB run_status/heartbeat | `lifecycle.json` |
| `alarm` | hook 入站→Kafka/DB 告警字段 | `alarm.json` / `kafka.json` |
| `ini` | 生成的 RUNTIME ini 关键键（允许路径绝对差用归一化） | `runtime.ini.norm` |
| `media`（P1+） | 转推存在性 / 码流探测摘要 | `stream.json` |
| `side_effect`（P1+） | MinIO 对象键前缀、后处理 enqueue 次数 | `effects.json` |

阈值文件：`testdata/video-java/thresholds.json`（待建）。  
报告：`docs/video-java/gates/PHASE_N_GATE.md` + `CERTIFY_STATUS.md`。

### 1.3 何谓 PASS

- 该 Phase 清单内 **P0 cases 全绿**（及约定 P1）  
- **无未解释红项**；豁免必须写入 `gates/EXEMPTIONS.md` 且有产品/编排签字栏  
- doctor 脚本通过（manifest、夹具、服务可达）

### 1.4 用例从哪来

1. **契约回归：** 从现网/OpenAPI/蓝图整理的最小 HTTP 序列（优先 algorithm + alert）。  
2. **吸收面：** `docs/runtime-parity/reports/04-video-absorb-surface.md` 的 CAP-*（Hook/心跳/匹配触发等）。  
3. **业务冒烟：** 单设备 + 单 cpp 任务 + 测试媒体（可复用 `testdata/runtime-parity/media` 获取方式，**拷贝策略走 safe_fsops / 下载脚本，不混 runtime-parity gate**）。

---

## 2. 分期与门禁

### Phase -1：基线与纪律（审查通过后立即）

- [ ] 打 tag `video-java-oracle-baseline`
- [ ] 创建 worktree + 空 `iot-video` 模块注册进 `DEVICE/pom.xml`
- [ ] `tools/video_java/doctor.py`（或 .ps1）检查目录/Java/ VIDEO oracle 可达
- [ ] 门禁文件：`gates/PHASE_-1_GATE.md` PASS

**Exit：** 能 `mvn -pl iot-video/iot-video-biz -am package` 空壳 + doctor PASS。

### Phase 0：最小闭环（替换证明）

**范围：**

| 能力 | 端点 / 行为 |
|------|-------------|
| Health | `GET /actuator/health`（DB） |
| 任务查询 | 最少 `GET` list/detail 只读（便于夹具） |
| 启停 RUNTIME | `POST .../task/{id}/start|stop`（仅 cpp） |
| ini 生成 | 关键键与 Python 归一化后一致 |
| 心跳 | `POST /video/algorithm/heartbeat/realtime`（及 patrol 若夹具需要） |
| Alert hook | `POST /video/alert/hook` → Kafka/DB 与 Python 同学段（mini 直连落库路径需双边可比） |
| 进程监督 | 意外退出重启语义有 case |

**不做：** 全量 camera CRUD、ffmpeg 转推、face/plate 库、远程 node 全路径（可 stub 为「仅本机」并在豁免登记）。

**门禁：** `gates/PHASE_0_GATE.md` — certify 用例表全绿。  
**Exit：** 「Java 能拉起 RUNTIME + hook/心跳双边可比」有报告证据。

### Phase 1：设备观看面 + 推流编排

- Camera 查询/启停观看转推（ffmpeg ProcessBuilder，编码器回退对齐 Python `ffmpeg_compat`）
- Stream forward 本机路径
- Nacos 双跑稳定；网关 `video-server-java` 路由文档化
- 健康恢复定时器对齐

**门禁：** media/lifecycle 层 cases。

### Phase 2：帧后平台面

- Face/Plate matching publish/process 与 sink 契约
- Post-process enqueue 触发（告警后编排，补吸收面缺口）
- Snap/Record/Playback 主路径
- Patrol / regions / media_hook

**门禁：** alarm + side_effect + 选定 API 面。

### Phase 3：切流与退役

- 网关切到 Java `video-server`；Python 下线 runbook
- 回滚演练一次（记录耗时与步骤）
- Python VIDEO 退役波次（safe_fsops dry-run→execute；**另门禁**）
- 文档与 CERTIFY 终态 PASS

---

## 3. 双跑、切流、回滚

### 3.1 双跑

| 项 | 策略 |
|----|------|
| 服务名 | Java：`video-server-java`；Python：`video-server` |
| 网关 | 保留现路由给 Python；新增 `video-java-admin-api` → `lb://video-server-java`（路径可 `/admin-api/video-java/**` 或同源不同 Header/端口仅测试用） |
| DB | 共用 `iot-video20`；**禁止**双边 auto_start 抢同一 `is_enabled` 任务 — certify 使用专用 task_id / 或一侧关 `VIDEO_SKIP_BACKGROUND_TASKS` |
| 端口 | Java `48096`；Python `6000` |

### 3.2 切流

1. Phase 2/3 certify 绿  
2. 停 Python auto_start；Java 接管 enabled 任务  
3. 改 Java `spring.application.name=video-server`（或改网关 uri）  
4. 下线 Python 注册  
5. 观察心跳/告警 15–30min

### 3.3 回滚

1. 网关指回 `lb://video-server`（Python）  
2. 停 Java 实例  
3. Python `auto_start_all_tasks`  
4. 写入事故记录到 `gates/ROLLBACK_LOG.md`

---

## 4. 数据模型

- **沿用** 现表（`algorithm_task`, `device`, `alert`, …）。  
- P0 不迁库、不改主键。  
- 若 Java 需新列：增量迁移 + oracle Python 忽略未知列（SQLAlchemy）或双写兼容说明。  
- iot-sink / iot-message 已读 `iot-video20`：切流后继续有效。

---

## 5. 进程模型要点

见 [STACK.md §3.3](./STACK.md)。远程：复用 iot-node workload（`algorithm_realtime|snap|patrol|stream_forward|post_process`）；P0 可仅本机并登记豁免。

---

## 6. 风险与非目标

| 风险 | 缓解 |
|------|------|
| 面宽导致「先写完再测」 | 分期门禁；P0 极窄 |
| 双跑抢任务 | 夹具隔离 + 关一侧后台 |
| Hook 字段 cpp/python 历史差 | 以吸收面契约 + DB 补齐规则为 golden |
| 估时膨胀或「3 小时」幻觉 | case 点数 × 闭环；retrospective 禁止类推 |
| 借机升 Boot 3 | STACK 明确否决 |
| 用旁路程序冒充实装 | 所有能力必须进 video-java certify |

**非目标：** 重写 RUNTIME；自研媒体服务器；自研深度学习栈；并入 AI/SAM 训练。

---

## 7. 估时方法（不写空想人月）

| 输入 | 用法 |
|------|------|
| Phase 用例数 | 每 case：录制 + Java 实装 + 修红 + 复核 |
| 模块切片 | controller/service/process 可并行但门禁串行 |
| 历史参照 | runtime-parity：**规划人月曾严重高估**；本任务**禁止**复制「2～4 人月」或「3 小时」 |

**方案阶段不给出虚假总人月。** Phase 0 启动后由编排在 `CERTIFY_STATUS.md` 维护「本周 case 燃尽」，再反推日历。

---

## 8. Phase 0 任务清单（审查通过后执行）

### Task A: Oracle tag + worktree

- [ ] `git tag video-java-oracle-baseline`
- [ ] `git worktree add ... feat/video-java`

### Task B: 空模块

- [ ] 创建 `DEVICE/iot-video` api+biz  
- [ ] Nacos 名 `video-server-java`，端口 48096  
- [ ] `/actuator/health` 返回 UP（可先无 DB）

### Task C: 测试场骨架

- [ ] `testdata/video-java/manifest.json` 至少 3 个 P0 case id  
- [ ] `tools/video_java/doctor.py`  
- [ ] `gates/PHASE_-1_GATE.md`

### Task D: 停 — 等 Phase -1 PASS 再开 Phase 0 业务代码

---

## 9. 成功画像（审查用）

- [x] 方法论与 runtime-parity 同构（本文 + testbed）  
- [x] 边界清晰：Java VIDEO ≠ RUNTIME/媒体服务器（STACK）  
- [x] P0 能证明 RUNTIME + hook/心跳可比（§2 Phase 0）  
- [x] 切流/回滚可操作（§3）  
- [x] 估时与切片挂钩、不空喊人月（§7）  
- [x] 技术栈开题锁定（STACK）
