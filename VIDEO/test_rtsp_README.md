# 📹 RTSP到RTMP推流测试工具使用文档

## 简介

`test_rtsp.py` 是一个基于 FFmpeg 的 RTSP 到 RTMP 推流测试脚本，用于将本地摄像头的 RTSP 流推送到远端 SRS RTMP 服务器。该工具主要用于测试 RTSP 摄像头连接、验证推流功能以及进行视频流传输测试。

## 功能特性

- ✅ **RTSP 到 RTMP 推流**：支持将 RTSP 流实时推送到 RTMP 服务器
- ✅ **连接测试**：启动前自动测试 RTSP 流是否可用
- ✅ **灵活配置**：支持自定义码率、编码预设、传输协议等参数
- ✅ **优雅退出**：支持 Ctrl+C 安全停止推流进程
- ✅ **实时日志**：实时显示推流状态和错误信息
- ✅ **错误处理**：完善的错误提示和处理机制
- ✅ **音频支持**：可选启用/禁用音频编码

## 前置要求

### 1. 安装 FFmpeg

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install ffmpeg ffprobe
```

#### CentOS/RHEL
```bash
sudo yum install epel-release
sudo yum install ffmpeg ffprobe
```

#### macOS
```bash
brew install ffmpeg
```

#### Windows
从 [ffmpeg 官网](https://ffmpeg.org/download.html) 下载并安装，或使用包管理器：
```powershell
choco install ffmpeg
# 或
scoop install ffmpeg
```

**注意**：`ffprobe` 用于 RTSP 连接测试，如果未安装，脚本会跳过连接测试但不会阻止推流。

### 2. 准备 RTSP 摄像头

确保摄像头支持 RTSP 协议，并获取 RTSP 流地址。常见的 RTSP 地址格式：

```
rtsp://username:password@ip:port/stream_path
```

例如：
- 海康威视：`rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101`
- 大华：`rtsp://admin:password@192.168.1.100:554/cam/realmonitor?channel=1&subtype=0`
- 通用格式：`rtsp://admin:password@192.168.1.100:554/stream1`

### 3. 启动 RTMP 服务器（SRS）

确保 RTMP 服务器正在运行。如果使用 SRS 服务器，可以参考以下命令：

```bash
# 使用 Docker 启动 SRS
docker run --rm -it -p 1935:1935 -p 1985:1985 -p 8080:8080 \
  registry.cn-hangzhou.aliyuncs.com/ossrs/srs:5 \
  ./objs/srs -c conf/docker.conf
```

或者使用本地安装的 SRS：
```bash
# 启动 SRS
./objs/srs -c conf/srs.conf
```

## 使用方法

### 基本用法

将 RTSP 流推送到 RTMP 服务器：

```bash
python3 test_rtsp.py rtsp://admin:password@192.168.1.100:554/stream \
    rtmp://srs.example.com:1935/live/stream1
```

或直接执行（已添加执行权限）：

```bash
./test_rtsp.py rtsp://admin:password@192.168.1.100:554/stream \
    rtmp://srs.example.com:1935/live/stream1
```

### 命令行参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `rtsp_url` | RTSP 输入流地址（必需） | - | `rtsp://admin:password@192.168.1.100:554/stream` |
| `rtmp_url` | RTMP 输出流地址（必需） | - | `rtmp://srs.example.com:1935/live/stream1` |
| `--bitrate` | 视频比特率 | `2000k` | `--bitrate 1500k` |
| `--preset` | 编码预设 | `veryfast` | `--preset ultrafast` |
| `--rtsp-transport` | RTSP 传输协议 | `tcp` | `--rtsp-transport udp` |
| `--enable-audio` | 启用音频编码 | `False`（禁用） | `--enable-audio` |
| `--skip-test` | 跳过 RTSP 连接测试 | `False`（测试） | `--skip-test` |

### 编码预设说明

`--preset` 参数支持以下选项（从快到慢，CPU占用从低到高）：

- `ultrafast`：最快编码，最低 CPU 占用，画质较低
- `superfast`：超快编码，低 CPU 占用
- `veryfast`：很快编码，平衡速度和画质（**默认**）
- `faster`：较快编码
- `fast`：快速编码
- `medium`：中等编码，平衡画质和速度
- `slow`：慢速编码，高画质
- `slower`：更慢编码，更高画质
- `veryslow`：最慢编码，最高画质，CPU 占用最高

**推荐**：
- 实时推流：使用 `ultrafast` 或 `veryfast`
- 画质优先：使用 `medium` 或 `slow`
- 低 CPU 占用：使用 `ultrafast`

### 使用示例

#### 示例 1：基本推流

```bash
python3 test_rtsp.py \
    rtsp://admin:password@192.168.1.100:554/stream \
    rtmp://localhost:1935/live/stream1
```

#### 示例 2：低 CPU 占用推流（推荐用于资源受限环境）

```bash
python3 test_rtsp.py \
    rtsp://admin:password@192.168.1.100:554/stream \
    rtmp://srs.example.com:1935/live/stream1 \
    --bitrate 1500k \
    --preset ultrafast
```

#### 示例 3：高画质推流

```bash
python3 test_rtsp.py \
    rtsp://admin:password@192.168.1.100:554/stream \
    rtmp://srs.example.com:1935/live/stream1 \
    --bitrate 4000k \
    --preset medium
```

#### 示例 4：使用 UDP 传输并启用音频

```bash
python3 test_rtsp.py \
    rtsp://admin:password@192.168.1.100:554/stream \
    rtmp://srs.example.com:1935/live/stream1 \
    --rtsp-transport udp \
    --enable-audio
```

#### 示例 5：跳过 RTSP 连接测试（快速启动）

```bash
python3 test_rtsp.py \
    rtsp://admin:password@192.168.1.100:554/stream \
    rtmp://srs.example.com:1935/live/stream1 \
    --skip-test
```

#### 示例 6：组合使用多个参数

```bash
python3 test_rtsp.py \
    rtsp://admin:password@192.168.1.100:554/stream \
    rtmp://srs.example.com:1935/live/stream1 \
    --bitrate 2000k \
    --preset veryfast \
    --rtsp-transport tcp \
    --enable-audio
```

## RTSP 连接测试

脚本在启动推流前会自动测试 RTSP 连接（除非使用 `--skip-test` 参数）。测试会：

1. 使用 `ffprobe` 连接 RTSP 流
2. 获取流的基本信息（编码、分辨率、帧率等）
3. 验证流是否可用

如果测试失败，脚本会询问是否继续推流，您可以选择：
- 输入 `y` 继续推流（可能仍然会失败）
- 输入 `n` 退出脚本

## 推流参数说明

脚本使用以下 FFmpeg 参数进行推流：

- `-rtsp_transport tcp/udp`：RTSP 传输协议（TCP 更稳定，UDP 延迟更低）
- `-i <rtsp_url>`：RTSP 输入流地址
- `-an`：禁用音频（默认，使用 `--enable-audio` 时移除）
- `-c:v libx264`：使用 H.264 视频编码器
- `-b:v <bitrate>`：视频比特率（默认 2000k）
- `-preset <preset>`：编码预设（默认 veryfast）
- `-tune zerolatency`：零延迟调优，减少推流延迟
- `-f flv`：输出格式为 FLV（RTMP 标准格式）
- `-c:a aac -b:a 128k`：音频编码（仅在使用 `--enable-audio` 时）

## 停止推流

按 `Ctrl+C` 可以安全停止推流。脚本会：

1. 发送终止信号给 FFmpeg 进程
2. 等待进程正常退出（最多 5 秒）
3. 如果进程未响应，会强制终止

**注意**：请使用 `Ctrl+C` 而不是直接关闭终端，以确保 FFmpeg 进程被正确清理。

## 常见问题

### Q1: 提示 "FFmpeg 未安装"

**解决方案**：
- 检查 FFmpeg 是否已正确安装：`ffmpeg -version`
- 如果未安装，请参考"前置要求"部分安装 FFmpeg
- 确保 FFmpeg 在系统 PATH 中

### Q2: RTSP 连接测试失败

**可能原因和解决方案**：

1. **RTSP 地址错误**
   - 检查 RTSP 地址格式是否正确
   - 确认用户名和密码是否正确
   - 验证 IP 地址和端口是否正确

2. **网络连接问题**
   - 使用 `ping` 测试摄像头 IP 是否可达
   - 检查防火墙设置，确保 RTSP 端口（通常是 554）未被阻止
   - 使用 `telnet <ip> 554` 测试端口是否开放

3. **摄像头不支持 RTSP**
   - 确认摄像头型号支持 RTSP 协议
   - 查看摄像头文档获取正确的 RTSP 地址格式

4. **RTSP 流路径错误**
   - 不同品牌的摄像头 RTSP 路径格式不同
   - 参考摄像头文档或使用 VLC 等工具测试 RTSP 地址

**临时解决方案**：
- 使用 `--skip-test` 参数跳过连接测试，直接尝试推流

### Q3: 推流失败，RTMP 连接被拒绝

**解决方案**：
- 检查 RTMP 服务器是否正在运行
- 确认 RTMP 服务器地址和端口是否正确（默认 1935）
- 检查防火墙设置，确保端口 1935 未被阻止
- 使用 `netstat -tulpn | grep 1935` 检查端口是否在监听
- 测试 RTMP 服务器连接：`telnet <rtmp_host> 1935`

### Q4: 推流延迟较高

**解决方案**：
- 使用 TCP 传输（`--rtsp-transport tcp`，默认）
- 降低视频比特率（`--bitrate 1500k`）
- 使用更快的编码预设（`--preset ultrafast`）
- 检查网络带宽是否足够
- 检查 RTSP 摄像头到推流服务器的网络延迟

### Q5: 视频播放卡顿

**解决方案**：
- 检查系统资源（CPU、内存）使用情况
- 降低视频比特率
- 使用更快的编码预设（如 `ultrafast`）
- 检查网络带宽是否足够
- 检查 RTMP 服务器性能

### Q6: CPU 占用过高

**解决方案**：
- 使用更快的编码预设（`--preset ultrafast`）
- 降低视频比特率（`--bitrate 1000k`）
- 检查是否有多个推流进程在运行
- 考虑使用硬件编码（需要修改脚本）

### Q7: 音频不同步或缺失

**解决方案**：
- 使用 `--enable-audio` 参数启用音频编码
- 检查 RTSP 流是否包含音频
- 如果 RTSP 流本身没有音频，启用音频参数也不会产生音频

### Q8: FFmpeg 进程立即退出

**可能原因**：
1. RTSP 流地址错误或不可用
2. RTMP 服务器地址错误或不可用
3. 网络连接问题
4. 编码参数错误

**解决方案**：
- 查看脚本输出的错误信息
- 检查 RTSP 和 RTMP 地址是否正确
- 使用 `--skip-test` 跳过测试，查看详细错误信息
- 手动运行 FFmpeg 命令进行调试

## 技术细节

### 脚本结构

- **依赖检查**：自动检查 FFmpeg 安装状态
- **连接测试**：使用 ffprobe 测试 RTSP 流可用性
- **进程管理**：使用 subprocess 管理 FFmpeg 进程
- **信号处理**：捕获 SIGINT 和 SIGTERM 信号，实现优雅退出
- **实时日志**：实时读取并显示 FFmpeg 的输出信息

### 编码参数优化

脚本使用的编码参数针对实时推流进行了优化：

- **veryfast 预设**：平衡编码速度和画质（默认）
- **zerolatency 调优**：最小化推流延迟
- **2000k 视频比特率**：适合大多数网络环境（默认）
- **TCP 传输**：更稳定的 RTSP 传输（默认）

### RTSP 传输协议选择

- **TCP**（默认）：更稳定，适合网络质量一般的环境
- **UDP**：延迟更低，但可能丢包，适合网络质量好的环境

**推荐**：大多数情况下使用 TCP，如果遇到延迟问题再尝试 UDP。

## 扩展使用

### 修改编码参数

如果需要修改编码参数（如分辨率、帧率等），可以编辑 `test_rtsp.py` 文件中的 `start_rtsp_to_rtmp_push` 函数，在 `ffmpeg_cmd` 列表中添加相应的 FFmpeg 参数。

例如，添加分辨率缩放：
```python
ffmpeg_cmd.extend(['-vf', 'scale=1280:720'])  # 缩放到 1280x720
```

### 添加视频滤镜

可以在 FFmpeg 命令中添加视频滤镜，例如：

```python
# 在 ffmpeg_cmd 列表中添加滤镜参数
"-vf", "scale=1280:720,fps=30",  # 缩放并设置帧率
"-vf", "hflip",                  # 水平翻转
"-vf", "vflip",                  # 垂直翻转
```

### 多路推流

可以修改脚本支持同时推流到多个 RTMP 地址，使用 FFmpeg 的输出映射功能：

```python
# 推流到多个地址
ffmpeg_cmd.extend([
    '-f', 'flv', rtmp_url1,
    '-f', 'flv', rtmp_url2,
])
```

### 录制推流

可以在推流的同时录制视频，使用 FFmpeg 的输出映射：

```python
# 同时推流和录制
ffmpeg_cmd.extend([
    '-f', 'flv', rtmp_url,      # 推流
    '-c', 'copy',               # 复制流（不重新编码）
    '-f', 'mp4', 'output.mp4',  # 录制
])
```

## 调试技巧

### 1. 手动测试 RTSP 流

使用 VLC 或其他播放器测试 RTSP 流是否可用：
```bash
vlc rtsp://admin:password@192.168.1.100:554/stream
```

### 2. 手动测试 RTMP 推流

使用 FFmpeg 手动推流，查看详细错误信息：
```bash
ffmpeg -rtsp_transport tcp -i rtsp://admin:password@192.168.1.100:554/stream \
    -c:v libx264 -b:v 2000k -preset veryfast -tune zerolatency \
    -f flv rtmp://localhost:1935/live/test
```

### 3. 查看 FFmpeg 详细日志

修改脚本中的日志级别为 `debug` 或 `verbose`，查看更详细的输出信息。

### 4. 检查网络连接

```bash
# 测试 RTSP 端口
telnet <camera_ip> 554

# 测试 RTMP 端口
telnet <rtmp_server_ip> 1935

# 查看网络延迟
ping <camera_ip>
ping <rtmp_server_ip>
```

## 相关资源

- [FFmpeg 官方文档](https://ffmpeg.org/documentation.html)
- [RTSP 协议规范](https://tools.ietf.org/html/rfc2326)
- [RTMP 协议规范](https://www.adobe.com/devnet/rtmp.html)
- [SRS 流媒体服务器](https://github.com/ossrs/srs)
- [H.264 编码指南](https://trac.ffmpeg.org/wiki/Encode/H.264)

## 许可证

本工具遵循项目整体许可证。

## 更新日志

### v1.0.0 (2025-01-XX)
- 初始版本发布
- 支持 RTSP 到 RTMP 推流功能
- 支持 RTSP 连接测试
- 支持命令行参数配置
- 完善的错误检查和提示
- 支持优雅退出

---

## 注意事项

1. **安全性**：RTSP 地址中包含用户名和密码，请注意保护脚本和命令行历史记录
2. **网络带宽**：推流会消耗网络带宽，请确保网络带宽足够
3. **系统资源**：推流会消耗 CPU 资源，请根据系统性能选择合适的编码参数
4. **法律法规**：使用本工具前，请确保已获得摄像头的使用授权，并遵守相关法律法规
5. **RTMP 服务器**：确保 RTMP 服务器配置正确，支持接收推流

## 联系支持

如有问题或建议，请联系：
- 作者：翱翔的雄库鲁
- 邮箱：andywebjava@163.com
- 微信：EasyAIoT2025
