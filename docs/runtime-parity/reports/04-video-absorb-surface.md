# Report: VIDEO 编排层可吸收「Python runtime 帧后能力」表面

- **Agent role:** 调研 Agent（VIDEO 编排层 / 帧后能力收归）
- **Scope paths:**
  - `VIDEO/app/services/algorithm_task_daemon.py`
  - `VIDEO/app/services/algorithm_task_launcher_service.py`
  - `VIDEO/app/services/runtime_config_service.py`
  - `VIDEO/app/services/alert_hook_service.py`
  - `VIDEO/app/services/face_matching_kafka_service.py`
  - `VIDEO/app/services/plate_matching_kafka_service.py`
  - `VIDEO/app/services/library_matching_service.py`
  - `VIDEO/app/services/post_process_*.py`
  - `WEB/src/views/camera/components/AlgorithmTask/AlgorithmTaskModal.vue`
- **Date:** 2026-08-09
- **Confidence:** high（编排层代码已精读；Python `run_deploy` 帧后触发链对照阅读；C++ RUNTIME 告警/心跳契约已核对）

## 1. Executive summary

VIDEO 编排层已具备 **executor 双轨启动**（`python` → `*_algorithm_service/run_deploy.py`；`cpp` → RUNTIME 二进制 + `runtime_config_service` 生成 ini），且 **告警 Hook / 心跳 / Kafka 落库 / 人脸车牌库匹配 / 后处理 Worker 拉起** 等「帧后」能力大多落在 VIDEO（或 VIDEO→iot-sink）侧，与执行器解耦良好。

当前缺口集中在：**C++ 执行器只会上报检测告警 Hook，不会在帧后触发人脸/车牌抓取投递、后处理入队、SAM/姿态/追踪等 Python `run_deploy` 内嵌逻辑**。若删除 Python runtime，这些能力应在 VIDEO 编排层补「告警后编排」或「检测结果回调」表面，而非全部下沉 C++。

`AlgorithmTaskModal.vue` 文案声明「高性能 = 本机加速、完整能力 = 未标注项」，但 **UI 未按 executor 隐藏/禁用 tracking/face/plate/post_process/pose 等开关**，cpp 任务可保存启用态却不生效，构成 **假开关风险**。

建议收归策略：**帧内推理与画框留 C++**；**帧后编排（Hook 增强、匹配触发、后处理入队、通知字段补齐）改 VIDEO**；UI 对 cpp 模式做能力门禁或明确标注。

## 2. Inventory / Findings

### 2.1 Daemon / Launcher：executor 分支

| 阶段 | `executor=python` | `executor=cpp` |
|------|-------------------|----------------|
| 入口 | `algorithm_task_launcher_service.start_task_services` L917–972 | 同左 L920–943 |
| 守护进程 | `AlgorithmTaskDaemon._get_deploy_args` → python 分支 L442–550 | `_get_cpp_deploy_args` L552–607 |
| 子进程命令 | `[python, services/{realtime\|snap\|patrol}_algorithm_service/run_deploy.py]` | `[RUNTIME_BIN, runtime.ini]` |
| 配置来源 | DB + 环境变量注入子进程（含 SAM、运动门控、Kafka 等） | `runtime_config_service.generate_runtime_ini` 写 ini；`ensure_runtime_bin_ready` |
| 远程部署 | `_deploy_task_on_remote_node` python 分支 L352–367 | 同函数 cpp 分支 L325–351 |
| 后处理 Worker | 任务启动后 `_start_post_process_cluster`（与 executor 无关） | 同左 |
| 不支持类型 | 无（python 三类型均支持） | 非 realtime/snap/patrol 拒绝 L922–923 |

**python 专属环境变量（daemon L482–499）**：`KAFKA_*`、`SAM_*`、`MOTION_GATE_*`、`AI_SERVICE_URL`、`VIDEO_HEARTBEAT_URL`（本机直连 `:port/video/...`）等。

**cpp 专属（daemon L572–578）**：`ALERT_HOOK_URL`、`RUNTIME_*`、GPU/LD_LIBRARY_PATH；**不注入** SAM/运动门控/人脸车牌 publish URL。

**心跳 URL 分叉（风险点）**：
- 本机 python daemon：`http://{POD_IP}:{port}/video/algorithm/heartbeat/{realtime\|patrol}`（绕过网关，`algorithm_task_daemon.py` L517–521）
- 远程 / `runtime_config_service`：`resolve_video_service_base_url()` + `/video/algorithm/heartbeat/...`（`runtime_config_service.py` L219–223, L366）
- Launcher 远程 env：`{gateway}/admin-api/video/algorithm/heartbeat/...`（`algorithm_task_launcher_service.py` L267–270）

### 2.2 能力清单（稳定 ID）

| ID | 能力 | 今天谁做 | VIDEO 已有表面 | Python 删掉后缺口 |
|----|------|----------|----------------|-------------------|
| `CAP-ALERT-HOOK` | 检测告警 HTTP 上报 | python `run_deploy` + cpp `Detech` 告警线程 | `alert.py` → `process_alert_hook` | 无（cpp 已上报） |
| `CAP-HEARTBEAT` | 任务存活心跳 | python 线程 + cpp `_heartbeatThreadFunc` | `algorithm_task.py` `/heartbeat/realtime\|patrol` | 无 |
| `CAP-ALERT-KAFKA` | 告警事件/通知 Kafka | `alert_hook_service` | 完整（含 mini 直连落库） | 无 |
| `CAP-ALERT-SUPPRESS` | 告警事件抑制 | 算法侧 + hook 侧 Kafka 抑制 | `_should_suppress_alert_event_kafka` | 需保证 cpp 侧冷却与 DB `alert_event_suppress_time` 一致 |
| `CAP-TRACKING` | BYTETrack 追踪 + 叠加/告警轨迹 | python `run_deploy` only | DB 字段 + UI；**ini 未写入** | cpp 无追踪；需 C++ 或 VIDEO 侧不承诺 |
| `CAP-FACE-MATCHING` | 人脸抓帧→裁剪→匹配链 | python `try_send_face_matching_for_frame` | publish/process API + Kafka + `library_matching_service` | **缺触发**：cpp 告警后无人脸队列 |
| `CAP-PLATE-MATCHING` | 车牌抓帧→识别→匹配链 | python `try_send_plate_matching_for_frame` | 同人脸 | **缺触发** |
| `CAP-FACE-DETECTION-FLAG` | Kafka 消息 `faceDetectionEnabled` | python 告警透传 `face_detection_enabled` | hook 从 alert_data/DB 解析 | cpp hook **未带**该字段；VIDEO 可从 DB 补 |
| `CAP-POST-PROCESS` | AI 后处理入队 | python `enqueue_post_process_request` | `post_process_sink_client` + launcher Worker | **缺触发**：cpp 不调用 sink enqueue |
| `CAP-POSE-ANALYSIS` | 姿态分析 | python 投递 + iot-sink Worker | `post_process_launcher_service` 可拉起 Worker | **缺触发** |
| `CAP-POSE-INTENT` | 姿态意图 | 同上 | 同上 | **缺触发** |
| `CAP-SAM-SUPPLEMENT` | SAM 开放词表/告警核验 | python `sam_supplement` + launcher env 注入 | env 注入仅 python 路径 | cpp 无；宜 VIDEO 帧后或放弃 cpp 支持 |
| `CAP-MOTION-GATE` | 运动门控抽帧 | python env `MOTION_GATE_*` | launcher `_inject_realtime_sampling_env` | cpp ini 无；宜 C++ 或 VIDEO 不管 |
| `CAP-REGIONS` | 检测区域 | python DB 读区；cpp ini `[regions]` | `runtime_config_service._regions_ini_block` | cpp 已支持 |
| `CAP-RTMP-OUTPUT` | 推理流推送 | python + cpp `[features] enable_rtmp` | ini 生成 L379 | cpp 已部分支持 |

### 2.3 告警 Hook 契约

**入口：** `POST /video/alert/hook`（网关形态 `/admin-api/video/alert/hook`），`alert.py:alert_hook` → `process_alert_hook`。

**请求体（执行器 → VIDEO，snake_case）：**

| 字段 | 必填 | python | cpp RUNTIME | VIDEO 用途 |
|------|------|--------|-------------|------------|
| `object` | 是 | ✓ | ✓ | 告警对象 |
| `event` | 是 | ✓ 任务名 | ✓ `algorithm_name` | 事件名 |
| `device_id` / `device_name` | 是 | ✓ | ✓ | 设备 |
| `task_type` | 否 | `realtime`/`snap`→hook 内归一 | ✓ ini `hook_tt` | Kafka 主题、任务查询 |
| `time` | 否 | 东八区墙钟 | UTC 格式字符串 | 归一化 `_normalize_alert_wall_time_str` |
| `image_path` | 否 | ✓ 本地路径 | ✓ `alert_image_dir` | Kafka `imagePath` / MinIO |
| `region` | 否 | ✓ | ✓ | 区域名 |
| `information` | 否 | JSON 字符串（含 detections） | JSON（detections 数组） | 展示 |
| `correlation_id` | 否 | ✓ UUID | `{taskId}_{ts}` | 链路关联 |
| `face_detection_enabled` / `plate_detection_enabled` | 否 | ✓ 透传 | **缺失** | Kafka 开关；hook 可回查 DB |

**VIDEO 侧处理链（`alert_hook_service.process_alert_hook`）：**
1. 查 `alert_event_enabled` 任务 → 否则 `skipped`
2. mini / `ALERT_USE_DIRECT_PERSIST` → 直连 `create_alert`
3. 否则构建 Kafka 消息（`faceDetectionEnabled`/`plateDetectionEnabled`）→ `iot-alert-notification` 或 `iot-snapshot-alert`
4. 有通知配置 → `shouldNotify` + channels；失败 → `_fallback_persist_on_kafka_failure`

**ini 写入（cpp）：** `[alarm] hook_url` + `[video_task] alert_hook_url`（`runtime_config_service.py` L349–365），由 `resolve_alert_hook_url()` 解析。

### 2.4 心跳 URL 契约

**入口：**
- 实时/抓拍：`POST /video/algorithm/heartbeat/realtime`
- 巡检：`POST /video/algorithm/heartbeat/patrol`

**请求体：**

```json
{
  "task_id": 123,
  "server_ip": "可选",
  "port": "可选，cpp 为 control_port",
  "process_id": "可选",
  "log_path": "可选",
  "total_patrols": "仅 patrol"
}
```

**响应：** `{ "code": 0, "msg": "心跳接收成功" }` → 更新 `AlgorithmTask.service_last_heartbeat`、`run_status`。

**间隔：** cpp ini `heartbeat_interval_sec`（realtime 10s / patrol 15s）；python 约 10s。

**健康检查：** `algorithm_task_launcher_service._algorithm_task_service_healthy` 结合本机 daemon + 心跳超时（默认 90s `ALGORITHM_HEARTBEAT_FAILOVER_SECONDS`）。

### 2.5 人脸 / 车牌匹配：触发链与 Python 删除后补段

**今天触发方：Python 执行器（非 VIDEO 编排主路径）**

```
run_deploy 告警帧
  → try_send_face_matching_for_frame / try_send_plate_matching_for_frame
  → face_capture_queue_service / plate_capture_queue_service（独立队列，ONNX 抓脸/牌）
  → HTTP POST resolve_face_matching_publish_url() → /video/face|plate/matching/publish
  → face_matching_kafka_service / plate_matching_kafka_service → Kafka (iot-face-matching / iot-plate-matching)
  → iot-sink FaceMatchingConsumer / PlateMatchingConsumer
  → HTTP POST /video/face|plate/matching/process
  → library_matching_service.process_*_matching_message（库匹配 + FaceMatchRecord/PlateMatchRecord + 命中告警）
```

**VIDEO 编排层已具备、无需重写：** `publish` API、`library_matching_service`、Kafka producer、DB 模型。

**Python 删掉后 VIDEO 需补的「触发段」（推荐落点）：**

1. **方案 A（推荐，纯 VIDEO）：** 在 `process_alert_hook` 或独立 `alert_post_orchestrator` 中，若任务 `face_matching_enabled`/`plate_matching_enabled` 且 `image_path` 存在：
   - 读盘裁剪或调用人脸/车牌检测服务（复用 `face_capture_queue_service` 逻辑）
   - 调 `build_*_matching_message` + `send_*_matching_async`
2. **方案 B：** 新增 `POST /video/algorithm/frame-post` 供 cpp 每帧/每次告警回调（需改 C++，非纯 VIDEO）
3. **方案 C：** cpp 直接 POST matching publish（重复造轮子，违背「帧后归 VIDEO」）

**注意：** `face_detection_enabled` 在 UI 提交时由 `face_matching_enabled` 派生（`AlgorithmTaskModal.vue` L1828–1830），用于 Kafka；cpp 路径需在 hook 侧从 DB 补齐。

### 2.6 后处理（post_process）编排表面

| 组件 | 职责 |
|------|------|
| `post_process_launcher_service` | 任务启动时按 `post_process_enabled` / `pose_*` 拉 Worker（`EASYAIOT_ENABLE_POST_PROCESS_WORKER` 门控） |
| `post_process_sink_client` | python 帧路径 HTTP 入队 iot-sink `/post-process/enqueue` |
| `post_process_service` | 工作区模板、`process(ctx)` 契约 |
| `post_process_consumer_service` | 生产消费在 iot-sink；VIDEO 仅保留回放入库 |

**缺口：** cpp 不调用 `publish_post_process_request`。VIDEO 可在 hook 收到告警且 `post_process_enabled` 时，用 hook 内 `information.detections` + `image_path` 组装 ctx 入队（需对齐 `build_post_process_request_message` 字段）。

### 2.7 UI：高性能 vs 完整能力

- 六模式：`task_mode` ↔ `task_type` + `executor`（`AlgorithmTaskModal.vue` L70–88）
- 文案 L583：`高性能` = cpp，本机；`未标注` = python 完整能力集
- **cpp 仅强制：** `schedule_policy=local`（L1690–1751）；**未禁用** tracking/face/plate/sam/pose/post_process 表单项（`ifShow` 仅按 `baseTaskType`，不区分 `_cpp`）
- 新建默认 `task_mode: realtime_cpp` 且 `tracking_enabled: true`（L1570–1582）→ 用户以为 cpp 有追踪

## 3. Placement hint

| Capability ID | 建议落点 (cpp / video / both / drop) | 理由 |
|---------------|--------------------------------------|------|
| `CAP-ALERT-HOOK` | both | cpp/python 均 POST；VIDEO 统一消费 |
| `CAP-HEARTBEAT` | both | 已实现；VIDEO 仅接收 |
| `CAP-ALERT-KAFKA` / `CAP-ALERT-SUPPRESS` | video | 已在 `alert_hook_service` |
| `CAP-FACE-DETECTION-FLAG` | video | hook 从 DB 补全，无需 cpp 改 payload |
| `CAP-FACE-MATCHING` | video | 匹配逻辑已在 VIDEO；补 hook 后触发 |
| `CAP-PLATE-MATCHING` | video | 同上 |
| `CAP-POST-PROCESS` | video | 入队客户端已有；补 hook/回调触发 |
| `CAP-POSE-ANALYSIS` / `CAP-POSE-INTENT` | video | Worker 由 launcher 拉起；补触发 |
| `CAP-SAM-SUPPLEMENT` | video 或 drop(cpp) | SAM 重；cpp 难等价；可仅 python 等价期保留或 VIDEO 异步 |
| `CAP-TRACKING` | cpp | 帧内轨迹；ini 未配置；短期 UI 应对 cpp 禁用 |
| `CAP-MOTION-GATE` | cpp | 帧内抽帧策略 |
| `CAP-REGIONS` / `CAP-RTMP-OUTPUT` | cpp | ini 已生成 |
| `CAP-INFER-CORE` | cpp | 检测推理主路径 |

## 4. Gaps / Risks

1. **假开关：** cpp 任务可启用 tracking/face/plate/post_process/pose，运行时无效果；与 helpMessage 承诺不一致。
2. **人脸/车牌链断：** 触发仅在 python `run_deploy`；cpp 仅告警 Hook，无 matching publish。
3. **后处理断：** cpp 不 enqueue；`post_process_enabled` 对 cpp 任务形同虚设（Worker 可能空转）。
4. **Hook 字段差异：** cpp 无 `face_detection_enabled`；时间格式可能与 python 东八区不一致（需 hook 归一化已覆盖）。
5. **心跳 URL 三套：** 本机 python 直连、ini 基址、远程 gateway 前缀不一致，排障易混淆。
6. **远程 cpp vs UI：** UI 禁止 cpp 远程调度，但 DB 仍可能历史脏数据。
7. **后处理 Worker 全局开关：** `EASYAIOT_ENABLE_POST_PROCESS_WORKER` 默认关，与任务开关叠加易误判。

## 5. Equivalence notes

**分层验收（平台 vs 执行器）：**

| 层级 | 验收对象 | 方法 |
|------|----------|------|
| **执行器侧** | cpp RUNTIME 单进程 | 固定 RTSP 样本；断言 ini 生成、进程拉起、心跳 200、Hook POST 字段与图片落盘；**不验** Kafka/人脸库 |
| **平台侧（VIDEO）** | `process_alert_hook` | Mock Hook payload（python 黄金 + cpp 黄金）；断言 Kafka topic/partition、`faceDetectionEnabled`、抑制、mini 直连落库 |
| **平台侧（匹配）** | `library_matching_service` | 向 `/face/matching/publish` 投递 → 消费链或直接 `/process`；断言 `FaceMatchRecord`、命中告警 |
| **平台侧（后处理）** | iot-sink + Worker | 向 `/post-process/enqueue` 投 golden ctx；断言 `algorithm_post_process_result` 与脚本产出 alerts |
| **端到端** | 同任务配置 python vs cpp | 对比告警条数（允许 cpp 检测差异阈值）、Hook 延迟、**匹配记录数**、通知 Kafka 条数 |

**黄金样本建议：**
- Hook：各 1 份 python 形（含 `face_detection_enabled`）与 cpp 形（缺开关）→ VIDEO 输出应一致
- 人脸：固定 `faceImagePath` + task 绑定库 → `process_face_matching_message` 结果
- 后处理：固定 detections JSON + `post_process.py` 返回 `alerts`/`counts`

**SAM / 追踪：** 列入执行器等价或明确「cpp 不支持」产品声明，避免用平台侧勉强补齐。

## 6. Evidence

- `VIDEO/app/services/algorithm_task_daemon.py:_get_deploy_args` L432–440（executor 分支）
- `VIDEO/app/services/algorithm_task_daemon.py:_get_cpp_deploy_args` L552–607
- `VIDEO/app/services/algorithm_task_launcher_service.py:start_task_services` L917–1003
- `VIDEO/app/services/runtime_config_service.py:generate_runtime_ini` L233–385（hook/heartbeat/regions）
- `VIDEO/app/services/runtime_config_service.py:resolve_alert_hook_url` 引用 `app/utils/service_urls.py` L77–83
- `VIDEO/app/services/alert_hook_service.py:process_alert_hook` L764–1034
- `VIDEO/app/blueprints/algorithm_task.py:receive_realtime_heartbeat` L282–335
- `VIDEO/app/blueprints/alert.py:alert_hook` L245–264
- `VIDEO/app/utils/service_urls.py:resolve_face_matching_publish_url` L86–92
- `VIDEO/app/utils/face_capture_queue_service.py:_publish_face_matching` L79–101
- `VIDEO/app/services/library_matching_service.py:process_face_matching_message` L215–300
- `VIDEO/app/services/post_process_sink_client.py:publish_post_process_request` L68–92
- `VIDEO/app/services/post_process_launcher_service.py:start_post_process_workers` L197–216
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:try_send_face_matching_for_frame` L2258–2291
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:enqueue_post_process_request` 引用 L4306–4316
- `RUNTIME/src/Detech.cpp` 告警 Hook JSON L900–975；心跳 L1008–1054
- `WEB/src/views/camera/components/AlgorithmTask/AlgorithmTaskModal.vue` task_mode L568–584；cpp 调度 L1748–1751；face 派生 L1828–1830
- `DEVICE/iot-sink/.../FaceMatchingServiceImpl.java:process` L74（sink 回调 VIDEO `/face/matching/process`）
