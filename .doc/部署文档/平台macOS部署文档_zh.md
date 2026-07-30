# EasyAIoT 平台 macOS 部署文档

> 文档版本：1.0  
> 更新日期：2026-07-30  
> 适用系统：macOS（Intel / Apple Silicon）  
> 部署方式：**仅预构建镜像**（不在本机编译业务代码）

总览与命令对照见 [平台部署文档_zh.md](./平台部署文档_zh.md#macos--windows-镜像部署)。

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

脚本会：

1. **前置环境检测**（Docker Desktop / Compose / bash 4+ / curl）：缺什么提示装什么，不满足则**中止**
2. 必要时尝试 `open -a Docker` 等待引擎就绪
3. 按部署规格（mini / standard / full）拉取预构建业务镜像
4. 通过 `install_middleware_desktop.sh` 拉取并启动中间件
5. 以 `EASYAIOT_SKIP_BUILD=1` 调用各模块 `install_linux.sh` 仅启动容器

**不支持**：`build`、`build-runtime`、`clean-build-runtime`。镜像需在 Linux CI/服务器上构建并推送到仓库（见 `runtime_registry.conf`）。

---

## 2. 环境准备

### 2.1 硬件建议

| 规格 | 内存建议 | 说明 |
|------|----------|------|
| mini | ≥ 8 GB | 边缘 / PoC（桌面建议略高于 Linux 4G 指引） |
| standard | ≥ 16 GB | 日常开发演示 |
| full | ≥ 20 GB（推荐 32 GB） | 完整功能 |

磁盘建议预留 **≥ 100 GB** 可用空间（镜像与数据卷）。

### 2.2 软件依赖

| 依赖 | 说明 |
|------|------|
| Docker Desktop | [官网下载](https://www.docker.com/products/docker-desktop) |
| Homebrew bash 4+ | `brew install bash`（系统 `/bin/bash` 为 3.2，无法跑镜像拉取逻辑） |
| Git | 用于 clone 仓库 |
| curl | 健康检查（一般系统自带） |

`install` / `pull` / `update` / `start` 会在真正部署前自动做前置检测。也可单独自检：

```bash
bash .scripts/docker/install_mac.sh check
```

验证：

```bash
docker --version
docker compose version
docker info
bash --version   # 建议 ≥ 4；Homebrew 路径多为 /opt/homebrew/bin/bash
```

### 2.3 镜像加速（推荐）

Docker Desktop → **Settings** → **Docker Engine**，例如：

```json
{
  "registry-mirrors": ["https://docker.m.daocloud.io"]
}
```

Apply & Restart 后再执行 `pull` / `install`。

### 2.4 Apple Silicon 说明

脚本按 `uname -m` 使用 `linux/arm64` 平台拉取运行时镜像。请确认远程仓库已发布对应架构清单；若只有 amd64 镜像，需在仓库侧补齐 arm64，或改用 Intel Mac / 远程 Linux。

---

## 3. 一键部署

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# 交互引导（推荐首次使用）
bash .scripts/docker/install_mac.sh

# 或指定命令
bash .scripts/docker/install_mac.sh pull
bash .scripts/docker/install_mac.sh install
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
| PANEL（若启用） | http://localhost:9200 |

---

## 4. 常用命令

```bash
bash .scripts/docker/install_mac.sh start
bash .scripts/docker/install_mac.sh stop
bash .scripts/docker/install_mac.sh restart
bash .scripts/docker/install_mac.sh status
bash .scripts/docker/install_mac.sh logs VIDEO
bash .scripts/docker/install_mac.sh update      # 强制拉最新镜像并重启
bash .scripts/docker/install_mac.sh check
bash .scripts/docker/install_mac.sh profile
```

日志目录：`.scripts/docker/logs/install_mac_*.log`

---

## 5. 注意事项与排障

| 问题 | 处理 |
|------|------|
| 需要 bash 4+ | `brew install bash`，确保 PATH 优先 Homebrew |
| Docker daemon 未就绪 | 打开 Docker Desktop，等待鲸鱼图标稳定后再试 |
| 媒体地址 / GB28181 异常 | `export HOST_IP=<本机局域网IP>` 后重新 `start` / `install` |
| 拉取镜像失败 | 检查网络与 Docker Engine `registry-mirrors`；确认 `runtime_registry.conf` |
| 误执行 `build` | 桌面端会直接拒绝；请改用 `pull` + `install` |
| SRS 等数据目录 | 脚本可能使用 `~/easyaiot/data` 作为宿主机数据兜底目录 |

生产与完整本地构建请使用 Linux：`.scripts/docker/install_linux.sh`。
