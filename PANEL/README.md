# EasyAIoT PANEL

独立于 WEB 的平台运维控制台（参考 1Panel）：管理本机 Docker 容器，界面化执行
统一安装脚本，并提供部署拓扑。

| 平台 | 部署脚本 | 能力 |
|------|----------|------|
| Linux | `install_linux.sh`（arm/kylin 变体） | 镜像拉取 **或** 本地构建 |
| macOS | `install_mac.sh` | **仅镜像部署**（无 build / build-runtime） |
| Windows | `install_windows.sh` | **仅镜像部署**（需 Git Bash + Docker Desktop） |

## 功能菜单

| 菜单 | 能力 |
|------|------|
| 系统概览 | 主机资源、部署形态、快捷入口；进入 WEB 管控台 |
| 容器管理 | 启停 / 重启 / 资源 / 日志 |
| 应用部署 | `install` `start` `stop` `restart` `update` + 进程管控 |
| 镜像中心 | **本地管理** + **构建拉取**（桌面端仅 `pull`；Linux 另有 `build`/`build-runtime`） |
| 系统诊断 | `check` `status` `verify` `profile` `logs` `analyze-logs` `analyze-disk` |
| 系统维护 | `clean`（及 Linux 的 `clean-build-runtime`；默认开启，可用 `PANEL_ALLOW_DANGEROUS=0` 关闭） |
| 服务拓扑 | 服务依赖与运行状态 |

概览页提供 **「进入管控台」**（WEB 未运行时显示「管控台未运行」），跳转到 WEB 管控台（默认 `http://<主机>:8888`）。

> **桌面端：** macOS / Windows 安装 COMPILE 产物后，PANEL 会自动选用 `install_mac.sh` / `install_windows.sh`，并强制「拉取预构建镜像」模式。

## 打包后看不到新菜单？

侧栏应显示 **7** 项：系统概览 / 容器管理 / 应用部署 / **镜像中心** / 系统诊断 / 系统维护 / 服务拓扑。

```bash
# Linux deb
bash COMPILE/build.sh ubuntu --deb
bash COMPILE/install_linux.sh install
sudo systemctl restart easyaiot-panel
```

Windows / macOS 见 `COMPILE/README.md`（产物含内置 `runtime/`）。

## 一键使用（Docker 容器版 PANEL）

```bash
cd PANEL
bash install.sh start
# http://127.0.0.1:9200/
```

容器内仍为 Linux 环境，默认走 `install_linux.sh`。

## 本机可执行文件

```bash
# Ubuntu
bash COMPILE/build.sh ubuntu-x86 --deb

# Windows（在 Windows 上执行）
bash COMPILE/build.sh windows --installer

# macOS（在 macOS 上执行）
bash COMPILE/build.sh macos --dmg
```

详见 `COMPILE/README.md`。

## 环境变量

见 `panel.env.example`（`PANEL_TOKEN`、`PANEL_ALLOW_DANGEROUS`、`INSTALL_SCRIPT`、`EASYAIOT_ROOT` 等）。
