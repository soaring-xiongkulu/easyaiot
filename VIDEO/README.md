# 🎥 VIDEO模块

VIDEO模块是一个基于Python的视频处理模块，负责视频流处理与传输。

## 功能特性

- **摄像头管理**: 支持摄像头设备的添加、删除、查询和管理，支持ONVIF协议自动发现和配置
- **PTZ控制**: 支持云台控制（上下左右移动、变焦、聚焦等），兼容ONVIF协议
- **视频流处理**: 支持RTSP流拉取、推流、转发，支持RTMP/HTTP流输出，实时视频流处理
- **抓拍功能**: 支持抓拍空间（Snap Space）管理，支持定时抓拍任务（Snap Task），支持Cron表达式配置
- **录像功能**: 支持录像空间（Record Space）管理，支持设备录像存储和回放
- **回放功能**: 支持历史录像查询和回放，支持按时间范围检索录像文件
- **算法任务**: 支持实时 / 抓拍 / 巡检算法任务，支持多算法模型并行处理，支持帧跳过配置
- **执行后端**: 三种任务默认 `executor=cpp`（本机拉起仓库 `RUNTIME` 二进制）；可选 `executor=python`。Linux 安装入口（`install_linux.sh` / `install_linux_arm.sh` / `install_linux_kylin.sh` 的 install|update）经 `scripts/ensure_runtime_cpp.sh` 编译 RUNTIME 并挂载进 VIDEO 容器；**本地 IDEA / `run.py` 启动时若本机尚无 RUNTIME 二进制，默认自动执行 `RUNTIME/install_linux.sh install`**（`RUNTIME_AUTO_INSTALL=0` 或 `EASYAIOT_RUNTIME_SKIP=1` 可关闭；容器内不自动编译）。推理默认 prefer GPU（ORT CUDA EP，失败回退 CPU）。mac 安装会跳过 RUNTIME 并提示；Windows 本轮无自动化。远程集群经 iot-node 分发 RUNTIME 后支持 executor=cpp（模型走 Ceph）。**心跳回本模块（HTTP）**；**告警/后处理默认走 MQTT → iot-sink**（`ALGO_BUS_TRANSPORT=mqtt`）
- **告警功能**: 算法事件经 MQTT 算法总线由 iot-sink 落库与通知；VIDEO **不再提供** `/video/alert/hook`
- **可重复验收**:
  - 控制面告警：`install_linux.sh verify-alert` 或 `python3 VIDEO/tools/verify_alert_ingest_e2e.py`
  - 节点 Ceph/共享媒体（列表·探针·告警图+录像目录）：`install_linux.sh ceph list|status|probe|verify`
- **设备目录**: 支持摄像头设备目录树管理，便于设备分类和组织
- **自动抽帧**: 支持从视频流中自动抽取关键帧，用于算法分析和存储
- **NVR支持**: 支持网络视频录像机（NVR）设备管理和多通道配置
- **流媒体协议**: 支持RTSP、RTMP、HTTP等主流流媒体协议
- **MinIO集成**: 支持抓拍图片和录像文件存储到MinIO对象存储（由 iot-sink 归档）
- **Kafka集成**: 告警 Kafka 由 iot-sink 消费/转发；VIDEO 不再作为告警事件主入口
- **Nacos集成**: 支持服务注册与发现，实现服务自动注册和健康检查
- **性能监控**: 实时监控视频处理性能，支持服务心跳监控和超时检测

## RUNTIME / GPU 部署覆盖

高性能执行器由共享脚本 [`scripts/ensure_runtime_cpp.sh`](scripts/ensure_runtime_cpp.sh) 接入：

| 安装入口 | RUNTIME 编译挂载 |
|----------|------------------|
| `install_linux.sh` | 是 |
| `install_linux_arm.sh` | 是 |
| `install_linux_kylin.sh` | 是 |
| `install_mac.sh` | 跳过并打印说明（非 Linux，无 CUDA 一键包） |
| Windows | 本轮无自动化 |
| 计算节点（iot-node 集群） | WEB 一键「分发 RUNTIME」或算法全量分发（控制面自动编译→导出→SSH 安装） |

推理默认 `prefer_gpu=true`（环境 `USE_GPU` / `RUNTIME_PREFER_GPU`）；ORT CUDA EP 失败则回退 CPU。强制 CPU：`RUNTIME_FORCE_CPU=1`。跳过编译：`EASYAIOT_RUNTIME_SKIP=1`。关闭本地启动自动编译：`RUNTIME_AUTO_INSTALL=0`。强制要求 RUNTIME 可用否则启动失败：`EASYAIOT_RUNTIME_REQUIRED=1`。

集群高性能路径（一键，无需先手跑 install）：WEB「业务运行时分发」→ RUNTIME(C++)「分发 RUNTIME」，或算法 bundle 全量分发。
