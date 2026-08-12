# CODE-PARITY Part1 完美收口包（CP-12）

> **发给主 Agent 的一次性执行包。**  
> **话术：** CODE-PARITY Part1 深对齐（CP-11）后仍未达完美；本包清 **P0 硬阻塞 + 关键 P1**，以行为证据收口；Part2 引擎另令；Python 仍为对照，禁止删除。  
> **工作树：** `F:/acme/.worktrees/video-java` @ `feat/video-java`  
> **Oracle：** `F:/acme/VIDEO/`（只读）  
> **Candidate：** `DEVICE/iot-video` + `DEVICE/iot-sink`  
> **前置终检：** 侧栏审计结论 — Part1 完美约 70–75%；CP-11 总评应视为 PARTIAL（证据多为 compile）。

---

## 0. 全局约束（强制）

1. **Leaf only：** 禁止嵌套 `Task` / 禁止再派子代理。主 Agent 自改、自测、写证据与报告。  
2. **零 Fallback：** `profile=local`；禁止 mini/direct/stub 当 PASS。  
3. **禁止 COMPLETE / 禁止删 `VIDEO/` / 禁止 FR-B 刷绿 / 禁止 Part2 装引擎。**  
4. **对照：** Python 行为为准；Kafka 失败不落库等「严于 Python」纪律保持。  
5. **证据必须是行为级：** HTTP/Kafka/DB/boot 日志摘录；**禁止**仅 `mvn compile` + 文件列表冒充 PASS（CP-11 教训）。本机栈 DOWN 时该项标 `BLOCKED`，不得写 PASS。  
6. **顺序：** 严格 **U1 → U10**（有依赖）。  
7. **交付：** `logs/cp-12-u*.json`；`.superpowers/sdd/briefs/cp-12-report.md`；更新 INDEX / BACKLOG / HANDOFF。

### 路径约定

| 角色 | 根 |
|------|----|
| Python | `F:/acme/VIDEO/` |
| Java video | `…/DEVICE/iot-video/iot-video-biz/src/main/java/com/basiclab/iot/video/` |
| Java sink | `…/DEVICE/iot-sink/` |

---

## 1. 为何还要 CP-12

CP-11 落地了大量骨架，但终检仍发现：

| 类 | 代表 |
|----|------|
| **假跑** | Auto-enroll 只翻 `is_running`，无 tick |
| **错包** | FlightHub 409 `data` 二次包裹 |
| **死代码** | `resolveAlternatePullUrl` 零调用 |
| **通知断链** | 缺 message-template → `notify_users` |
| **假绿窗口** | sink enqueue 未等 Kafka ack |
| **证据水分** | CP-11 JSON 多为 compile 摘要 |

本包目标：把 Part1「可代码复刻」推到 **完美收口**（仍不删 Python、不做 Part2）。

---

## 2. 任务总表

| ID | 标题 | 优先级 | 依赖 |
|----|------|--------|------|
| **U1** | Auto-enroll tick（face + plate） | P0 | — |
| **U2** | FlightHub 409 `data` 扁平同形 | P0 | — |
| **U3** | GB28181 alternate 接线（或删死代码+契约） | P0 | — |
| **U4** | 通知 template → `notify_users` | P0 | — |
| **U5** | sink enqueue `future.get` ack | P1 | — |
| **U6** | Matching：无 plate_no 仍可 publish 图路径 | P1 | — |
| **U7** | 远程 start 去预种心跳；机器人渠道兜底 | P1 | — |
| **U8** | （可选）SRS `fix_srs` 自动修复钩子 | P1 | — |
| **U9** | 本机栈行为证据重跑（含 CP-11 关键项补证） | P0 | U1–U7 后 |
| **U10** | 文档收口 + 诚实总评 | — | U9 |

**本包默认必做：** U1–U7、U9–U10。  
**U8** 可做；若环境无 Docker/SRS 权限，标 `BLOCKED` 并写入报告，不挡 U10（但不得假装 PASS）。

**明确不在本包：** InsightFace/Milvus/模型命中、真机联调、Patrol worker 纯 Java 化、record/playback/media_hook 全量深验（可另开 CP-13；本包 U9 仅要求关键路径行为证据）。

---

## U1 — Auto-enroll 完整 tick（P0）

### 问题
Java `startAutoEnroll` **只** `updateRunning(true)`，无调度 → UI/DB 显示 running 但 **永不抽帧入库**（假跑）。Python 每 5s `run_auto_enroll_tick`。

### 位置

| 侧 | 路径 |
|----|------|
| **坏（Java）** | `…/service/face/FaceLibraryService.java` `startAutoEnroll` 约 L304–310；plate 对等 `PlateLibraryService`；仅有 `AutoEnrollBootResetScheduler`（reset ≠ tick） |
| **好（Python）** | `VIDEO/app/services/face_auto_enroll_service.py`：`start_auto_enroll` L99–115 → `_ensure_scheduler_job` L130–154 → `run_auto_enroll_tick` L265+ / `_tick_single_task` L174+；`plate_auto_enroll_service.py` 同构 |

### 怎么改

1. 新增 `@Scheduled(fixedDelayString=…)` 或与现有 scheduler 同风格的 `FaceAutoEnrollTickScheduler` / `PlateAutoEnrollTickScheduler`（可合并为一个服务两类任务）。  
2. 对齐 Python tick 语义：  
   - 只处理 `is_running=true`  
   - 过期 → stop + `is_running=false`  
   - 按 interval 抽帧（调用已有抓拍/硬件能力）  
   - 入库存（库条目写入；**embedding/识别质量属 Part2**，但入库记录与计数必须发生）  
   - 更新计数 / last_run 等字段（对照 Python）  
3. `startAutoEnroll`：置 running **并**确保 scheduler job 存在（对齐 `_ensure_scheduler_job`）；重置过期时间/计数若 Python 有。  
4. `stopAutoEnroll`：停标志；tick 自然跳过。  
5. 受 `video.skip-background-tasks` 门控。  
6. **禁止**仅改文档宣称「依赖外部 worker」。

### Done when
- start 后日志出现周期性 tick；过期任务被停。  
- 无引擎时：允许入库失败/跳过检测，但 **不得** 只亮 running 零 tick。  
- 证据：`logs/cp-12-u1-auto-enroll.json`（含 boot/tick 日志行、DB `is_running` 前后）。

### Out
InsightFace 向量质量、Milvus（Part2）。

---

## U2 — FlightHub 409 `data` 扁平同形（P0）

### 问题
Controller 已填 `data`，但 `failure(code,msg,richMap)` 把 rich 塞进 `raw`，外层 `provider/url_type=null`，`suggestion` 变成英文 msg。Python 要求扁平 `data={provider,url_type,suggestion,raw}`。

### 位置

| 侧 | 路径 |
|----|------|
| **坏** | `…/service/camera/CameraFlighthubService.java` 409 分支约 L107–120；`failure()` 约 L217–228 |
| **好** | `VIDEO/app/blueprints/camera.py` 约 L894–909 |
| Controller | `CameraController.java` 约 L217–224（保持传 payload 即可，修好 service 形状） |

### 怎么改

1. 改 `failure`：若传入已是 `{provider,url_type,suggestion,raw}` map，**直接作为 payload**，不要再包一层。  
2. 409 分支：构造扁平 map 后 `result.put("payload", flat)` 或直接返回该结构。  
3. 400/502：与 Python 对齐 `suggestion` 可为 null（不要一律用 msg 填 suggestion，除非 Python 同形）。  
4. 单测或短验：断言 JSON `data.provider` 非 null（SDK 场景）。

### Done when
- 409 响应：`data.provider` / `data.url_type` / `data.suggestion` 在顶层；`data.raw` 为上游 body。  
- 证据：`logs/cp-12-u2-flighthub-409.json`（完整响应 JSON，可脱敏 token）。

---

## U3 — GB28181 alternate 接线（P0）

### 问题
`Gb28181SourceResolver.resolveAlternatePullUrl` **有实现、零 Java 调用** = 死代码。Python 定义在 `gb28181_source.py`；实际降级常在 EDGE `run_deploy.py` OpenCV 失败路径。

### 位置

| 侧 | 路径 |
|----|------|
| **死代码** | `…/service/camera/Gb28181SourceResolver.java` `resolveAlternatePullUrl` 约 L210–258 |
| **可能挂点** | `CameraHardwareService.captureSnapshot` / 预览拉流失败路径；或 EDGE worker（若拉流不在 Java） |
| **Python** | `VIDEO/app/utils/gb28181_source.py` L315+；EDGE `run_deploy.py` 调用点 |

### 怎么改（二选一，必须显式选并写进报告）

**方案 A（推荐若 Java 有拉流/抓拍失败路径）：**  
在 OpenCV/RTMP 失败处调用 `resolveAlternatePullUrl`，成功则重试 RTSP。

**方案 B（若拉流只在 EDGE）：**  
1. 确认 EDGE 已调用 Python alternate（或改为调共享逻辑）；  
2. **删除或 `@Deprecated` 并文档声明** Java 方法非运行时路径，避免假 PASS；  
3. 在 CP-12 报告写明「执行体在 EDGE，Java 不重复接线」。

禁止：保留无调用的「已实现」却标 PASS。

### Done when
- 方案 A：失败→alternate→重试有日志/证据；或  
- 方案 B：死代码移除/标注 + EDGE 调用证据摘录。  
- 证据：`logs/cp-12-u3-gb-alternate.json`。

---

## U4 — 通知 template → `notify_users`（P0）

### 问题
channels 带 `template_id`、配置未落用户时，Python 从 MESSAGE 模板 API 抽用户；Java 不抽 → `shouldNotify` 常 false → 回退 minimal，通知链断。

### 位置

| 侧 | 路径 |
|----|------|
| **坏** | `AlertKafkaMessageBuilder.extractNotifyUsers`；`AlertNotificationConfigService`（无模板回退） |
| **好** | `VIDEO/app/services/alert_hook_service.py` L1126–1128 → `_get_notify_users_from_message_templates` L538–556；`algorithm_task_service._extract_notify_users_from_templates` |

### 怎么改

1. 移植模板用户抽取（HTTP/DB，对照 Python MESSAGE 模板接口）。  
2. `buildNotificationMessage`：config 用户空时调用模板回退，再算 `shouldNotify`。  
3. 顺带核对 `isRobotFallbackChannel`：尽量对齐 Python `_is_robot_fallback_channel`（template 元数据 / wxcp），作为 U4 子项或 U7。

### Done when
- 仅有 template_id、无 DB 用户的配置：Kafka 消息 `shouldNotify=true` 且 `notifyUsers` 非空（或与 Python 同库结果一致）。  
- 证据：`logs/cp-12-u4-notify-template.json`（消息字段摘录）。

---

## U5 — sink enqueue 等 Kafka ack（P1）

### 问题
`PostProcessServiceImpl.publishKafka`：`send` 后直接 return，无 `future.get` → HTTP 可先成功、broker 稍后失败（假绿窗口）。Alert/Matching 已等 ack。

### 位置

| 侧 | 路径 |
|----|------|
| **坏** | `DEVICE/iot-sink/.../PostProcessServiceImpl.java` `publishKafka` 约 L204–214 |
| **对照** | `AlertKafkaProducer` / `MatchingKafkaProducer` 的 `future.get(timeout)` |

### 怎么改

1. `send(...).get(timeout, unit)`；超时/异常抛出 → Controller `CommonResult.error`。  
2. timeout 与 video 侧 Kafka 发送超时同量级。  
3. 回归：Kafka 正常时 enqueue 仍成功。

### Done when
- 代码审查 + 可选：注入失败/短超时见 HTTP 错误。  
- 证据：`logs/cp-12-u5-sink-ack.json`。

---

## U6 — Matching：无 plate_no 仍可走图路径（P1）

### 问题
`AlertMatchingTriggerService.tryPlateMatching`：detections 无 `plate_no` 直接 return；Python 对帧 OCR 再 publish。`LibraryMatchingProcessor.processPlate` 本可对图 OCR。

### 位置

| 侧 | 路径 |
|----|------|
| **坏** | `…/service/AlertMatchingTriggerService.java` `tryPlateMatching` 约 L84–88 |
| **好** | `VIDEO/app/services/alert_post_orchestrator.py` + `plate_capture_queue_service.py` |
| process | `LibraryMatchingProcessor.processPlate`（已有 OCR 入口则复用） |

### 怎么改

1. **最低对齐（本包要求）：** 无 `plate_no` 时仍 publish（带 `plateImagePath`/告警图），让 process/OCR 决定；不要静默 skip。  
2. **加分：** 引入轻量 capture 队列对齐 Python（若工作量大，可先做最低对齐，报告注明完整 worker 为 follow-up）。  
3. Face：保持 publish；引擎缺失 → `bypassed`（已有）。

### Done when
- 无 plate_no 的告警编排：日志显示 plate publish 尝试（非 skip）。  
- 证据：`logs/cp-12-u6-matching-nopath.json`。  
- **不得** `use-direct-process=true`。

### Out
OCR/InsightFace 命中率（Part2）。

---

## U7 — 远程预种心跳 + 机器人渠道（P1）

### 问题
1. 本地 start 已不预种 HB；`AlgorithmRemoteDeployService` 成功后仍 `updateHeartbeat` → 远程杀进程后短暂假 running。  
2. `isRobotFallbackChannel` 弱于 Python。

### 位置

| 侧 | 路径 |
|----|------|
| 心跳 | `…/service/AlgorithmRemoteDeployService.java` 约 L108–111 |
| 机器人 | `AlertKafkaMessageBuilder.isRobotFallbackChannel`；Python `_is_robot_fallback_channel` L558–579 |

### 怎么改

1. 删除远程成功后的预种 `updateHeartbeat`（或仅在真实 heartbeat API 上报时写）。  
2. 机器人兜底对齐 template 元数据（可与 U4 合并提交）。

### Done when
- 远程 start 代码路径无预种 HB。  
- 证据：`logs/cp-12-u7-remote-hb-robot.json`（diff/日志即可）。

---

## U8 — SRS 自动修复钩子（可选 P1）

### 问题
Java `SrsStartupGuardService` 只 warn「未执行 fix_srs.sh」；Python `maybe_fix_srs_on_startup` 可修。

### 位置
- Java：`SrsStartupGuardService.java`  
- Python：`srs_container_guard_service.py`；`run.py` L1008–1010  

### 怎么改
在检测失败且 `SRS_AUTO_FIX_ON_START` 开启时调用等价脚本；容器内跳过；失败诚实日志。

### Done when
有修复尝试日志，或环境不允许时 **BLOCKED**（诚实，不 PASS）。

---

## U9 — 本机栈行为证据重跑（P0）

### 要求
在 `profile=local`、本机 PG:15432 / Kafka / 网关 / video-server / iot-sink 可用时，重跑并重写证据：

| 证据文件 | 必须包含 |
|----------|----------|
| `logs/cp-12-u1-auto-enroll.json` | tick 日志 + DB |
| `logs/cp-12-u2-flighthub-409.json` | 响应 JSON 同形 |
| `logs/cp-12-u3-gb-alternate.json` | 接线或方案 B 证明 |
| `logs/cp-12-u4-notify-template.json` | Kafka 消息字段 |
| `logs/cp-12-u5-sink-ack.json` | ack/失败路径 |
| `logs/cp-12-u6-matching-nopath.json` | publish 审计 |
| `logs/cp-12-u9-stack-smoke.json` | 汇总：告警 Kafka 成功/失败、sink enqueue_ok、matching 触发、boot reset/NVR/SRS 行 |

栈 DOWN → 对应项 `status=BLOCKED`，**禁止**写 PASS。

同时：**作废/覆盖** 仅含 compile 的旧 `logs/cp-11-t*.json` 可信度说明写入报告（可保留文件但标注 superseded）。

---

## U10 — 文档收口

1. `.superpowers/sdd/briefs/cp-12-report.md`：逐项 PASS/BLOCKED/PARTIAL + 证据路径 + commit。  
2. 更新 `CODE_PARITY_INDEX.md`（CP-12 行）。  
3. 更新 `CODE_PARITY_BACKLOG.md` / `HANDOFF.md`：  
   - 页眉改为含 CP-12  
   - **诚实总评：** 若 U1–U7+U9 全 PASS →「Part1 可复刻逻辑已完美收口；Part2 另令；禁止删 Python」  
   - 若有 BLOCKED → 「Part1 完美未完成，阻塞项=…」  
4. **禁止**写 COMPLETE / Ready to delete Python。

---

## 3. Part2 边界（禁止塞进本包当完成）

- InsightFace / Milvus / ONNX / YOLO / OCR **命中质量**  
- RUNTIME 真推理、真机 ONVIF/NVR/SIP、真司空 token  
- 远程 node 真部署、Ceph  
- Patrol worker 纯 Java 重写  
- record/playback/media_hook/forward **全量**深验（另包 CP-13）

---

## 4. 主 Agent 开场提示词（可直接粘贴）

```text
执行 docs/video-java/CODE_PARITY_PERFECT_GAP_PACK.md（CP-12 Part1 完美收口包）。

约束：
- 工作树 F:/acme/.worktrees/video-java；Oracle F:/acme/VIDEO 只读
- Leaf only：禁止嵌套 Task；禁止 COMPLETE；禁止删 Python；禁止 Part2 装引擎
- local 零 Fallback；按 U1→U10 执行（U8 可选）
- 证据必须是行为级（HTTP/Kafka/DB/boot），禁止仅 mvn compile 冒充 PASS；栈 DOWN 标 BLOCKED
- 报告 .superpowers/sdd/briefs/cp-12-report.md；更新 INDEX / BACKLOG / HANDOFF

先读完整包再改代码。做完给出每项 PASS|BLOCKED|PARTIAL、证据路径、提交哈希。
```

---

## 5. Brief 镜像

`.superpowers/sdd/briefs/cp-12-perfect-gap-brief.md` → 指向本文件为 SSOT。
