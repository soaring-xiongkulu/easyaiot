# 修复 SRS StreamBusy 错误

## 问题描述

当多个客户端尝试发布同一个 RTMP 流时，SRS 会返回 `StreamBusy` 错误：

```
[ERROR] serve error code=1028(StreamBusy)(Stream already exists or busy) : 
rtmp: stream /live/1764341204704370859 is busy
```

## 问题原因

1. **旧的发布连接未正确关闭**：之前的 FFmpeg 推流进程异常退出，但 SRS 中的流资源未及时释放
2. **重复推流**：多个客户端同时尝试发布同一个流，SRS 不允许同一流的多个发布者
3. **缺少流冲突检测**：在启动新推流前，没有检查并停止现有的流

## 解决方案

### 1. 在推流前检查并停止现有流

在 `VIDEO/services/realtime_algorithm_service/run_deploy.py` 中：

- 添加了 `check_and_stop_existing_stream()` 函数，用于检查并停止现有的 RTMP 流
- 在 `buffer_streamer_worker()` 中，启动 FFmpeg 推流前调用此函数

**实现逻辑**：
1. 通过 SRS HTTP API 查询现有流列表
2. 如果发现匹配的流，尝试以下方法停止：
   - 方法1：断开发布者客户端连接（推荐）
   - 方法2：通过流ID停止流
   - 方法3：查找并终止占用该流的 ffmpeg 进程

### 2. 改进 on_publish 回调

在 `VIDEO/app/blueprints/camera.py` 中：

- 改进了 `on_publish_callback()` 函数，使其能够检测并处理流冲突

**实现逻辑**：
1. 当客户端尝试发布流时，检查是否已有该流的发布者
2. 如果已有发布者且不是当前客户端，尝试停止旧的发布者
3. 然后允许新的发布请求

## 代码变更

### 1. `run_deploy.py`

- 添加了 `check_and_stop_existing_stream()` 函数（约 170 行代码）
- 在 `buffer_streamer_worker()` 中，启动 FFmpeg 推流前添加了流检查：

```python
# 在启动推流前，检查并停止现有流（避免StreamBusy错误）
logger.info(f"🔍 检查设备 {device_id} 是否存在占用该地址的流...")
check_and_stop_existing_stream(rtmp_url)
```

### 2. `camera.py`

- 改进了 `on_publish_callback()` 函数，添加了流冲突检测和处理逻辑
- 添加了 `os` 模块导入

## 使用方法

### 环境变量配置

可以通过环境变量配置 SRS 服务器地址：

```bash
# 在 .env 文件中设置
SRS_HOST=localhost  # 默认值：localhost
```

### 日志监控

当检测到流冲突时，会输出以下日志：

```
🔍 检查现有流: live/1764341204704370859
⚠️  发现现有流: live/1764341204704370859 (ID: xxx)，正在停止...
   尝试断开发布者客户端: xxx
✅ 已断开发布者客户端，流将自动停止
```

## 注意事项

1. **SRS API 端口**：默认使用 1985 端口，如果 SRS 配置了不同的端口，需要修改代码
2. **网络延迟**：停止现有流后，会等待 2 秒让流完全停止，然后再启动新推流
3. **异常处理**：如果检查或停止流失败，不会阻止新推流的启动，避免影响正常流程

## 测试建议

1. **测试场景1**：正常推流
   - 启动一个设备的推流，应该能正常推流

2. **测试场景2**：重复推流
   - 启动一个设备的推流
   - 立即再次启动同一设备的推流
   - 应该自动停止旧的推流，启动新的推流

3. **测试场景3**：异常恢复
   - 手动终止一个 ffmpeg 进程
   - 重新启动该设备的推流
   - 应该能检测到旧的流并清理，然后正常启动新推流

## 相关文件

- `VIDEO/services/realtime_algorithm_service/run_deploy.py` - 推流服务主文件
- `VIDEO/app/blueprints/camera.py` - SRS 回调接口
- `VIDEO/test_services_pipeline.py` - 参考实现（包含 `check_and_stop_existing_stream` 函数）

## 后续优化建议

1. **配置化**：将 SRS API 地址和端口配置化，支持从环境变量读取
2. **重试机制**：如果停止流失败，可以添加重试机制
3. **监控告警**：当频繁出现流冲突时，可以添加监控告警
4. **流状态缓存**：可以缓存流的发布状态，减少 API 调用

