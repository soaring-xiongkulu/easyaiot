# 📹 视频推流测试工具使用文档

## 简介

`test_video.py` 是一个基于 ffmpeg 的视频推流测试脚本，用于将本地视频文件循环推流到 RTMP 服务器。该工具主要用于测试 RTMP 服务器配置、验证推流功能以及进行视频流传输测试。

## 功能特性

- ✅ **循环推流**：支持视频文件无限循环播放和推流
- ✅ **自动检测**：自动检查 ffmpeg 安装状态和视频文件存在性
- ✅ **灵活配置**：支持自定义 RTMP 地址、视频文件路径等参数
- ✅ **优雅退出**：支持 Ctrl+C 安全停止推流进程
- ✅ **实时日志**：可配置不同级别的日志输出
- ✅ **错误处理**：完善的错误提示和处理机制

## 前置要求

### 1. 安装 ffmpeg

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

#### CentOS/RHEL
```bash
sudo yum install epel-release
sudo yum install ffmpeg
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

### 2. 准备视频文件

确保视频文件存在于以下路径：
```
VIDEO/video/video1.mp4
```

### 3. 启动 RTMP 服务器

确保 RTMP 服务器正在运行并监听 `localhost:1935`。如果使用 SRS 服务器，可以参考以下命令：

```bash
# 使用 Docker 启动 SRS
docker run --rm -it -p 1935:1935 -p 1985:1985 -p 8080:8080 \
  registry.cn-hangzhou.aliyuncs.com/ossrs/srs:5 \
  ./objs/srs -c conf/docker.conf
```

## 使用方法

### 基本用法

使用默认配置推流（循环播放 `VIDEO/video/video1.mp4` 到 `rtmp://localhost:1935/live/video1`）：

```bash
python test_video.py
```

或直接执行（已添加执行权限）：

```bash
./test_video.py
```

### 命令行参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--rtmp` | RTMP 推流地址 | `rtmp://localhost:1935/live/video1` | `--rtmp rtmp://192.168.1.100:1935/live/stream1` |
| `--video` | 视频文件路径 | `VIDEO/video/video1.mp4` | `--video /path/to/video.mp4` |
| `--no-loop` | 不循环播放（只播放一次） | `False`（默认循环） | `--no-loop` |
| `--log-level` | ffmpeg 日志级别 | `info` | `--log-level debug` |

### 使用示例

#### 示例 1：使用默认配置推流
```bash
python test_video.py
```

#### 示例 2：推流到远程 RTMP 服务器
```bash
python test_video.py --rtmp rtmp://192.168.1.100:1935/live/stream1
```

#### 示例 3：使用自定义视频文件
```bash
python test_video.py --video /path/to/your/video.mp4
```

#### 示例 4：只播放一次（不循环）
```bash
python test_video.py --no-loop
```

#### 示例 5：显示详细调试信息
```bash
python test_video.py --log-level debug
```

#### 示例 6：组合使用多个参数
```bash
python test_video.py \
  --rtmp rtmp://192.168.1.100:1935/live/test \
  --video /path/to/test.mp4 \
  --log-level verbose
```

## 日志级别说明

`--log-level` 参数支持以下级别（从低到高）：

- `quiet`：静默模式，不输出任何日志
- `panic`：仅输出致命错误
- `fatal`：输出致命错误
- `error`：输出错误信息
- `warning`：输出警告和错误
- `info`：输出信息、警告和错误（默认）
- `verbose`：详细输出
- `debug`：调试模式，输出所有信息
- `trace`：跟踪模式，最详细的输出

## 推流参数说明

脚本使用以下 ffmpeg 参数进行推流：

- `-re`：以原始帧率读取输入，保持视频播放速度
- `-stream_loop -1`：无限循环播放（使用 `--no-loop` 时改为 `0`）
- `-c:v libx264`：使用 H.264 视频编码器
- `-preset veryfast`：快速编码预设，适合实时推流
- `-tune zerolatency`：零延迟调优，减少推流延迟
- `-c:a aac`：使用 AAC 音频编码器
- `-b:v 2000k`：视频比特率 2000kbps
- `-b:a 128k`：音频比特率 128kbps
- `-f flv`：输出格式为 FLV（RTMP 标准格式）

## 停止推流

按 `Ctrl+C` 可以安全停止推流。脚本会：

1. 发送停止信号给 ffmpeg 进程
2. 等待进程正常退出（最多 5 秒）
3. 如果进程未响应，会强制终止

## 常见问题

### Q1: 提示 "ffmpeg 未安装"

**解决方案**：
- 检查 ffmpeg 是否已正确安装：`ffmpeg -version`
- 如果未安装，请参考"前置要求"部分安装 ffmpeg
- 确保 ffmpeg 在系统 PATH 中

### Q2: 提示 "视频文件不存在"

**解决方案**：
- 检查视频文件路径是否正确
- 使用 `--video` 参数指定正确的视频文件路径
- 确保视频文件有读取权限

### Q3: 推流失败，连接被拒绝

**解决方案**：
- 检查 RTMP 服务器是否正在运行
- 确认 RTMP 服务器地址和端口是否正确
- 检查防火墙设置，确保端口 1935 未被阻止
- 使用 `netstat -tulpn | grep 1935` 检查端口是否在监听

### Q4: 推流延迟较高

**解决方案**：
- 检查网络带宽是否足够
- 尝试降低视频比特率（需要修改脚本中的 `-b:v` 参数）
- 使用更快的编码预设（如 `ultrafast`，但会降低画质）

### Q5: 视频播放卡顿

**解决方案**：
- 检查系统资源（CPU、内存）使用情况
- 降低视频分辨率或比特率
- 使用更快的编码预设

## 技术细节

### 脚本结构

- **依赖检查**：自动检查 ffmpeg 和视频文件
- **进程管理**：使用 subprocess 管理 ffmpeg 进程
- **信号处理**：捕获 SIGINT 和 SIGTERM 信号，实现优雅退出
- **实时日志**：实时读取并显示 ffmpeg 的输出信息

### 编码参数优化

脚本使用的编码参数针对实时推流进行了优化：

- **veryfast 预设**：平衡编码速度和画质
- **zerolatency 调优**：最小化推流延迟
- **2000k 视频比特率**：适合大多数网络环境
- **128k 音频比特率**：保证音频质量的同时控制带宽

## 扩展使用

### 修改编码参数

如果需要修改编码参数（如比特率、分辨率等），可以编辑 `test_video.py` 文件中的 `start_streaming` 函数，修改相应的 ffmpeg 参数。

### 添加视频滤镜

可以在 ffmpeg 命令中添加视频滤镜，例如：

```python
# 在 cmd 列表中添加滤镜参数
"-vf", "scale=1280:720",  # 缩放视频
"-vf", "fps=30",          # 设置帧率
```

### 多路推流

可以修改脚本支持同时推流到多个 RTMP 地址，使用 ffmpeg 的输出映射功能。

## 相关资源

- [ffmpeg 官方文档](https://ffmpeg.org/documentation.html)
- [RTMP 协议规范](https://www.adobe.com/devnet/rtmp.html)
- [SRS 流媒体服务器](https://github.com/ossrs/srs)

## 许可证

本工具遵循项目整体许可证。

## 更新日志

### v1.0.0 (2025-01-XX)
- 初始版本发布
- 支持基本的循环推流功能
- 支持命令行参数配置
- 完善的错误检查和提示

---

**注意**：使用本工具前，请确保已获得视频文件的使用授权，并遵守相关法律法规。

