# EasyAIoT TERMINAL（终端）

一站式多协议终端与远程运维客户端，是 EasyAIoT 平台的终端模块。支持 SSH、RDP、VNC、SFTP、数据库、Kubernetes 等 30 余种协议，并内置可自主规划、多轮执行 Shell 命令的 AI Agent。

> 本模块基于开源项目 [uniTerm](https://github.com/ys-ll/uniterm) 集成改名而来，遵循其原 Apache 2.0 许可证，第三方组件声明见 `THIRD_PARTY_NOTICES.md`。

## 功能特性

### 终端与会话

- **远程终端**：SSH / Telnet / Mosh / Raw TCP，支持密码与密钥认证，可经 SSH 跳板做隧道端口转发
- **本地与串口终端**：PowerShell / CMD / Git Bash / WSL，以及可配置波特率、数据位、停止位、校验位的串口连接
- **远程桌面**：RDP（Windows）、VNC（Linux）、SPICE（KVM/QEMU 虚拟机）、X11 转发
- **Shell 集成**：OSC7 目录上报、命令历史与智能补全

### 文件传输

- SFTP / SCP / FTP / FTPS / SMB / WebDAV / S3，双栏文件管理器
- SSH 终端内 `rz` / `sz`（Zmodem），传输任务中心统一管理进度

### 数据库与容器

- 数据库客户端：MySQL / PostgreSQL / Oracle / SQL Server / rqlite / Redis / MongoDB / Elasticsearch
- 容器接入：Kubernetes / Docker / Podman / nerdctl（containerd）/ WSLC
- 连接配置导入：uniTerm（.utm）/ WindTerm / SecureCRT / Xshell / MobaXterm / DBeaver / Navicat / OpenSSH
- **EasyAIoT 中间件快捷配置**：内置平台全部中间件的默认连接，打开即用、双击直连（详见下方[中间件快捷配置](#中间件快捷配置)）

### 监控与同步

- 服务器实时监控：CPU、内存、磁盘、网络、进程、端口、网卡
- 配置经 Git 仓库多机同步，密钥存入系统钥匙串（Keychain / Credential Manager）

### AI Agent

- 自主规划并多轮执行 Shell 命令，可按危险等级控制确认策略
- 侧边栏对话接入 Anthropic / OpenAI 兼容大模型，会话按连接持久化
- 命令智能补全与 AI 改写，支持在分屏中固定或跟随活动终端

## 技术栈

- 后端：Go 1.26+，Wails v3（桌面 GUI / 无头 HTTP server 双形态）
- 前端：Vue 3 + TypeScript + Vite，xterm.js、Element Plus、CodeMirror
- 构建：wails3 CLI + Taskfile

## 目录结构

```
TERMINAL/
├── main.go            # 应用入口（GUI / server 双模式）
├── app*.go            # 暴露给前端的应用层 API
├── backend/           # 会话、存储、凭据、容器、K8s、数据库、更新等后端包
├── frontend/          # Vue 3 前端（绑定代码构建期生成到 frontend/bindings/）
├── build/             # 各平台打包资产与 Taskfile
└── docs/              # 用户手册站点（VitePress，继承自上游）
```

## 从源码构建

### 环境要求

- Go ≥ 1.26
- Node.js ≥ 20（含 npm）
- Wails v3 CLI：`go install github.com/wailsapp/wails/v3/cmd/wails3@v3.0.0-beta.16`
- 平台依赖：Linux 需 `pkg-config` 与 `libwebkit2gtk-4.1-dev` 等 GTK/WebKit 开发库；Windows 需 WebView2 Runtime；macOS 需 Xcode

### 常用命令

```bash
cd TERMINAL

wails3 task dev            # 开发调试
wails3 task build          # 构建桌面应用，产物在 bin/
wails3 task package        # 打包生产安装包
wails3 task build:server   # 无 GUI 的纯 HTTP server 模式，产物 bin/Terminal-server
wails3 task run:server     # 运行 server 模式
wails3 task build:docker   # 构建 server 模式 Docker 镜像
wails3 task run:docker     # 构建并运行容器
```

版本号通过 `VERSION` 变量注入：`wails3 task build VERSION=v1.0.0`。

在没有桌面依赖的环境（如 CI 容器）中，可先交叉验证 Go 侧代码：

```bash
CGO_ENABLED=0 go build -tags server ./...
```

## 运行时路径

- 数据目录：`<UserConfigDir>/Terminal`（Linux `~/.config/Terminal`，macOS `~/Library/Application Support/Terminal`，Windows `%APPDATA%\Terminal`）；如需便携化，可在可执行文件旁放置 `data/bootstrap.json` 指定自定义数据目录
- 日志文件：`~/.terminal/terminal.log`

## 中间件快捷配置

TERMINAL 预置了 EasyAIoT 平台所用全部中间件的默认连接。首次启动（以及完成凭据初始化 / 解锁）时，会自动在连接库中创建「EasyAIoT 中间件」分组，首页顶部同步展示该分组的卡片——**双击即可直接访问**：

| 预置项 | 类型 | 默认地址 | 双击行为 |
|--------|------|----------|----------|
| PostgreSQL | 数据库 | `:5432`，账号 `postgres`，默认库 `iot-device20` | 打开内置 SQL 客户端 |
| MySQL | 数据库 | `:3306`，账号 `root` | 打开内置 SQL 客户端 |
| Redis | 数据库 | `:6379` | 打开内置键值浏览器 |
| RustFS (S3) | 对象存储 | `:9000`，路径风格寻址（path-style） | 打开内置 S3 浏览器 |
| Docker | 容器 | 本地 socket | 打开内置容器管理器 |
| TDengine | 本地终端 | — | 打开本地终端并自动执行 `docker exec -it tdengine-server taos` |
| Kafka | 本地终端 | — | 打开本地终端并自动执行 `docker exec -it kafka-server bash` |
| Nacos / EMQX / RustFS 控制台 / Node-RED / FUXA / ZLMediaKit / SRS | Web 应用 | `:8848/nacos`、`:18083`、`:9001`、`:1880`、`:1881`、`:6080`、`:8080` | 调用系统默认浏览器打开对应控制台 |

这些预置项就是普通连接：可以随意编辑、收藏、搜索、删除，凭据同样存入加密仓库；分组名按界面语言本地化。种子逻辑幂等——删除后不会被原样复活，仅当内置预设版本升级时才补种缺失条目，用户已有的修改不会被覆盖。

### 主机地址覆盖

预设默认连接 `localhost`。当中间件部署在别处（或 TERMINAL 以 server 模式跑在容器里）时，用环境变量重定向，无需逐条手改：

```bash
EASYAIOT_MIDDLEWARE_HOST=192.168.1.10   # 一次覆盖全部预设的主机
EASYAIOT_POSTGRES_HOST=db.internal      # 单项覆盖（服务名：POSTGRES / MYSQL / REDIS / RUSTFS /
                                        #   NACOS / EMQX / NODERED / FUXA / ZLMEDIAKIT / SRS）
```

Web 应用类预设支持整条 URL 覆盖：如 `EASYAIOT_NACOS_HOST=http://10.0.0.5:28848/nacos`（值里带 `://` 时作为完整地址使用——已含服务路径不会重复拼接，裸主机则按 `http://<host>:<默认端口>` 拼接）。

Docker 部署（`docker-compose.yml`）已默认注入 `EASYAIOT_MIDDLEWARE_HOST=host.docker.internal` 并配置 `host-gateway` 映射，容器内即可直达宿主机发布的各中间件端口。

## 许可证

Apache 2.0。
