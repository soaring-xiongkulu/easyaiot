# EasyAIoT 平台 Windows 本地部署指南

> 文档版本：2.1  
> 更新日期：2026-08-01  
> 适用系统：Windows 10/11（推荐 Docker Desktop + WSL2）  
> **推荐部署方式：预构建镜像一键部署**（见下文第 0 章）

总览与跨平台对照见 [平台部署文档_zh.md](./平台部署文档_zh.md#macos--windows-镜像部署)。  
macOS 对照见 [平台macOS部署文档_zh.md](./平台macOS部署文档_zh.md)。  
PANEL 安装包编译见 [COMPILE/README.md](../../COMPILE/README.md)。

---

## 0. 推荐：镜像一键部署（2026）

Windows 桌面端与 macOS 一样，**只通过远程预构建镜像部署**，不在本机编译 Java / 前端 / Python 业务镜像。

| 入口 | 说明 |
|------|------|
| `.scripts/docker/install_windows.ps1` | PowerShell：先汇总检测 Docker / Compose / Git Bash（或缺什么提示装什么并中止），再转发 |
| `.scripts/docker/install_windows.sh` | 在 Git Bash / WSL 中直接执行（安装前同样会做前置检测） |

**不支持**：`build`、`build-runtime`、`clean-build-runtime`。

### 0.1 硬件与引擎内存

| 规格 | 主机建议 | Docker / WSL2 引擎目标内存 |
|------|----------|----------------------------|
| mini | ≥ 8 GB | **4 GB** |
| standard | ≥ 24 GB | **16 GB** |
| full | ≥ 32 GB | **24 GB** |

磁盘建议预留 **≥ 100 GB**。C 盘紧张时可：`.\.scripts\docker\install_windows.ps1 movedata`。

### 0.2 前置条件

1. 安装并启动 [Docker Desktop](https://www.docker.com/products/docker-desktop)（建议启用 **WSL2** 后端）
2. 安装 [Git for Windows](https://git-scm.com/download/win)（提供 `bash` 4+），或启用 WSL
3. clone 本仓库（compose 与脚本需要；业务产物来自镜像仓库）

`install` / `pull` / `update` / `start` / `check` 会在真正部署前自动做前置检测：缺少组件时打印安装指引并**中止**。

建议首次流程：

```powershell
.\.scripts\docker\install_windows.ps1 bootstrap   # WSL2 + Docker Desktop + mirrors + resources
.\.scripts\docker\install_windows.ps1 check
.\.scripts\docker\install_windows.ps1 mirrors     # 国内 registry-mirrors（对齐 Linux）
.\.scripts\docker\install_windows.ps1 resources   # mini 4G / standard 16G / full 24G
```

验证：

```powershell
docker --version
docker compose version
docker info
```

**资源调配**：WSL2 后端以 `%USERPROFILE%\.wslconfig` 为准，脚本同时更新 Desktop `settings-store.json`。  
覆盖：`$env:EASYAIOT_DOCKER_MEMORY_GB` / `$env:EASYAIOT_DOCKER_CPUS`；跳过：`$env:EASYAIOT_DOCKER_SKIP_RESOURCES = "1"`。

**国内镜像加速**（与 Linux / macOS 一致）：写入 `%USERPROFILE%\.docker\daemon.json`  
默认 DaoCloud → 1ms → 1panel。**FUXA** 走 `pull_fuxa.sh`（**1ms 优先**）。跳过：`$env:EASYAIOT_DOCKER_SKIP_MIRROR = "1"`。  
业务镜像（如 `docker.cnb.cool`）不受 `registry-mirrors` 影响。

### 0.3 快速安装

```powershell
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

.\.scripts\docker\install_windows.ps1
.\.scripts\docker\install_windows.ps1 pull
$env:EASYAIOT_DEPLOY_PROFILE = "full"
.\.scripts\docker\install_windows.ps1 install
.\.scripts\docker\install_windows.ps1 verify
```

Git Bash：

```bash
bash .scripts/docker/install_windows.sh install
```

### 0.4 常用命令

| 命令 | 说明 |
|------|------|
| `bootstrap` | 安装 WSL2 / Docker Desktop，并尝试 mirrors + resources |
| `check` | 前置自检 |
| `mirrors` | 配置国内 registry-mirrors |
| `resources` | 调配引擎 CPU/内存（`resources force` 强制） |
| `movedata` | 将 Docker WSL 数据迁到 E:\DockerDesktop |
| `install` / `pull` / `update` | 部署与更新 |
| `start` / `stop` / `status` / `logs` / `verify` | 运维 |
| `profile` | 查看部署形态 |

```powershell
.\.scripts\docker\install_windows.ps1 start
.\.scripts\docker\install_windows.ps1 logs VIDEO
.\.scripts\docker\install_windows.ps1 update
```

安装完成后访问：`http://localhost:8888`（Gateway `:48080`，Nacos `:8848/nacos`，FUXA full `:1881`）。

### 0.5 排障速查

| 问题 | 处理 |
|------|------|
| 找不到 bash | 安装 Git for Windows，或改用 WSL 后重跑 `install_windows.ps1` |
| Docker 未就绪 | 启动 Docker Desktop，等待引擎 Ready；必要时先 `wsl --install` 并重启 |
| 引擎内存不足 | `.\install_windows.ps1 resources`；或编辑 `.wslconfig` 后 `wsl --shutdown` |
| 中间件拉不动 | `.\install_windows.ps1 mirrors`；FUXA 看专用拉取日志 |
| 业务镜像拉不动 | 检查到 `runtime_registry.conf` 仓库的网络/代理（非 registry-mirrors） |
| C 盘满 / pull 只读 | `.\install_windows.ps1 movedata` |
| 宿主机 IP 不准 | `$env:HOST_IP = "192.168.x.x"` 后重新 start/install |
| `build` 被拒绝 | 预期行为；请用 `pull` + `install` |
| 日志 | `.scripts/docker/logs/install_windows_*.log` |

> 下文第 1～8 章为早期「本机安装 JDK / Node / Python 再部署」记录，适用于特殊排障或对照端口配置；**新环境请优先使用本章镜像部署**。

---

## 目录

1. [系统概述](#1-系统概述)
2. [环境准备](#2-环境准备)
3. [中间件部署](#3-中间件部署)
4. [服务启动](#4-服务启动)
5. [视频流媒体配置](#5-视频流媒体配置)
6. [踩坑记录与解决方案](#6-踩坑记录与解决方案)
7. [常用命令汇总](#7-常用命令汇总)
8. [附录](#8-附录)

---

## 1. 系统概述

### 1.1 项目简介

EasyAIoT 是一个物联网+AI视频分析平台，支持摄像头接入、视频流转发、AI算法分析等功能。

### 1.2 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         WEB 前端 (Vue3)                          │
│                         端口: 3100                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DEVICE 网关 (Spring Cloud)                    │
│                         端口: 48080                              │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  VIDEO 服务   │       │   AI 服务     │       │ DEVICE 微服务 │
│  端口: 6000   │       │  端口: 8100   │       │  多个微服务   │
│  (Python)     │       │  (Python)     │       │  (Java)       │
└───────────────┘       └───────────────┘       └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          中间件层                                │
│  PostgreSQL | Redis | Nacos | MinIO | Kafka | TDengine | SRS   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 服务组件说明

| 服务 | 技术栈 | 端口 | 说明 |
|------|--------|------|------|
| WEB | Vue3 + Vite | 3100 | 前端界面 |
| Gateway | Spring Cloud | 48080 | API网关 |
| VIDEO | Python Flask | 6000 | 视频服务 |
| AI | Python FastAPI | 8100 | AI推理服务 |
| DEVICE | Spring Boot | 多个 | 设备管理微服务 |

---

## 2. 环境准备

### 2.1 硬件要求

- CPU: 4核以上
- 内存: 16GB以上（推荐32GB）
- 硬盘: 100GB以上可用空间
- 网络: 能访问摄像头的局域网

### 2.2 软件依赖

#### 2.2.1 JDK 21

下载地址：https://adoptium.net/

安装后配置环境变量：
```
JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.x
Path 添加: %JAVA_HOME%\bin
```

验证安装：
```powershell
java -version
```

#### 2.2.2 Node.js 18+

下载地址：https://nodejs.org/

验证安装：
```powershell
node -v
npm -v
```

#### 2.2.3 Python 3.10+ (Anaconda)

下载地址：https://www.anaconda.com/

创建虚拟环境：
```powershell
conda create -n easyaiot python=3.10
conda activate easyaiot
```

#### 2.2.4 FFmpeg

下载地址：https://www.gyan.dev/ffmpeg/builds/

下载 `ffmpeg-release-essentials.zip`，解压到指定目录，例如：
```
G:\ffmpeg-7.0.2-essentials_build\
```

验证安装：
```powershell
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" -version
```

#### 2.2.5 Docker Desktop

下载地址：https://www.docker.com/products/docker-desktop/

用于运行 SRS 流媒体服务器。   docker仅用于运行SRS流媒体服务器  其他服务全部本地部署不适用docker

### 2.3 项目路径规划

本文档假设项目路径为：
```
F:\EASYLOT\easyaiot-V4.0.0\
```

中间件安装路径：
```
F:\EASYLOT\PostgreSQL16\
F:\EASYLOT\Redis\
F:\EASYLOT\nacos\     ####要开启鉴权   自行百度
F:\EASYLOT\minio\  #####项目里边有数据库或者说minio的密码  所有密码都要和项目的配套一至  如minion  账号：minionminion 密码iot******
F:\EASYLOT\kafka\   ###自行下载
F:\EASYLOT\TDengine\  ####自行下载
```

---

## 3. 中间件部署

### 3.1 PostgreSQL

#### 安装信息
- 版本：16.x
- 端口：5432
- 用户名：postgres
- 密码：`iot45722414822`

#### 启动命令
```powershell
# 启动 PostgreSQL 服务
pg_ctl -D "F:\EASYLOT\PostgreSQL16\data" start

# 或者使用 Windows 服务
net start postgresql-x64-16
```

#### 创建数据库
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "CREATE DATABASE \"iot-system\";"
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "CREATE DATABASE \"iot-video20\";"
```

#### 验证连接
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"
```

---

### 3.2 Redis

#### 安装信息
- 版本：7.x
- 端口：6379
- 密码：`basiclab@iot975248395`

#### 启动命令
```powershell
cd F:\EASYLOT\Redis
.\redis-server.exe redis.windows.conf
```

#### 验证连接
```powershell
cd F:\EASYLOT\Redis
.\redis-cli.exe -a "basiclab@iot975248395" ping
# 应返回 PONG
```

---

### 3.3 Nacos

#### 安装信息
- 版本：2.x
- 端口：8848
- 用户名：nacos
- 密码：`basiclab@iot78475418754`
- 命名空间：local

#### 启动命令
```powershell
cd F:\EASYLOT\nacos\bin
.\startup.cmd -m standalone
```

#### 访问地址
```
http://localhost:8848/nacos
```

#### 配置命名空间
1. 登录 Nacos 控制台
2. 进入「命名空间」
3. 创建命名空间，ID 设置为 `local`

---

### 3.4 MinIO

#### 安装信息
- 版本：最新版
- API端口：9000
- 控制台端口：9001
- 用户名：minioadmin
- 密码：`basiclab@iot975248395`

#### 启动命令
```powershell
cd F:\EASYLOT\minio
.\minio.exe server data --console-address ":9001"
```

#### 访问地址
```
控制台：http://localhost:9001
API：http://localhost:9000
```

---

### 3.5 Kafka

#### 安装信息
- 版本：3.x
- 端口：9092
- Zookeeper端口：2181

#### 启动命令（需要先启动 Zookeeper）
```powershell
# 终端1：启动 Zookeeper
cd F:\EASYLOT\kafka
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties

# 终端2：启动 Kafka
cd F:\EASYLOT\kafka
.\bin\windows\kafka-server-start.bat .\config\server.properties
```

---

### 3.6 TDengine

#### 安装信息
- 版本：3.x
- 端口：6030（原生连接）、6041（REST API）
- 用户名：root
- 密码：taosdata

#### 启动命令
```powershell
# 启动 TDengine 服务
net start taosd

# 或者手动启动
cd F:\EASYLOT\TDengine
.\taosd.exe
```

#### 验证连接
```powershell
cd F:\EASYLOT\TDengine
.\taos.exe -u root -p taosdata
```

---

### 3.7 SRS 流媒体服务器（Docker）

#### 安装信息
- 版本：ossrs/srs:5
- RTMP端口：1935
- HTTP-FLV端口：8080
- HTTP API端口：1985
- WebRTC端口：8000/udp

#### 创建配置文件

在项目目录创建配置文件 `.scripts/srs/conf/simple.conf`：
```conf
# SRS 简化配置
listen              1935;
max_connections     1000;
daemon              off;

http_server {
    enabled         on;
    listen          8080;
    dir             ./objs/nginx/html;
}

http_api {
    enabled         on;
    listen          1985;
}

vhost __defaultVhost__ {
    http_remux {
        enabled     on;
        mount       [vhost]/[app]/[stream].flv;
    }
}
```

#### 启动命令
```powershell
docker run -d --name srs-server `
  -p 1935:1935 `
  -p 8080:8080 `
  -p 1985:1985 `
  -p 8000:8000/udp `
  -v "F:\EASYLOT\easyaiot-V4.0.0\.scripts\srs\conf\simple.conf:/usr/local/srs/conf/docker.conf" `
  ossrs/srs:5 ./objs/srs -c conf/docker.conf
```

#### 验证 SRS 运行状态
```powershell
# 查看容器状态
docker ps | findstr srs

# 查看 SRS API
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/versions"
```

#### 常用 Docker 命令
```powershell
# 停止 SRS
docker stop srs-server

# 启动 SRS
docker start srs-server

# 查看日志
docker logs srs-server

# 删除容器（需要重新创建时）
docker rm srs-server
```

---

## 4. 服务启动

### 4.1 启动顺序

**必须按以下顺序启动：**

1. 中间件（PostgreSQL → Redis → Nacos → MinIO → Kafka → TDengine → SRS）
2. DEVICE 微服务（Java）
3. VIDEO 服务（Python）
4. AI 服务（Python）
5. WEB 前端（Vue）

---

### 4.2 DEVICE 微服务启动

DEVICE 目录下有多个 Spring Boot 微服务，需要分别启动。

#### 4.2.1 启动网关服务
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-gateway
mvn spring-boot:run
# 或者使用 IDE 启动
```

#### 4.2.2 启动系统服务
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-system\iot-system-biz
mvn spring-boot:run
```

#### 4.2.3 启动基础设施服务
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-infra\iot-infra-biz
mvn spring-boot:run
```

#### 配置文件位置
- 网关：`DEVICE/iot-gateway/src/main/resources/bootstrap-dev.yaml`
- 系统：`DEVICE/iot-system/iot-system-biz/src/main/resources/bootstrap-dev.yaml`
- 基础设施：`DEVICE/iot-infra/iot-infra-biz/src/main/resources/bootstrap-dev.yaml`

---

### 4.3 VIDEO 服务启动

#### 4.3.1 安装依赖
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
pip install -r requirements.txt
```

#### 4.3.2 配置环境变量

编辑 `VIDEO/.env` 文件，确保以下配置正确：
```properties
# 数据库
DATABASE_URL=postgresql://postgres:iot45722414822@localhost:5432/iot-video20

# Nacos
NACOS_SERVER=localhost:8848
NACOS_NAMESPACE=local
NACOS_USERNAME=nacos
NACOS_PASSWORD=basiclab@iot78475418754

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=basiclab@iot975248395

# FFmpeg 路径（Windows 必须配置完整路径）
FFMPEG_PATH=G:/ffmpeg-7.0.2-essentials_build/bin/ffmpeg.exe

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

#### 4.3.3 启动服务
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
python run.py
```

服务启动后监听端口：6000

---

### 4.4 AI 服务启动

#### 4.4.1 安装依赖
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
pip install -r requirements.txt
```

#### 4.4.2 启动服务
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
python run.py
```

服务启动后监听端口：8100

---

### 4.5 WEB 前端启动

#### 4.5.1 安装依赖
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm install
# 或者使用 pnpm
pnpm install
```

#### 4.5.2 启动开发服务器
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm run dev
```

服务启动后访问地址：http://localhost:3100

#### 4.5.3 登录信息
- 用户名：admin
- 密码：admin123

---


## 5. 视频流媒体配置

### 5.1 视频播放流程

```
摄像头(RTSP) → FFmpeg → SRS(RTMP) → HTTP-FLV → 前端播放器(flv.js)
```

### 5.2 添加摄像头

1. 登录前端系统
2. 进入「流媒体」→「设备列表」
3. 点击「新增视频源设备」
4. 选择摄像头类型（海康/大华/宇视/自定义）
5. 填写摄像头信息：
   - IP地址
   - 端口（默认554）
   - 用户名
   - 密码
6. 点击确定，系统会自动生成 RTSP 地址

### 5.3 启动推流

1. 在设备列表中找到已添加的摄像头
2. 点击「启用RTSP转发」按钮
3. 系统会自动启动 FFmpeg 推流到 SRS
4. 点击「播放」按钮查看视频

### 5.4 手动测试推流

如果自动推流失败，可以手动测试：

```powershell
# 测试推流命令
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/camera1"
```

### 5.5 测试播放

推流成功后，可以通过以下方式测试播放：

1. **SRS 自带播放器**
   ```
   http://127.0.0.1:8080/players/srs_player.html?autostart=true&stream=live/camera1.flv
   ```

2. **HTTP-FLV 地址**
   ```
   http://127.0.0.1:8080/live/camera1.flv
   ```

3. **VLC 播放器**
   - 打开 VLC
   - 媒体 → 打开网络串流
   - 输入：`rtmp://127.0.0.1:1935/live/camera1`

---

## 6. 踩坑记录与解决方案

### 6.1 SRS 流名称长度限制

#### 问题描述
使用设备ID（如 `1765004744998329500`）作为流名称时，FFmpeg 推流报错：
```
Error opening output rtmp://127.0.0.1:1935/live/1765004744998329500: I/O error
```

但使用短名称（如 `camera1`）可以正常推流。

#### 解决方案
修改流名称生成逻辑，使用 `cam_` + 设备ID前8位：
```python
# VIDEO/app/services/camera_service.py
short_stream_name = f"cam_{device_id[:8]}"
rtmp_stream = f"rtmp://127.0.0.1:1935/live/{short_stream_name}"
http_stream = f"http://127.0.0.1:8080/live/{short_stream_name}.flv"
```

#### 手动修复已有数据
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "UPDATE device SET rtmp_stream = 'rtmp://127.0.0.1:1935/live/cam_' || SUBSTRING(id, 1, 8), http_stream = 'http://127.0.0.1:8080/live/cam_' || SUBSTRING(id, 1, 8) || '.flv';"
```

---

### 6.2 FFmpeg 路径问题（Windows）

#### 问题描述
VIDEO 服务启动推流时报错，找不到 `ffmpeg` 命令。

#### 原因分析
Windows 系统中，如果 FFmpeg 没有添加到系统 PATH，需要使用完整路径。

#### 解决方案
1. 在 `VIDEO/.env` 中配置 FFmpeg 完整路径：
   ```properties
   FFMPEG_PATH=G:/ffmpeg-7.0.2-essentials_build/bin/ffmpeg.exe
   ```

2. 修改 `VIDEO/app/blueprints/camera.py` 中的 FFmpegDaemon 类：
   ```python
   ffmpeg_path = os.getenv('FFMPEG_PATH', 'ffmpeg')
   ffmpeg_cmd = [
       ffmpeg_path,
       '-re',
       '-rtsp_transport', 'tcp',
       '-i', self.source,
       '-c:v', 'copy',
       '-an',
       '-f', 'flv',
       self.rtmp_stream
   ]
   ```

---

### 6.3 SRS Docker 配置 daemon 问题

#### 问题描述
SRS Docker 容器启动后立即退出。

#### 原因分析
SRS 配置文件中 `daemon on;` 会导致 SRS 进入后台运行，但 Docker 容器需要前台进程。

#### 解决方案
在 SRS 配置文件中设置：
```conf
daemon off;
```

---

### 6.4 端口 8080 被占用

#### 问题描述
SRS 的 HTTP-FLV 端口 8080 与其他服务冲突。

#### 解决方案
1. 检查占用端口的进程：
   ```powershell
   netstat -ano | findstr :8080
   ```

2. 如果是其他服务占用，可以修改 SRS 配置使用其他端口，或者停止占用的服务。

3. 确保 Java 网关使用的是 48080 端口，不是 8080。

---

### 6.5 flv.js 播放器音频问题

#### 问题描述
前端播放视频时报错，或者视频无法播放。

#### 原因分析
摄像头可能没有音频流，但 FFmpeg 尝试编码音频导致错误。

#### 解决方案
1. FFmpeg 推流时禁用音频：
   ```
   -an
   ```

2. flv.js 配置禁用音频：
   ```javascript
   flvPlayer = flvjs.createPlayer({
       type: 'flv',
       url: url,
       isLive: true,
       hasAudio: false,  // 禁用音频
       hasVideo: true,
   });
   ```

---

### 6.6 数据库连接失败

#### 问题描述
VIDEO 服务启动时报数据库连接错误。

#### 排查步骤
1. 确认 PostgreSQL 服务已启动：
   ```powershell
   $env:PGPASSWORD='iot45722414822'
   & "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"
   ```

2. 确认数据库 `iot-video20` 存在

3. 检查 `VIDEO/.env` 中的 DATABASE_URL 配置

---

### 6.7 Nacos 注册失败

#### 问题描述
服务启动时无法注册到 Nacos。

#### 排查步骤
1. 确认 Nacos 服务已启动：
   ```
   http://localhost:8848/nacos
   ```

2. 确认命名空间 `local` 已创建

3. 检查配置文件中的 Nacos 地址和密码

---

### 6.8 前端验证码不显示

#### 问题描述
前端登录页面验证码图片无法加载。

#### 原因分析
通常是网关服务未启动，或者端口配置错误。

#### 解决方案
1. 确认 DEVICE 网关服务已启动（端口 48080）
2. 确认前端配置的 API 地址正确
3. 检查浏览器控制台的网络请求错误

---

## 7. 常用命令汇总

### 7.1 数据库操作

```powershell
# 设置密码环境变量
$env:PGPASSWORD='iot45722414822'

# 连接数据库
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20"

# 查看所有数据库
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"

# 查看设备表
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "SELECT id, name, source, rtmp_stream, http_stream FROM device;"

# 更新设备流地址
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "UPDATE device SET http_stream = 'http://127.0.0.1:8080/live/cam_12345678.flv' WHERE id = '1234567890';"
```

### 7.2 SRS 操作

```powershell
# 查看 SRS 容器状态
docker ps | findstr srs

# 查看 SRS 日志
docker logs srs-server

# 重启 SRS
docker restart srs-server

# 查看当前推流列表
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/streams/" | ConvertTo-Json

# 查看 SRS 版本
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/versions"
```

### 7.3 FFmpeg 推流测试

```powershell
# 海康摄像头推流测试
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/test"

# 大华摄像头推流测试
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/cam/realmonitor?channel=1&subtype=0" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/test"
```

### 7.4 服务启停

```powershell
# VIDEO 服务
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
python run.py

# AI 服务
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
python run.py

# WEB 前端
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm run dev
```

---

## 8. 附录

### 8.1 端口汇总表

| 服务 | 端口 | 协议 | 说明 |
|------|------|------|------|
| PostgreSQL | 5432 | TCP | 数据库 |
| Redis | 6379 | TCP | 缓存 |
| Nacos | 8848 | HTTP | 服务注册中心 |
| MinIO API | 9000 | HTTP | 对象存储 API |
| MinIO Console | 9001 | HTTP | 对象存储控制台 |
| Kafka | 9092 | TCP | 消息队列 |
| Zookeeper | 2181 | TCP | Kafka 依赖 |
| TDengine | 6030 | TCP | 时序数据库原生连接 |
| TDengine REST | 6041 | HTTP | 时序数据库 REST API |
| SRS RTMP | 1935 | TCP | RTMP 推流/拉流 |
| SRS HTTP-FLV | 8080 | HTTP | HTTP-FLV 播放 |
| SRS API | 1985 | HTTP | SRS 管理 API |
| SRS WebRTC | 8000 | UDP | WebRTC |
| DEVICE Gateway | 48080 | HTTP | Java 网关 |
| VIDEO | 6000 | HTTP | 视频服务 |
| AI | 8100 | HTTP | AI 服务 |
| WEB | 3100 | HTTP | 前端开发服务器 |

### 8.2 密码汇总表

| 服务 | 用户名 | 密码 |
|------|--------|------|
| PostgreSQL | postgres | iot45722414822 |
| Redis | - | basiclab@iot975248395 |
| Nacos | nacos | basiclab@iot78475418754 |
| MinIO | minioadmin | basiclab@iot975248395 |
| TDengine | root | taosdata |
| WEB 前端 | admin | admin123 |
| 测试摄像头 | admin | sr336699 |

### 8.3 摄像头 RTSP 地址格式

#### 海康威视
```
rtsp://用户名:密码@IP:554/Streaming/Channels/101  # 主码流
rtsp://用户名:密码@IP:554/Streaming/Channels/102  # 子码流
```

#### 大华
```
rtsp://用户名:密码@IP:554/cam/realmonitor?channel=1&subtype=0  # 主码流
rtsp://用户名:密码@IP:554/cam/realmonitor?channel=1&subtype=1  # 子码流
```

#### 宇视
```
rtsp://用户名:密码@IP:554/unicast/c1/s0/live  # 主码流
rtsp://用户名:密码@IP:554/unicast/c1/s1/live  # 子码流
```

### 8.4 常见问题 FAQ

**Q: 前端页面打不开？**
A: 检查 WEB 服务是否启动，端口 3100 是否被占用。

**Q: 登录时提示网络错误？**
A: 检查 DEVICE 网关服务是否启动，端口 48080 是否正常。

**Q: 视频播放黑屏？**
A: 
1. 检查 SRS 是否运行：`docker ps | findstr srs`
2. 检查是否有推流：访问 `http://127.0.0.1:1985/api/v1/streams/`
3. 手动测试推流命令是否正常

**Q: 推流失败？**
A: 
1. 检查 FFmpeg 路径是否正确
2. 检查摄像头 RTSP 地址是否可访问
3. 检查 SRS 是否运行
4. 检查流名称是否过长

**Q: 服务注册到 Nacos 失败？**
A: 
1. 检查 Nacos 是否启动
2. 检查命名空间 `local` 是否存在
3. 检查密码是否正确

---

> 文档结束
> 如有问题，请联系AI
