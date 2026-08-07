# RUNTIME 模块

EasyAIoT 的 **C++ 帧执行器**（由原 TASK 演进）。负责拉流、解码、AI 推理与结果回传；**不替代 VIDEO**。

## 与 VIDEO 的关系

| 角色 | 模块 | 职责 |
|------|------|------|
| 编排 / 预览 / 告警面 | **VIDEO** | 设备流、SRS 转发、任务生命周期、alert hook、Kafka、落库 |
| 高速执行后端 | **RUNTIME** | 拉流 → 解码 → 推理 → 结构化结果 |

算法任务默认 `executor=cpp`：VIDEO 守护进程生成 `config/task_{id}.ini` 并拉起本二进制；可选 `executor=python`。

单二进制支持三种 `task_type`：

| task_type | 行为 |
|-----------|------|
| `realtime` | 长连接拉流 + Pipeline（FFmpeg），可配置抽帧 |
| `snap` | Cron 调度抓拍（SnapScheduler） |
| `patrol` | 多设备轮巡（PatrolScheduler） |

> 当前仅本机部署；远程节点 `executor=cpp` 会被 VIDEO 拒绝。与 `EDGE/runtime/`（Python 边缘运行包）不是同一回事。

## 环境（本机已用 conda 配好）

系统 apt 无写权限时，使用 Miniconda 环境 `easyaiot-runtime`：

```bash
source RUNTIME/scripts/env.sh
# 或手动：
# source ~/miniconda3/etc/profile.d/conda.sh && conda activate easyaiot-runtime
```

依赖：cmake、OpenCV 5、FFmpeg、glog 0.6、jsoncpp、libcurl，以及官方 ONNX Runtime C++ SDK（默认：仓库根 `.deps/onnxruntime-linux-x64-1.23.2`）。

## 编译

```bash
source RUNTIME/scripts/env.sh
./RUNTIME/scripts/build_linux.sh
# 产出: RUNTIME/build/RUNTIME
```

## 运行

```bash
source RUNTIME/scripts/env.sh
$RUNTIME_BIN RUNTIME/config/config.example.ini
```

VIDEO 侧将任务 `executor` 设为 `cpp` 后，启停走原有任务接口即可（需保证 `LD_LIBRARY_PATH` 含 conda lib 与 ORT `lib`）。

## 流水线

`Pull+Decode → FrameRing(drop-oldest) → Infer → ResultRing → Emit(VIDEO hook)`

- 心跳：realtime/snap → `POST /video/algorithm/heartbeat/realtime`；patrol → `.../heartbeat/patrol`
- 告警：`POST /video/alert/hook`（snap 的 hook `task_type` 为 `snapshot`）
- 健康：`GET /health`（含 drop/latency 指标）；控制口可 `POST /stop` 优雅退出

## 配置

见 [config/config.example.ini](config/config.example.ini)。VIDEO 对接段为 `[video_task]`，可含 `devices_json`、`cron_expression`、`patrol_*`、`frame_skip`、检测区域等。
