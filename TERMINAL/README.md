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

## 更新检查

默认查询上游 GitHub / Gitee 的最新 release，但仅匹配 `terminal-<os>-<arch>-*` 命名的资源，上游 uniTerm 构建不会被自动安装。自建发布通道时可用环境变量覆盖 API 地址（需提供 GitHub 风格的 `/releases/latest` 接口）：

```bash
TERMINAL_UPDATE_API_BASE=https://your-mirror.example.com
```

## 许可证

Apache 2.0。
