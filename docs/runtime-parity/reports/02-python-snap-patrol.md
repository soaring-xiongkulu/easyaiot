# Report: Python snap + patrol 算法执行后端

- **Agent role:** 调研 Agent（精读 `executor=python` 的 snap/patrol 子进程，对照 realtime 与 C++ RUNTIME）
- **Scope paths:**
  - `VIDEO/services/snapshot_algorithm_service/`
  - `VIDEO/services/patrol_algorithm_service/`
  - 交叉引用：`VIDEO/services/realtime_algorithm_service/`、`VIDEO/app/utils/cron_utils.py`、`RUNTIME/src/pipeline/SnapScheduler.*`、`RUNTIME/src/pipeline/PatrolScheduler.*`
- **Date:** 2026-08-09
- **Confidence:** high（主逻辑集中在 `run_deploy.py`；snap 约 2658 行、patrol 约 695 行，已逐段核对调度与输出路径）

## 1. Executive summary

Python **snap**（`snapshot_algorithm_service`）与 **patrol**（`patrol_algorithm_service`）同属 `executor=python` 算法子进程，由 `algorithm_task_launcher_service` / `patrol_session_service` 拉起，共享 VIDEO 公共库（`stream_adapter`、`algo_model_detect`、`alert_hook`、`post_process_runner` 等），但调度模型与 realtime 根本不同：**snap 长连接 + Cron 槽位抽帧**；**patrol 短连接抓帧 + 间隔/池化轮巡**。

snap 每设备独立 `buffer_streamer_worker` 维持源流，仅在 `cron_slot_for_time` 窗口内抽 1 帧入检测队列，检测完成后直接告警/入库抓拍空间（**不推 RTMP**）。支持 6 段秒级 Cron（东八区）、花屏重试、pending 超时回收、人脸/车牌匹配队列（可选）。

patrol 由单线程 `patrol_scheduler_worker` 调度，支持 **pool / rotate / hybrid** 三模式；每轮 `capture_frame` 短连拉流、预热若干帧后取 1 帧、立即 `release`。到期设备以线程池并行巡检（上限 `pool_size`），进度经 `/video/patrol/heartbeat` 上报。C++ `SnapScheduler`/`PatrolScheduler` 已存在骨架，但 Cron 精度、hybrid、抓拍空间入库、人脸/车牌链路与 Python 差距明显，等价收归需以本报告能力 ID 为验收清单。

## 2. Inventory / Findings

### 2.1 架构与进程模型

| 维度 | snap (`snapshot_algorithm_service`) | patrol (`patrol_algorithm_service`) |
|------|-------------------------------------|-------------------------------------|
| 入口 | `run_deploy.py:main` | `run_deploy.py:main` |
| 配置来源 | `TASK_ID` → `AlgorithmTask`（`task_type=snap`） | `PATROL_SESSION_ID`（`PatrolSession`）或 `TASK_ID`（`task_type=patrol`） |
| 设备列表 | `task.devices` 关联 | Session `device_ids` JSON 或 Task `devices` |
| 每设备连接 | **长连接** `open_device_stream`，独立缓流线程 | **短连接** 每次 `capture_frame` 开流→读帧→`release` |
| 检测并发 | `YOLO_WORKER_THREADS` 线程池轮询多设备 `detection_queues` | 调度线程内 `_run_patrol_batch` 每设备一线程 |
| 推流 | **无**（注释与 env 均明确不推 RTMP） | **无** |
| 心跳 | `algorithm/heartbeat/realtime`（与 realtime 同 URL，port=None） | `/video/patrol/heartbeat`（含 `progress`） |

### 2.2 能力 ID 清单

#### 与 realtime 共享（复用 CAP-*，snap/patrol 均涉及）

| ID | 说明 | snap | patrol | 主要证据 |
|----|------|------|--------|----------|
| `CAP-DECODE` | GB28181 解析、`open_device_stream`、异步 FIFO、RTSP 传输策略 | ✓ 长连 | ✓ 短连 | snap `buffer_streamer_worker`；patrol `capture_frame` |
| `CAP-MODEL-LOAD` | AI 服务拉元数据、MinIO/集群路径、YOLO/ONNX | ✓ | ✓ | `load_yolo_models` / `_load_models` |
| `CAP-GPU-SCHED` | `get_infer_device` / hash/round_robin 多卡 | ✓ | ✗ patrol YOLO 默认 cpu | snap `get_assigned_gpu_id` |
| `CAP-DETECT` | `run_model_detection` 多模型合并 | ✓ | ✓ | `yolo_detection_worker` / `_run_detection` |
| `CAP-ALERT-HOOK` | `resolve_alert_hook_url` → POST JSON | ✓ | ✓ | `send_alert_event_async` / `_send_alert` |
| `CAP-ALERT-SUPPRESS` | 设备级告警抑制间隔 | ✓ | ✓ | `last_alert_time` + `alert_event_suppress_time` |
| `CAP-ALERT-CLASS-FILTER` | `filter_detections_for_alert` | ✓（检测告警） | ✓ | snap `try_send_snapshot_detection_alert` |
| `CAP-POST-PROCESS` | `enqueue_post_process_request`（iot-sink 后处理） | ✓ | ✓ | `_finish_snapshot_detection` / `_process_patrol_device` |
| `CAP-ALERT-IMAGES` | 本地 `alert_images` 落盘 | ✓ | ✓ | `save_alert_image` / `_save_alert_image` |
| `CAP-HEARTBEAT` | 周期心跳上报 | ✓（realtime 端点） | ✓（patrol 专用端点） | `heartbeat_worker` |
| `CAP-ENV-LOAD` | `load_video_env`、`.env`、节点注入 | ✓ | ✓ | 文件头部 |
| `CAP-CONFIG-RETRY` | 配置加载失败循环重试不退出 | ✓ | ✓ | `TASK_CONFIG_RETRY_INTERVAL` |

#### snap 特有

| ID | 说明 | 证据 |
|----|------|------|
| `CAP-CRON-SNAP` | 6 段秒级 Cron、东八区槽位匹配、每槽每设备 1 帧 | `cron_utils.cron_slot_for_time`；`should_extract_frame_by_cron`；`mark_cron_slot_captured` |
| `CAP-CRON-NO-FALLBACK` | 无 Cron 时 `should_extract_frame_by_cron` 恒 true，靠循环 sleep 近似连续抽帧 | `should_extract_frame_by_cron` L1328–1329 |
| `CAP-SNAP-SPACE` | Cron 帧写入抓拍空间（MinIO / Kafka staging） | `upload_frame_to_snap_space`；`SNAP_SAVE_CRON_FRAME` |
| `CAP-SNAPSHOT-PENDING` | 入队后 pending 跟踪 + `SNAPSHOT_RESULT_MAX_WAIT_SEC` 超时清理 | `pending_snapshots`；`_cleanup_stale_pending_snapshots` |
| `CAP-DETECTION-KEEP-LATEST` | 检测队列积压丢弃旧帧保最新 Cron 帧 | `DETECTION_KEEP_LATEST`；`_enqueue_detection_frame` |
| `CAP-CRON-GRAY-SKIP` | Cron 槽位花屏跳过并在窗口内重试；预热期不判灰屏 | `is_likely_rtsp_flat_corrupt_frame`；`SNAP_CRON_SKIP_GRAY_CHECK` |
| `CAP-TRACKING` | 可选 `SimpleTracker`（Cron 帧上追踪画框） | `trackers`；`yolo_detection_worker` |
| `CAP-FACE-MATCH` | 检测告警后 `enqueue_face_capture` | `try_send_face_matching_for_frame`；`start_face_capture_workers` |
| `CAP-PLATE-MATCH` | 检测告警后 `enqueue_plate_capture` | `try_send_plate_matching_for_frame` |
| `CAP-NO-PUSH` | 无 FFmpeg 编码、无 RTMP 推流、无 overlay 叠框推流 | 全局注释 L366；无 `push_queue` |
| `CAP-SRS-CLEANUP` | 后台 SRS 录像磁盘守护（与 realtime 同套） | `srs_recording_cleanup_worker` |

#### patrol 特有

| ID | 说明 | 证据 |
|----|------|------|
| `CAP-PATROL-POOL` | 间隔到期设备批量并行，上限 `pool_size` | `patrol_scheduler_worker` pool 分支；`_run_patrol_batch` |
| `CAP-PATROL-ROTATE` | 单设备顺序轮巡，休眠 `interval/设备数` | `mode == 'rotate'` |
| `CAP-PATROL-HYBRID` | 焦点设备 `interval/2` + 背景池 `pool_size-1` | `mode == 'hybrid' and focus_id` |
| `CAP-PATROL-ONESHOT` | 短连：开流→预热 `PATROL_READ_WARMUP_FRAMES`→取帧→释放 | `capture_frame` |
| `CAP-PATROL-SNAP-UPLOAD` | 巡检帧上传抓拍空间 `source=patrol` | `upload_patrol_frame_to_snap_space`；`PATROL_SAVE_SNAP` |
| `CAP-PATROL-PROGRESS` | 每设备 `last_patrol_at/last_result/detection_count`；心跳汇总 | `device_progress`；`send_heartbeat` payload |
| `CAP-PATROL-SESSION` | `PatrolSession` 独立会话进程（`PATROL_SESSION_ID`） | `patrol_session_service`；`load_patrol_config` |
| `CAP-PATROL-DUE` | `_devices_due` 基于 UTC ISO 时间戳与 `interval_sec` | `_devices_due` |
| `CAP-PATROL-NO-TRACK` | 无追踪器、无长连接、无人脸/车牌队列 | 全文件无 tracker/face/plate worker |

### 2.3 调度模型（详述）

#### snap：Cron + 长连接多设备

```
每 device_id ──► buffer_streamer_worker（独立线程，长连接 cap）
                    │
                    ├─ 非 Cron 窗口 → 读帧丢弃（仅 _cleanup_stale_pending_snapshots）
                    │
                    └─ Cron 窗口内 → 缩放 → detection_queue.put
                                              │
                    YOLO_WORKER_THREADS 池 ────┘ 轮询各设备队列
                                              │
                                              ▼
                         追踪(可选) → 画框 → _finish_snapshot_detection
                              ├─ 有目标 + sink → post_process
                              ├─ 有目标 → alert_hook + face/plate 队列
                              └─ 始终（SNAP_SAVE_CRON_FRAME）→ snap-space
```

- **Cron 表达式**：`AlgorithmTask.cron_expression` → `normalize_cron_for_croniter`；6 段时 `second_at_beginning=True`（`cron_utils.py`）。
- **匹配窗口**：`snap_cron_match_window_seconds`，默认 floor `SNAPSHOT_CRON_WINDOW_SEC`（5s）；短周期 Cron 窗口约为间隔的 45% 且 capped（避免 `*/30` 秒级误匹配）。
- **槽位去重**：`device_last_extract_cron_time[device_id] == fire_time` 则本槽不再抽帧；成功入队后 `mark_cron_slot_captured`。
- **多设备切换**：非「轮巡切换连接」，而是**每设备并行长连接**；Cron 触发时各设备独立判槽。YOLO worker 公平轮询各 `detection_queues`。
- **无 Cron**：逻辑上每轮循环均「允许抽帧」（间隔约 `sleep(0.1)` + 读帧速率），等价于高频 fallback，与 C++ `frameSkip` 秒级间隔不同。

#### patrol：间隔 + 连接池 + 模式切换

```
patrol_scheduler_worker（单线程）
  │
  ├─ rotate:  device_list[idx] → _process_patrol_device → sleep(interval/N)
  │
  ├─ hybrid:  focus 若 due(interval/2) → 处理焦点
  │           background due(interval) → batch[:bg_pool]
  │
  └─ pool:    due_devices(interval) → batch[:pool_size] 并行线程
                    │
                    └─ _process_patrol_device
                         capture_frame（短连）
                         → optional snap upload
                         → detect → alert / post_process
```

- **到期判定**：`last_patrol_at` 为 UTC `YYYY-MM-DDTHH:MM:SSZ`；首次无记录视为 due。
- **并行度**：`pool_size`（Session/Task 默认 4，创建 Session 时 cap 16）；`hybrid` 背景池 `max(1, pool_size-1)`。
- **连接模型**：与 realtime/snap 长连相反；每轮新建 `open_device_stream`，超时 `PATROL_CONNECT_TIMEOUT_SEC`（默认 8s）。
- **多设备切换**：pool/hybrid 在同一调度周期内**同时**拉起多线程处理多台；rotate **严格串行**。

### 2.4 与 realtime 共享 vs 独有

| 能力面 | realtime | snap | patrol |
|--------|----------|------|--------|
| 长连接拉流 + 持续读帧 | ✓ 主路径 | ✓ 每设备缓流线程 | ✗ 短连 |
| RTMP/叠框推流 | ✓ | ✗ `CAP-NO-PUSH` | ✗ |
| extract_interval / overlay 分轨 | ✓ | ✗（仅 Cron/无 Cron fallback） | ✗（仅 `interval_sec`） |
| Cron 槽位抓拍 | ✗ | ✓ `CAP-CRON-SNAP` | ✗ |
| 抓拍空间入库 | ✗ | ✓ `CAP-SNAP-SPACE` | ✓ `CAP-PATROL-SNAP-UPLOAD` |
| 追踪 SimpleTracker | ✓ 连续帧 | ✓ Cron 帧上可选 | ✗ |
| 人脸/车牌匹配队列 | ✓ | ✓ | ✗ |
| GPU 多卡调度 | ✓ | ✓ | 基本 cpu |
| 巡检 pool/rotate/hybrid | ✗ | ✗ | ✓ |
| 巡检进度心跳 | ✗ | ✗ | ✓ `CAP-PATROL-PROGRESS` |
| PatrolSession 子进程 | ✗ | ✗ | ✓ |
| 任务配置热重载 | ✓ 30s worker | ✗ 仅启动加载 | ✗ 仅启动加载 |
| motion_gate 等 realtime 专有 | ✓ | ✗ | ✗ |

### 2.5 与 C++ RUNTIME 差异摘要（等价对标对象）

| 能力 | Python snap/patrol | C++ SnapScheduler / PatrolScheduler |
|------|-------------------|-------------------------------------|
| Cron | 6 段秒级 + 动态匹配窗口 + 花屏重试 | 仅分+时字段，`*/step`；槽键分钟级 `YYYYMMDDHHMM` |
| snap 连接 | 长连接 per device | 长连接 `VideoCapture` per device（对齐） |
| snap 无 Cron | 高频读帧 fallback | `frameSkip` 秒间隔 |
| snap 入库 | MinIO/Kafka 抓拍空间 | 仅告警回调，无 snap-space |
| patrol 模式 | pool / rotate / **hybrid** | pool / rotate（**无 hybrid**） |
| patrol 预热 | `PATROL_READ_WARMUP_FRAMES`（默认 3） | 固定读 5 帧再取 1 帧 |
| 模型 | YOLO + ONNX + ultralytics GPU | Yolov11ThreadPool |
| 区域过滤 | 任务级 alert_class；区域多边形在 C++ 有 | C++ `pointInRegions` |

## 3. Placement hint

| Capability ID | 建议落点 (cpp / video / both / drop) | 理由 |
|---------------|--------------------------------------|------|
| `CAP-CRON-SNAP` | cpp | 调度核心，对标 `SnapScheduler::cronDue`；须补齐 6 段秒级与 `cron_utils` 语义 |
| `CAP-SNAP-SPACE` | video | MinIO/Kafka/元数据属 VIDEO 媒体域；C++ 回调帧后由 VIDEO 入库 |
| `CAP-SNAPSHOT-PENDING` | cpp | 帧内队列与超时属执行器状态 |
| `CAP-DETECTION-KEEP-LATEST` | cpp | 检测队列策略，帧内背压 |
| `CAP-CRON-GRAY-SKIP` | both | 解码健康 cpp 判帧；槽位重试策略可与 VIDEO 告警策略对齐 |
| `CAP-NO-PUSH` | drop（对 snap/patrol） | 故意不做推流，非缺口 |
| `CAP-PATROL-POOL` | cpp | `PatrolScheduler` pool 分支已存在，对齐 `_devices_due` 语义 |
| `CAP-PATROL-ROTATE` | cpp | 已存在，对齐休眠 `interval/N` |
| `CAP-PATROL-HYBRID` | cpp | Python 独有，C++ 需新增 |
| `CAP-PATROL-ONESHOT` | cpp | 短连抓帧在 `grabOneShot`，对齐预热帧数与超时 |
| `CAP-PATROL-SNAP-UPLOAD` | video | 与 snap 共用 `patrol_snap_upload` / staging |
| `CAP-PATROL-PROGRESS` | video | 心跳 API、`patrol_progress_hub` 已在 VIDEO |
| `CAP-PATROL-SESSION` | video | 会话 CRUD、子进程编排非 RUNTIME 职责 |
| `CAP-FACE-MATCH` / `CAP-PLATE-MATCH` | video | 帧后队列服务在 VIDEO；C++ 仅透传检测结果 |
| `CAP-POST-PROCESS` | video | 已有 `post_process_runner` |
| `CAP-TRACKING`（snap Cron） | cpp 或 both | snap 低频帧追踪可 cpp 简化；高保真可保留 VIDEO |
| `CAP-ALERT-HOOK` 等共享面 | both | 契约在 VIDEO，触发时机在 cpp |

## 4. Gaps / Risks

1. **Cron 语义不等价**：C++ 仅分/时且分钟级去重；Python 东八区 6 段秒级 + 动态窗口 + 槽内花屏重试。直接切换会导致抓拍时刻漂移或漏拍。
2. **snap 无 Cron fallback 不一致**：Python 无 Cron 时近似连续抽帧；C++ 用 `frameSkip` 秒——产品需统一规则。
3. **patrol hybrid 仅 Python**：C++ 无焦点设备半间隔 + 背景池，hybrid 会话无法直接迁 cpp。
4. **抓拍入库依赖 VIDEO**：C++ 路径若不做回调帧上传，图库会空；需明确帧后契约（HTTP/Kafka）。
5. **patrol 无 GPU 调度**：大模型多设备并行时 CPU 瓶颈；与 snap/realtime 多卡策略不一致。
6. **心跳端点不统一**：snap 误用 `heartbeat/realtime`，patrol 用专用端点；运维监控需分路径。
7. **配置热更新**：snap/patrol 仅启动加载；设备增删需重启子进程（realtime 有 reload worker）。
8. **时间基准**：patrol `last_patrol_at` 用 UTC；snap Cron 用东八区 naive——跨模式测试需注意时钟语义。
9. **追踪/人脸/车牌**：patrol 全缺；snap 有而 C++ patrol 无——行为差异属产品可见面。

## 5. Equivalence notes

### 5.1 怎样算「表现一致」

**snap（单设备）**

- 给定固定 Cron（如 `0 */30 * * * *` 东八区）与录制源流，在 ±`snap_cron_match_window_seconds` 内每槽 **最多 1 张** 入库抓拍（或告警图），时间戳与槽位 `fire_time` 对齐（上海时区）。
- 检测：同模型、同 `detect_conf`、同分辨率下，框数量/类别与 Python 路径差异 ≤ 约定阈值（建议：同帧 IoU≥0.5 匹配率 ≥95%）。
- 有目标时：告警 hook payload 字段集合一致（`task_type=snapshot`、`correlation_id`、`information` 结构）。
- 花屏注入：槽位窗口内应跳过低质量帧并在窗口内重试，而非整槽放弃（对比 `device_cron_gray_warn_slot` 日志）。

**snap（多设备）**

- N 设备共享任务 Cron 时，各设备在同一槽位 **均应** 产生独立抓拍（并行缓流线程），不应串行延迟导致某设备错过窗口（除非队列 pending 超时清理）。
- 验收：N 路录制源 + 同一 Cron，统计每设备每槽入库数 ≤1 且覆盖率 100%。

**patrol（pool 模式）**

- `interval_sec=T`、`pool_size=K`、M 台设备：每台设备相邻两次成功巡检间隔 ∈ [T, T+Δ]（Δ 建议 ≤2s + 连接超时余量）。
- 同一时刻并行巡检数 ≤ K；M 台全到期时应分多批完成，总完成时间符合批次数 × 单路 `capture_frame` 耗时。
- 每轮巡检 1 帧（短连），连接不复用；与 Python `capture_frame` 行为一致。

**patrol（rotate 模式）**

- 设备顺序固定（`device_list` 顺序），周期约为 `M × (T/M)` = T（Python：`interval / len(device_list)` 休眠）。

**patrol（hybrid 模式）**

- 焦点设备平均间隔 ≈ `T/2`；背景设备间隔 ≈ `T`；背景并行度 `min(|bg|, pool_size-1)`。

**patrol（多路一致性）**

- **顺序一致性**：rotate 下 M 路循环顺序与 `device_streams` 键序一致（黄金日志：每轮 `设备 X 拉流` 顺序）。
- **时间一致性**：pool 下同时到期设备应在同一调度周期内启动线程（日志时间戳簇集）；不应长期饿死某 `device_id`（统计各设备 `last_patrol_at` 间隔方差）。
- **结果一致性**：同录制源、同模型，Python vs 候选 cpp 路径检测框 IoU 阈值同上；告警/suppress 行为一致（同设备 suppress 期内第二次有目标不重复告警）。

### 5.2 建议夹具 / 黄金样本

| 夹具 | 用途 |
|------|------|
| 多路 MP4/RTSP 回放源（≥8 路，可配置不同延迟） | pool/rotate/hybrid 调度与并行度 |
| 固定 Cron 任务配置 + 上海时区容器 `TZ=Asia/Shanghai` | snap 槽位对齐 |
| 注入花屏/灰屏帧片段 | `CAP-CRON-GRAY-SKIP` |
| 带已知检测目标的循环视频 | 检测框黄金 JSON（每帧 bbox 列表） |
| Mock `ALERT_HOOK_URL` + MinIO test bucket | 告警 payload 与 snap-space object 计数 |
| `PatrolSession` 进度订阅（`patrol_progress_hub`） | `CAP-PATROL-PROGRESS` 端到端 |
| 对比跑：Python 子进程 vs C++ ini（同设备列表、同模型） | 回归报表：每设备间隔分布、每槽抓拍数、告警数 |

**多路轮巡一致性测试步骤（最小闭环）**

1. 创建 M=8 设备 patrol Session，`pool` 模式 `interval_sec=30`、`pool_size=4`，源为循环 MP4。
2. 运行 10 分钟，采集心跳 `progress` 与日志。
3. 断言：每设备 `last_patrol_at` 间隔 30s±3s；任意 1s 窗口内活跃巡检线程 ≤4；8 设备巡检次数差 ≤2（无饿死）。
4. 切换 `rotate`，断言顺序与 `device_ids` 一致且全周期 ≈30s。
5. 若有 `focus_device_id`，`hybrid` 下焦点间隔 ≈15s±2s。

## 6. Evidence

- `VIDEO/services/snapshot_algorithm_service/run_deploy.py:main` — snap 主入口与线程编排
- `VIDEO/services/snapshot_algorithm_service/run_deploy.py:should_extract_frame_by_cron` — Cron 槽位判定
- `VIDEO/services/snapshot_algorithm_service/run_deploy.py:buffer_streamer_worker` — 长连接缓流 + Cron 抽帧
- `VIDEO/services/snapshot_algorithm_service/run_deploy.py:_finish_snapshot_detection` — 检测完成 → 告警/入库
- `VIDEO/services/snapshot_algorithm_service/run_deploy.py:upload_frame_to_snap_space` — 抓拍空间上传
- `VIDEO/services/snapshot_algorithm_service/app/utils/tracker.py:SimpleTracker` — 追踪器（与 realtime 同源）
- `VIDEO/services/snapshot_algorithm_service/env.example` — snap 环境变量（Cron、队列、无推流）
- `VIDEO/app/utils/cron_utils.py:cron_slot_for_time` — Cron 窗口与东八区语义
- `VIDEO/services/patrol_algorithm_service/run_deploy.py:patrol_scheduler_worker` — pool/rotate/hybrid 调度
- `VIDEO/services/patrol_algorithm_service/run_deploy.py:capture_frame` — 短连预热抓帧
- `VIDEO/services/patrol_algorithm_service/run_deploy.py:_devices_due` — 间隔到期计算
- `VIDEO/services/patrol_algorithm_service/run_deploy.py:send_heartbeat` — 巡检进度心跳
- `VIDEO/app/utils/patrol_snap_upload.py:upload_patrol_frame_to_snap_space` — 巡检帧入库
- `VIDEO/app/services/patrol_session_service.py:start_patrol_session` — Session 子进程拉起
- `VIDEO/app/services/algorithm_task_launcher_service.py:get_service_script_path` — snap/patrol 脚本映射
- `VIDEO/models.py:AlgorithmTask` — `cron_expression`、`patrol_mode`、`patrol_interval_sec` 字段
- `VIDEO/models.py:PatrolSession` — 巡检会话表
- `RUNTIME/src/pipeline/SnapScheduler.cpp:cronDue` — C++ Cron（分/时）
- `RUNTIME/src/pipeline/SnapScheduler.cpp:loop` — C++ 长连接 + 槽位触发
- `RUNTIME/src/pipeline/PatrolScheduler.cpp:loop` — C++ pool/rotate（无 hybrid）
- `RUNTIME/src/pipeline/PatrolScheduler.cpp:grabOneShot` — C++ 短连 5+1 帧
