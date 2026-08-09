# Report: C++ RUNTIME 基线能力与 Windows 阻滞

- **Agent role:** C++ RUNTIME 基线调研 Agent
- **Scope paths:** `RUNTIME/`（`src/`、`CMakeLists.txt`、`README.md`、`config/`、`scripts/`、`install_*.sh`）；交叉 `VIDEO/scripts/ensure_runtime_cpp.sh`、`VIDEO/app/services/runtime_config_service.py`
- **Date:** 2026-08-09
- **Confidence:** high（源码与配置生成器已逐文件核对；Python 报告 `01/02` 尚未落盘，CAP ID 与 realtime 调研 prompt 约定对齐）

## 1. Executive summary

EasyAIoT **C++ RUNTIME** 是 VIDEO `executor=cpp` 的帧内执行后端：单二进制 `RUNTIME`，经 ini 启动，覆盖 **realtime / snap / patrol** 三种 `task_type`。核心路径为 **Pull+Decode → SPSC FrameRing（drop-oldest）→ YOLOv11 ONNX 推理 → ResultRing → 异步告警 Emit（HTTP hook）**；realtime 另含可选 RTMP 叠框推流与控制口 `GET /health`。

**模型侧**：仅 **ONNX**（`Yolov11Engine` + ORT C++ API），**单模型**（`model_path` 取 map 首项，`Detech.cpp` 明示 TODO 多模型）；GPU 为 **CUDA EP 优先、失败回退 CPU**，无 TensorRT/DirectML。推理阈值在引擎内硬编码 `score_threshold=0.25`，与任务 `detect_conf`（仅用于告警过滤）分离。

**与 Python 路径差距**：tracking、face/plate 检测过滤与匹配、motion_gate、SAM、姿态、后处理脚本、多模型融合、overlay/alert 双队列、布防时段、`alert_class_names` 等均 **未实现**；且 `generate_runtime_ini` **未写入** 对应 DB 字段，C++ 侧也无解析段，属 **静默能力丢失**。

**Windows**：文档与安装链 **明确「本轮不管」**；`ensure_runtime_cpp.sh` 非 Linux 直接跳过；源码依赖 `sigaction`、`unistd.h`、`localtime_r`/`gmtime_r`、`pthread`、`dl`、`mkdir(0755)`；CMake 仅 Linux 式 `-pthread`/`find_library`；ORT 依赖脚本只拉 `onnxruntime-linux-*`。Windows 需独立 EP（DirectML/CUDA on Windows）、vcpkg/MSVC 工具链、POSIX 垫片与 `install_windows` 集成。

**可作等价黄金参考的部分**：单模型 YOLO 检测 + 区域过滤 + 置信度告警 + cooldown + VIDEO hook JSON 契约 + 心跳 + realtime 三阶段流水线指标 + snap cron/间隔抓拍 + patrol pool/rotate 轮巡骨架。

---

## 2. Inventory / Findings

### 2.1 任务形态与调度

| Capability ID | 状态 | 说明 |
|---------------|------|------|
| `CAP-TASK-REALTIME` | **已实现** | `task_type=realtime`：FFmpeg 长连接 + `Pipeline` 三线程 |
| `CAP-TASK-SNAP` | **已实现** | `SnapScheduler`：cron 或 `frame_skip` 秒级间隔，多设备 `VideoCapture` |
| `CAP-TASK-PATROL` | **部分** | `PatrolScheduler` 支持 `pool`/`rotate`；**无** Python 的 `hybrid` + `focus_device_id` |
| `CAP-CRON-SNAP` | **部分** | 仅解析 cron 的 **分+时** 字段（`SnapScheduler::parseCronFields`），日/月/周忽略；空 cron 退化为 `frame_skip` 秒间隔 |
| `CAP-PATROL-POOL` | **已实现** | `patrol_mode=pool`，`patrol_pool_size` 限制每轮并发设备数 |
| `CAP-PATROL-ROTATE` | **已实现** | `patrol_mode=rotate`，顺序单设备，`interval ≈ patrol_interval_sec / N` |
| `CAP-PATROL-HYBRID` | **缺失** | Python `patrol_algorithm_service` 有 `hybrid`+`focus_device_id`；C++ `Config` 无字段 |
| `CAP-MULTI-DEVICE` | **部分** | snap/patrol 经 `devices_json` 多路；realtime 主路仍单 `rtsp_url`（首设备） |

### 2.2 流水线（Pull / Decode / Infer / Emit）

| Capability ID | 状态 | 说明 |
|---------------|------|------|
| `CAP-PIPELINE-PULL` | **已实现** | `Pipeline::pullDecodeLoop`：FFmpeg `av_read_frame` → 解码 → `sws_scale` BGR24 |
| `CAP-PIPELINE-RING` | **已实现** | `frameRing_(8)` + `framePool_`；满则 drop-oldest（`pushDropOldest`） |
| `CAP-PIPELINE-INFER` | **已实现** | `inferLoop`：按 `frame_skip` 提交 `Yolov11ThreadPool`；非阻塞取最近 30 帧内结果并 **复用 lastDetections** |
| `CAP-PIPELINE-EMIT` | **已实现** | `emitLoop`：区域内高置信目标 → `alarmFn_` → 异步入队 HTTP |
| `CAP-STREAM-RECONNECT` | **已实现** | Pull 断流指数退避重连 + `reopenStream` |
| `CAP-OVERLAY-QUEUE` | **缺失** | Python 独立 overlay 队列/worker/叠框追踪；C++ 在 infer 线程内同步画框+推流 |
| `CAP-FRAME-SAMPLE` | **部分** | 仅单一 `frame_skip`（ini `[ai]`/`[video_task]`）；无 overlay/alert 分离采样 |

**realtime 数据流（摘要）：**

```
RTSP ──FFmpeg──► FrameRing(8, drop-oldest) ──► Infer(YOLO, skip=N) ──► ResultRing ──► AlarmQueue ──► POST /video/alert/hook
                                                      │
                                                      └──► RTMP（enable_rtmp 且 streaming enabled）
```

**SnapScheduler 行为：**

- 200ms 轮询；`cron_expression` 非空 → 匹配当前 **时+分**（同分钟槽去重 `lastSlot_`）；为空 → 每 `max(1, frame_skip)` 秒触发一轮。
- 每设备持久 `cv::VideoCapture`；失败则 reopen。
- 每帧 **同步** `submitTask` + `getTargetResult`（阻塞等待），与 realtime 异步池不同。

**PatrolScheduler 行为：**

- **pool**：扫描 `lastPatrolTime_`，到期设备最多取 `patrol_pool_size` 个；每设备 `grabOneShot`（临时 `VideoCapture`，预热 5 帧后取一帧）。
- **rotate**：严格轮转单设备，间隔 `max(3, patrol_interval_sec / device_count)` 秒。
- 推理同 snap：同步等待结果。

### 2.3 推理与模型

| Capability ID | 状态 | 说明 |
|---------------|------|------|
| `CAP-YOLO-INFER` | **已实现** | `Yolov11Engine::Inference`：ORT Session，letterbox + NMS |
| `CAP-ONNX-ONLY` | **已实现** | 仅 `.onnx`；`runtime_config_service._resolve_model_paths` 集群/本地均找首个 onnx |
| `CAP-MULTI-MODEL` | **缺失** | `Config.modelPaths` 为 map，但 `Detech::_init_yolo11_detector` 只加载 **第一个**；`model_ids` 多选时 Python 会 `load_yolo_models` 多路 |
| `CAP-PT-ULTRALYTICS` | **缺失** | Python 可 `.pt`（ultralytics）；C++ 无 |
| `CAP-GPU-CUDA-EP` | **已实现** | `AppendExecutionProvider_CUDA`；失败 catch 后 CPU；`GET /health` 返回 `infer_ep` |
| `CAP-GPU-DIRECTML` | **缺失** | Windows 推理 EP 未实现 |
| `CAP-INFER-THRESHOLD` | **部分** | 引擎内固定 `0.25`/`0.45` NMS；任务 `detect_conf` 仅用于 **告警**（`alarmConfidenceThreshold`），非推理阈值 |

### 2.4 检测后处理与 VIDEO 交互

| Capability ID | 状态 | 说明 |
|---------------|------|------|
| `CAP-REGION-FILTER` | **已实现** | `[regions]` 多边形；支持 0–1 归一化坐标；中心点 `pointPolygonTest` |
| `CAP-ALERT-HOOK` | **已实现** | `Detech::_alarmSenderThreadFunc`：VIDEO 契约 JSON（`object/event/device_id/information/...`） |
| `CAP-ALERT-COOLDOWN` | **已实现** | `alarmCooldownTime` 秒级全局冷却 |
| `CAP-ALERT-CLASS-FILTER` | **缺失** | DB `alert_class_names` 未进 ini；C++ 无类别白名单 |
| `CAP-ALERT-IMAGE` | **已实现** | `_saveAlertImage` 缩略至宽 640 落盘，`image_path` 写入 hook |
| `CAP-TRACKING` | **缺失** | 无 ByteTrack/相似度追踪；无 `track_id` 输出 |
| `CAP-FACE-DETECT` | **缺失** | 无 `face_detection_enabled` 类别过滤 |
| `CAP-PLATE-DETECT` | **缺失** | 无 `plate_detection_enabled` 类别过滤 |
| `CAP-FACE-MATCH` | **缺失** | 无 Kafka/队列人脸匹配 |
| `CAP-PLATE-MATCH` | **缺失** | 无车牌匹配 |
| `CAP-MOTION-GATE` | **缺失** | 无 `MotionGate` |
| `CAP-SAM` | **缺失** | 无 SAM 补充识别 |
| `CAP-POSE-ANALYSIS` | **缺失** | 无姿态模型/意图库 |
| `CAP-POST-PROCESS` | **缺失** | 无用户 Python 后处理脚本 |
| `CAP-DEFENSE-SCHEDULE` | **缺失** | 无 `defense_mode` / `defense_schedule` 布防时段 |
| `CAP-HEARTBEAT` | **已实现** | 周期 POST `heartbeat_url`（realtime/patrol 路径由 VIDEO 生成）；含 `task_id/port/process_id/log_path`；patrol 附加 `total_patrols/total_detections` |
| `CAP-RTMP` | **部分** | `RTMPEncoder` + `enable_rtmp`；可运行时 `/control/streaming/start|stop`；无 overlay 追踪插值 |
| `CAP-CONTROL-HTTP` | **部分** | `GET /health`、推流控制；**无** README 写的 `POST /stop` 优雅退出 |
| `CAP-HEADLESS` | **已实现** | `headless=true` 强制 pipeline；非 headless 亦强制 headless（display 路径未用于生产） |

### 2.5 ini 与 `generate_runtime_ini` 字段映射

**VIDEO 已写入且 C++ 已解析：**

| ini 段 | 字段 | C++ `ConfigParser` |
|--------|------|-------------------|
| `[video]` | `rtsp_url`, `rtmp_url`, `width`, `height`, `fps` | ✓ |
| `[ai]` | `enable`, `model_path`, `classes_path`, `threads`, `frame_skip`, `prefer_gpu`, `force_cpu`, `gpu_device_id` | ✓ |
| `[alarm]` | `enable`, `hook_url`, `confidence_threshold`, `cooldown_time`, `image_dir` | ✓ |
| `[task]` | `id`, `control_port` | ✓ |
| `[video_task]` | `device_id/name`, `task_type`, `algorithm_name`, `alert_hook_url`, `heartbeat_url`, `heartbeat_interval_sec`, `log_path`, `alert_image_dir`, `headless`, `frame_skip`, `cron_expression`, `patrol_*`, `devices_json` | ✓ |
| `[features]` | `enable_rtmp`, `enable_draw`, `enable_alarm` | ✓ |
| `[regions]` | `{deviceId}_{region}=[[x,y],...]` | ✓ |

**`AlgorithmTask` 存在但 `generate_runtime_ini` 未写入 → C++ 无法感知（静默丢失）：**

| DB 字段 | 影响能力 | 备注 |
|---------|----------|------|
| `tracking_enabled` + `tracking_*` | `CAP-TRACKING` | Python 告警/叠框可带 track_id |
| `face_detection_enabled` | `CAP-FACE-DETECT` | 人脸类过滤 |
| `plate_detection_enabled` | `CAP-PLATE-DETECT` | 车牌类过滤 |
| `face_matching_enabled` + `face_library_ids` + `face_matching_threshold` | `CAP-FACE-MATCH` | 帧后 Kafka/队列 |
| `plate_matching_enabled` + `plate_library_ids` | `CAP-PLATE-MATCH` | 同上 |
| `matching_business_tags` | 匹配透传 | hook 扩展字段 |
| `motion_gate_enabled` + `motion_gate_config` | `CAP-MOTION-GATE` | 实时省算力 |
| `sam_supplement_enabled` + `sam_supplement_config` | `CAP-SAM` | |
| `pose_analysis_enabled` + `pose_*` | `CAP-POSE-ANALYSIS` | |
| `post_process_enabled` + `post_process_*` | `CAP-POST-PROCESS` | |
| `defense_mode` + `defense_schedule` | `CAP-DEFENSE-SCHEDULE` | |
| `alert_class_names` | `CAP-ALERT-CLASS-FILTER` | 告警类别白名单 |
| `rtmp_input_url` | 拉流源 | cpp 仅用设备 RTSP + 任务 `rtmp_output_url` |
| `focus_device_id` | `CAP-PATROL-HYBRID` | patrol hybrid 模式 |
| `model_ids`（多模型） | `CAP-MULTI-MODEL` | 生成器只解析 **首个** onnx 路径写入 `model_path` |
| `extract_interval` vs `frame_skip` | 语义混用 | realtime 用 `extract_interval`→`frame_skip`；snap 的 DB `frame_skip`（抽帧）**未映射**（generate 对 snap 也用 `extract_interval`） |

**环境变量覆盖（C++ 解析后）：** `RUNTIME_FORCE_CPU`、`RUNTIME_PREFER_GPU`、`USE_GPU`、`RUNTIME_GPU_DEVICE_ID`。

### 2.6 部署与工具链

| 项 | Linux 现状 | Windows 阻滞 |
|----|------------|--------------|
| 一键编译 | `install_linux.sh` + conda `easyaiot-runtime` + `build_linux.sh` | 无 `install_windows.*` |
| VIDEO 挂钩 | `ensure_runtime_cpp.sh` | `uname != Linux` → 警告并 **return 0 跳过** |
| ORT 包 | `.deps/onnxruntime-linux-{x64,aarch64}[-gpu]-1.23.2` | 需 `onnxruntime-win-*` 或 DirectML 包 |
| 文档立场 | `RUNTIME/README.md` 表：**Windows 本轮不管** | 建议 `executor=python` 或手工编译 |

---

## 3. Placement hint

| Capability ID | 建议落点 | 理由 |
|---------------|----------|------|
| `CAP-PIPELINE-*` / `CAP-YOLO-INFER` / `CAP-GPU-CUDA-EP` | **cpp** | 已在 RUNTIME；性能核心 |
| `CAP-TRACKING` | **cpp**（帧内）或 **video**（若仅告警需要） | Python 在帧内；叠框追踪可拆 |
| `CAP-FACE-MATCH` / `CAP-PLATE-MATCH` | **video** | Python 已队列+Kafka；适合帧后 |
| `CAP-MOTION-GATE` | **cpp** | 在 infer 前省算力；需 ini 字段 |
| `CAP-SAM` / `CAP-POSE-*` / `CAP-POST-PROCESS` | **video** 或 **cpp**（视延迟） | 非当前 RUNTIME 范围 |
| `CAP-ALERT-CLASS-FILTER` / `CAP-DEFENSE-SCHEDULE` | **both** | ini 下发 + cpp 执行或 video hook 过滤 |
| `CAP-MULTI-MODEL` | **cpp** | 需引擎级多 session 或融合 |
| `CAP-PATROL-HYBRID` | **cpp** | 扩展 `PatrolScheduler` |
| `CAP-OVERLAY-QUEUE` | **cpp**（简化）或 **video** | 可与 RTMP 推理解耦 |
| `CAP-HEARTBEAT` / `CAP-ALERT-HOOK` | **cpp** 发送，**video** 消费 | 现状即可 |

---

## 4. Gaps / Risks

### 4.1 功能缺口（相对 Python executor）

1. **多模型与 .pt**：仅单 ONNX；多 `model_ids` 时 VIDEO 只导出第一个，与 Python `load_yolo_models` 行为不一致。
2. **追踪与 ID 稳定性**：无 track_id → 告警关联、叠框平滑、人脸裁剪链路均不等价。
3. **帧后能力全缺**：face/plate 匹配、SAM、姿态、后处理脚本 — 即使用户在 WEB 开启，cpp 任务 **无提示地** 不生效。
4. **motion_gate / 双采样**：Python `OVERLAY_EXTRACT_INTERVAL` ≠ `ALERT_EXTRACT_INTERVAL`；cpp 单 `frame_skip`。
5. **Patrol hybrid**：集群常见「焦点设备+池化」模式未覆盖。
6. **告警语义**：无 `alert_class_names`；推理阈值固定 0.25，可能与 Python ultralytics `conf` 不一致。
7. **控制面**：README 承诺 `POST /stop`，代码未实现；Daemon 可能依赖进程信号（POSIX）。

### 4.2 Windows 移植清单（具体点）

| # | 类别 | 位置/现象 | 移植动作 |
|---|------|-----------|----------|
| W1 | 安装脚本 | `ensure_runtime_cpp.sh:127-129` | 增加 `MINGW/MSVC` 分支或 `install_windows.ps1` 调 cmake；非静默跳过 |
| W2 | 文档 | `RUNTIME/README.md:59` | 明确 EP 选型：CUDA（NVIDIA 驱动）或 **DirectML**（通用 GPU） |
| W3 | 信号 | `Manage.cpp:12-20` `sigaction` | `SIGINT/SIGTERM` → `SetConsoleCtrlHandler`；`SIGPIPE` 可忽略或 `WSA` 等效 |
| W4 | 进程 | `Detech.cpp:1034` `getpid()` | `_getpid()` / `GetCurrentProcessId()` |
| W5 | 时间 | `SnapScheduler.cpp:127` `localtime_r`；`Detech.cpp:25` `gmtime_r` | `localtime_s` / `gmtime_s` 或 C++20 `chrono` |
| W6 | 文件系统 | `Detech.cpp:1065` `mkdir(..., 0755)` | `_mkdir` / `std::filesystem::create_directories` |
| W7 | 头文件 | `Detech.cpp:16`, `Yolov11ThreadPool.cpp:3` `unistd.h` | 移除或 `#ifdef _WIN32`；`access`/`dirent` 死代码可删 |
| W8 | CMake | `CMakeLists.txt:12-14,101-102` | `-pthread`→ MSVC 线程；`pthread`/`dl`→ 条件链接；`find_library` 改 vcpkg/conda-win |
| W9 | 依赖路径 | `CMakeLists.txt:52-56` 硬编码 `/usr/include` | `ONNXRUNTIME_ROOT` 必填；OpenCV FFmpeg 走 vcpkg 或 conda-forge win-64 |
| W10 | ORT 获取 | `install_linux.sh` / `build_linux.sh` | 下载 `onnxruntime-win-x64-gpu-1.23.2` 或 CPU+DirectML；`deploy.env` 改 `PATH`/`LIB` 为 Windows |
| W11 | 动态库 | `export_runtime_cpp.sh` 打包 `ldd` | 改为 `dumpbin /dependents` 或静态链接 ORT/OpenCV 子集 |
| W12 | VIDEO 默认 | `VIDEO/.env.acme` 注释 prefer python | Windows 部署默认 `executor=python` 直至 W1–W10 完成 |
| W13 | httplib | `3rdparty/cpp-httplib` 已支持 WinSock | 确保 `CPPHTTPLIB_USE_POLL` 等宏与链接 `ws2_32` |

### 4.3 配置与运维风险

- **静默降级**：WEB 开启 tracking/face/motion_gate 等，切 `executor=cpp` 后无报错、无 capability 位上报。
- **snap `frame_skip` 语义**：DB 字段与 realtime `extract_interval` 在 `generate_runtime_ini` 中混用同一 `frame_skip` 键。
- **cron 简化**：复杂 cron 在 snap 上与 Python 调度不一致。
- **心跳 `server_ip`**：固定 `127.0.0.1`，多网卡/容器可能误导 VIDEO 调度展示。

---

## 5. Equivalence notes

### 5.1 适合作为「黄金参考」的 cpp 基线

在 **单模型 ONNX YOLO、关闭 tracking/face/plate/motion_gate/SAM、单设备 realtime、regions + detect_conf 告警、cooldown** 条件下，以下可与 Python 对比：

| 维度 | 等价标准 | 夹具建议 |
|------|----------|----------|
| 检测框 | 同 RTSP 片段、同 onnx+names，框 IoU≥0.5 且 class 一致的比例 ≥ 阈值 | 固定 `RUNTIME/models/yolov11n.onnx` + 录制的 30s 视频 |
| 告警触发 | 同区域、同 `confidence_threshold`，告警次数/时间戳偏差 ≤ cooldown | 注入已知目标进 ROI |
| 流水线背压 | 高 FPS 下 `frames_dropped` 单调增、服务不崩溃 | `GET /health` metrics |
| snap 调度 | cron `0 * * * *` 与 Python 同分钟触发次数 | 日志对齐 `SNAP cron slot fired` |
| patrol pool | N 设备、`patrol_interval_sec=T`，单位时间巡检次数 | 对比 `total_patrols` 心跳字段 |
| GPU 回退 | 无 CUDA 时 `infer_ep=cpu` 且任务存活 | `RUNTIME_FORCE_CPU=1` |

### 5.2 当前 **不能** 作为黄金参考

- 多模型叠加、追踪 ID、face/plate 匹配链路、motion_gate 省算力比例、SAM/姿态/后处理、hybrid patrol、`alert_class_names` 过滤、overlay 与 alert 分离采样、推理 conf 与 ultralytics 默认对齐。

### 5.3 推荐对比方法

1. **同一 `task_{id}.ini`**（由 `generate_runtime_ini` 生成）分别启动 cpp 与 python（python 需补全缺失字段的环境/DB）。
2. 录制 RTSP → 离线回放（后续 testbed 报告）消除网络抖动。
3. hook 落库对比：`correlation_id`、`detections[].bbox`、`detection_count`。
4. 允许 cpp **延迟更低、CPU 更低**；召回率差异 >5% 或告警计数差异 >1 次/分钟需判定不通过。

---

## 6. Evidence

### 流水线

- `RUNTIME/src/pipeline/Pipeline.cpp:71-78` — `start()` 启动 pull/infer/emit 三线程
- `RUNTIME/src/pipeline/Pipeline.cpp:329-340` — FrameRing drop-oldest
- `RUNTIME/src/pipeline/Pipeline.cpp:388-444` — frame_skip 推理与区域告警
- `RUNTIME/src/pipeline/SnapScheduler.cpp:125-145` — cron 分/时匹配
- `RUNTIME/src/pipeline/PatrolScheduler.cpp:177-216` — pool/rotate 主循环

### 模型与 GPU

- `RUNTIME/src/Yolov11Engine.cpp:34-45` — `AppendExecutionProvider_CUDA`
- `RUNTIME/src/Yolov11Engine.cpp:110-115` — 固定 `score_threshold=0.25`
- `RUNTIME/src/Detech.cpp:523-524` — `TODO: Support multiple models`
- `RUNTIME/src/Detech.cpp:565-572` — 单模型 `setUp`

### VIDEO 对接

- `VIDEO/app/services/runtime_config_service.py:233-385` — `generate_runtime_ini` 模板
- `VIDEO/app/services/runtime_config_service.py:80-162` — `_resolve_model_paths` 首个 onnx
- `RUNTIME/src/ConfigParser.cpp:97-351` — ini 解析全集
- `RUNTIME/src/Detech.cpp:984-1054` — 心跳线程
- `RUNTIME/src/Detech.cpp:865-982` — 告警队列与 VIDEO hook JSON

### Windows / 构建

- `RUNTIME/README.md:58-59` — Windows「本轮不管」
- `VIDEO/scripts/ensure_runtime_cpp.sh:127-129` — 非 Linux 跳过
- `RUNTIME/CMakeLists.txt:12-14,52-56,100-102` — Linux 标志与链接
- `RUNTIME/src/Manage.cpp:12-20` — `sigaction`
- `RUNTIME/src/pipeline/SnapScheduler.cpp:127` — `localtime_r`
- `RUNTIME/install_linux.sh:69-88` — conda 依赖（无 Windows 对应）

### 数据模型（未传递字段源）

- `VIDEO/models.py:924-1026` — `AlgorithmTask` tracking/face/plate/motion_gate/SAM/pose/defense 等列

---

## 附录：CAP 状态速查

| 状态 | CAP IDs |
|------|---------|
| **已实现** | `CAP-TASK-REALTIME`, `CAP-TASK-SNAP`, `CAP-PIPELINE-*`, `CAP-STREAM-RECONNECT`, `CAP-YOLO-INFER`, `CAP-ONNX-ONLY`, `CAP-GPU-CUDA-EP`, `CAP-REGION-FILTER`, `CAP-ALERT-HOOK`, `CAP-ALERT-COOLDOWN`, `CAP-ALERT-IMAGE`, `CAP-HEARTBEAT`, `CAP-PATROL-POOL`, `CAP-PATROL-ROTATE`, `CAP-HEADLESS` |
| **部分** | `CAP-TASK-PATROL`, `CAP-CRON-SNAP`, `CAP-MULTI-DEVICE`, `CAP-FRAME-SAMPLE`, `CAP-INFER-THRESHOLD`, `CAP-RTMP`, `CAP-CONTROL-HTTP` |
| **缺失** | `CAP-PATROL-HYBRID`, `CAP-OVERLAY-QUEUE`, `CAP-MULTI-MODEL`, `CAP-PT-ULTRALYTICS`, `CAP-GPU-DIRECTML`, `CAP-ALERT-CLASS-FILTER`, `CAP-TRACKING`, `CAP-FACE-DETECT`, `CAP-PLATE-DETECT`, `CAP-FACE-MATCH`, `CAP-PLATE-MATCH`, `CAP-MOTION-GATE`, `CAP-SAM`, `CAP-POSE-ANALYSIS`, `CAP-POST-PROCESS`, `CAP-DEFENSE-SCHEDULE` |
