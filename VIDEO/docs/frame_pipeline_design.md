# 多摄像头帧处理管道设计文档

## 概述

本文档描述了用于多摄像头并行处理的帧数据传输结构设计。该设计支持1个抽帧器、1个排序器、1个推送器和多个模型服务同时处理多个摄像头的帧数据。

## 架构设计

### 核心组件

1. **FrameData** - 帧数据结构
   - 位置: `app/utils/frame_data.py`
   - 用途: 在抽帧器、排序器、推送器之间传输帧数据
   - 特点: 包含摄像头ID标记，支持多摄像头并行处理

2. **FrameQueueManager** - 队列管理器
   - 位置: `app/utils/frame_queue_manager.py`
   - 用途: 管理3个内存队列（抽帧器、排序器、推送器）
   - 特点: 支持按设备ID分组，提供统计和监控功能

3. **Pusher模型增强** - 多摄像头RTMP推送支持
   - 位置: `models.py`
   - 新增字段: `device_rtmp_mapping` (JSON格式，存储device_id -> rtmp_url映射)

## 数据结构

### FrameData 类

```python
@dataclass
class FrameData:
    device_id: str          # 摄像头ID（关键字段，用于区分不同摄像头）
    task_id: int            # 算法任务ID
    frame_index: int        # 帧序号
    frame_data: np.ndarray  # OpenCV帧数据
    frame_bytes: bytes      # 帧字节流（用于序列化）
    timestamp: float        # 时间戳
    capture_time: datetime  # 捕获时间
    metadata: dict          # 元数据
    detection_results: list # 检测结果
    confidence_scores: list  # 置信度分数
    processed_frame: np.ndarray # 处理后的帧
    is_processed: bool     # 是否已处理
    is_sorted: bool         # 是否已排序
    is_pushed: bool         # 是否已推送
```

### 队列结构

系统包含3个主队列和按设备ID分组的子队列：

1. **extractor_queue** - 抽帧器队列
   - 从摄像头流中抽取的原始帧
   - 按device_id标记

2. **sorter_queue** - 排序器队列
   - 经过算法处理后的帧
   - 按device_id和置信度排序

3. **pusher_queue** - 推送器队列
   - 准备推送到RTMP流的帧
   - 按device_id分组，推送到对应的RTMP地址

## 数据流程

```
摄像头1 ──┐
摄像头2 ──┤
摄像头3 ──┼──> [抽帧器] ──> extractor_queue ──> [算法服务1,2,3...] ──> sorter_queue ──> [排序器] ──> pusher_queue ──> [推送器] ──> RTMP流1,2,3...
摄像头N ──┘
```

### 详细流程

1. **抽帧阶段**
   - 抽帧器从多个摄像头流中抽取帧
   - 为每个帧创建FrameData对象，标记device_id
   - 将FrameData放入extractor_queue

2. **算法处理阶段**
   - 从extractor_queue获取帧（可按device_id过滤）
   - 多个模型服务并行处理不同摄像头的帧
   - 处理结果写入FrameData的detection_results和confidence_scores
   - 将处理后的帧放入sorter_queue

3. **排序阶段**
   - 从sorter_queue获取帧（可按device_id过滤）
   - 根据置信度、时间等规则排序
   - 将排序后的帧放入pusher_queue

4. **推送阶段**
   - 从pusher_queue获取帧（按device_id分组）
   - 根据device_rtmp_mapping查找对应的RTMP地址
   - 推送到对应摄像头的RTMP流

## 数据库变更

### Pusher表新增字段

```sql
ALTER TABLE pusher ADD COLUMN device_rtmp_mapping TEXT NULL 
COMMENT '多摄像头RTMP推送映射（JSON格式，device_id -> rtmp_url）';
```

### 字段格式示例

```json
{
  "device_id_1": "rtmp://server1/live/stream1",
  "device_id_2": "rtmp://server1/live/stream2",
  "device_id_3": "rtmp://server2/live/stream3"
}
```

## 使用示例

### 1. 创建队列管理器

```python
from app.utils.frame_queue_manager import get_queue_manager

queue_manager = get_queue_manager()
```

### 2. 抽帧器使用

```python
from app.utils.frame_data import FrameData
import cv2

# 从摄像头流中抽取帧
ret, frame = cap.read()
if ret:
    frame_data = FrameData(
        device_id="camera_001",
        task_id=1,
        frame_index=frame_count,
        frame_data=frame
    )
    # 放入抽帧器队列
    queue_manager.put_to_extractor_queue(frame_data)
```

### 3. 算法服务使用

```python
# 从抽帧器队列获取帧
frame_data = queue_manager.get_from_extractor_queue(device_id="camera_001")

if frame_data:
    # 处理帧
    results = model.detect(frame_data.get_frame_for_processing())
    frame_data.detection_results = results
    frame_data.confidence_scores = [r.confidence for r in results]
    frame_data.is_processed = True
    
    # 放入排序器队列
    queue_manager.put_to_sorter_queue(frame_data)
```

### 4. 排序器使用

```python
# 从排序器队列获取帧
frame_data = queue_manager.get_from_sorter_queue(device_id="camera_001")

if frame_data:
    # 根据置信度排序
    if frame_data.has_detections():
        max_confidence = frame_data.get_max_confidence()
        # 排序逻辑...
        frame_data.is_sorted = True
        
        # 放入推送器队列
        queue_manager.put_to_pusher_queue(frame_data)
```

### 5. 推送器使用

```python
from models import Pusher

# 从推送器队列获取帧
frame_data = queue_manager.get_from_pusher_queue(device_id="camera_001")

if frame_data:
    # 获取推送器配置
    pusher = Pusher.query.get(pusher_id)
    
    # 获取该摄像头对应的RTMP地址
    rtmp_url = pusher.get_rtmp_url_for_device(frame_data.device_id)
    
    # 推送到RTMP流
    push_frame_to_rtmp(frame_data.processed_frame, rtmp_url)
    frame_data.is_pushed = True
```

## 监控和统计

### 获取队列状态

```python
# 获取所有队列大小
queue_sizes = queue_manager.get_queue_sizes()
print(f"抽帧器队列: {queue_sizes['extractor_queue_size']}")
print(f"排序器队列: {queue_sizes['sorter_queue_size']}")
print(f"推送器队列: {queue_sizes['pusher_queue_size']}")

# 获取设备特定队列大小
device_queues = queue_sizes['device_queues']
for device_id, queues in device_queues.items():
    print(f"设备 {device_id}:")
    print(f"  抽帧器队列: {queues['extractor']}")
    print(f"  排序器队列: {queues['sorter']}")
    print(f"  推送器队列: {queues['pusher']}")
```

### 获取统计信息

```python
stats = queue_manager.get_stats()
print(f"总处理帧数: {stats['total_frames_processed']}")
print(f"总排序帧数: {stats['total_frames_sorted']}")
print(f"总推送帧数: {stats['total_frames_pushed']}")
```

## 前端配置

### 推送器多摄像头配置

在创建或编辑推送器时，可以配置多摄像头RTMP映射：

```javascript
{
  pusher_name: "多摄像头推送器",
  video_stream_enabled: true,
  device_rtmp_mapping: {
    "camera_001": "rtmp://server1/live/stream1",
    "camera_002": "rtmp://server1/live/stream2",
    "camera_003": "rtmp://server2/live/stream3"
  },
  video_stream_format: "rtmp",
  video_stream_quality: "high"
}
```

## 注意事项

1. **内存管理**: 队列大小有限制（默认1000），需要及时处理队列中的帧，避免内存溢出
2. **线程安全**: FrameQueueManager使用线程锁保证线程安全
3. **设备ID一致性**: 确保在整个流程中使用相同的device_id
4. **RTMP映射**: 如果device_rtmp_mapping中没有对应设备，会回退到video_stream_url
5. **序列化**: FrameData支持序列化，但frame_data和frame_bytes需要单独处理

## 迁移步骤

1. 执行数据库迁移脚本：
   ```bash
   psql -d your_database -f migrations/add_device_rtmp_mapping_to_pusher.sql
   ```

2. 更新后端代码，使用新的FrameData和FrameQueueManager

3. 更新前端代码，支持多摄像头RTMP映射配置

4. 测试多摄像头并行处理流程

## 扩展性

该设计支持：
- 动态添加/删除摄像头
- 不同摄像头使用不同的算法服务
- 不同摄像头推送到不同的RTMP服务器
- 队列监控和性能统计
- 故障恢复和重试机制

