# 本地连接

无需网络，直接在本机打开终端、打开 WSL 发行版或连接串口设备。

## Local Shell

### 连接参数

| 参数 | 说明 |
|------|------|
| Shell 类型 | 选择要打开的本地 Shell |
| 字符编码 | 终端字符集，默认 UTF-8，可选 GBK、GB2312、Big5、Shift-JIS 等 |
| 启动脚本 | 终端启动后自动执行的命令或脚本（可选） |
| 连接时自动记录日志 | 连接建立时自动开始记录会话日志 |

支持的 Shell 类型（根据操作系统不同，自动检测）：

**Windows：**
- PowerShell
- CMD
- 命令提示符（Clink）
- 命令提示符（管理员）/ PowerShell（管理员）— 经 UAC 提权后以普通标签页嵌入
- Git Bash
- Cygwin / MSYS2
- Nushell

**macOS / Linux：**
- bash
- zsh
- 其他已安装的 Shell

## WSL

在 Windows 上打开已安装的 WSL Linux 发行版（如 Ubuntu、Debian），每个发行版作为独立的 Shell 列出。

**WSL 文件管理：** 文件边栏支持直接浏览与管理 WSL 发行版的文件，无需在发行版内安装任何服务，详见[边栏](/zh/features/sidebar)。

## Serial（串口）

连接串口设备，如路由器控制台、嵌入式开发板、工业设备等。

### 连接参数

| 参数 | 说明 |
|------|------|
| 端口 | 串口号（Windows 下为 COMx，Linux 下为 /dev/ttyUSBx） |
| 波特率 | 传输速率，常用 9600、115200 |
| 数据位 | 每帧数据位，常用 8 |
| 停止位 | 停止位，常用 1 |
| 校验位 | 错误检测，可选 None、Even、Odd、Mark、Space |
| 字符编码 | 终端字符集，默认 UTF-8，可选 GBK、GB2312、Big5、Shift-JIS 等 |
| 退格键 | 终端退格键发送字节，默认 DEL（0x7F），可选 BS（0x08）和 VT220 Delete（ESC[3~） |
| 本地回显 | 是否在本地显示输入内容，按需开启 |
| 换行模式 | CR（默认）或 CR+LF |
| 连接时自动记录日志 | 连接建立时自动开始记录会话日志 |


::: tip 相关内容
- [远程终端](/zh/connections/remote-terminal) —— SSH/Telnet/Mosh 远程连接
- [边栏](/zh/features/sidebar) —— 本地 Shell 快捷启动入口
:::
