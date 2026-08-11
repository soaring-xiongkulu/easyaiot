# EasyAIoT 平台 macOS 部署文档

> 文档版本：1.1  
> 更新日期：2026-08-01  
> 适用系统：macOS（Intel / Apple Silicon）  
> 部署方式：**仅预构建镜像**（不在本机编译业务代码）

总览与命令对照见 [平台部署文档_zh.md](./平台部署文档_zh.md#macos--windows-镜像部署)。  
PANEL 桌面安装包编译见仓库根目录 [COMPILE/README.md](../../COMPILE/README.md)。

---

## 目录

1. [概述](#1-概述)
2. [环境准备](#2-环境准备)
3. [一键部署](#3-一键部署)
4. [常用命令](#4-常用命令)
5. [注意事项与排障](#5-注意事项与排障)

---

## 1. 概述

macOS 使用统一入口：

```bash
.scripts/docker/install_mac.sh
```

建议使用 Homebrew bash 4+ 执行（系统 `/bin/bash` 为 3.2）：

```bash
/opt/homebrew/bin/bash .scripts/docker/install_mac.sh <命令>
```

脚本会：

1. **前置环境检测**（Docker Desktop / Compose / bash 4+ / curl）：缺什么提示装什么，不满足则**中止**
2. 必要时尝试 `open -a Docker` 等待引擎就绪
3. **按需**写入国内 `registry-mirrors`、按部署形态调配 Docker 引擎内存
4. 按部署规格（mini / standard / full）拉取预构建业务镜像
5. 通过 `install_middleware_desktop.sh` 拉取并启动中间件（**FUXA** 走专用 `pull_fuxa.sh`）
6. 以 `EASYAIOT_SKIP_BUILD=1` 调用各模块 `install_linux.sh` 仅启动容器

**不支持**：`build`、`build-runtime`、`clean-build-runtime`。镜像需在 Linux CI/服务器上构建并推送到仓库（见 `runtime_registry.conf`）。

---

## 2. 环境准备

### 2.1 硬件与 Docker 引擎内存

| 规格 | 主机建议 | Docker 引擎目标内存 | 说明 |
|------|----------|---------------------|------|
| mini | ≥ 8 GB | **8 GB** | 边缘 / PoC |
| standard | ≥ 24 GB | **16 GB** | 日常开发演示 |
| full | ≥ 32 GB（推荐 48 GB+） | **24 GB** | 完整功能 |

磁盘建议预留 **≥ 100 GB** 可用空间（镜像与数据卷）。

> Desktop 默认常只给引擎约 8 GB；`resources` / `bootstrap` / `install` 在不足时会自动调高（写入 Docker Desktop `settings-store.json` 并重启引擎）。可用环境变量覆盖：`EASYAIOT_DOCKER_MEMORY_GB` / `EASYAIOT_DOCKER_CPUS` / `EASYAIOT_DOCKER_DISK_GB`；`EASYAIOT_DOCKER_SKIP_RESOURCES=1` 跳过。

### 2.2 软件依赖

| 依赖 | 说明 |
|------|------|
| Homebrew | [brew.sh](https://brew.sh) |
| Docker 引擎 | Docker Desktop（推荐）或 Colima（`brew install docker colima`）；`docker info` 可用即可 |
| Homebrew bash 4+ | `brew install bash`（系统 `/bin/bash` 为 3.2，无法跑镜像拉取逻辑） |
| Git | 用于 clone 仓库 |
| curl | 健康检查（一般系统自带） |
| python3 | `mirrors` / `resources` 改写配置时使用（macOS / Homebrew 一般自带） |

### 2.3 一键安装前置依赖（推荐）

首次部署前先装依赖并自检（脚本会打印前置操作清单，缺什么提示装什么）：

```bash
bash .scripts/docker/install_mac.sh bootstrap   # Homebrew bash + Docker Desktop（失败可回退 Colima）+ 镜像源/资源
bash .scripts/docker/install_mac.sh check       # 前置环境自检
bash .scripts/docker/install_mac.sh mirrors     # 国内 registry-mirrors（对齐 Linux）
bash .scripts/docker/install_mac.sh resources   # 按形态调引擎内存：mini 8G / standard 16G / full 24G
```

`install` / `pull` / `update` / `start` 会在真正部署前**自动做前置检测**；不满足则打印安装指引并中止。

验证：

```bash
docker --version
docker compose version
docker info | grep -A5 'Registry Mirrors'
docker info | grep -E 'CPUs|Total Memory'
bash --version   # 建议 ≥ 4；Homebrew 路径多为 /opt/homebrew/bin/bash
```

### 2.4 国内镜像加速（与 Linux 一致）

桌面端与 Linux 共用 `DOCKER_MIRROR` / `DOCKER_MIRROR_FALLBACKS`：

| 用途 | 行为 |
|------|------|
| Docker Hub / 中间件 | 写入 `~/.docker/daemon.json` 的 `registry-mirrors`：默认 DaoCloud → 1ms → 1panel |
| **FUXA** | **例外**：`pull_fuxa.sh` **优先 docker.1ms.run**（DaoCloud 对 `frangoteam/fuxa` 常 403）；compose 固定名为 `docker.1panel.live/frangoteam/fuxa:…` |
| 业务预构建镜像 | 来自 `runtime_registry.conf`（如 `docker.cnb.cool/...`），**不受** `registry-mirrors` 影响 |

```bash
# 自动写入并重启 Docker Desktop（也可由 bootstrap / install 触发）
bash .scripts/docker/install_mac.sh mirrors

# 跳过自动写 mirrors
EASYAIOT_DOCKER_SKIP_MIRROR=1 bash .scripts/docker/install_mac.sh install
```

手动等价配置（一般无需再改 GUI）：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1ms.run",
    "https://docker.1panel.live"
  ]
}
```

### 2.5 Apple Silicon 说明

脚本按 `uname -m` 使用 `linux/arm64` 平台拉取运行时镜像与 Nacos。请确认远程仓库已发布对应架构清单；若只有 amd64 镜像，需在仓库侧补齐 arm64，或改用 Intel Mac / 远程 Linux。勿对 Nacos 强制 amd64，以免 QEMU 极慢。

### 2.6 PANEL 桌面安装包（可选）

若需要「双击即用」的运维面板，可在本机编译 macOS 安装包（圆形白底图标与 Linux 一致）：

```bash
bash COMPILE/build.sh macos --dmg
# 产物：COMPILE/dist/macos/easyaiot-panel-<版本>.dmg
```

详见 [COMPILE/README.md](../../COMPILE/README.md#macos-打包dmg)。

---

## 3. 一键部署

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# 首次：安装前置依赖 → 自检 → 部署
bash .scripts/docker/install_mac.sh bootstrap
bash .scripts/docker/install_mac.sh check
EASYAIOT_DEPLOY_PROFILE=full bash .scripts/docker/install_mac.sh install

# 或交互引导
bash .scripts/docker/install_mac.sh

# 验证
bash .scripts/docker/install_mac.sh verify
```

非交互指定形态：

```bash
export EASYAIOT_DEPLOY_PROFILE=mini   # 或 standard / full
bash .scripts/docker/install_mac.sh install
```

安装完成后访问：

| 服务 | 地址 |
|------|------|
| WEB | http://localhost:8888 |
| Gateway | http://localhost:48080 |
| Nacos | http://localhost:8848/nacos |
| MinIO | http://localhost:9001 |
| FUXA（full） | http://localhost:1881 |
| PANEL（若启用） | http://localhost:9200 |

---

## 4. 常用命令

| 命令 | 说明 |
|------|------|
| `bootstrap` | 安装前置依赖（bash4 + Docker）；并尝试 mirrors / resources |
| `check` | 前置自检（打印清单；缺什么提示装什么） |
| `mirrors` | 配置国内 `registry-mirrors`（对齐 Linux） |
| `resources` | 按形态调配 Docker CPU/内存/磁盘（`resources force` 强制重写） |
| `install` | 拉取镜像并安装启动 |
| `pull` / `update` | 仅拉取 / 拉最新并重启 |
| `start` / `stop` / `restart` | 启停 |
| `status` / `logs` / `verify` | 状态、日志、健康检查 |
| `profile` / `menu` / `help` | 规格、交互菜单、帮助 |

```bash
bash .scripts/docker/install_mac.sh start
bash .scripts/docker/install_mac.sh stop
bash .scripts/docker/install_mac.sh logs VIDEO
bash .scripts/docker/install_mac.sh update
```

日志目录：`.scripts/docker/logs/install_mac_*.log`

---

## 5. 注意事项与排障

| 问题 | 处理 |
|------|------|
| 需要 bash 4+ | `brew install bash`，用 `/opt/homebrew/bin/bash` 执行脚本；或先 `bootstrap` |
| Docker daemon 未就绪 | 打开 Docker Desktop，等待鲸鱼图标稳定后再试 |
| 引擎内存不足 / OOM | `EASYAIOT_DEPLOY_PROFILE=full bash .scripts/docker/install_mac.sh resources`；或在 Desktop → Settings → Resources 手动调到 ≥24GB |
| 中间件拉不动 | `bash .scripts/docker/install_mac.sh mirrors` 后 `docker info` 确认 Registry Mirrors；FUXA 看 `pull_fuxa.sh` 日志 |
| 业务镜像（cnb）拉不动 | `registry-mirrors` 不作用于 `docker.cnb.cool`；检查本机网络 / 代理 / `runtime_registry.conf` |
| Nacos 长期 unhealthy | 确认 `NACOS_PLATFORM=linux/arm64`；冷启动可达数分钟；`docker logs nacos-server` |
| iot-tdengine Restarting | 先保证 `tdengine-server` healthy，再 `start` |
| 媒体地址 / GB28181 异常 | `export HOST_IP=<本机局域网IP>` 后重新 `start` / `install` |
| 误执行 `build` | 桌面端会直接拒绝；请改用 `pull` + `install` |
| SRS 等数据目录 | 媒体根 `EASYAIOT_MEDIA_ROOT`（默认 `/mnt/easyaiot-media`；桌面端 fallback `$HOME/easyaiot/media`） |
| Colima 与 Desktop 混用 | `docker context use desktop-linux`（或 `colima`）；部署前只保留一个引擎 |

生产与完整本地构建请使用 Linux：`.scripts/docker/install_linux.sh`。
