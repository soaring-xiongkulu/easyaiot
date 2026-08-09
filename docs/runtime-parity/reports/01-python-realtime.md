# Report: Python realtime 算法执行后端能力清单

- **Agent role:** 调研 Agent（只读代码、不写业务）
- **Scope paths:**
  - `VIDEO/services/realtime_algorithm_service/`（主入口 `run_deploy.py`、本地 `app/utils/tracker.py`）
  - 交叉引用 `VIDEO/app/utils/`（tracker、motion_gate、onnx、SAM、face/plate 队列、decode、post_process 等）
  - 任务模型 `VIDEO/models.py`（`AlgorithmTask`）
  - 启动器 `VIDEO/app/services/algorithm_task_launcher_service.py`
- **Date:** 2026-08-09
- **Confidence:** high（主路径 `run_deploy.py` 已逐段核对；部分边缘环境变量组合未做运行时实测）

## 1. Executive summary

Python realtime 热路径由 `algorithm_task_daemon` / `algorithm_task_launcher_service` 按 `TASK_ID` 拉起 `run_deploy.py` 子进程实现，与 `executor=cpp` 的 RUNTIME 路径并列，是 VIDEO 模块内 **executor=python** 的实时算法执行后端（**不是** `AI/` 训练模块）。

单进程内完成：**多路拉流 → 双队列 YOLO/ONNX 推理 → overlay 叠框缓存 → FFmpeg RTMP 推流 → 告警 HTTP hook（下游 Kafka）→ 人脸/车牌匹配旁路队列 → 心跳**。推流与检测完全解耦：缓流器以固定输出帧率推 AI 画面，overlay/告警各自抽帧入队，Worker 异步推理。

推理栈：**Ultralytics（.pt）+ ONNXRuntime（.onnx）** 多模型串联；可选 **SAM 补充**（HTTP 调 AI model-server）、**运动门控**补检、**SimpleTracker** 轨迹关联。与 VIDEO 主服务交互主要为 **HTTP**（心跳、告警 hook、人脸/车牌 publish、模型元数据）；Kafka 由 hook/sink 侧投递，本进程不直连 Kafka 生产者。

收归 C++ 时，帧内推理/叠框/推流编码宜进 RUNTIME；任务配置热更新、告警图片落盘、hook 回调、后处理投递、SRS 清理等宜留 VIDEO 帧后。

## 2. Inventory / Findings

### 2.1 进程与配置加载

| ID | 能力 | 输入 | 输出 | 关键配置（DB / env） | 依赖 | VIDEO 交互 |
|----|------|------|------|---------------------|------|------------|
| **CAP-TASK-BOOT** | 任务启动与配置加载 | `TASK_ID`、PostgreSQL `AlgorithmTask`、关联 `Device` | 内存中的 `task_config`、`device_streams`、模型实例 | env: `TASK_ID`, `DATABASE_URL`, `TASK_CONFIG_RETRY_INTERVAL`, `TASK_CONFIG_RELOAD_INTERVAL`；DB: `model_ids`, `devices`, 各功能开关 | SQLAlchemy, `dotenv`, `load_video_env` | 由 `algorithm_task_launcher_service` 拉起子进程；daemon 注入 env |
| **CAP-TASK-HOT-RELOAD** | 任务配置热更新（30s） | DB 任务行 | 刷新采样间隔、运动门控、告警开关；可动态拉起告警 Worker | `TASK_CONFIG_RELOAD_INTERVAL` | 同 DB | 无直接 HTTP；变更来自 DB |
| **CAP-MODEL-LOAD** | 模型下载与加载 | `model_ids`（JSON）；正数走 AI 服务，负数默认 pt | `yolo_models` 字典 | DB: `model_ids`；env: `AI_SERVICE_URL`, `JWT_TOKEN`, MinIO 相关 | HTTP, MinIO, `ultralytics`, `ONNXInference` | HTTP GET `{AI_SERVICE_URL}/model/{id}` |
| **CAP-MULTI-MODEL** | 多模型同帧串联推理 | 单帧 BGR | 合并后的 `all_detections` | 同 `model_ids` 列表顺序 | 各模型实例 | 无 |
| **CAP-GPU-SCHED** | 推理/FFmpeg GPU 分配 | `device_id` / `model_id` | `cuda:N` 或 CPU；FFmpeg `-gpu` | `USE_GPU`, `GPU_IDS`, `GPU_POLICY`, `INFER_GPU_POLICY`, `FFMPEG_GPU_POLICY` | `torch.cuda`（探测） | 无 |

### 2.2 拉流与解码

| ID | 能力 | 输入 | 输出 | 关键配置 | 依赖 | VIDEO 交互 |
|----|------|------|------|----------|------|------------|
| **CAP-STREAM-INPUT** | RTSP/RTMP 输入拉流 | `device.source` 解析后的 URL | BGR 帧流 | DB: `Device.source`；env: `AI_RTSP_TRANSPORT`, `OPENCV_FFMPEG_CAPTURE_OPTIONS`, `RTSP_*_TIMEOUT_*` | OpenCV, `stream_adapter` | `resolve_gb28181_source` 可能 HTTP 调 GB28181 播放 API |
| **CAP-GB28181-SOURCE** | GB28181 虚拟源解析与重连 | `gb28181://...` | 实际 RTSP/RTMP URL | env: `GB28181_*`, `GB28181_PLAY_PROTOCOL`, `AI_GB28181_ASYNC_QUEUE_MAX` | `gb28181_source` | HTTP 国标播放接口 |
| **CAP-DECODE-FFMPEG** | FFmpeg 硬件解码路径 | 网络流 URL | `FfmpegVideoStream` 帧 | `AI_DECODE_USE_FFMPEG`（默认 1）, `AI_DECODE_FRAME_QUEUE_SIZE` | `video_decoder`, 共享内存 | 无 |
| **CAP-DECODE-ASYNC** | OpenCV 异步缓冲拉流 | RTSP/RTMP | `AsyncVideoStream` 最新/FIFO 帧 | `AI_RTSP_ASYNC_READ`, `AI_RTSP_ASYNC_QUEUE_MAX` | `async_video_stream` | 无 |
| **CAP-GRAY-RECONNECT** | RTSP 灰屏/塌缩检测重连 | 连续异常帧 | 释放并重连 | `AI_RTSP_GRAY_RECONNECT`, `AI_RTSP_GRAY_*` | OpenCV, numpy | 无 |
| **CAP-STREAM-STAGGER** | 多路建连错峰 | 设备列表 | 延迟启动 | `REALTIME_STREAM_STAGGER_SEC` | threading | 无 |

### 2.3 推理与后处理

| ID | 能力 | 输入 | 输出 | 关键配置 | 依赖 | VIDEO 交互 |
|----|------|------|------|----------|------|------------|
| **CAP-YOLO-INFER** | Ultralytics .pt 检测 | BGR 帧 | `detections[]`（bbox, class, conf） | `YOLO_IMG_SIZE`, `YOLO_DETECT_CONF`, `YOLO_DETECT_IOU`, `YOLO26_IMG_SIZE`；DB: `extract_interval`（告警侧） | `ultralytics`, `torch`, `algo_model_detect` | 模型元数据 HTTP |
| **CAP-PT-ULTRALYTICS** | 默认内置 pt 模型 | 负数 model_id | YOLO 实例 | 默认: `-1` yolo11n, `-2` yolov8n, `-3` yolo26n | `ultralytics` | 无 |
| **CAP-ONNX-INFER** | ONNX 模型检测 | BGR 帧 | 同 YOLO 格式 | `USE_GPU`；路径 `.onnx` | `onnxruntime`, `ONNXInference` | 模型 API 可返回 `onnx_model_path` |
| **CAP-YOLO26-E2E** | YOLO26 / end2end 特化 | 模型与帧 | 调高 conf/imgsz/max_det | `YOLO26_IMG_SIZE`, ultralytics>=8.4.0 | `is_yolo26_model`, `is_end2end_ultralytics_model` | 无 |
| **CAP-CLASS-FILTER** | 人脸/车牌类过滤 | 检测类名 | 过滤后列表 | DB: `face_detection_enabled`, `plate_detection_enabled` | 类名关键词匹配 | 无 |
| **CAP-ALERT-CLASS-FILTER** | 告警类别白名单 | 检测列表 | 可告警子集 | DB: `alert_class_names` | `alert_class_filter` | 无 |
| **CAP-SAM** | SAM 补充识别 | 帧 + YOLO 框 | 合并/精修检测 | DB: `sam_supplement_enabled`, `sam_supplement_config`；env: `SAM_*`（launcher 注入） | `sam_supplement`, HTTP → AI `/model/sam/predict` | HTTP AI 服务 |
| **CAP-MOTION-GATE** | 运动检测门控 | 采样帧 | `triggered`；可触发告警队列 | DB: `motion_gate_enabled`, `motion_gate_config`；env: `MOTION_*`, `ALERT_MOTION_SYNC` | `motion_gate`, OpenCV | launcher 注入 env |
| **CAP-TRACKING** | 多目标轨迹关联 | 每帧检测 | `track_id`, `duration`, `is_cached` | DB: `tracking_enabled`, `tracking_similarity_threshold`, `tracking_max_age`, `tracking_smooth_alpha`；env: `OVERLAY_USE_TRACKING` | 本地 `SimpleTracker` | 无 |

### 2.4 双队列架构与叠框

| ID | 能力 | 输入 | 输出 | 关键配置 | 依赖 | VIDEO 交互 |
|----|------|------|------|----------|------|------------|
| **CAP-SAMPLING** | overlay/告警独立抽帧 | 帧序号 | 入队与否 | env: `OVERLAY_EXTRACT_INTERVAL`, `EXTRACT_INTERVAL`, `ALERT_EXTRACT_INTERVAL`；DB: `extract_interval`（告警） | 取模逻辑 | 无 |
| **CAP-OVERLAY-QUEUE** | Overlay 检测队列 | 帧 payload | Worker 消费 | `OVERLAY_DETECTION_QUEUE_SIZE`, `OVERLAY_KEEP_LATEST`, `OVERLAY_WORKER_THREADS*` | `queue`, ThreadPoolExecutor | 无 |
| **CAP-ALERT-QUEUE** | 告警检测队列 | 帧 payload | Worker 消费 | `ALERT_DETECTION_QUEUE_SIZE`, `ALERT_KEEP_LATEST`, `ALERT_WORKER_THREADS*` | 同上 | 无 |
| **CAP-OVERLAY-CACHE** | 最新叠框缓存 | 检测结果 | `device_latest_overlays` | `LATEST_OVERLAY_MAX_AGE_MS`, overlay TTL 自动计算 | threading.Lock | 无 |
| **CAP-DRAW-OVERLAY** | 推流侧叠框绘制 | 原帧 + 缓存检测 | 标注 BGR 帧 | `OVERLAY_USE_TRACKING` | OpenCV, `draw_detection_label`（UTF-8/CJK） | 无 |
| **CAP-FIXED-RATE-PUSH** | 固定帧率推帧线程 | `device_output_frames` | FFmpeg stdin RGB24 | `AI_OUTPUT_FPS`, `AI_PUSH_FLUSH_EVERY` | threading, FFmpeg pipe | 无 |

### 2.5 RTMP 推流与画质

| ID | 能力 | 输入 | 输出 | 关键配置 | 依赖 | VIDEO 交互 |
|----|------|------|------|----------|------|------------|
| **CAP-RTMP-PUSH** | AI 画面 RTMP 推流 | RGB24 rawvideo | SRS `rtmp://.../ai/{device_id}` | env: `AI_OUTPUT_FPS`, `TARGET_*`, `FFMPEG_*`, `REALTIME_*` | FFmpeg subprocess | `resolve_device_ai_rtmp_stream`；`POD_IP` → 127.0.0.1 |
| **CAP-NVENC** | NVENC 硬件编码与回退 | 帧 | H.264 FLV | `FFMPEG_HWACCEL`, `REALTIME_NVENC_*` | FFmpeg h264_nvenc | 无 |
| **CAP-QUALITY-AUTO** | 推流失败自动降档 | 失败计数 | low/medium/high 档位切换 | `AUTO_QUALITY_*`, `AI_VIDEO_QUALITY_PROFILE` | 内部状态机 | 无 |
| **CAP-SRS-STREAM-MGMT** | SRS 流占用检查/踢流 | RTMP URL | 清理僵尸发布者 | `SRS_API_PORT`, `SRS_RTMP_PORT` | SRS HTTP API | 无 |

### 2.6 告警、匹配与帧后

| ID | 能力 | 输入 | 输出 | 关键配置 | 依赖 | VIDEO 交互 |
|----|------|------|------|----------|------|------------|
| **CAP-ALERT-HOOK** | 告警事件上报 | 告警 JSON + 图片路径 | HTTP 200 / hook status | DB: `alert_event_enabled`, `alert_event_suppress_time`；env: `ALERT_HOOK_URL`, `GATEWAY_URL` | `requests` | **HTTP POST** → `/video/alert/hook` 或 gateway；sink → **Kafka** |
| **CAP-ALERT-IMAGE** | 告警图落盘 | 标注帧 | 本地 jpg 路径 | `ALERT_IMAGES_DIR` | OpenCV, `alert_images_paths` | 与 iot-sink 共享目录 |
| **CAP-ALERT-SUPPRESS** | 设备级告警抑制 | 时间戳 | 跳过重复告警 | DB: `alert_event_suppress_time`；env: `ALERT_EVENT_SUPPRESS_INTERVAL` | threading | 无 |
| **CAP-FACE-MATCH** | 人脸匹配旁路 | 告警帧 | HTTP publish + 裁剪图 | DB: `face_matching_enabled`, `face_library_ids`, `face_matching_threshold` | `face_capture_queue_service`, ONNX 人脸检测 | **HTTP POST** `FACE_MATCHING_PUBLISH_URL` |
| **CAP-PLATE-MATCH** | 车牌匹配旁路 | 告警帧 | HTTP publish + 裁剪图 | DB: `plate_matching_enabled`, `plate_library_ids` | `plate_capture_queue_service`, 车牌 pipeline | **HTTP POST** `PLATE_MATCHING_PUBLISH_URL` |
| **CAP-POST-PROCESS-SINK** | iot-sink 后处理投递 | 检测 + 可选告警图 | 队列请求 | DB: `post_process_enabled`, `pose_analysis_enabled`, `pose_intent_enabled` | `post_process_runner` | 异步 Worker（非本进程执行） |
| **CAP-HEARTBEAT** | 存活心跳 | task 元数据 | HTTP 200 | env: `VIDEO_HEARTBEAT_URL`, `VIDEO_SERVICE_PORT`, `POD_IP` | `requests` | **HTTP POST** `/video/algorithm/heartbeat/realtime` |

### 2.7 运维与清理

| ID | 能力 | 输入 | 输出 | 关键配置 | 依赖 | VIDEO 交互 |
|----|------|------|------|----------|------|------------|
| **CAP-SRS-CLEANUP** | SRS 录像磁盘守护 | SRS 录像目录 | 删除旧文件 | `SRS_RECORD_DIR` | `playback_disk_guard_service` | 本地文件系统 |
| **CAP-ALERT-IMAGE-CLEANUP** | 告警图目录清理 | task 目录 | 删除最旧 90% | 硬编码 max 300 张 | os | 无 |
| **CAP-GRACEFUL-STOP** | SIGTERM 优雅停机 | 信号 | 释放 GPU/FFmpeg/队列 | 信号处理 | `shutdown_yolo_workers`, `cleanup_all_resources` | daemon 识别 exit 0 |

## 3. Placement hint

| Capability ID | 建议落点 (cpp / video / both / drop) | 理由 |
|---------------|--------------------------------------|------|
| CAP-YOLO-INFER, CAP-ONNX-INFER, CAP-PT-ULTRALYTICS, CAP-YOLO26-E2E, CAP-MULTI-MODEL | **cpp** | 帧内推理热路径，RUNTIME 已承载同类能力 |
| CAP-SAM | **both** | 帧内触发 + HTTP 调远程 SAM；C++ 可内嵌或保留 VIDEO 调 AI 服务 |
| CAP-TRACKING, CAP-DRAW-OVERLAY, CAP-OVERLAY-CACHE | **cpp** | 与推流同进程低延迟叠框；SimpleTracker 逻辑轻量可移植 |
| CAP-OVERLAY-QUEUE, CAP-ALERT-QUEUE, CAP-SAMPLING | **cpp** | 双队列架构是 realtime 核心调度，宜与解码/推理同仓 |
| CAP-STREAM-INPUT, CAP-DECODE-FFMPEG, CAP-DECODE-ASYNC, CAP-GB28181-SOURCE, CAP-GRAY-RECONNECT | **cpp** | 拉流解码属帧内管线前端 |
| CAP-RTMP-PUSH, CAP-FIXED-RATE-PUSH, CAP-NVENC, CAP-QUALITY-AUTO | **cpp** | FFmpeg 推流与 RUNTIME 推流职责重叠 |
| CAP-MOTION-GATE | **cpp** | 帧差轻量，宜在采样点同进程执行 |
| CAP-CLASS-FILTER, CAP-ALERT-CLASS-FILTER | **both** | 规则简单，C++ 帧内过滤；类别配置仍由 VIDEO DB 下发 |
| CAP-ALERT-HOOK, CAP-ALERT-IMAGE, CAP-ALERT-SUPPRESS | **video** | HTTP hook、落盘、抑制策略属帧后业务 |
| CAP-FACE-MATCH, CAP-PLATE-MATCH | **video** | 已是独立队列 + HTTP publish，与主推理解耦 |
| CAP-POST-PROCESS-SINK | **video** | 明确投递 iot-sink，非实时热路径 |
| CAP-HEARTBEAT | **video** | 进程监管属 VIDEO daemon 契约 |
| CAP-TASK-BOOT, CAP-TASK-HOT-RELOAD, CAP-MODEL-LOAD | **video** | 任务编排、DB、模型分发由 VIDEO 负责 |
| CAP-GPU-SCHED | **cpp** | 推理/编码 GPU 绑定在 RUNTIME 内更合适 |
| CAP-SRS-CLEANUP, CAP-ALERT-IMAGE-CLEANUP, CAP-SRS-STREAM-MGMT | **video** | 运维与 SRS 交互属平台侧 |
| CAP-GRACEFUL-STOP | **both** | C++ runtime 需对等信号语义；VIDEO daemon 保留拉起/监控 |

## 4. Gaps / Risks

1. **双份推理**：overlay 与 alert 队列对同一路可各跑一遍 `_run_yolo_on_frame`，C++ 收归时需明确是否合并为单次推理 + 分支消费，否则算力对等难保证。
2. **overlay 与 alert imgsz 不一致**：overlay 用 `OVERLAY_YOLO_IMG_SIZE`，告警用 `YOLO_IMG_SIZE`（`run_deploy.py` overlay_worker vs alert_worker），等价测试需分别覆盖。
3. **SAM 外部依赖**：SAM 走 AI HTTP 服务，延迟与可用性不在 realtime 进程内；C++ 路径需定义 SAM 缺失时的降级行为。
4. **Kafka 非直连**：告警经 hook 入 Kafka，等价验证需包含 hook + sink 全链路，不能只对比 runtime 进程日志。
5. **GB28181 / 录像回放**：帧消费速率、FIFO 缓冲、URL 重解析等行为复杂，C++ 需单独回归场景。
6. **热更新不重启模型**：`load_task_config` 热更不改 `yolo_models` 与 overlay 队列实例，仅采样/门控/告警开关；模型变更仍需重启任务。
7. **Ultralytics 线程安全**：`algo_model_detect` 对 YOLO 加锁；多 Worker 并发时 ONNX 与 YOLO 锁粒度不同，高并发下延迟分布可能不同。
8. **Windows**：当前路径依赖 FFmpeg NVENC/CUDA、Linux 式进程管理；收归 RUNTIME 时 Windows 对等是显式风险项（见 `03-cpp-runtime-baseline`）。

## 5. Equivalence notes

与 C++ `executor=cpp` 路径「表现一致」建议按以下维度验收（需 `06-equivalence-testbed` 夹具）：

| 维度 | 一致标准 | 夹具/方法 |
|------|----------|-----------|
| **检测框** | 同输入帧、同模型、同 conf/iou/imgsz 下，bbox IoU≥0.5 匹配率 ≥ 约定阈值（建议 ≥95% 主类）；YOLO26 需固定 ultralytics/ORT 版本 | 录制 RTSP 黄金片段 + 离线逐帧对比 JSON |
| **轨迹 ID** | `tracking_enabled=true` 时，同序列 track_id 切换次数、平均持续时长差异在容忍范围内（建议 ±10%） | 固定摄像头 60s 样本，对比 track 日志 |
| **叠框时序** | overlay 缓存 TTL、抽帧间隔下，框出现/消失延迟 ≤ Python 路径实测 P95 + δ（建议 δ≤200ms@25fps） | 带时间戳的推流录屏 + 检测日志对齐 |
| **推流观感** | AI 输出分辨率、fps、码率档位一致；无系统性灰屏/快进 | SRS 拉流 + ffprobe；GB28181 回放专项 |
| **告警事件** | 同场景告警次数、primary_object、`information` 内检测数一致；抑制间隔内不重复 | hook mock 捕获 JSON；对比 correlation_id 流 |
| **告警图** | 落盘路径规则、`task_{id}/{device_id}` 结构、叠框样式一致 | 目录 diff + 像素 diff（允许 JPEG 压缩差） |
| **人脸/车牌匹配** | 启用时 publish 次数、裁剪 bbox 与阈值行为一致 | mock publish URL；对比队列深度日志 |
| **运动门控** | `alert_motion_sync=true` 时补检触发次数一致 | 合成运动序列 + 静止序列 |
| **SAM** | 启用时合并框数量、source 标记（yolo/sam/yolo+sam）一致 | 固定 prompt + 框输入；mock SAM API |
| **心跳** | 10s 周期 POST，字段 `task_id/server_ip/process_id/log_path` 完整 | VIDEO API 访问日志 |
| **性能** | C++ 允许更快；若更慢需 P95 端到端延迟不超过 Python×1.2 | 同硬件多路并发压测 |

**不等价可接受项（需文档化）**：Python 独有 `OVERLAY_USE_TRACKING` 假框插值、自动画质降档、NVENC 自检回退策略差异，若 C++ 采用不同实现须在报告中标注。

## 6. Evidence

- `VIDEO/services/realtime_algorithm_service/run_deploy.py:1-94` — 模块职责、import 栈（onnx、face/plate、SAM、decode、algo_model_detect）
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:140-224` — GPU 调度 `get_infer_device`, `resolve_onnx_gpu_id`
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:393-445` — 全局状态：双队列、overlay 缓存、SAM 客户端
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:1008-1086` — `_run_yolo_on_frame`：多模型、追踪、SAM
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:1127-1213` — `_apply_runtime_sampling_config`, `_feed_stream_detection_queues`
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:1255-1287` — 人脸/车牌类过滤 `_should_keep_detection`
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:1578-1752` — `load_yolo_models`：ONNX vs Ultralytics、默认 pt、预热
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:1765-1910` — `load_task_config`：设备流、追踪器、SAM DB 配置
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:1961-2127` — `send_alert_event_async`, `try_send_alert_for_detections`
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:2258-2324` — 人脸/车牌匹配入队
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:2327-2392` — `send_heartbeat`, `heartbeat_worker`
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:2608-2696` — `_build_realtime_ffmpeg_push_cmd`
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:2827-2839` — `_resolve_ai_rtmp_push_url`
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:3167-3258` — `_fixed_rate_push_worker`
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:3270-4015` — `buffer_streamer_worker` 主循环：拉流、叠框、入队
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:4061-4141` — `draw_detections`
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:4144-4355` — `overlay_detection_worker`, `alert_detection_worker`
- `VIDEO/services/realtime_algorithm_service/run_deploy.py:4474-4648` — `main` 启动顺序
- `VIDEO/services/realtime_algorithm_service/app/utils/tracker.py:11-306` — `SimpleTracker.update`
- `VIDEO/services/realtime_algorithm_service/env.example` — 环境变量全集（采样、队列、运动门控、FFmpeg）
- `VIDEO/app/utils/algo_model_detect.py:95-158` — `run_model_detection` 统一入口
- `VIDEO/app/utils/onnx_inference.py:1-80` — ONNXRuntime CUDA provider
- `VIDEO/app/utils/motion_gate.py:1-120` — `MotionGateConfig.from_env/from_task`
- `VIDEO/app/utils/sam_supplement.py:29-145` — SAM env 与 `SamClient.predict`
- `VIDEO/app/utils/face_capture_queue_service.py:1-80` — 人脸队列与 publish
- `VIDEO/app/utils/service_urls.py:77-100` — alert/face/plate URL 解析
- `VIDEO/app/utils/decode/stream_adapter.py:1-80` — FFmpeg/OpenCV 解码适配
- `VIDEO/app/utils/post_process_runner.py:41-48` — `task_needs_sink_processing`
- `VIDEO/app/services/algorithm_task_launcher_service.py:194-227` — SAM/MOTION env 注入
- `VIDEO/models.py:902-940` — `AlgorithmTask` 核心字段（追踪、告警、人脸车牌、SAM、运动门控）
