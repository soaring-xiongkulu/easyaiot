# RUNTIME 模块

EasyAIoT 的 **C++ 帧执行器**（由原 TASK 演进）。负责拉流、解码、AI 推理与结果回传；**不替代 VIDEO**。

## 与 VIDEO 的关系

| 角色 | 模块 | 职责 |
|------|------|------|
| 编排 / 预览 / 告警面 | **VIDEO** | 设备流、SRS 转发、任务生命周期、alert hook、Kafka、落库 |
| 高速执行后端 | **RUNTIME** | 拉流 → 解码 → 推理 → 结构化结果 |

realtime 任务设置 `executor=cpp` 时，VIDEO 守护进程生成 `config/task_{id}.ini` 并拉起本二进制；默认仍为 `executor=python`。

> 与 `EDGE/runtime/`（Python 边缘运行包）不是同一回事。

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

VIDEO 侧将 realtime 任务 `executor` 设为 `cpp` 后，启停走原有任务接口即可。

## 流水线

`Pull+Decode → FrameRing(drop-oldest) → Infer → ResultRing → Emit(VIDEO hook)`

- 心跳：`POST /video/algorithm/heartbeat/realtime`
- 告警：`POST /video/alert/hook`
- 健康：`GET /health`（含 drop/latency 指标）

## 配置

见 [config/config.example.ini](config/config.example.ini)。VIDEO 对接段为 `[video_task]`。
