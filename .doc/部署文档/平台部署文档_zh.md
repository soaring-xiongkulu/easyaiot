# EasyAIoT 平台部署文档

## 📋 目录

- [概述](#概述)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [脚本使用说明](#脚本使用说明)
- [模块说明](#模块说明)
- [服务端口](#服务端口)
- [常见问题](#常见问题)
- [日志管理](#日志管理)

## 概述

EasyAIoT 是一个云边一体化智能算法应用平台，采用统一安装脚本进行一键部署。该平台支持 Docker 容器化部署，可以快速安装和启动所有服务模块。

### 平台架构

EasyAIoT 平台由以下核心模块组成：

- **基础服务** (`.scripts/docker`): 包含 Nacos、PostgreSQL、Redis、TDEngine、Kafka、MinIO 等中间件
- **DEVICE 服务**: 设备管理和网关服务（基于 Java）
- **AI 服务**: 人工智能处理服务（基于 Python）
- **VIDEO 服务**: 视频处理服务（基于 Python）
- **WEB 服务**: Web 前端服务（基于 Vue）

## 环境要求

### 系统要求

- **操作系统**: 
  - Linux (推荐 Ubuntu 24.04)
  - macOS (推荐 macOS 10.15+)
  - Windows (推荐 Windows 10/11，需要 PowerShell 5.1+)
- **内存**: 推荐 32GB（最低 16GB）
- **磁盘**: 建议 50GB 以上可用空间
- **CPU**: 推荐 8 核（最低 4 核）

### 软件依赖

在运行部署脚本之前，需要确保已安装以下软件：

1. **Docker** (必须版本 v29.0.0+)
   - 安装指南: https://docs.docker.com/get-docker/
   - 验证安装: `docker --version`
   - **注意**: Docker 版本必须为 v29.0.0 或更高版本，低于此版本将无法正常运行

2. **Docker Compose** (必须版本 v2.35.0+)
   - 安装指南: https://docs.docker.com/compose/install/
   - 验证安装: `docker compose version`
   - **注意**: Docker Compose 版本必须为 v2.35.0 或更高版本，低于此版本将无法正常运行

3. **其他依赖**:
   - **Linux/macOS**: `curl` (用于健康检查，通常系统已自带)
   - **Windows**: PowerShell 5.1+ (通常系统已自带)

### Docker 权限配置

#### Linux

确保当前用户有权限访问 Docker daemon：

```bash
# 方法1: 将用户添加到 docker 组（推荐）
sudo usermod -aG docker $USER
# 然后重新登录或运行
newgrp docker

# 方法2: 使用 sudo 运行脚本（不推荐）
sudo ./install_linux.sh [命令]
```

验证 Docker 权限：

```bash
docker ps
```

#### macOS

macOS 通常不需要特殊权限配置，Docker Desktop 会自动处理权限。

#### Windows

Windows 上 Docker Desktop 会自动处理权限，确保以管理员身份运行 PowerShell（如需要）。

## 快速开始

### Linux 部署

#### 1. 获取项目代码

```bash
# 克隆项目（如果还没有）
git clone <repository-url>
cd easyaiot
```

#### 2. 进入脚本目录

```bash
cd .scripts/docker
```

#### 3. 赋予脚本执行权限

```bash
chmod +x install_linux.sh
```

#### 4. 一键安装所有服务

```bash
./install_linux.sh install
```

该命令会：
- 检查 Docker 和 Docker Compose 环境
- 创建统一网络 `easyaiot-network`
- 按依赖顺序安装所有模块
- 启动所有服务容器

#### 5. 验证服务状态

```bash
./install_linux.sh verify
```

如果所有服务正常运行，将显示服务访问地址。

### macOS 部署

#### 1. 获取项目代码

```bash
# 克隆项目（如果还没有）
git clone <repository-url>
cd easyaiot
```

#### 2. 进入脚本目录

```bash
cd .scripts/docker
```

#### 3. 赋予脚本执行权限

```bash
chmod +x install_mac.sh
```

#### 4. 一键安装所有服务

```bash
./install_mac.sh install
```

该命令会：
- 检查 Docker 和 Docker Compose 环境
- 创建统一网络 `easyaiot-network`
- 按依赖顺序安装所有模块
- 启动所有服务容器

#### 5. 验证服务状态

```bash
./install_mac.sh verify
```

如果所有服务正常运行，将显示服务访问地址。

### Windows 部署

#### 1. 获取项目代码

```powershell
# 克隆项目（如果还没有）
git clone <repository-url>
cd easyaiot
```

#### 2. 进入脚本目录

```powershell
cd .scripts\docker
```

#### 3. 设置执行策略（如需要）

如果首次运行 PowerShell 脚本，可能需要设置执行策略：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 4. 一键安装所有服务

```powershell
.\install_win.ps1 install
```

该命令会：
- 检查 Docker 和 Docker Compose 环境
- 创建统一网络 `easyaiot-network`
- 按依赖顺序安装所有模块
- 启动所有服务容器

#### 5. 验证服务状态

```powershell
.\install_win.ps1 verify
```

如果所有服务正常运行，将显示服务访问地址。

## 脚本使用说明

### 脚本位置

统一安装脚本位于项目根目录下的 `.scripts/docker/` 目录：

- **Linux**: `install_linux.sh`
- **macOS**: `install_mac.sh`
- **Windows**: `install_win.ps1`

### 可用命令

所有操作系统支持相同的命令，但脚本名称不同：

| 命令 | 说明 | Linux 示例 | macOS 示例 | Windows 示例 |
|------|------|-----------|-----------|-------------|
| `install` | 安装并启动所有服务（首次运行） | `./install_linux.sh install` | `./install_mac.sh install` | `.\install_win.ps1 install` |
| `start` | 启动所有服务 | `./install_linux.sh start` | `./install_mac.sh start` | `.\install_win.ps1 start` |
| `stop` | 停止所有服务 | `./install_linux.sh stop` | `./install_mac.sh stop` | `.\install_win.ps1 stop` |
| `restart` | 重启所有服务 | `./install_linux.sh restart` | `./install_mac.sh restart` | `.\install_win.ps1 restart` |
| `status` | 查看所有服务状态 | `./install_linux.sh status` | `./install_mac.sh status` | `.\install_win.ps1 status` |
| `logs` | 查看所有服务日志 | `./install_linux.sh logs` | `./install_mac.sh logs` | `.\install_win.ps1 logs` |
| `build` | 重新构建所有镜像 | `./install_linux.sh build` | `./install_mac.sh build` | `.\install_win.ps1 build` |
| `clean` | 清理所有容器和镜像（危险操作） | `./install_linux.sh clean` | `./install_mac.sh clean` | `.\install_win.ps1 clean` |
| `update` | 更新并重启所有服务 | `./install_linux.sh update` | `./install_mac.sh update` | `.\install_win.ps1 update` |
| `verify` | 验证所有服务是否启动成功 | `./install_linux.sh verify` | `./install_mac.sh verify` | `.\install_win.ps1 verify` |

### 命令详细说明

#### install - 安装服务

首次部署时使用，会安装并启动所有服务模块：

**Linux/macOS**:
```bash
./install_linux.sh install    # Linux
./install_mac.sh install       # macOS
```

**Windows**:
```powershell
.\install_win.ps1 install
```

**执行流程**:
1. 检查 Docker 和 Docker Compose 环境
2. 创建 Docker 网络 `easyaiot-network`
3. 按依赖顺序安装各模块：
   - 基础服务（Nacos、PostgreSQL、Redis 等）
   - DEVICE 服务
   - AI 服务
   - VIDEO 服务
   - WEB 服务
4. 显示安装结果统计

#### start - 启动服务

启动所有已安装的服务：

**Linux/macOS**:
```bash
./install_linux.sh start    # Linux
./install_mac.sh start      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 start
```

#### stop - 停止服务

停止所有运行中的服务（按逆序停止）：

**Linux/macOS**:
```bash
./install_linux.sh stop    # Linux
./install_mac.sh stop      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 stop
```

#### restart - 重启服务

重启所有服务：

**Linux/macOS**:
```bash
./install_linux.sh restart    # Linux
./install_mac.sh restart      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 restart
```

#### status - 查看状态

查看所有服务的运行状态：

**Linux/macOS**:
```bash
./install_linux.sh status    # Linux
./install_mac.sh status      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 status
```

#### logs - 查看日志

查看所有服务的日志（最近 100 行）：

**Linux/macOS**:
```bash
./install_linux.sh logs    # Linux
./install_mac.sh logs      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 logs
```

#### build - 构建镜像

重新构建所有服务的 Docker 镜像（使用 `--no-cache` 选项）：

**Linux/macOS**:
```bash
./install_linux.sh build    # Linux
./install_mac.sh build      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 build
```

**注意**: 构建过程可能需要较长时间，请耐心等待。

#### clean - 清理服务

**⚠️ 危险操作**: 删除所有容器、镜像和数据卷

**Linux/macOS**:
```bash
./install_linux.sh clean    # Linux
./install_mac.sh clean      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 clean
```

执行前会要求确认，输入 `y` 或 `Y` 继续，其他输入将取消操作。

**清理内容**:
- 所有服务容器
- 所有服务镜像
- 所有数据卷
- Docker 网络 `easyaiot-network`

#### update - 更新服务

拉取最新镜像并重启所有服务：

**Linux/macOS**:
```bash
./install_linux.sh update    # Linux
./install_mac.sh update      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 update
```

**执行流程**:
1. 拉取各模块的最新镜像
2. 重启所有服务以使用新镜像

#### verify - 验证服务

验证所有服务是否正常启动并可访问：

**Linux/macOS**:
```bash
./install_linux.sh verify    # Linux
./install_mac.sh verify      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 verify
```

**验证内容**:
- 检查服务端口是否可访问
- 检查健康检查端点是否正常响应
- 显示服务访问地址

**成功输出示例**:
```
[SUCCESS] 所有服务运行正常！

服务访问地址:
  基础服务 (Nacos):     http://localhost:8848/nacos
  基础服务 (MinIO):     http://localhost:9000 (API), http://localhost:9001 (Console)
  Device服务 (Gateway):  http://localhost:48080
  AI服务:                http://localhost:5000
  Video服务:             http://localhost:6000
  Web前端:               http://localhost:8888
```

## 模块说明

### 基础服务 (`.scripts/docker`)

**说明**: 包含平台运行所需的所有中间件服务

**包含服务**:
- **Nacos**: 服务注册与配置中心
- **PostgreSQL**: 关系型数据库
- **Redis**: 缓存数据库
- **TDEngine**: 时序数据库
- **Kafka**: 消息队列
- **MinIO**: 对象存储服务

**部署方式**: 
- **Linux**: 使用 `install_middleware_linux.sh` 脚本
- **macOS**: 使用 `install_middleware_mac.sh` 脚本
- **Windows**: 使用 `install_middleware_win.ps1` 脚本

### DEVICE 服务

**说明**: 设备管理和网关服务，提供设备接入、产品管理、数据标注、规则引擎等功能

**技术栈**: Java (Spring Cloud)

**部署方式**: 
- **Linux**: 使用 `install_linux.sh` 脚本
- **macOS**: 使用 `install_mac.sh` 脚本
- **Windows**: 使用 `install_win.ps1` 脚本

**主要功能**:
- 设备管理
- 产品管理
- 数据标注
- 规则引擎
- 算法商店
- 系统管理

### AI 服务

**说明**: 人工智能处理服务，负责视频分析和 AI 算法执行

**技术栈**: Python

**部署方式**: 
- **Linux**: 使用 `install_linux.sh` 脚本
- **macOS**: 使用 `install_mac.sh` 脚本
- **Windows**: 使用 `install_win.ps1` 脚本

**主要功能**:
- 视频分析
- AI 算法执行
- 模型推理

### VIDEO 服务

**说明**: 视频处理服务，负责视频流处理与传输

**技术栈**: Python

**部署方式**: 
- **Linux**: 使用 `install_linux.sh` 脚本
- **macOS**: 使用 `install_mac.sh` 脚本
- **Windows**: 使用 `install_win.ps1` 脚本

**主要功能**:
- 视频流处理
- 视频传输
- 流媒体服务

### WEB 服务

**说明**: Web 前端服务，提供用户界面

**技术栈**: Vue.js

**部署方式**: 
- **Linux**: 使用 `install_linux.sh` 脚本
- **macOS**: 使用 `install_mac.sh` 脚本
- **Windows**: 使用 `install_win.ps1` 脚本

**主要功能**:
- 用户界面
- 数据可视化
- 系统管理界面

## 服务端口

| 服务模块 | 端口 | 说明 | 访问地址 |
|---------|------|------|----------|
| Nacos | 8848 | 服务注册与配置中心 | http://localhost:8848/nacos |
| MinIO API | 9000 | 对象存储 API | http://localhost:9000 |
| MinIO Console | 9001 | 对象存储控制台 | http://localhost:9001 |
| DEVICE Gateway | 48080 | 设备服务网关 | http://localhost:48080 |
| AI 服务 | 5000 | AI 处理服务 | http://localhost:5000 |
| VIDEO 服务 | 6000 | 视频处理服务 | http://localhost:6000 |
| WEB 前端 | 8888 | Web 前端界面 | http://localhost:8888 |

### 健康检查端点

各服务的健康检查端点：

| 服务模块 | 健康检查端点 |
|---------|-------------|
| 基础服务 (Nacos) | `/nacos/actuator/health` |
| DEVICE 服务 | `/actuator/health` |
| AI 服务 | `/actuator/health` |
| VIDEO 服务 | `/actuator/health` |
| WEB 服务 | `/health` |

## 常见问题

### 1. Docker 权限问题

**问题**: 执行脚本时提示 "没有权限访问 Docker daemon"

**解决方案**:

**Linux**:
```bash
# 将用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录或运行
newgrp docker

# 验证权限
docker ps
```

**macOS**: 
macOS 通常不需要特殊配置，确保 Docker Desktop 正在运行即可。

**Windows**: 
Windows 上 Docker Desktop 会自动处理权限，确保 Docker Desktop 正在运行。

### 2. 端口被占用

**问题**: 启动服务时提示端口已被占用

**解决方案**:

**Linux**:
```bash
# 查看端口占用情况
sudo netstat -tulpn | grep <端口号>
# 或
sudo lsof -i :<端口号>

# 停止占用端口的进程或修改服务配置中的端口
```

**macOS**:
```bash
# 查看端口占用情况
lsof -i :<端口号>

# 停止占用端口的进程或修改服务配置中的端口
```

**Windows**:
```powershell
# 查看端口占用情况
netstat -ano | findstr :<端口号>

# 停止占用端口的进程或修改服务配置中的端口
```

### 3. 服务启动失败

**问题**: 某个服务模块启动失败

**解决方案**:

**Linux/macOS**:
```bash
# 1. 查看服务日志
./install_linux.sh logs    # Linux
./install_mac.sh logs      # macOS

# 2. 查看特定模块的详细日志
cd <模块目录>
docker-compose logs

# 3. 检查 Docker 资源
docker ps -a
docker images

# 4. 检查网络
docker network ls
docker network inspect easyaiot-network
```

**Windows**:
```powershell
# 1. 查看服务日志
.\install_win.ps1 logs

# 2. 查看特定模块的详细日志
cd <模块目录>
docker-compose logs

# 3. 检查 Docker 资源
docker ps -a
docker images

# 4. 检查网络
docker network ls
docker network inspect easyaiot-network
```

### 4. 镜像构建失败

**问题**: 构建镜像时失败

**解决方案**:

**Linux/macOS**:
```bash
# 1. 检查 Docker 磁盘空间
docker system df

# 2. 清理未使用的资源
docker system prune -a

# 3. 检查网络连接（如需拉取基础镜像）
ping registry-1.docker.io

# 4. 单独构建失败模块的镜像
cd <模块目录>
docker-compose build --no-cache
```

**Windows**:
```powershell
# 1. 检查 Docker 磁盘空间
docker system df

# 2. 清理未使用的资源
docker system prune -a

# 3. 检查网络连接（如需拉取基础镜像）
Test-NetConnection registry-1.docker.io -Port 443

# 4. 单独构建失败模块的镜像
cd <模块目录>
docker-compose build --no-cache
```

### 5. 服务无法访问

**问题**: 服务已启动但无法通过浏览器访问

**解决方案**:

**Linux**:
```bash
# 1. 验证服务是否正常运行
./install_linux.sh verify

# 2. 检查防火墙设置
sudo ufw status
# 如需开放端口
sudo ufw allow <端口号>

# 3. 检查服务日志
./install_linux.sh logs

# 4. 检查容器状态
docker ps
```

**macOS**:
```bash
# 1. 验证服务是否正常运行
./install_mac.sh verify

# 2. 检查防火墙设置（系统偏好设置 > 安全性与隐私 > 防火墙）

# 3. 检查服务日志
./install_mac.sh logs

# 4. 检查容器状态
docker ps
```

**Windows**:
```powershell
# 1. 验证服务是否正常运行
.\install_win.ps1 verify

# 2. 检查防火墙设置（Windows 防火墙设置）

# 3. 检查服务日志
.\install_win.ps1 logs

# 4. 检查容器状态
docker ps
```

### 6. 数据丢失问题

**问题**: 清理服务后数据丢失

**说明**: `clean` 命令会删除所有数据卷，导致数据丢失。这是预期行为。

**预防措施**:
- 执行 `clean` 前请备份重要数据
- 生产环境谨慎使用 `clean` 命令
- 建议使用数据卷备份工具

## 日志管理

### 日志文件位置

脚本执行日志保存在 `.scripts/docker/logs/` 目录下：

- **Linux**: `install_linux_YYYYMMDD_HHMMSS.log`
- **macOS**: `install_mac_YYYYMMDD_HHMMSS.log`
- **Windows**: `install_win_YYYYMMDD_HHMMSS.log`

日志文件名包含时间戳，便于区分不同执行记录。

### 查看日志

#### 查看脚本执行日志

**Linux/macOS**:
```bash
# 查看最新的日志文件
ls -lt .scripts/docker/logs/ | head -5

# 查看特定日志文件
tail -f .scripts/docker/logs/install_linux_20240101_120000.log    # Linux
tail -f .scripts/docker/logs/install_mac_20240101_120000.log      # macOS
```

**Windows**:
```powershell
# 查看最新的日志文件
Get-ChildItem .scripts\docker\logs\ | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# 查看特定日志文件
Get-Content .scripts\docker\logs\install_win_20240101_120000.log -Wait
```

#### 查看服务容器日志

**Linux/macOS**:
```bash
# 查看所有服务日志
./install_linux.sh logs    # Linux
./install_mac.sh logs      # macOS

# 查看特定服务的日志（需要进入对应模块目录）
cd DEVICE
docker-compose logs -f
```

**Windows**:
```powershell
# 查看所有服务日志
.\install_win.ps1 logs

# 查看特定服务的日志（需要进入对应模块目录）
cd DEVICE
docker-compose logs -f
```

### 日志内容

脚本日志包含：
- 执行时间戳
- 执行的命令
- 各模块的执行结果
- 错误信息和警告
- 服务状态信息

## 部署流程建议

### 首次部署

#### Linux

1. **环境准备**
   ```bash
   # 检查系统要求
   uname -a
   free -h
   df -h
   
   # 安装 Docker 和 Docker Compose
   # 参考: https://docs.docker.com/get-docker/
   ```

2. **获取代码**
   ```bash
   git clone <repository-url>
   cd easyaiot
   ```

3. **执行安装**
   ```bash
   cd .scripts/docker
   chmod +x install_linux.sh
   ./install_linux.sh install
   ```

4. **验证部署**
   ```bash
   ./install_linux.sh verify
   ```

5. **访问服务**
   - 打开浏览器访问各服务地址
   - 检查服务是否正常运行

#### macOS

1. **环境准备**
   ```bash
   # 检查系统要求
   uname -a
   system_profiler SPHardwareDataType | grep Memory
   df -h
   
   # 安装 Docker Desktop for Mac
   # 参考: https://docs.docker.com/desktop/install/mac-install/
   ```

2. **获取代码**
   ```bash
   git clone <repository-url>
   cd easyaiot
   ```

3. **执行安装**
   ```bash
   cd .scripts/docker
   chmod +x install_mac.sh
   ./install_mac.sh install
   ```

4. **验证部署**
   ```bash
   ./install_mac.sh verify
   ```

5. **访问服务**
   - 打开浏览器访问各服务地址
   - 检查服务是否正常运行

#### Windows

1. **环境准备**
   ```powershell
   # 检查系统要求
   systeminfo | findstr /C:"OS Name" /C:"Total Physical Memory"
   
   # 安装 Docker Desktop for Windows
   # 参考: https://docs.docker.com/desktop/install/windows-install/
   ```

2. **获取代码**
   ```powershell
   git clone <repository-url>
   cd easyaiot
   ```

3. **执行安装**
   ```powershell
   cd .scripts\docker
   .\install_win.ps1 install
   ```

4. **验证部署**
   ```powershell
   .\install_win.ps1 verify
   ```

5. **访问服务**
   - 打开浏览器访问各服务地址
   - 检查服务是否正常运行

### 日常运维

#### Linux/macOS

1. **启动服务**
   ```bash
   ./install_linux.sh start    # Linux
   ./install_mac.sh start      # macOS
   ```

2. **停止服务**
   ```bash
   ./install_linux.sh stop    # Linux
   ./install_mac.sh stop      # macOS
   ```

3. **重启服务**
   ```bash
   ./install_linux.sh restart    # Linux
   ./install_mac.sh restart      # macOS
   ```

4. **查看状态**
   ```bash
   ./install_linux.sh status    # Linux
   ./install_mac.sh status      # macOS
   ```

5. **查看日志**
   ```bash
   ./install_linux.sh logs    # Linux
   ./install_mac.sh logs      # macOS
   ```

#### Windows

1. **启动服务**
   ```powershell
   .\install_win.ps1 start
   ```

2. **停止服务**
   ```powershell
   .\install_win.ps1 stop
   ```

3. **重启服务**
   ```powershell
   .\install_win.ps1 restart
   ```

4. **查看状态**
   ```powershell
   .\install_win.ps1 status
   ```

5. **查看日志**
   ```powershell
   .\install_win.ps1 logs
   ```

### 更新部署

#### Linux/macOS

1. **拉取最新代码**
   ```bash
   git pull
   ```

2. **更新服务**
   ```bash
   cd .scripts/docker
   ./install_linux.sh update    # Linux
   ./install_mac.sh update      # macOS
   ```

3. **验证更新**
   ```bash
   ./install_linux.sh verify    # Linux
   ./install_mac.sh verify      # macOS
   ```

#### Windows

1. **拉取最新代码**
   ```powershell
   git pull
   ```

2. **更新服务**
   ```powershell
   cd .scripts\docker
   .\install_win.ps1 update
   ```

3. **验证更新**
   ```powershell
   .\install_win.ps1 verify
   ```

## 注意事项

1. **版本要求**: **必须**安装 Docker v29.0.0+ 和 Docker Compose v2.35.0+，低于此版本将无法正常运行
2. **网络要求**: 确保服务器可以访问 Docker Hub 或配置的镜像仓库
3. **资源要求**: 确保服务器有足够的 CPU、内存和磁盘空间
4. **端口冲突**: 确保所需端口未被其他服务占用
5. **数据备份**: 生产环境部署前请做好数据备份
6. **安全配置**: 生产环境请配置防火墙和安全组规则
7. **日志管理**: 定期清理旧日志文件，避免磁盘空间不足

## 技术支持

如遇到问题，请：

1. 查看本文档的 [常见问题](#常见问题) 部分
2. 查看服务日志: `./install_all.sh logs`
3. 检查 Docker 状态: `docker ps -a`
4. 提交 Issue 到项目仓库

---

**文档版本**: 1.0  
**最后更新**: 2024-01-01  
**脚本位置**: `.scripts/docker/install_all.sh`

