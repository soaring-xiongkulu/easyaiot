# 远程桌面

终端 集成了四种远程桌面协议，提供流畅的图形化远程控制体验。

## RDP

RDP（Remote Desktop Protocol）是 Windows 系统内置的远程桌面协议。

> 仅支持 Windows 版本客户端，macOS 和 Linux 版本该功能隐藏。使用系统内置的远程桌面控件。

![RDP](/imgs/rdp_light.webp)

### 连接参数

| 参数 | 说明 |
|------|------|
| 主机 | Windows 主机 IP 或域名 |
| 端口 | 默认 3389 |
| 用户名 | Windows 登录用户名 |
| 密码 | Windows 登录密码 |
| 域 | 可选，Windows 域名（如 `WORKGROUP`） |
| 会话模式 | 普通会话 / 管理员会话（连接到控制台会话，类似 `mstsc /admin`） |
| 分辨率 | 默认**全屏**；也可选预设固定分辨率或自定义分辨率 |
| 智能缩放 | 开启后远程桌面自动缩放适配窗口大小，默认关闭 |
| 网络身份认证 | 开启（兼容所有版本 Windows，需在凭据弹窗中手动输入密码）/ 关闭（仅兼容 Windows 7 / Server 2008 等关闭 NLA 的服务器） |
| SSH 隧道 | 选择已有的 SSH 连接作为跳板机 |

## VNC

VNC（Virtual Network Computing）广泛用于 Linux 系统远程控制，通过 RFB 协议传输。

### 连接参数

| 参数 | 说明 |
|------|------|
| 主机 | VNC 服务器 IP 或域名 |
| 端口 | 默认 5900。小于 100 则视为 libvirt 显示器编号（自动加 5900） |
| 密码 | VNC 认证密码 |
| 共享会话 | 开启后允许与其他客户端同时连接同一 VNC 服务器，关闭则独占连接 |
| VNC Repeater ID | 通过 UltraVNC 兼容的中继器连接时填写，留空则直连 VNC 服务器 |
| SSH 隧道 | 选择已有的 SSH 连接作为跳板机 |

## SPICE

SPICE（Simple Protocol for Independent Computing Environments）专为 KVM/QEMU 虚拟机优化，提供高性能的虚拟桌面体验。

### 连接参数

| 参数 | 说明 |
|------|------|
| 主机 | SPICE 服务器 IP 或域名 |
| 端口 | 默认 5900 |
| 密码 | SPICE 认证密码 |

> SPICE 不支持 SSH 隧道。

## X11 Desktop

X11 Desktop 通过 SSH 连接启动完整的 Linux 桌面环境（GNOME、KDE、XFCE、MATE、Cinnamon、Openbox），无需在远程主机上安装 VNC 或 RDP 服务。

![X11 Desktop](/imgs/x11_desktop_light.webp)

> Windows 版本内置 VcXsrv X Server，开箱即用。macOS 用户需安装 XQuartz（`brew install --cask xquartz`）。

### 连接参数

| 参数 | 说明 |
|------|------|
| 主机 | SSH 服务器 IP 或域名 |
| 端口 | 默认 22 |
| 用户名 | SSH 登录用户名 |
| 认证方式 | 密钥库 / 密码 / 密钥路径 / 密钥文本 / Kerberos / SSH Agent |
| 桌面环境 | 可选 GNOME、KDE、XFCE、MATE、Cinnamon、Openbox 或自定义命令 |

::: tip 相关内容
- [远程终端](/zh/connections/remote-terminal) —— SSH 隧道可用于保护 RDP/VNC 连接
:::
