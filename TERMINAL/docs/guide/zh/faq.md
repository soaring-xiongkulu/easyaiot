# 常见问题与排错

## 安装问题

### 杀毒软件报毒 / 文件被删除

本软件未购买代码签名证书，未签名的可执行文件可能被部分杀毒引擎（如 Windows Defender）误报，这是 Go/Wails 应用的已知问题（参见 [wailsapp/wails#3308](https://github.com/wailsapp/wails/issues/3308)）。

- 可在杀毒软件中添加排除规则放行
- 请务必仅从官方开源渠道下载：[GitHub](https://github.com/ys-ll/uniterm/releases) 与 [Gitee](https://gitee.com/ys-l/uniterm/releases)
- 如仍有疑虑，可下载源码自行构建运行

## 连接问题

### SSH 连接失败，提示 "Connection refused"

- 确认目标服务器 SSH 服务是否在运行
- 检查 IP 地址和端口是否正确
- 检查防火墙是否允许该端口

### SSH 密钥认证失败

- 确认密钥文件路径和权限正确；私钥有口令时在「密钥密码」中填写
- 可使用密钥路径字段的一键「使用默认密钥」自动填入本机标准 OpenSSH 密钥
- 也可改用「密钥文本」直接粘贴 PEM 私钥，或使用[密钥库](/zh/features/keystore)身份
- 确认服务器 `~/.ssh/authorized_keys` 中包含对应公钥
- 尝试使用密码认证验证服务器可达性

### SSH 键盘交互认证被拒绝

服务端直接拒绝 keyboard-interactive 认证时，错误提示会显示服务器返回的原始原因，可据此排查（如账号被锁定、PAM 限制等）。

### Kerberos 认证失败

- Windows 会自动使用当前登录会话的凭据；Linux / macOS 需先运行 `kinit` 获取凭据
- 目标为 IP 地址时将请求 `host/<IP>@<REALM>`，需填写 Kerberos Realm；域名目标可留空
- 确认本机时间与域控制器时间偏差不大

### SSH Agent 选项没有出现

SSH Agent 认证仅在 Windows 和 macOS 上提供。Windows 需运行 Pageant 或 Windows OpenSSH Agent 服务；macOS 走系统 `SSH_AUTH_SOCK`。

### 串口连接无反应

- 确认串口号正确（Windows 下为 COMx，Linux 下为 /dev/ttyUSBx）
- 检查波特率等参数是否与设备一致
- 尝试开启"本地回显"以确认输入是否发出

## 终端问题

### 退格键行为异常（删除整词、无法删除字符）

退格键默认值为 DEL（0x7F）。若连接是在旧版本创建且保存过退格键设置，请在连接设置中手动改回 DEL。Windows 本地终端固定按 DEL 处理。

### macOS 输入法丢字、重复或误触发快捷键

v1.9.4 起已修复快速输入丢字/重复、输入法回车上屏误触发应用快捷键、大写字母被吞等问题，请升级到最新版本。

## 功能问题

### AI 助理不响应

- 确认 API 地址和密钥配置正确
- 检查网络是否可访问 API 端点；系统级代理环境下，AI 请求支持「使用系统代理」选项
- 查看 AI 模型配置页面的连接测试结果

### 云同步失败

- 确认 Git 仓库地址和访问令牌正确
- 确认仓库为私有仓库
- 检查网络是否可访问 Git 服务

## 更多帮助

如果您的问题未在此列出，请通过以下渠道反馈：

- [GitHub Issues](https://github.com/ys-ll/uniterm/issues)
