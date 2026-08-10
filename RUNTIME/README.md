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

> 本机与集群节点均支持 `executor=cpp`（需先经 iot-node 分发 RUNTIME）。与 `EDGE/runtime/`（Python 边缘运行包）不是同一回事。

## GPU 推理策略（默认）

- 默认 **prefer GPU**：ONNX Runtime 优先挂载 `CUDAExecutionProvider`，Session 创建失败则自动回退 CPU，任务不中断。
- 配置（`[ai]` / 环境变量）：
  - `prefer_gpu` / `RUNTIME_PREFER_GPU`（默认 `true`）
  - `force_cpu` / `RUNTIME_FORCE_CPU`（强制仅 CPU）
  - `gpu_device_id` / `RUNTIME_GPU_DEVICE_ID` 或 `CUDA_VISIBLE_DEVICES`
- 日志会出现 `Using CUDA EP` 或 `Using CPU execution (fallback)`；`GET /health` 含 `infer_ep=cuda|cpu`。
- **本轮不做**：TensorRT EP、FFmpeg NVDEC/NVENC。

安装侧：检测到 `nvidia-smi` 时优先下载 **GPU ORT** 包（如 `onnxruntime-linux-x64-gpu-*`），写入 `deploy.env` 的 CUDA lib 路径；无 GPU / 下载失败则用 CPU 包并告警。

## 原子模式（只部署 RUNTIME · 计算节点）

用于**只装高性能执行器**的机器（边缘算力盒 / 集群计算节点），不部署 VIDEO/WEB/DEVICE。

```bash
# 顶层入口
VIDEO_BASE_URL=http://<中心VIDEO主机>:6000 bash .scripts/docker/install_linux.sh runtime

# 或模块入口
VIDEO_BASE_URL=http://192.168.1.10:6000 ./RUNTIME/install_linux.sh atomic
# 等价：./RUNTIME/install_linux.sh atomic http://192.168.1.10:6000
```

行为：

1. 同源容器编译 RUNTIME（默认 `EASYAIOT_RUNTIME_BUILD_MODE=docker`）
2. `export_runtime_cpp.sh` 打离线包
3. 安装到 `${EASYAIOT_RUNTIME_INSTALL_DIR:-/opt/easyaiot/RUNTIME}`
4. 写入 `node.env` / `env.sh` / `config/atomic.example.ini`

**汇聚上报（必填）**：`VIDEO_BASE_URL` 指向中心 VIDEO。节点上的告警/心跳 HTTP 回调：

| 类型 | URL |
|------|-----|
| 告警 | `${VIDEO_BASE_URL}/video/alert/hook` |
| 心跳 realtime | `${VIDEO_BASE_URL}/video/algorithm/heartbeat/realtime` |
| 心跳 patrol | `${VIDEO_BASE_URL}/video/algorithm/heartbeat/patrol` |

本节点**不落库**；正式任务仍由中心 VIDEO + Agent 下发 `task_*.ini` 并拉起二进制。手工调试：

```bash
source /opt/easyaiot/RUNTIME/env.sh
$RUNTIME_BIN /opt/easyaiot/RUNTIME/config/atomic.example.ini
```

## 集群分发（iot-node · 一键）

**页面只需一步**：WEB「业务运行时分发」→ **高性能算法 · RUNTIME(C++)** →「分发 RUNTIME」  
（或算法 bundle「全量分发」，会顺带安装 RUNTIME。）

控制面后台自动串联：`install_linux.sh`（若未编译）→ `export_runtime_cpp.sh` → SSH 安装到节点 `/opt/easyaiot/RUNTIME`。

- 节点二进制：`/opt/easyaiot/RUNTIME/bin/RUNTIME`
- 远程任务：VIDEO 写 ini → Agent 落盘启动；模型走 Ceph
- API：`POST /admin-api/node/workload-bundle/runtime-cpp/batch-deploy-ssh`
- 关闭自动编译：环境变量 `RUNTIME_AUTO_INSTALL=0`（仅当你要手工控制编译时）

## 一键部署（推荐 · 本机 VIDEO）

VIDEO 各 Linux 安装入口通过共享脚本 [`VIDEO/scripts/ensure_runtime_cpp.sh`](../VIDEO/scripts/ensure_runtime_cpp.sh) 编译并挂载 RUNTIME：

| 入口 | RUNTIME |
|------|---------|
| `VIDEO/install_linux.sh` | 编译 + 挂载 |
| `VIDEO/install_linux_arm.sh` | 同上 |
| `VIDEO/install_linux_kylin.sh` | 同上 |
| 顶层 `install_business_linux.sh` / centos / openeuler | 委托 VIDEO，间接覆盖 |
| `VIDEO/install_mac.sh` | **跳过**并打印说明（非 Linux / 无 CUDA 一键包） |
| Windows | **本轮不管**；需手工编译或后续 DirectML 专题 |
| 计算节点（集群） | 走上方 **集群分发**，不是 compose 挂载 |

```bash
# 业务一键部署里包含 VIDEO 时会连带执行
./VIDEO/install_linux.sh install

# 或单独安装 RUNTIME
./RUNTIME/install_linux.sh
```

产出：

- `RUNTIME/build/RUNTIME`
- `RUNTIME/deploy.env`（供 VIDEO 写入 compose 挂载，含 ORT/CUDA lib）
- `VIDEO/.docker-compose.runtime.override.yaml`（容器内 `/opt/easyaiot/RUNTIME` + conda/ORT[/cuda] lib）
- `RUNTIME/.bundle-runtime/{arch}/easyaiot-runtime-*.tar.gz`（集群离线包）

跳过：`EASYAIOT_RUNTIME_SKIP=1`  
强制失败中止 VIDEO：`EASYAIOT_RUNTIME_REQUIRED=1`

## 手动环境 / 编译

默认 **方案 1：VIDEO 同源容器编译**（系统 `g++`，与 `video-service` 同 Ubuntu/glibc，无需降级 conda sysroot）：

```bash
./RUNTIME/install_linux.sh build
# 等价：EASYAIOT_RUNTIME_BUILD_MODE=docker ./RUNTIME/install_linux.sh build
```

- 构建镜像优先：`video-service:latest` → 已缓存的 `pytorch/pytorch:2.9.0-cuda12.8-cudnn9-devel` → `ubuntu:22.04`
- 覆盖镜像：`EASYAIOT_RUNTIME_BUILD_IMAGE=...`
- 宿主机 conda `easyaiot-runtime` 只提供 OpenCV5/glog/ffmpeg 等依赖库，并挂进 VIDEO 容器

回退本机编译（新 glibc 主机上产物可能无法进 VIDEO 容器）：

```bash
EASYAIOT_RUNTIME_BUILD_MODE=host ./RUNTIME/install_linux.sh build
# 或：source RUNTIME/scripts/env.sh && ./RUNTIME/scripts/build_linux.sh
```

依赖：OpenCV 5、FFmpeg、glog、jsoncpp、libcurl，以及官方 ONNX Runtime C++ SDK（有 GPU 时优先 `onnxruntime-linux-*-gpu-1.23.2`，否则 CPU 包；默认下载到仓库根 `.deps/`）。

## 运行

```bash
source RUNTIME/scripts/env.sh
$RUNTIME_BIN RUNTIME/config/config.example.ini
```

VIDEO 侧默认走高性能任务时，启停走原有任务接口即可。强制 CPU 可设 `RUNTIME_FORCE_CPU=1`。

## 流水线

`Pull+Decode → FrameRing(drop-oldest) → Infer → ResultRing → Emit(VIDEO hook)`

- 心跳：realtime/snap → `POST /video/algorithm/heartbeat/realtime`；patrol → `.../heartbeat/patrol`
- 告警：`POST /video/alert/hook`（snap 的 hook `task_type` 为 `snapshot`）
- 健康：`GET /health`；控制口可 `POST /stop` 优雅退出

## 配置

见 [config/config.example.ini](config/config.example.ini)。VIDEO 对接段为 `[video_task]`。
