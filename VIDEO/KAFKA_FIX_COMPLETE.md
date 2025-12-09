# Kafka 配置修复完整方案

## 问题总结

1. **连接地址错误**：日志显示连接尝试使用 `Kafka:9092`，但 `realtime_algorithm_service` 使用 `host` 网络模式，应该使用 `localhost:9092`
2. **元数据超时**：`KafkaTimeoutError: Failed to update metadata after 60.0 secs`
3. **方法不存在**：`'KafkaProducer' object has no attribute 'list_topics'`

## 修复内容

### 1. 修复文件清单

#### 代码修复
- ✅ `VIDEO/services/realtime_algorithm_service/run_deploy.py`
  - 在 `get_flask_app()` 中添加 Kafka 配置和容器名检测
  - 在 `load_dotenv()` 之后立即强制覆盖环境变量

- ✅ `VIDEO/app/services/alert_hook_service.py`
  - 在 `get_kafka_producer()` 中添加容器名检测
  - 修复 `list_topics` 方法调用问题（添加 `hasattr` 检查）

- ✅ `VIDEO/app/services/notification_service.py`
  - 在 `get_kafka_producer()` 中添加容器名检测

- ✅ `VIDEO/app/services/algorithm_task_daemon.py`
  - 在启动 `realtime_algorithm_service` 时检测并转换环境变量

- ✅ `VIDEO/run.py`
  - 在 Flask 应用配置中添加容器名检测

#### 配置文件修复
- ✅ `VIDEO/.env.prod`
  - 将 `KAFKA_BOOTSTRAP_SERVERS=Kafka:9092` 改为 `KAFKA_BOOTSTRAP_SERVERS=localhost:9092`

### 2. 修复逻辑

所有修复都遵循以下逻辑：
```python
# 检测容器名并转换为 localhost
kafka_bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
if 'Kafka' in kafka_bootstrap_servers or 'kafka-server' in kafka_bootstrap_servers:
    # 强制使用 localhost:9092
    kafka_bootstrap_servers = 'localhost:9092'
    # 记录日志
    logger.warning(f'检测到 Kafka 配置使用容器名，强制覆盖为 localhost:9092')
```

### 3. 关键修复点

#### 修复点 1: `run_deploy.py` - 环境变量强制覆盖
```python
# 加载环境变量
load_dotenv()

# 重要：在加载环境变量后，立即强制覆盖 Kafka 配置
kafka_bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
if 'Kafka' in kafka_bootstrap_servers or 'kafka-server' in kafka_bootstrap_servers:
    os.environ['KAFKA_BOOTSTRAP_SERVERS'] = 'localhost:9092'
    print(f'⚠️  检测到 Kafka 配置使用容器名，已强制覆盖为 localhost:9092')
```

#### 修复点 2: `alert_hook_service.py` - 修复 list_topics 方法
```python
# 如果已经初始化成功，检查连接健康状态
if _producer is not None:
    try:
        # 注意：某些版本的 kafka-python 可能没有 list_topics 方法
        if hasattr(_producer, 'list_topics'):
            _producer.list_topics(timeout=1)
        return _producer
    except Exception as e:
        # 连接已断开，重置生产者
        ...
```

## 验证步骤

### 1. 检查配置文件
```bash
cd /opt/projects/easyaiot/VIDEO
grep KAFKA_BOOTSTRAP_SERVERS .env.prod
# 应该显示：KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

### 2. 检查 Kafka 服务
```bash
# 检查端口是否监听
netstat -tlnp | grep 9092
# 或
ss -tlnp | grep 9092

# 测试连接
python3 -c "import socket; s = socket.socket(); result = s.connect_ex(('localhost', 9092)); s.close(); print('连接测试:', '成功' if result == 0 else '失败')"
```

### 3. 重启服务
```bash
# 重启 VIDEO 容器
docker restart video-service

# 或重启 realtime_algorithm_service 进程
# 停止现有进程后重新启动
```

### 4. 检查日志
重启后，查看日志应该显示：
- ✅ `检测到 Kafka 配置使用容器名，已强制覆盖为 localhost:9092`
- ✅ `Kafka生产者初始化成功: localhost:9092`
- ✅ 连接地址应该是 `localhost:9092`，不再是 `Kafka:9092`
- ✅ 不再出现 `socket disconnected` 错误
- ✅ 不再出现 `KafkaTimeoutError` 错误

## 注意事项

1. **网络模式**：`realtime_algorithm_service` 使用 `host` 网络模式，所有服务都应该通过 `localhost` 访问
2. **环境变量优先级**：代码中的强制覆盖逻辑会确保使用 `localhost:9092`，即使配置文件中有容器名
3. **多进程问题**：如果有多个 Kafka producer 实例，每个实例都会独立检测和转换配置
4. **Kafka 服务位置**：确保 Kafka 服务确实在 `localhost:9092` 上运行

## 测试脚本

运行测试脚本验证修复：
```bash
cd /opt/projects/easyaiot/VIDEO
python3 test_kafka_config.py
```

## 如果问题仍然存在

1. **检查是否有其他 .env 文件**：
   ```bash
   find . -name ".env*" -type f
   ```

2. **检查环境变量**：
   ```bash
   # 在容器内或进程中检查
   echo $KAFKA_BOOTSTRAP_SERVERS
   ```

3. **检查 Kafka 服务状态**：
   ```bash
   # 检查 Kafka 是否正常运行
   # 检查防火墙规则
   # 检查网络连接
   ```

4. **查看完整日志**：
   - 查找所有包含 "Kafka" 的日志行
   - 确认是否所有连接都使用 `localhost:9092`

