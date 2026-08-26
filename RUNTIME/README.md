# RUNTIME 模块

EasyAIoT 的 **C++ 帧执行器**。负责拉流、解码、AI 推理与结果回传；**不替代 VIDEO**。

| 角色 | 模块 | 职责 |
|------|------|------|
| 编排 / 预览 / 任务管理 | **VIDEO** | 设备流、SRS 转发、任务生命周期、**HTTP 心跳**、启停 |
| 事件落库 / 通知 / 归档 | **iot-sink** | 订阅 MQTT 算法总线，告警入库、MinIO 归档、通知 enrichment |
| 高速执行后端 | **RUNTIME** | 拉流 → 解码 → 推理 → **MQTT 告警** + **HTTP 心跳**；`realtime` 默认推带框流到 `ai_rtmp` |

双路媒体（互不占用）：

| 链路 | 谁推 | SRS 路径 | 用途 |
|------|------|----------|------|
| 原画预览 | VIDEO 推流转发 | `live/{device_id}` | WEB 实时预览 |
| AI 检测画 | **RUNTIME**（`enable_rtmp=true`） | `ai/{device_id}` | WEB 看带框图 |

算法任务默认 `executor=cpp`：VIDEO 守护进程生成 `config/task_{id}.ini` 并拉起本二进制；可选 `executor=python`。

单二进制支持三种 `task_type`：

| task_type | 行为 |
|-----------|------|
| `realtime` | 长连接拉流 + Pipeline（FFmpeg），可配置抽帧；**默认推 `ai/` 带框流** |
| `snap` | Cron 调度抓拍（SnapScheduler）；以结构化结果/告警为主 |
| `patrol` | 多设备轮巡（PatrolScheduler）；以结构化结果/告警为主 |

> 事件面默认 `ALGO_BUS_TRANSPORT=mqtt`（`mqtt/iot-alert-notification` 等）→ iot-sink；心跳仍 HTTP → VIDEO。原 EDGE 模块已移除，边缘算力请用**云边一体**（`integrated` / `atomic`）。

---

## 目录

- [部署场景怎么选](#部署场景怎么选)
- [云边一体（integrated）](#云边一体integrated)
- [纯边缘（部署规格 edge）](#纯边缘部署规格-edge)
- [原子模式（向后兼容别名）](#原子模式向后兼容别名)
- [集群分发（iot-node · 一键）](#集群分发iot-node--一键)
- [本机 VIDEO 一键挂载（推荐中心机）](#本机-video-一键挂载推荐中心机)
- [编译与依赖](#编译与依赖)
- [版本控制](#版本控制)
- [运行与运维](#运行与运维)
- [流水线与回调](#流水线与回调)
- [配置说明](#配置说明)
- [GPU 推理策略](#gpu-推理策略)
- [常见问题](#常见问题)

---

## 部署场景怎么选

边缘侧有两种正式部署形态；平台规格 `mini` / `standard` / `full` 用于中心或一体机交付。

| 场景 | 定位 | 入口 | 适用 |
|------|------|------|------|
| **纯边缘形态** | 汇聚面与边缘算力同机，业务本地闭环 | `install` → `edge` → `standalone` | 独立站点、轻量边缘主机 |
| **云边一体形态** | 本机仅部署算力节点，汇聚面在中心 | `install` → `edge` → `integrated` | 算力扩展、多节点推理 |
| **中心 / 一体机** | 平台全量或精简规格 | `EASYAIOT_DEPLOY_PROFILE=mini\|standard\|full ... install` | 编排、预览与集中管理 |
| **批量节点** | 多机分发算力 | WEB「业务运行时分发」 | 集群一键 |
| **开发调试** | 源码树编译 | `./RUNTIME/install_linux.sh build` | 改代码、本地联调 |

> **操作系统限制**：命令部署会自动检测本机 `os_family + arch`，必须在 [RUNTIME 覆盖矩阵](scripts/runtime_os_matrix.sh) 内（ubuntu/el/openeuler/麒麟等），否则拒绝部署并提示支持的 OS 列表。

### 边缘两种形态怎么装

| 形态 | 命令 | 汇聚面 | 典型场景 |
|------|------|--------|----------|
| **纯边缘形态** | `install` → 选 `edge` → 选 `standalone` | 本机 | 一台机器闭环 |
| **云边一体形态** | `install` → 选 `edge` → 选 `integrated` | 远端中心 | 边缘算力盒接入已有平台 |

兼容：`EASYAIOT_DEPLOY_PROFILE=edge EASYAIOT_EDGE_MORPHOLOGY=standalone ... install`；  
`EASYAIOT_DEPLOY_PROFILE=edge EASYAIOT_EDGE_MORPHOLOGY=integrated VIDEO_BASE_URL=... install`。`atomic` / `runtime-integrated` 为历史别名。

拓扑示意（能力视角）：

```text
摄像头 ──► 汇聚面（原画预览、任务编排、心跳）
              │
              │ 下发任务配置并拉起执行器
              ▼
         边缘算力 ──► 心跳 / 告警回传汇聚面
                   ──► 检测流推送至流媒体
```

汇聚面与中间件可在远端（云边一体）或本机（纯边缘）。

---

## 云边一体（integrated）

用于**仅部署边缘算力节点**的场景：汇聚面指向已有中心平台。除命令独立部署外，也可通过控制台「业务运行时分发」或 Agent 远程安装。

> **云边一体 ≠ 永不推流。** 中心下发正式实时任务时，执行器仍会按配置推送带框检测流。

### 前置条件

- Linux x86_64 或 aarch64；操作系统在 RUNTIME 矩阵内
- Docker（默认同源容器编译）
- 能访问 VIDEO HTTP 口（默认 `:6000`）；正式推流时还能访问 SRS RTMP（默认 `:1935`）

### 命令独立部署（算力节点）

```bash
# 方式 A：仓库顶层入口
VIDEO_BASE_URL=http://<VIDEO>:6000 \
GATEWAY_URL=http://<Gateway>:48080 \
MQTT_BROKER_URLS=<EMQX>:1883 \
SRS_RTMP_BASE=rtmp://<SRS>:1935 \
  bash .scripts/docker/install_linux.sh runtime-integrated

# 方式 B：模块入口
VIDEO_BASE_URL=http://192.168.1.10:6000 \
GATEWAY_URL=http://192.168.1.10:48080 \
  ./RUNTIME/install_linux.sh integrated

# 向后兼容别名
VIDEO_BASE_URL=http://192.168.1.10:6000 ./RUNTIME/install_linux.sh atomic
```

脚本会：① 校验 OS 是否在矩阵内 → ② 按本机 OS 自动编译/导出离线包 → ③ 安装到 `/opt/easyaiot/RUNTIME` → ④ 写入 `node.env`（含汇聚地址）。

### 安装过程做了什么

1. 检测 `os_family + arch`，不在矩阵内则拒绝
2. 查找或按本机 OS 编译导出离线包
3. `install_runtime_cpp.sh` 安装到 `${EASYAIOT_RUNTIME_INSTALL_DIR:-/opt/easyaiot/RUNTIME}`
4. 写入节点配置：

| 文件 | 作用 |
|------|------|
| `node.env` | `EASYAIOT_RUNTIME_DEPLOY_MODE=integrated`、`VIDEO_BASE_URL`、`GATEWAY_URL`、MQTT、可选 `AI_RTMP_URL` |
| `env.sh` | `source` 后导出 `RUNTIME_BIN`、`LD_LIBRARY_PATH`、汇聚变量 |
| `config/atomic.example.ini` | **手工调试**示例任务 |

### 汇聚上报（必填）

`VIDEO_BASE_URL` 必须指向 VIDEO（远端或本机）。节点上的 HTTP 回调：

| 类型 | URL |
|------|-----|
| 告警 | MQTT → EMQX → iot-sink |
| 心跳 realtime / snap | `${VIDEO_BASE_URL}/video/algorithm/heartbeat/realtime` |
| 心跳 patrol | `${VIDEO_BASE_URL}/video/algorithm/heartbeat/patrol` |

---

## 纯边缘形态（部署规格 edge）

汇聚面与边缘算力**同机**：在平台 `install` 中选择 `edge` → `standalone`。

```bash
# 推荐：install 交互 → edge → standalone
bash .scripts/docker/install_linux.sh install

# 非交互等价
EASYAIOT_DEPLOY_PROFILE=edge EASYAIOT_EDGE_MORPHOLOGY=standalone \
  bash .scripts/docker/install_linux.sh install
```

### 能力约定

- **同机闭环**：编排、预览与边缘推理部署在同一主机
- **本地存储**：告警图与录像落本地媒体目录，不经对象存储
- **告警链路**：边缘推理经 HTTP 直连业务面落库；录像回调本地登记
- **无 MQTT 总线**：纯边缘形态不部署 EMQX，VIDEO 生成 ini 时强制 `algo_bus_transport=http`，告警经 `alert_hook_url`（本机 VIDEO `/video/alert/hook`）投递，`mqtt_broker_urls` 等 `mqtt_*` 配置在该形态下不生效

### 部署后访问

| 入口 | 默认端口 | 用途 |
|------|----------|------|
| 控制台 | `:8888` | 算法任务、设备管理、实时预览 |
| 业务 API | `:6000` | 编排、登录、心跳、告警与推流协作 |
| 流媒体 RTMP | `:1935` | 原画与检测流 |

### 登录

默认账号：`admin` / `admin123`（控制台 `:8888`）。

与「云边一体形态」的区别：纯边缘形态不依赖远端中心；云边一体形态本机仅部署算力，须在 install 中选择 `edge` → `integrated` 并填写中心汇聚面地址。

---

## 原子模式（向后兼容别名）

`atomic` = `integrated`（云边一体），以下文档保留原有用法说明。

### 前置条件

- Linux x86_64 或 aarch64；Docker（默认同源容器编译）
- 能访问中心汇聚面 HTTP 口（默认 `:6000`）；正式推流时还能访问中心/集群流媒体 RTMP（默认 `:1935`）
- 有 GPU 时建议装好驱动 + `nvidia-smi`（可选，失败会回退 CPU）

### 一键安装

```bash
# 方式 A：平台 install → edge → integrated
bash .scripts/docker/install_linux.sh install

# 方式 A（自动化）
EASYAIOT_DEPLOY_PROFILE=edge \
EASYAIOT_EDGE_MORPHOLOGY=integrated \
VIDEO_BASE_URL=http://<中心主机>:6000 \
  bash .scripts/docker/install_linux.sh install

# 兼容别名
# ... install_linux.sh runtime-integrated

# 方式 B：模块入口
VIDEO_BASE_URL=http://192.168.1.10:6000 ./RUNTIME/install_linux.sh integrated
# 或把地址当参数：
./RUNTIME/install_linux.sh integrated http://192.168.1.10:6000

# 可选：安装时就写好手工调试用的检测流地址（正式任务仍由中心下发）
SRS_RTMP_BASE=rtmp://192.168.1.10:1935 \
  VIDEO_BASE_URL=http://192.168.1.10:6000 \
  ./RUNTIME/install_linux.sh atomic
# 或直接指定完整 AI 地址：
# AI_RTMP_URL=rtmp://192.168.1.10:1935/ai/my_cam ...
```

安装目录可用 `EASYAIOT_RUNTIME_INSTALL_DIR` 覆盖（默认 `/opt/easyaiot/RUNTIME`）。

### 安装过程做了什么

1. 同源容器编译 RUNTIME（默认 `EASYAIOT_RUNTIME_BUILD_MODE=docker`）
2. `export_runtime_cpp.sh` 打离线包 → `.bundle-runtime/<arch>/easyaiot-runtime-*.tar.gz`
3. `install_runtime_cpp.sh` 安装到 `${EASYAIOT_RUNTIME_INSTALL_DIR:-/opt/easyaiot/RUNTIME}`
4. 写入节点配置：

| 文件 | 作用 |
|------|------|
| `node.env` | `VIDEO_BASE_URL`、告警/心跳 URL、可选 `AI_RTMP_URL` |
| `env.sh` | `source` 后导出 `RUNTIME_BIN`、`LD_LIBRARY_PATH`、汇聚变量 |
| `config/atomic.example.ini` | **手工调试**示例任务（非正式生产任务） |
| 仓库内 `RUNTIME/atomic.env` | 指向本次安装目录的本地指针 |

### 汇聚上报（必填）

`VIDEO_BASE_URL` 必须指向中心 VIDEO。节点上的 HTTP 回调：

| 类型 | URL |
|------|-----|
| 告警 | `${VIDEO_BASE_URL}/video/alert/hook` |
| 心跳 realtime / snap | `${VIDEO_BASE_URL}/video/algorithm/heartbeat/realtime` |
| 心跳 patrol | `${VIDEO_BASE_URL}/video/algorithm/heartbeat/patrol` |

本节点**不落库**；告警与任务状态由中心 VIDEO 入库 / Kafka。

### 检测推流

| 场景 | 行为 |
|------|------|
| VIDEO 下发 `executor=cpp` + `realtime` | 必有独立 `rtmp://…/ai/{device}`，`enable_rtmp=true`，启动即推 |
| 原子安装待命 / 未设 SRS 变量 | 示例 ini 可不推，仅告警/心跳 |
| 原子安装且设置了 `SRS_RTMP_BASE` 或 `AI_RTMP_URL` | 示例 ini 打开 `enable_rtmp`，便于手工冒烟 |

### 安装后检查

```bash
./RUNTIME/install_linux.sh status
# 或直接看节点目录
ls -l /opt/easyaiot/RUNTIME/bin/RUNTIME
cat /opt/easyaiot/RUNTIME/node.env
```

### 手工调试（冒烟）

1. 编辑 `/opt/easyaiot/RUNTIME/config/atomic.example.ini`：改 `rtsp_url`、模型路径等  
2. 启动：

```bash
source /opt/easyaiot/RUNTIME/env.sh
$RUNTIME_BIN /opt/easyaiot/RUNTIME/config/atomic.example.ini
```

3. 另开终端验证：

```bash
# 控制口默认 8123（见 ini [task].control_port）
curl -s http://127.0.0.1:8123/health
# 中心侧应能看到 heartbeat / alert；若开了 enable_rtmp，SRS 上应有 ai/ 应用
```

4. 优雅停止：`curl -s -X POST http://127.0.0.1:8123/stop`

### 正式任务怎么跑

原子节点装好后**不必**长期手工跑 `atomic.example.ini`。正式流程：

1. 中心已部署 VIDEO（及 SRS / WEB 等）
2. 节点已装 RUNTIME（原子安装，或 WEB「节点管理 → 业务运行时分发 → 分发 RUNTIME」），且 Agent 在线
3. WEB **算法任务** → 新建 → 选「实时/抓拍/巡检算法任务（高性能）」
4. **调度策略**选「本机」/「自动调度节点」/「指定节点」（指定时选目标原子/计算节点）→ 保存
5. 列表点 **启动**：中心 VIDEO 生成含 `ai_rtmp` 的 ini，经 iot-node 下发到节点并拉起 `/opt/easyaiot/RUNTIME/bin/RUNTIME`
6. 告警/心跳回中心；realtime 带框流进中心 `ai/{device}`，原画仍走 `live/`

> 无已分发原子节点时：调度选 **本机** 即可——中心 VIDEO 安装时会经 `ensure_runtime_cpp.sh` 挂载本机 RUNTIME，任务仍可跑。选自动/指定节点但目标机未装 RUNTIME 时，启动会明确失败并提示先分发。

### 边缘计算节点（摄像头接入边缘节点）

摄像头/NVR 可通过**边缘节点接入**（WEB 添加设备时选择接入节点；Agent 代执行 ONVIF 发现、网段扫描、RTSP 验证）。这类任务的执行器运行在**边缘节点**上，RUNTIME 负责三件事：

1. **拉流**：直接拉取边缘侧可达的摄像头 RTSP（VIDEO 下发 `rtsp_url` 原地址）。
2. **回传**：心跳、告警、带框检测流全部回中心——心跳/告警回中心 VIDEO/MQTT，`ai/{device}` 推中心 SRS（VIDEO 下发 `rtmp_url`）。
3. **身份归属**：心跳上报**节点真实 IP**（`HOST_IP`/`POD_IP` 环境变量优先，否则探测本机非回环网卡；不依赖 127.0.0.1）+ **节点标识**（ini `compute_node_id`，回退 `COMPUTE_NODE_ID`/`NODE_ID` 环境变量）。VIDEO 远程部署时自动把目标节点 id 写入 ini/env，因此：

   - 控制面任务列表「服务地址」显示边缘节点真实地址（python 执行器行为一致）；
   - MQTT 告警与 HTTP 心跳载荷中的 `node_id` 归属到实际执行节点，而不是控制面自身；
   - 边缘节点转发的推流任务同样上报真实地址，避免播放地址回退到 127.0.0.1。

   告警总线地址（`mqtt_broker_urls`）由 VIDEO 远程部署时**重写为控制面可达地址**：边缘节点不安装 EMQX，若 ini 中残留 `127.0.0.1:1883`，MQTT 告警将连自身回环而静默丢失；本地运行（主节点）仍默认 `127.0.0.1:1883`。

调度约束由 VIDEO 完成（边缘接入摄像头 ⇒ `schedule_policy=node` + 目标节点=接入节点），RUNTIME 侧无需额外配置；`compute_node_id` 仅为身份上报字段，不影响拉流/推流目标。

---

## 集群分发（iot-node · 一键）

**页面只需一步**：WEB「业务运行时分发」→ **高性能算法 · RUNTIME(C++)** →「分发 RUNTIME」  
（或算法 bundle「全量分发」，会顺带安装 RUNTIME。）

控制面按节点 **OS family + arch** 选本地 tarball，SSH 安装到 `/opt/easyaiot/RUNTIME`。**缺包时在 SSH 之前即失败**，并提示对应 OS 的容器内导出命令（不会把 Ubuntu 包发到 openEuler / 麒麟）。

- 节点二进制：`/opt/easyaiot/RUNTIME/bin/RUNTIME`
- 远程任务：VIDEO 写 ini → Agent 落盘启动；模型可走对象存储 / Ceph
- API：`POST /admin-api/node/workload-bundle/runtime-cpp/batch-deploy-ssh`
- 关闭自动编译：环境变量 `RUNTIME_AUTO_INSTALL=0`（仅当你要手工控制编译时）

### 分发前预检（推荐）

```bash
# 按 Sentinel 节点 id 检查（读 os_family + 本地 tarball）
bash RUNTIME/scripts/preflight_runtime_bundle.sh --node 5

# 或显式 OS
bash RUNTIME/scripts/preflight_runtime_bundle.sh openeuler22 x86_64

# 顶层 install_linux 入口（各 OS 一键脚本均委托此命令）
bash .scripts/docker/install_linux.sh preflight-runtime-cpp --node 5
```

缺包时 iot-node 会提示：

```bash
bash RUNTIME/scripts/export_runtime_os_container.sh openeuler22
```

### 矩阵构建（与 COMPILE 对齐）

| 命令 | 说明 |
|------|------|
| `bash RUNTIME/build_runtime_matrix.sh` | 默认实验室优先包（openeuler22 / ubuntu26 / el9） |
| `bash RUNTIME/build_runtime_matrix.sh --all` | 全矩阵 |
| `bash RUNTIME/build_runtime_matrix.sh --compile-target openeuler` | 与 `COMPILE/build.sh openeuler` 同范围 |
| `bash .scripts/docker/install_linux.sh build-runtime-cpp openeuler22` | 顶层一键入口 |
| `bash .scripts/docker/install_linux_openeuler.sh build-runtime-cpp openeuler22` | openEuler 入口（转交 install_linux） |
| `bash .scripts/docker/install_linux_kylin.sh build-runtime-cpp kylin10` | 麒麟须单独镜像，见下 |

产物路径：`RUNTIME/.bundle-runtime/{os_family}/{arch}/easyaiot-runtime-*.tar.gz`

**麒麟（Kylin）**：RUNTIME 与 openEuler **不能混用**。须设置专用容器镜像后再导出，例如：

```bash
export RUNTIME_KYLIN10_ARM64_IMAGE=<kylin-v10-sp3-arm64-image>
bash RUNTIME/scripts/export_runtime_os_container.sh kylin10
```

或在实机麒麟上：`bash RUNTIME/export_runtime_cpp.sh`（本机 ABI 一致时控制面可自动导出）。

> 批量分发后，各节点仍建议配置可达的中心 `VIDEO_BASE_URL`（原子安装会写 `node.env`；分发场景由 Agent/平台约定工作目录与环境）。

---

## 本机 VIDEO 一键挂载（推荐中心机）

VIDEO 各 Linux 安装入口通过 [`VIDEO/scripts/ensure_runtime_cpp.sh`](../VIDEO/scripts/ensure_runtime_cpp.sh) 编译并挂载 RUNTIME：

| 入口 | RUNTIME |
|------|---------|
| `VIDEO/install_linux.sh` | 编译 + 挂载 |
| `VIDEO/install_linux_arm.sh` | 同上 |
| `VIDEO/install_linux_kylin.sh` | 同上 |
| 顶层 `install_business_linux.sh` / centos / openeuler | 委托 VIDEO，间接覆盖 |
| `VIDEO/install_mac.sh` | **跳过**并打印说明（非 Linux / 无 CUDA 一键包） |
| Windows | **本轮不管**；需手工编译或后续 DirectML 专题 |
| 计算节点（集群） | 走 **原子模式** 或 **集群分发**，不是 compose 挂载 |

```bash
# 业务一键部署里包含 VIDEO 时会连带执行
./VIDEO/install_linux.sh install

# 或单独在源码树安装/编译 RUNTIME（供本机挂载，不是原子节点目录）
./RUNTIME/install_linux.sh
./RUNTIME/install_linux.sh build
```

产出：

- `RUNTIME/build/RUNTIME`
- `RUNTIME/deploy.env`（供 VIDEO 写入 compose 挂载，含 ORT/CUDA lib）
- `VIDEO/.docker-compose.runtime.override.yaml`（容器内 `/opt/easyaiot/RUNTIME` + conda/ORT[/cuda] lib）
- `RUNTIME/.bundle-runtime/{arch}/easyaiot-runtime-*.tar.gz`（集群离线包）

跳过：`EASYAIOT_RUNTIME_SKIP=1`  
强制失败中止 VIDEO：`EASYAIOT_RUNTIME_REQUIRED=1`

---

## 编译与依赖

**统一入口（推荐）：**

```bash
./RUNTIME/install_linux.sh
```

在终端（TTY）下会弹出交互菜单：选择「编译」后，再选择 **本机 conda** 或 **Docker 同源容器** 编译方式；脚本会自动识别当前用户的 conda 与 ORT 路径。

非交互环境（CI/脚本）默认 Docker 编译，可用 `EASYAIOT_RUNTIME_BUILD_MODE=host|docker` 覆盖。

```bash
./RUNTIME/install_linux.sh build          # 直接编译（TTY 下仍可选方式）
EASYAIOT_RUNTIME_BUILD_MODE=host ./RUNTIME/install_linux.sh build   # 强制本机 conda
./RUNTIME/install_linux.sh compile        # 强制本机 conda（跳过交互）
./RUNTIME/install_linux.sh status         # 查看编译产物
```

Docker 同源容器编译（与 `video-service` 同 Ubuntu/glibc）：

```bash
./RUNTIME/install_linux.sh build
# 等价：EASYAIOT_RUNTIME_BUILD_MODE=docker ./RUNTIME/install_linux.sh build
```

- 构建镜像优先：`video-service:latest` → 已缓存的 `pytorch/pytorch:2.9.0-cuda12.8-cudnn9-devel` → `ubuntu:22.04`
- 覆盖镜像：`EASYAIOT_RUNTIME_BUILD_IMAGE=...`
- 宿主机 conda `easyaiot-runtime` 只提供 OpenCV5/glog/ffmpeg 等依赖库，并挂进构建容器

回退本机编译（新 glibc 主机上产物可能无法进 VIDEO 容器）：

```bash
EASYAIOT_RUNTIME_BUILD_MODE=host ./RUNTIME/install_linux.sh build
# 或：source RUNTIME/scripts/env.sh && ./RUNTIME/scripts/build_linux.sh
```

依赖：OpenCV 5、FFmpeg、glog、jsoncpp、libcurl，以及官方 ONNX Runtime C++ SDK（有 GPU 时优先 `onnxruntime-linux-*-gpu-1.23.2`，否则 CPU 包；默认下载到仓库根 `.deps/`）。

模块脚本子命令：

| 命令 | 说明 |
|------|------|
| `./install_linux.sh` | 交互式菜单（TTY）或安装并编译 |
| `build` / `install` | 编译（TTY 下可选 conda / Docker） |
| `compile` | 本机 conda 编译（跳过方式选择） |
| `status` | 检查二进制、`node.env`（若已节点安装） |
| `integrated [VIDEO_URL]` | 云边一体算力节点：编译 → 导出 → 安装，需 VIDEO 地址 |
| `atomic [VIDEO_URL]` | `integrated` 别名（向后兼容） |
| `help` | 帮助 |

---

## 版本控制

每次成功编译 / 导出会写出统一 `VERSION`（key=value），便于对照升级与维护。

### 标识格式（全自动，无手工版本文件）

- **不维护** `VERSION_BASE` 之类基线文件；版本号编译时由 **git 自动生成**
- 优先：`git describe --tags --always --dirty`（有 tag 则带上，如 `v1.2.3-5-gabcdef1`）
- 无 describe 时回退：`g{短哈希}`，工作区有未提交改动则加 `-dirty`
- 无 git 环境：`unknown`
- 其它字段：`git` / `built_at` / `arch` / `build_mode` / `ort` / `source`（`local-build` | `export` | `atomic-install`）

| 落点 | 路径 |
|------|------|
| 源码树编译产物 | `RUNTIME/build/VERSION`、`RUNTIME/VERSION`（**构建生成**，勿手改）；`deploy.env` 含 `RUNTIME_VERSION` |
| 节点安装 | `/opt/easyaiot/RUNTIME/VERSION` |
| 二进制内嵌 | CMake `-DRUNTIME_VERSION_STR=...`；`RUNTIME --version` |

```bash
# 查看本机编译产物版本
cat RUNTIME/build/VERSION
./RUNTIME/build/RUNTIME --version

# 节点
cat /opt/easyaiot/RUNTIME/VERSION
```

### 界面哪里看

| 位置 | 内容 |
|------|------|
| WEB「节点管理 → 业务运行时分发 → RUNTIME」 | 控制面版本 + 检测结果里的节点版本；不一致标黄，建议重新「分发 RUNTIME」 |
| WEB「算法任务」选高性能（`*_cpp`） | 展示 VIDEO 本机 RUNTIME 版本（`GET /video/algorithm/runtime/info`） |

### 升级约定

1. 中心/控制面重新编译（或 VIDEO 本地自动编译）→ 新 git 版本写入 `VERSION`
2. WEB「分发 RUNTIME」覆盖安装到节点（**不会因版本不一致自动强推**）
3. 远程任务启动时若节点版本 ≠ 本机，VIDEO **仅打 warning 日志**，仍允许启动，避免误伤生产

版本不一致时请在维护窗口重新分发；不强制阻断算法任务。

---

## 运行与运维

### 源码树手工跑

```bash
source RUNTIME/scripts/env.sh
$RUNTIME_BIN RUNTIME/config/config.example.ini
```

### 原子节点手工跑

```bash
source /opt/easyaiot/RUNTIME/env.sh
$RUNTIME_BIN /opt/easyaiot/RUNTIME/config/atomic.example.ini
```

### VIDEO 托管（生产）

WEB / API 创建算法任务，`executor=cpp` 时由 VIDEO 生成 ini 并拉起二进制；启停走原有任务接口即可。强制 CPU：`RUNTIME_FORCE_CPU=1`。

### 常用环境变量

| 变量 | 含义 |
|------|------|
| `VIDEO_BASE_URL` / `EASYAIOT_VIDEO_BASE_URL` | 云边一体必填：中心 VIDEO 根地址 |
| `GATEWAY_URL` / `EASYAIOT_GATEWAY_URL` | 云边一体可选：中心 Gateway（默认同主机 :48080） |
| `EASYAIOT_RUNTIME_DEPLOY_MODE` | 固定 `integrated`（云边一体） |
| `EASYAIOT_DEPLOY_PROFILE` | 单机合装用 `edge`（平台 install 规格，非 RUNTIME 独立形态） |
| `EASYAIOT_RUNTIME_INSTALL_DIR` | 原子安装目录，默认 `/opt/easyaiot/RUNTIME` |
| `SRS_RTMP_BASE` / `AI_RTMP_URL` | 原子安装可选：示例 ini 检测流 |
| `EASYAIOT_RUNTIME_BUILD_MODE` | `docker`（默认）/ `host` |
| `EASYAIOT_RUNTIME_BUILD_IMAGE` | 覆盖构建镜像 |
| `EASYAIOT_RUNTIME_SKIP` | `1` 跳过安装 |
| `EASYAIOT_RUNTIME_REQUIRED` | `1` 失败则中止上层 VIDEO 安装 |
| `RUNTIME_PREFER_GPU` / `RUNTIME_FORCE_CPU` | 推理设备策略 |
| `RUNTIME_GPU_DEVICE_ID` / `CUDA_VISIBLE_DEVICES` | GPU 选择 |
| `RUNTIME_PREFER_HWACCEL` / `RUNTIME_FORCE_SOFT_AV` | FFmpeg NVDEC/NVENC 策略 |
| `RUNTIME_NVENC_PRESET` | NVENC preset（默认 `p3`） |
| `RUNTIME_AUTO_INSTALL` | `0` 时跳过自动编译（export/分发、以及 VIDEO 本地启动 / 任务拉起） |

### 健康与控制

ini 中 `[task].control_port`（示例 `8123`）：

```bash
curl -s http://127.0.0.1:8123/health    # 含 infer_ep / decode_ep / encode_ep、丢帧/时延等
curl -s -X POST http://127.0.0.1:8123/stop
```

---

## 流水线与回调

`Pull+Decode → FrameRing(drop-oldest) → Infer(+draw) → ResultRing → Emit(MQTT alert) + 可选 RTMP(ai/)`

- 心跳：realtime/snap → `POST /video/algorithm/heartbeat/realtime`；patrol → `.../heartbeat/patrol`（**仍 HTTP → VIDEO**）
- 告警：默认 MQTT `mqtt/iot-alert-notification`（snap → `mqtt/iot-snapshot-alert`）→ iot-sink；`ALGO_BUS_TRANSPORT=http` 时才回退 `/video/alert/hook`
- 检测流：`realtime` 默认 `enable_rtmp=true`，推到设备独立 `ai_rtmp`（与 `live/` 预览分离）
- 健康：`GET /health`；控制口可 `POST /stop` 优雅退出

---

## 配置说明

完整字段见 [config/config.example.ini](config/config.example.ini)。VIDEO 对接段为 `[video_task]`。

关键段：

| 段 | 要点 |
|----|------|
| `[video]` | `rtsp_url` 拉流；`rtmp_url` 为检测推流目标（正式 realtime 由 VIDEO 写成 `…/ai/{device}`） |
| `[ai]` | 模型路径、`prefer_gpu` / `force_cpu` |
| `[alarm]` / `[video_task]` | `alert_hook_url`、`heartbeat_url`、`task_type` |
| `[features]` | `enable_rtmp` / `enable_draw` / `enable_alarm` |
| `[regions]` | 可选报警多边形；不配则全画面 |

原子节点示例由安装脚本生成：`/opt/easyaiot/RUNTIME/config/atomic.example.ini`。

---

## 模型支持（YOLOv8 / YOLO11 / YOLO26 + 自定义）

RUNTIME 推理引擎为 **`YoloEngine`（ONNX Runtime）**，与 VIDEO Python 对齐的检测能力：

| 模型 | `.onnx` | `.pt` | 说明 |
|------|---------|-------|------|
| YOLOv8 / YOLO11 | ✅ | ✅（自动导出） | classic detect：`[1,4+C,N]` + NMS |
| YOLO26 | ✅ | ✅（自动导出） | **end2end**：输出末维=6 `[x1,y1,x2,y2,conf,cls]`，不再 NMS |
| 用户自定义 | ✅（优先） | ✅（导出为 `model.onnx`） | 需为 Ultralytics detect / end2end；拒 YOLOv5 |

**`.pt` 怎么用：** 二进制本身只跑 ORT。若 ini/`model_path` 指向 `.pt`，或 VIDEO 解析到 `.pt`：

1. VIDEO `runtime_config_service` 调用 [`scripts/ensure_onnx_model.py`](scripts/ensure_onnx_model.py) 导出并缓存 `.onnx`（旁路写 `.names`）
2. RUNTIME 启动时若仍收到 `.pt`，也会再调同一脚本做兜底导出

导出依赖 **ultralytics**。优先用环境变量指定解释器：`RUNTIME_PYTHON` / `EASYAIOT_PYTHON` / `VIDEO_PYTHON`（原子包 `env.sh` 可取消注释）。

**任务 `model_ids` 映射（与 VIDEO 一致）：**

| id | 模型文件（规范名） |
|----|------|
| `-1` | `yolo11n.onnx`（历史别名 `yolov11n.onnx` 仍可用） |
| `-2` | `yolov8n.onnx` |
| `-3` | `yolo26n.onnx`（end2end，输出 `[1,N,6]`） |
| `>0` | 自定义目录优先 `model.onnx`，否则从 `best.pt`/`model.pt` 导出 |

`/health` 增加 `model_layout=detect|end2end`。离线包会带上 `scripts/ensure_onnx_model.py` 与已有内置 `.onnx`。

手工导出：

```bash
export RUNTIME_PYTHON=/path/to/python   # 需已装 ultralytics
"$RUNTIME_PYTHON" RUNTIME/scripts/ensure_onnx_model.py -i yolov8n.pt -o RUNTIME/models/yolov8n.onnx
"$RUNTIME_PYTHON" RUNTIME/scripts/ensure_onnx_model.py -i yolo26n.pt -o RUNTIME/models/yolo26n.onnx
```

---

## GPU 推理与硬解硬编

### 推理（ORT）

- 默认 **prefer GPU**：ONNX Runtime 优先挂载 `CUDAExecutionProvider`，Session 创建失败则自动回退 CPU，任务不中断。
- 配置（`[ai]` / 环境变量）：
  - `prefer_gpu` / `RUNTIME_PREFER_GPU`（默认 `true`）
  - `force_cpu` / `RUNTIME_FORCE_CPU`（强制仅 CPU）
  - `gpu_device_id` / `RUNTIME_GPU_DEVICE_ID` 或 `CUDA_VISIBLE_DEVICES`
- 日志会出现 `Using CUDA EP` 或 `Using CPU execution (fallback)`；`GET /health` 含 `infer_ep=cuda|cpu`、`model_layout`。

### 硬解 / 硬编（NVIDIA，realtime）

- **硬解**：FFmpeg CUDA hwdevice（NVDEC）→ `av_hwframe_transfer_data` 到主机内存 → `sws` 成 BGR → 现有推理/画框。
- **硬编**：RTMP 推流优先 `h264_nvenc`（分辨率 16 对齐，`preset` 默认 `p3`），失败回退 `libx264`。
- 配置（`[ai]` / 环境变量）：

| 字段 / 环境变量 | 默认 | 含义 |
|-----------------|------|------|
| `prefer_hwaccel` / `RUNTIME_PREFER_HWACCEL` | `true` | 优先硬解+硬编 |
| `force_soft_av` / `RUNTIME_FORCE_SOFT_AV` | `false` | 强制软解软编 |
| `hwaccel_device_id` | 同 `gpu_device_id` | CUDA 设备 |
| `nvenc_preset` / `RUNTIME_NVENC_PRESET` | `p3` | NVENC preset（对齐 VIDEO） |
| `bitrate` / `RUNTIME_VIDEO_BITRATE`（或 `FFMPEG_VIDEO_BITRATE`） | 按分辨率自动 | RTMP 重编码 ABR；1080p 默认约 `4500k`（旧版写死 `2500k` 易发糊） |
| `gop` / `RUNTIME_GOP_SIZE`（或 `FFMPEG_GOP_SIZE`） | `2 * fps` | 关键帧间隔；过短会浪费码率、画面更糊 |

- `prefer_gpu=false` 或 `force_cpu=true` 时会同步 `force_soft_av`，避免 CPU 任务抢 NVENC。
- 硬解连续 `transfer` 失败会在本会话降级软解；硬编 open 失败用 `libx264`，任务不中断。
- `GET /health` 增加 `decode_ep=cuda|cpu`、`encode_ep=h264_nvenc|libx264|none`。
- **snap/patrol** 仍走 OpenCV `VideoCapture`（本轮无硬解硬编）。
- **本轮不做**：TensorRT EP、VAAPI/QSV、GPU 零拷贝贯通。

安装侧：检测到 `nvidia-smi` 时优先下载 **GPU ORT** 包（如 `onnxruntime-linux-x64-gpu-*`），写入 `deploy.env` 的 CUDA lib 路径；无 GPU / 下载失败则用 CPU 包并告警。硬解硬编还依赖本机 FFmpeg 是否编入 CUDA/`h264_nvenc`（conda 栈通常具备）。

---

## 常见问题

| 现象 | 处理 |
|------|------|
| 云边一体安装提示缺少 `VIDEO_BASE_URL` | 安装前导出或作为参数传入中心 VIDEO 地址 |
| 单机合装安装失败 / 内存不足 | 确认宿主机 ≥ 3 GB；`EASYAIOT_DEPLOY_PROFILE=edge ... install`；查看中间件与 VIDEO 日志 |
| 提示操作系统不支持 | 当前 OS 不在 RUNTIME 矩阵内，见 `runtime_os_matrix.sh`；麒麟需专用镜像 |
| 二进制在 VIDEO 容器内无法运行 | 使用默认 `EASYAIOT_RUNTIME_BUILD_MODE=docker` 同源编译，避免新 glibc 主机 `host` 编译 |
| realtime 无带框预览 | 确认任务为 `executor=cpp` + `realtime`，ini 中 `enable_rtmp=true` 且 `rtmp_url` 为独立 `ai/` 路径（不要写成 `live/`） |
| 只有告警没有画面 | 抓拍/巡检默认不以长推流为主；看结构化告警即可。需要画面时给 realtime 或显式配置 `ai_rtmp` |
| `/health` 显示 `infer_ep=cpu` | 正常回退；检查驱动、`nvidia-smi`、ORT GPU 包与 `LD_LIBRARY_PATH` |
| cpp 任务没用上自定义模型 | 确认目录有 `.onnx`，或本机可跑 `ensure_onnx_model.py` 从 `.pt` 导出；看 VIDEO 日志 `RUNTIME model export` |
| YOLO26 框异常 | `/health` 应显示 `model_layout=end2end`；否则导出的不是 end2end ONNX |
| `/health` 显示 `decode_ep=cpu` / `encode_ep=libx264` | 无 NVIDIA、FFmpeg 无 CUDA/nvenc，或 `force_soft_av=true`；属正常回退 |
| 本地 mp4/文件播完后任务结束 | 有限媒体（裸路径 / `file://`）遇 EOF **干净退出**，不再狂重连；直播 RTSP/UDP 仍会退避重连 |
| `control_port` 变成 8000 | 端口必须在 **8000–9000**（与 VIDEO 一致）；越界会 ERROR 日志并回退 8000 |
| MQTT 未通 | 检查 `MQTT_BROKER_URLS` / ini `[mqtt]`；iot-sink 须订阅 `mqtt/iot-*` |
| 告警无图 | 确认 `ALERT_IMAGES_DIR` 与 sink 共享挂载；MQTT 只传路径 |

更细的平台级部署步骤见 [`.doc/部署文档/平台部署文档_zh.md`](../.doc/部署文档/平台部署文档_zh.md) 与 [部署最佳实践](../.doc/部署文档/部署最佳实践.md) 中的 **RUNTIME 原子模式** 小节。
