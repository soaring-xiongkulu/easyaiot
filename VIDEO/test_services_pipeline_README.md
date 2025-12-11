# 视频流处理管道测试脚本使用文档

## 简介

`test_services_pipeline.py` 是一个视频流处理管道测试脚本，用于验证缓流器、抽帧器、推帧器的逻辑。该脚本实现了以下功能：

- **缓流器**：缓冲源流，接收推帧器插入的处理后的帧
- **抽帧器**：从缓流器抽帧并标记位置，发送给YOLO检测
- **推帧器**：将YOLO检测后的帧推送给缓流器插入

## 功能特性

### 流畅度优化算法

1. **精确帧率控制**：使用基于时间戳的帧率控制，替代简单的sleep，确保帧输出时间精确
2. **减少等待时间**：将最大等待处理时间从1秒减少到0.1秒，大幅降低延迟
3. **帧插值算法**：对于未及时处理的帧，使用上一帧的检测结果进行插值，避免使用原始帧
4. **缓冲区优化**：限制缓冲区大小，使用滑动窗口机制，及时清理旧帧
5. **异步非阻塞处理**：优化等待逻辑，避免长时间阻塞，提升响应速度
6. **YOLO推理优化**：使用优化的推理参数，在保持精度的同时提升检测速度

### 性能优化

1. **分辨率优化**：所有帧统一缩放到1280x720（16:9），保持良好清晰度
2. **码率优化**：输入流2000kbps，输出流1500kbps，平衡清晰度和传输速度
3. **FFmpeg优化**：使用-nobuffer标志降低延迟，BGR像素格式提升处理速度
4. **YOLO检测优化**：使用640尺寸进行检测（自动保持宽高比），提升检测速度

## 前置要求

### 系统依赖

- Python 3.7+
- FFmpeg
- RTMP服务器（SRS）

### Python依赖

```bash
pip install ultralytics opencv-python numpy requests
```

### 文件要求

- 视频文件：默认使用 `video/video2.mp4`，可通过命令行参数指定
- YOLO模型：`yolo11n.pt`（位于脚本目录）

## 使用方法

### 基本用法

```bash
# 使用默认视频文件（video/video2.mp4）
python test_services_pipeline.py

# 使用相对路径指定视频文件
python test_services_pipeline.py -v video/video1.mp4

# 使用绝对路径指定视频文件
python test_services_pipeline.py --video /path/to/your/video.mp4
```

### 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--video` | `-v` | 视频文件路径（相对或绝对路径） | `video/video2.mp4` |

### 参数说明

- **视频文件路径**：
  - 如果不提供 `-v` 或 `--video` 参数，脚本将使用默认视频文件 `video/video2.mp4`
  - 如果提供相对路径，将相对于脚本所在目录解析
  - 如果提供绝对路径，将直接使用该路径

## 配置说明

### RTMP服务器配置

脚本默认使用以下RTMP地址：

- **输入流**：`rtmp://localhost:1935/live/test_input`
- **输出流**：`rtmp://localhost:1935/live/test_output`
- **服务器地址**：`localhost:1935`

### 视频处理配置

- **目标分辨率**：1280x720
- **输入流码率**：2000kbps
- **输出流码率**：1500kbps
- **原始视频帧率**：25fps（假设值，可根据实际情况调整）
- **抽帧间隔**：每5帧抽一次

### 缓冲区配置

- **缓冲区大小**：2.5秒（约62-70帧，根据帧率计算）
- **最小缓冲帧数**：12帧（约0.6秒）
- **最大等待处理时间**：0.08秒

## 启动RTMP服务器

在运行脚本之前，需要先启动RTMP服务器（SRS）：

### 使用Docker Compose启动

```bash
cd /opt/projects/easyaiot/.scripts/docker
docker-compose up -d SRS
```

### 使用Docker直接启动

```bash
docker run -d --name srs-server -p 1935:1935 -p 1985:1985 -p 8080:8080 ossrs/srs:5
```

### 检查SRS服务状态

```bash
# 检查容器状态
docker ps | grep srs

# 检查API状态
curl http://localhost:1985/api/v1/versions
```

## 运行示例

### 示例1：使用默认视频

```bash
cd /opt/projects/easyaiot/VIDEO
python test_services_pipeline.py
```

输出示例：
```
[2024-01-01 10:00:00] [__main__] [INFO] 📹 使用视频文件: /opt/projects/easyaiot/VIDEO/video/video2.mp4
[2024-01-01 10:00:00] [__main__] [INFO] ============================================================
[2024-01-01 10:00:00] [__main__] [INFO] 🚀 服务管道测试脚本启动
[2024-01-01 10:00:00] [__main__] [INFO] ============================================================
...
```

### 示例2：指定自定义视频文件

```bash
cd /opt/projects/easyaiot/VIDEO
python test_services_pipeline.py -v video/custom_video.mp4
```

### 示例3：使用绝对路径

```bash
python test_services_pipeline.py --video /home/user/videos/test.mp4
```

## 停止脚本

按 `Ctrl+C` 停止脚本，脚本会自动清理所有资源并退出。

## 输出说明

脚本运行时会输出以下信息：

- **系统状态**：每10秒输出一次队列状态、缓冲区使用情况和FFmpeg推流状态
- **处理日志**：显示帧处理进度、检测结果等信息
- **警告信息**：当缓冲区过大或队列堆积时输出警告

## 故障排查

### 问题1：视频文件不存在

**错误信息**：
```
❌ 视频文件不存在: /path/to/video.mp4
```

**解决方案**：
- 检查视频文件路径是否正确
- 使用 `-v` 参数指定正确的视频文件路径
- 确保视频文件有读取权限

### 问题2：RTMP服务器不可用

**错误信息**：
```
❌ RTMP 服务器不可用: localhost:1935
```

**解决方案**：
- 确保SRS服务器正在运行
- 检查端口1935是否被占用
- 参考"启动RTMP服务器"章节启动SRS

### 问题3：FFmpeg未安装

**错误信息**：
```
❌ ffmpeg 未安装，请先安装: sudo apt-get install ffmpeg
```

**解决方案**：
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

### 问题4：YOLO模型文件不存在

**错误信息**：
```
❌ YOLO 模型文件不存在: /path/to/yolo11n.pt
```

**解决方案**：
- 确保 `yolo11n.pt` 文件位于脚本目录
- 或下载YOLO模型文件到脚本目录

## 性能调优

### 调整缓冲区大小

在脚本中修改以下配置：

```python
BUFFER_SECONDS = 2.5  # 调整缓冲区时间长度（秒）
MIN_BUFFER_SECONDS = 0.6  # 调整最小缓冲时间（秒）
```

### 调整抽帧间隔

```python
EXTRACT_INTERVAL = 5  # 调整抽帧间隔（每N帧抽一次）
```

### 调整等待时间

```python
MAX_WAIT_TIME = 0.08  # 调整最大等待处理时间（秒）
```

## 注意事项

1. **视频格式**：建议使用MP4格式的视频文件
2. **视频分辨率**：脚本会自动将视频缩放到1280x720
3. **网络延迟**：确保RTMP服务器和脚本运行在同一网络或低延迟网络
4. **资源占用**：脚本会占用一定的CPU和内存资源，建议在性能较好的机器上运行

## 技术支持

如遇到问题，请检查：

1. 日志输出中的错误信息
2. RTMP服务器状态
3. 视频文件格式和路径
4. 系统资源使用情况

## 更新日志

- **v1.0.0**：初始版本，支持基本的视频流处理管道
- **v1.1.0**：添加命令行参数支持，默认使用video2.mp4

