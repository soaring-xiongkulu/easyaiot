# CODE-PARITY Part1 深对齐清理包（CP-11）

> **发给主 Agent 的一次性执行包。**  
> **话术：** CODE-PARITY Part1（CP-1…CP-10）包门卡已收口；本包清理「可代码复刻但仍未对齐」的深层 gap；Part2 引擎另令；Python 仍为对照，禁止删除。  
> **工作树：** `F:/acme/.worktrees/video-java` @ `feat/video-java`  
> **Oracle：** `F:/acme/VIDEO/`（只读，禁止改业务语义、禁止删）  
> **Candidate：** `DEVICE/iot-video` + `DEVICE/iot-sink`

---

## 0. 全局约束（强制）

1. **Leaf worker only：** 禁止嵌套 `Task` / 禁止再派子代理。主 Agent 自己改代码、自测、写证据与报告。  
2. **零 Fallback：** `profile=local` 上禁止用 stub/direct/mini/假成功冒充 PASS。  
3. **禁止 COMPLETE / 禁止删 `VIDEO/` / 禁止 FR-B 矩阵刷绿。**  
4. **禁止 Part2：** 不装 InsightFace/Milvus/模型；不接真 SIP/ONVIF/司空账号冒充本包完成。  
5. **对照纪律：** 以 Python 行为为准；仅当文档已声明「严于 Python」（如 Kafka 失败不落库）时保持 Java 更严。  
6. **证据：** 每项改动写入 `logs/cp-11-*.json`；总报告 `.superpowers/sdd/briefs/cp-11-report.md`；更新 `CODE_PARITY_INDEX.md` / `CODE_PARITY_BACKLOG.md` / `HANDOFF.md`。  
7. **执行顺序：** 严格按下文 **T1 → T12**（有依赖）。可同文件内连做，但不得跳过 T1–T3 先做边角。  
8. **验收口径：** 不是「Controller 200」，而是 **与 Python 关键语义一致** + 失败诚实。

### Oracle / Candidate 根路径

| 角色 | 根 |
|------|----|
| Python | `F:/acme/VIDEO/` |
| Java video | `F:/acme/.worktrees/video-java/DEVICE/iot-video/` |
| Java sink | `F:/acme/.worktrees/video-java/DEVICE/iot-sink/` |

下文 Java 路径均相对 `iot-video-biz/src/main/java/com/basiclab/iot/video/`（除非标明 iot-sink）。

---

## 1. 背景（为何还要做本包）

CP-1…CP-10 按各包 Done when 已 PASS，但门卡偏「路径/错误码/调度骨架」。连读后仍有一批 **纯 Java 可复刻** 的断链：

- 告警 Kafka **通知载荷**缺失 → 下游永远不通知  
- 告警后编排 **不触发 face/plate matching**  
- sink enqueue 在无 KafkaTemplate 时仍 HTTP 成功  
- FlightHub 失败丢 `data`、AudioTalk 固定端口、GB28181 缺 alternate/属性、directory 缺隐式 sync、boot 缺 auto_enroll reset / NVR 修复等  

本包目标：把这些 **一次性清干净**，使 Part1「能代码替换的」真正接近可替换；仍不宣称可删 Python。

---

## 2. 任务总表

| ID | 标题 | 优先级 | 依赖 |
|----|------|--------|------|
| **T1** | 告警 Kafka 完整通知消息构建 | P0 | — |
| **T2** | AlertPostOrchestrator 触发 face/plate matching | P0 | T1 后或并行（不同文件） |
| **T3** | iot-sink enqueue 无 Kafka 时诚实失败 | P0 | — |
| **T4** | FlightHub 失败响应回填 `data` | P0 | — |
| **T5** | AudioTalk 动态 RTP 端口 + 降噪落地 | P0 | — |
| **T6** | GB28181 alternate pull + sync 通道属性 | P0 | — |
| **T7** | Directory list/devices 隐式 sync + 空间级联 | P1 | T6 后更稳 |
| **T8** | Boot：auto_enroll reset + NVR repair | P0 | — |
| **T9** | Boot：SRS 自检 +（可选）IP 在线监控 | P1 | T8 后 |
| **T10** | CP-5 去掉 start 预种心跳；consumer 互斥 | P1 | — |
| **T11** | Patrol SSE 编码核实；关机钩子；silent fallback 扫尾 | P2 | — |
| **T12** | 证据汇总 + 文档收口 | — | T1–T11 |

---

## T1 — 告警 Kafka 完整通知消息（P0）

### 问题
Java 只发 `buildMinimal`，`shouldNotify` **写死 `false`**，`notifyUsers/notifyMethods/channels` 恒 null。Python 有配置时走完整 builder，按渠道/用户计算 `shouldNotify`。结果：Kafka 通了，**通知链实质断裂**。

### 位置

| 侧 | 路径 |
|----|------|
| **坏（Java）** | `…/service/AlertKafkaMessageBuilder.java` L50–56：`shouldNotify=false`；`…/service/AlertHookService.java` 仅调用 `buildMinimal`（约 L76） |
| **好（Python）** | `VIDEO/app/services/alert_hook_service.py`：`_query_alert_notification_config`；`_build_notification_message_for_kafka`（约 L873–877 调用；L1133–1226 构建 `shouldNotify`） |

### 怎么改

1. 在 Java 增加与 Python 对等的 **通知配置查询**（同库表/字段：告警事件任务上的通知渠道、用户、模板等——以 Python `_query_alert_notification_config` 为准，逐字段移植）。  
2. 在 `AlertKafkaMessageBuilder` 新增 `buildNotificationMessage(...)`（或扩展现有 builder）：  
   - 填充 `channels` / `notifyMethods` / `notifyUsers`  
   - `shouldNotify = has_channels && (has_users || has_userless)`（对齐 Python L1133–1138）  
   - 保留 `faceDetectionEnabled` / `plateDetectionEnabled`  
3. `AlertHookService.sendViaKafka`：有通知配置 → 用完整消息；无配置 → 可保留 minimal（与 Python「无配置走 minimal」一致）。  
4. **不要**恢复 Kafka 失败后的 `direct_persist` 成功兜底（Part1 故意严于 Python）。

### Done when
- 有通知配置的任务：发出的 Kafka JSON 中 `shouldNotify` 可为 `true`，且 channels/users 非空（与 DB 一致）。  
- 无配置：仍可 minimal + `shouldNotify=false`。  
- 证据：`logs/cp-11-t1-alert-notify.json`（含消息字段摘录，可脱敏）。

### Out
不测真短信/邮件投递；不改 iot-sink 消费通知的业务（若 sink 另查库，至少保证消息字段与 Python 同形）。

---

## T2 — 告警后编排触发 face/plate matching（P0）

### 问题
Python `run_post_alert_orchestration` 在 `needs_matching` 时加载告警图并调用 `_try_face_matching` / `_try_plate_matching`（capture → publish）。  
Java `AlertPostOrchestratorService` **只**做 post-process enqueue，全文无人脸/车牌匹配触发 → **匹配上游断链**（CP-2 只证明「有人 publish 后能消费」，不证明告警后会 publish）。

### 位置

| 侧 | 路径 |
|----|------|
| **坏（Java）** | `…/service/AlertPostOrchestratorService.java`（依赖仅 `PostProcessService` + `PostProcessSinkClient`；`runPostAlertOrchestration` 约 L62–83 只 enqueue） |
| **好（Python）** | `VIDEO/app/services/alert_post_orchestrator.py` L320–347：`needs_matching` → `_try_face_matching` / `_try_plate_matching`；并读同文件内 `_try_*` 与 capture worker 逻辑 |

相关 Java 已有能力（复用，勿重造）：
- `FaceMatchingService` / `PlateMatchingService` 的 publish  
- capture / library matching 相关 service（以 Python `_try_*` 调用链为准定位）

### 怎么改

1. 对照 Python：实现 `needs_matching` 判定（任务开关：face/plate detection 等，字段名对齐）。  
2. 能加载告警图时：分别尝试 face / plate matching 入队或直接 publish（**行为对齐 Python**，包括跳过条件、日志、失败不拖垮 post-process）。  
3. 引擎缺失时：允许后续 process 侧 `bypassed`（Part2）；本任务要求的是 **publish/触发路径存在**，不得静默整段删掉。  
4. 编排异常：去掉空 `catch`；至少 `log.warn/error`（顺手修 `AlertHookService` 里编排空 catch）。

### Done when
- 构造/使用带 matching 开关的算法任务 + 告警 hook：日志或审计证明尝试 face/plate publish（或明确 skip 原因）。  
- 证据：`logs/cp-11-t2-post-matching.json`。  
- **不得**靠 `use-direct-process=true`。

### Out
不要求 InsightFace/Milvus 命中（Part2）。

---

## T3 — iot-sink enqueue 诚实失败（P0）

### 问题
`PostProcessServiceImpl.publishKafka`：`iotKafkaTemplate == null` 时仅 warn 并 return；`PostProcessController.enqueue` 仍 `CommonResult.success(true)` → VIDEO 以为入队成功（**假绿**）。

### 位置

| 侧 | 路径 |
|----|------|
| **坏** | `DEVICE/iot-sink/iot-sink-biz/.../service/impl/PostProcessServiceImpl.java` L204–208；`.../controller/PostProcessController.java` L27–29 |
| **对照 VIDEO 客户端** | `…/service/PostProcessSinkClient.java`（非 2xx / code!=0 → false） |

### 怎么改

1. `publishKafka`：template null 或 send 失败 → **抛业务异常**（或返回失败结果），禁止静默成功。  
2. Controller：失败映射为 `CommonResult` 错误（非 success）；保证 VIDEO 客户端 `enqueue_ok=false`。  
3. 可选加固：`KafkaTemplate.send` 等待 ack（或明确 document 异步风险）；至少异常路径要失败。  
4. 回归：Kafka 正常时 CP-3 路径仍 `enqueue_ok=true`。

### Done when
- 模拟/构造 KafkaTemplate 不可用（或测试钩子）：HTTP 非成功，VIDEO 侧 `enqueue_ok=false`。  
- 证据：`logs/cp-11-t3-sink-enqueue-fail.json`。

---

## T4 — FlightHub 失败响应回填 `data`（P0）

### 问题
Python 409/502 把 `provider/url_type/suggestion/raw` 放进响应 `data`。  
Java `CameraController` 失败走 `VideoApiResponse.error(code,msg)` → **`data=null`**；`CameraFlighthubService.failure()` 细节在 `payload` 键，Controller 未回填。

### 位置

| 侧 | 路径 |
|----|------|
| **坏** | `…/controller/CameraController.java` 约 L218–222；`…/domain/vo/VideoApiResponse.java` L39–45（error 置 data=null）；`…/service/camera/CameraFlighthubService.java` `failure()` 约 L217–226（`payload` 键） |
| **好** | `VIDEO/app/blueprints/camera.py` 约 L894–909 |

### 怎么改

1. Controller 失败分支：从 service 的 `payload`（或统一改成 `data`）填入 `VideoApiResponse` 的 `data`。  
2. 可新增 `VideoApiResponse.error(code, msg, data)` 重载，避免到处 set。  
3. 字段对齐：`provider` / `url_type` / `suggestion` / `raw`。  
4. 缺凭证 400、成功路径回归不破坏。

### Done when
- 无凭证/错误 provider：响应 `code` 对，且 `data` 含 suggestion 等（与 Python 同形）。  
- 证据：`logs/cp-11-t4-flighthub-data.json`。

---

## T5 — AudioTalk 动态端口 + 降噪（P0）

### 问题
1. `new DatagramSocket(5000)` 硬编码 → 多会话互斥/失败。  
2. `noise_suppression` / `echo_cancellation` 只回显；`pcmToG711` 仅 volumeGain；Python `AudioSender` 有阈值降噪。

### 位置

| 侧 | 路径 |
|----|------|
| **坏** | `…/service/talk/AudioTalkSession.java` L81（`DatagramSocket(5000)`）；L134–146（`pcmToG711`） |
| **好** | `VIDEO/app/services/audio_talk_service_onvif.py` 约 L316–320（`noise_threshold=500`）；RTP/SETUP 端口分配逻辑（同文件/相关） |

### 怎么改

1. **动态绑定：** `new DatagramSocket(0)` 或从端口池取偶端口；SETUP `client_port` 用实际本地端口与 port+1。  
2. **降噪：** 在 PCM 转 G.711 前，若 `noiseSuppression==true`，对齐 Python：`abs(sample) < 500 → 0`（Int16 little-endian）。  
3. `echo_cancellation`：若 Python 也基本是声明式，保持声明 + 文档一致即可；不要假装已做 AEC。  
4. capabilities：若某能力未实现，勿报 `supported` 误导（与实现一致）。

### Done when
- 代码审查：无硬编码 5000；两会话可同时占不同端口（单测或短验）。  
- 开 `noise_suppression` 时 PCM 路径有阈值处理。  
- 证据：`logs/cp-11-t5-audiotalk.json`（可含端口分配日志）。  

### Out
真机 ONVIF DESCRIBE/SETUP/PLAY 联调 = Part2；本任务是代码正确性。

---

## T6 — GB28181 alternate pull + 通道属性（P0）

### 问题
1. Python 有 `resolve_gb28181_alternate_pull_url`（OpenCV RTMP 失败时可降级 RTSP）；Java **无**。  
2. Python sync 写 `ptz_type/direction_type/.../resolution`；Java `upsertGbDevice` 只写位置+流地址。

### 位置

| 侧 | 路径 |
|----|------|
| **好（Python alternate）** | `VIDEO/app/utils/gb28181_source.py` L315–334+ |
| **好（Python attrs）** | `VIDEO/app/services/gb28181_sync_service.py`：`_CHANNEL_ATTR_KEYS` L265–311；`_upsert_gb_device(..., attributes=...)` 约 L486–490 |
| **坏（Java）** | `…/service/camera/Gb28181SourceResolver.java`（无 alternate）；`…/service/camera/Gb28181SyncService.java` `upsertGbDevice` 约 L334–388 |

### 怎么改

1. 在 `Gb28181SourceResolver`（或并列工具类）移植 `resolveGb28181AlternatePullUrl`，尊重 env `GB28181_OPENCV_RTMP_FALLBACK_RTSP`（默认开）。  
2. 在拉流/预览失败降级路径挂上该 API（对照 Python 谁调用它，就挂到 Java 对等调用点，常见于 hardware/preview）。  
3. Sync：移植 `_extract_channel_attributes` / `_apply_gb_attributes`；`Device` 实体/表已有列则 set，无列则先确认 schema（与 Python 同库 `iot-video20`）。  
4. WVP 不可达：保持诚实 null/stats（勿假成功）。

### Done when
- fixture/单元：alternate 在 RTMP→RTSP 条件返回非空。  
- sync 后 DB 通道行可见属性字段（有源数据时）或代码路径可测。  
- 证据：`logs/cp-11-t6-gb28181.json`。

### Out
真 WVP/SIP 设备联调 = Part2。

---

## T7 — Directory 隐式 sync + 空间级联（P1）

### 问题
| 行为 | Python | Java |
|------|--------|------|
| `GET /directory/list` | `ensure_directory_layout` + **非严格 GB sync** | `listTree()` 仅 `ensureDefault` |
| `GET /directory/{id}/devices` | 默认分组 sync + `ensure_device_spaces` | 都不做 |
| 移设备 | `sync_device_spaces_to_directory` | 只改 `directory_id` |
| 更新目录 snap/record_save_time | 级联空间 | 只改目录行 |

### 位置

| 侧 | 路径 |
|----|------|
| **坏** | `…/service/camera/CameraDirectoryService.java` `listTree` L32–35；devices/move/update 相关方法 |
| **好** | `VIDEO/app/blueprints/camera.py` 约 L2509–2513（list 前 sync）；devices / move / update 同文件对应路由 |

已有可复用：`Gb28181SyncService.syncFromWvp(strict=false)`；查找 Java 是否已有 `ensureDeviceSpaces` / `SpaceSaveTimeSupport`（清理包里提过未接入目录更新）。

### 怎么改

1. `listTree()`：ensureDefault 后调用非严格 GB sync（失败 log.warn，不阻断列表——对齐 Python）。  
2. `listDevices(dirId)`：默认分组时 sync；调用 `ensure_device_spaces` 等价。  
3. 移动设备：改 directory 后 sync spaces。  
4. 更新 save_time：级联到下属空间（对齐 Python）。  
5. `monitor-tree` 已有 skip_sync 的保持兼容。

### Done when
- 证据说明 list 触发 sync（日志计数即可）；移设备/改 save_time 有 DB 或日志旁证。  
- `logs/cp-11-t7-directory.json`。

---

## T8 — Boot：auto_enroll reset + NVR repair（P0）

### 问题
1. Python 重启将 face/plate `is_running=True` 批量置 false（不自动恢复）；Java 仅 API stop，**无 boot reset** → 进程挂死后 UI 假 running。  
2. Python `_start_search` **不是** ONVIF 搜索，而是 `_init_all_cameras` → `repair_nvr_channel_links` + IP 监控登记。CP-10 报告误称 ONVIF——本任务按真实语义做。

### 位置

| 侧 | 路径 |
|----|------|
| **好（reset）** | `VIDEO/run.py` L1448–1454 |
| **好（NVR）** | `VIDEO/app/services/camera_service.py`：`_start_search` L876–891；`repair_nvr_channel_links`；`_init_all_cameras` |
| **缺（Java）** | 无 `ApplicationReady` 批量 reset；`FaceLibraryService.stopAutoEnroll` 仅按 library；需新增 Scheduler |

### 怎么改

1. 新增 `AutoEnrollBootResetScheduler`（或并入现有 boot runner）：`ApplicationReadyEvent` 上  
   `UPDATE … SET is_running=false WHERE is_running=true`（face + plate 表），打日志计数。  
2. 新增 boot 调用 `repairNvrChannelLinks()`（从 Python 移植逻辑到已有 Camera 服务或新建 `NvrLinkRepairService`）。  
3. 受 `video.skip-background-tasks` 门控。  
4. 修正文档：CP-10 M-04 注释改为「NVR repair + online monitor」，删「ONVIF search thread」误称。

### Done when
- 启动日志可见 reset 计数与 NVR repair 计数（可为 0）。  
- 证据：`logs/cp-11-t8-boot-reset-nvr.json`（可截 boot log）。

---

## T9 — Boot：SRS 自检 + 可选 IP 监控（P1）

### 问题
- Python `maybe_fix_srs_on_startup`；Java 无 boot hook。  
- Python `IpReachabilityMonitor` 周期探测；Java 仅有启发式 `resolveOnline`，无对等守护。

### 位置

| 侧 | 路径 |
|----|------|
| SRS | `VIDEO/run.py` L1008–1012；`VIDEO/app/services/srs_container_guard_service.py` |
| IP | `VIDEO/app/utils/ip_utils.py` `IpReachabilityMonitor`；`camera_service._add_online_monitor` |

### 怎么改

1. SRS：移植检测逻辑为 `ApplicationReady`；尊重 `SRS_AUTO_FIX_ON_START`；容器内跳过；失败诚实日志，**不要**假报 healthy。  
2. IP 监控（可选但建议做）：登记设备 IP，周期更新在线状态；注意 Python 对部分 RTSP 已弱化 ICMP——**对齐弱化策略**，避免假离线。  
3. 门控：`skip-background-tasks`。

### Done when
- boot log 有 SRS 检查结果行；IP monitor 启动行（若做）。  
- `logs/cp-11-t9-boot-srs-ip.json`。

### Out
深度 Docker/Ceph 运维 = Part2。

---

## T10 — status 预种心跳 + plate consumer 互斥（P1）

### 问题
1. Java algorithm `start` 后立刻 `updateHeartbeat(NOW())` → 外杀进程后 ≤60s 仍可能 `status=running`；Python 本地 start **不**预种 HB。  
2. 若 `plate-matching-consumer-enabled=true` 且 sink 同时消费 → 双 group 重复 process。

### 位置

| 侧 | 路径 |
|----|------|
| 心跳 | `…/service/AlgorithmTaskLifecycleService.java`（`start` / `updateRunState` / `updateHeartbeat`）；对照 Python start 不写 HB |
| Consumer | `…/config/VideoProperties.java` Matching；`PlateMatchingKafkaConsumerRunner`；sink `PlateMatchingConsumer` |

### 怎么改

1. 去掉 start 时的预种心跳（或仅 remote 场景保留并文档化）；让 HB 只来自真实 `/heartbeat/*` 或进程保活。  
2. 互斥：local 默认保持 video plate consumer=false；若启用，强制与 sink **同 group id** 或启动时检测 sink 在线则拒绝启用 video consumer（二选一，推荐 **同 group** 或 **配置互斥断言**）。  
3. 回归 CP-5：杀进程后 status 尽快 `stopped`（不等 60s 假 running）。

### Done when
- 证据：`logs/cp-11-t10-status-consumer.json`（杀进程后 status；配置互斥说明）。

---

## T11 — 扫尾加固（P2）

按优先级尽量做完：

| 项 | 位置 | 改法 |
|----|------|------|
| Patrol SSE 双重 JSON | `PatrolProgressHub` / SSE emitter | 核实：若对 `data` 先 `writeValueAsString` 再交给会再序列化的 API，改为传对象或 raw |  
| 关机钩子 | stream-forward / algorithm `*Supervisor` | 确认 `@PreDestroy` 杀子进程，对齐 `safe_shutdown_daemons` |  
| Alert 统计 silent 0 | `AlertService.getDashboardStatistics` | catch 后勿伪装全 0；返回错误或显式 degraded |  
| Snap 缺设备文案/计数 | `SnapTaskCaptureService` / `recordExecutionResult` | 对齐 Python「关联设备或空间不存在」且不++ total |  
| Snap restart | `SnapTaskService.restart` | 对齐：保留 is_enabled，仅 enabled 才 schedule |  
| 编排空 catch | `AlertHookService` | 打日志（若 T2 未做） |

证据可合并：`logs/cp-11-t11-hardening.json`。

---

## T12 — 收口（必须）

1. 汇总证据索引写入 `.superpowers/sdd/briefs/cp-11-report.md`（每项 PASS/缺口/文件/commit）。  
2. 更新：
   - `.superpowers/sdd/CODE_PARITY_INDEX.md`（新增 CP-11 行）  
   - `docs/video-java/CODE_PARITY_BACKLOG.md`（G-A1… 等标状态）  
   - `docs/video-java/HANDOFF.md`（下一焦点：Part2 引擎；**仍禁止删 Python**）  
3. 修正 CP-10 文档中 M-04「ONVIF search」误称。  
4. **禁止**在报告写 COMPLETE / Ready to delete Python。

---

## 3. 明确不在本包（Part2）

- InsightFace / Milvus / `face_rec.onnx` / YOLO / OCR 模型质量  
- RUNTIME 二进制真拉起与推理效果  
- 真机 ONVIF/NVR/SIP、真 FlightHub token  
- 巡检 worker 从 Python 脚本 **重写成纯 Java**（本包只要求控制面正确；worker 仍可拉脚本）  
- 远程 node / Ceph  

---

## 4. 建议提交策略

- 按 T1 / T2 / T3… 逻辑提交（或 T1–T3 一提、T4–T6 一提），message 聚焦 **why**。  
- 每提后跑相关短验，证据落 `logs/cp-11-*.json`。  
- 不 push 除非用户另令。

---

## 5. 主 Agent 开场提示词（可直接粘贴）

```text
执行 docs/video-java/CODE_PARITY_DEEP_GAP_PACK.md（CP-11 深对齐清理包）。

约束：
- 工作树 F:/acme/.worktrees/video-java；Oracle F:/acme/VIDEO 只读
- Leaf only：禁止嵌套 Task；禁止 COMPLETE；禁止删 Python；禁止 Part2 装引擎
- local 零 Fallback；按 T1→T12 顺序清理
- 每项按文档「位置 + 怎么改」落地；证据 logs/cp-11-*.json；报告 .superpowers/sdd/briefs/cp-11-report.md
- 更新 CODE_PARITY_INDEX / BACKLOG / HANDOFF；修正 CP-10 M-04 ONVIF 误称

先读完整包文档再改代码。做完给出每项 PASS/证据路径/主提交哈希。
```

---

## 6. Brief 镜像

同内容索引见：`.superpowers/sdd/briefs/cp-11-deep-parity-brief.md`（指向本文件为 SSOT）。
