# 视频流处理管道测试脚本（带目标追踪）使用文档

## 简介

`test_services_pipeline_tracking.py` 是一个带目标追踪功能的视频流处理管道测试脚本。该脚本在基础版本的基础上，增加了目标追踪功能，能够：

- **追踪目标**：为每个检测到的目标分配唯一追踪ID，保持追踪连续性
- **平滑显示**：使用框缓存机制，避免框闪烁
- **轨迹显示**：显示目标的移动轨迹和中心点历史

## 功能特性

### 基础功能

与基础版本相同的所有功能（详见 `test_services_pipeline_README.md`）

### 目标追踪功能

1. **框近似度匹配**：使用框相似度算法（IOU+中心点距离+形状相似度）匹配，不依赖识别结果
2. **框缓存机制**：每个目标缓存上一次的框位置，避免框闪烁
3. **平滑显示**：对于未检测到的目标，使用缓存的框进行平滑显示
4. **追踪ID管理**：为每个目标分配唯一追踪ID，保持追踪连续性
5. **轨迹可视化**：显示目标的移动轨迹和中心点历史

### 追踪配置参数

- **相似度阈值**：`0.5` - 框相似度匹配阈值，低于此值认为不匹配
- **最大存活帧数**：`15` - 追踪目标最大存活帧数（未匹配时保留的帧数）
- **平滑系数**：`0.92` - 框位置平滑系数（0-1），值越大越平滑，但响应越慢
- **中心点历史**：`30` - 中心点历史最大保留数量
- **离开时间阈值**：`0.5` 秒 - 确认物体离开所需的时间阈值
- **离开检测比阈值**：`0.0` - 确认物体离开时所需的检测比

## 前置要求

### 系统依赖

- Python 3.7+
- FFmpeg
- RTMP服务器（SRS）

### Python依赖

```bash
pip install ultralytics opencv-python numpy requests pillow
```

### 文件要求

- 视频文件：默认使用 `video/video2.mp4`，可通过命令行参数指定
- YOLO模型：`yolo11n.pt`（位于脚本目录）

## 使用方法

### 基本用法

```bash
# 使用默认视频文件（video/video2.mp4）
python test_services_pipeline_tracking.py

# 使用相对路径指定视频文件
python test_services_pipeline_tracking.py -v video/video1.mp4

# 使用绝对路径指定视频文件
python test_services_pipeline_tracking.py --video /path/to/your/video.mp4
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

### 目标追踪配置

可在脚本中修改以下追踪参数：

```python
TRACKING_SIMILARITY_THRESHOLD = 0.5  # 框相似度匹配阈值
TRACKING_MAX_AGE = 15  # 追踪目标最大存活帧数
TRACKING_SMOOTH_ALPHA = 0.92  # 框位置平滑系数
TRACKING_CENTER_HISTORY_MAX = 30  # 中心点历史最大保留数量
TRACKING_CENTER_SIMILARITY_THRESHOLD = 50  # 中心点相似度阈值（像素）
TRACKING_LEAVE_TIME_THRESHOLD = 0.5  # 确认物体离开所需的时间阈值（秒）
TRACKING_LEAVE_PERCENT_THRESHOLD = 0.0  # 确认物体离开时所需的检测比
```

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
python test_services_pipeline_tracking.py
```

输出示例：
```
[2024-01-01 10:00:00] [__main__] [INFO] 📹 使用视频文件: /opt/projects/easyaiot/VIDEO/video/video2.mp4
[2024-01-01 10:00:00] [__main__] [INFO] ============================================================
[2024-01-01 10:00:00] [__main__] [INFO] 🚀 服务管道测试脚本启动
[2024-01-01 10:00:00] [__main__] [INFO] ============================================================
[2024-01-01 10:00:00] [__main__] [INFO] ✅ 目标追踪器初始化成功
[2024-01-01 10:00:00] [__main__] [INFO]    追踪配置: 相似度阈值=0.5, 最大存活=15帧, 平滑系数=0.92, 中心点历史=30点
...
```

### 示例2：指定自定义视频文件

```bash
cd /opt/projects/easyaiot/VIDEO
python test_services_pipeline_tracking.py -v video/custom_video.mp4
```

### 示例3：使用绝对路径

```bash
python test_services_pipeline_tracking.py --video /home/user/videos/test.mp4
```

## 输出说明

### 追踪信息显示

脚本会在视频帧上显示以下追踪信息：

- **追踪ID**：每个目标的唯一标识符
- **类别名称**：检测到的目标类别（如 person, car 等）
- **置信度**：检测置信度
- **开始时间**：目标首次出现的时间
- **持续时间**：目标在画面中的持续时间
- **移动轨迹**：目标的中心点移动轨迹（绿色线条）
- **中心点**：当前帧的中心点位置（绿色圆点）

### 框样式说明

- **实心绿色框**：新检测到的目标（当前帧检测到）
- **半透明绿色框**：使用缓存框的目标（当前帧未检测到，使用上一帧的框）

### 日志输出

脚本运行时会输出以下信息：

- **系统状态**：每10秒输出一次队列状态、缓冲区使用情况和FFmpeg推流状态
- **追踪信息**：显示目标追踪状态、离开事件等
- **处理日志**：显示帧处理进度、检测结果等信息
- **警告信息**：当缓冲区过大或队列堆积时输出警告

## 停止脚本

按 `Ctrl+C` 停止脚本，脚本会自动清理所有资源并退出。

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

### 问题4：PIL/Pillow未安装

**错误信息**：
```
ModuleNotFoundError: No module named 'PIL'
```

**解决方案**：
```bash
pip install pillow
```

### 问题5：追踪效果不理想

**可能原因和解决方案**：

1. **目标ID频繁切换**：
   - 降低 `TRACKING_SIMILARITY_THRESHOLD`（如改为0.3）
   - 增加 `TRACKING_MAX_AGE`（如改为20）

2. **框位置跳跃**：
   - 增加 `TRACKING_SMOOTH_ALPHA`（如改为0.95）

3. **目标消失太快**：
   - 增加 `TRACKING_MAX_AGE`（如改为25）
   - 增加 `TRACKING_LEAVE_TIME_THRESHOLD`（如改为1.0）

## 性能调优

### 调整追踪参数

根据实际场景调整追踪参数：

```python
# 更严格的匹配（减少ID切换）
TRACKING_SIMILARITY_THRESHOLD = 0.6

# 更长的存活时间（目标消失后保留更久）
TRACKING_MAX_AGE = 20

# 更平滑的框位置（减少跳跃）
TRACKING_SMOOTH_ALPHA = 0.95

# 更长的轨迹历史
TRACKING_CENTER_HISTORY_MAX = 50
```

### 调整缓冲区大小

```python
BUFFER_SECONDS = 2.5  # 调整缓冲区时间长度（秒）
MIN_BUFFER_SECONDS = 0.6  # 调整最小缓冲时间（秒）
```

### 调整抽帧间隔

```python
EXTRACT_INTERVAL = 5  # 调整抽帧间隔（每N帧抽一次）
```

## 追踪算法说明

### 框相似度计算

追踪器使用以下公式计算框相似度：

```
相似度 = IOU × 0.4 + 中心点距离相似度 × 0.2 + 形状相似度 × 0.4
```

- **IOU**：两个框的交并比
- **中心点距离相似度**：基于中心点距离的相似度（0-1）
- **形状相似度**：基于框宽度和高度的相似度（0-1）

### 匹配策略

1. 对每个检测结果，找到最佳匹配的追踪目标（基于框相似度）
2. 如果相似度 >= 阈值，则匹配成功，更新追踪目标
3. 如果相似度 < 阈值，则创建新的追踪目标

### 平滑算法

使用指数移动平均（EMA）平滑框位置：

```
新框位置 = 旧框位置 × α + 检测框位置 × (1 - α)
```

其中 `α` 是平滑系数（`TRACKING_SMOOTH_ALPHA`）。

## 注意事项

1. **视频格式**：建议使用MP4格式的视频文件
2. **视频分辨率**：脚本会自动将视频缩放到1280x720
3. **网络延迟**：确保RTMP服务器和脚本运行在同一网络或低延迟网络
4. **资源占用**：脚本会占用一定的CPU和内存资源，建议在性能较好的机器上运行
5. **追踪精度**：追踪效果受视频质量、目标大小、移动速度等因素影响
6. **中文显示**：脚本支持中文标签显示，如果字体加载失败会自动降级为英文

## 与基础版本的区别

| 特性 | 基础版本 | 追踪版本 |
|------|---------|---------|
| 目标检测 | ✅ | ✅ |
| 目标追踪 | ❌ | ✅ |
| 追踪ID | ❌ | ✅ |
| 轨迹显示 | ❌ | ✅ |
| 框缓存 | ❌ | ✅ |
| 平滑显示 | ❌ | ✅ |
| 时间信息 | ❌ | ✅ |

## 技术支持

如遇到问题，请检查：

1. 日志输出中的错误信息
2. RTMP服务器状态
3. 视频文件格式和路径
4. 系统资源使用情况
5. 追踪参数配置是否合理

## 更新日志

- **v1.0.0**：初始版本，支持基本的视频流处理管道
- **v1.1.0**：添加目标追踪功能
- **v1.2.0**：添加命令行参数支持，默认使用video2.mp4

