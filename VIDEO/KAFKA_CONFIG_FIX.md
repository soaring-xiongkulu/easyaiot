# Kafka 配置修复说明

## 问题描述

`realtime_algorithm_service` 容器内出现 Kafka 连接错误：
```
[ERROR] socket disconnected
[ERROR] Closing connection. KafkaConnectionError: socket disconnected
```

日志显示连接地址是 `Kafka:9092`，解析到 `198.18.0.31:9092`，但连接建立后立即断开。

## 根本原因

1. **网络模式不匹配**：`realtime_algorithm_service` 使用 `host` 网络模式，应该使用 `localhost:9092` 访问 Kafka
2. **配置错误**：环境变量 `KAFKA_BOOTSTRAP_SERVERS` 被设置为容器名 `Kafka:9092`，导致连接失败
3. **配置传递问题**：`realtime_algorithm_service` 继承父进程的环境变量，如果父进程配置了容器名，子进程也会使用

## 修复方案

在三个关键位置添加了容器名检测和转换逻辑：

### 1. `run_deploy.py` - Flask 应用配置

**文件**：`VIDEO/services/realtime_algorithm_service/run_deploy.py`

**修复内容**：
- 在 `get_flask_app()` 函数中添加 Kafka 配置
- 检测环境变量中的容器名（`Kafka` 或 `kafka-server`）
- 自动转换为 `localhost:9092`

```python
# 重要：设置 Kafka 配置，realtime_algorithm_service 使用 host 网络模式
# 必须使用 localhost 访问 Kafka，不能使用容器名
kafka_bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
# 如果配置中包含容器名（Kafka 或 kafka-server），强制使用 localhost
if 'Kafka' in kafka_bootstrap_servers or 'kafka-server' in kafka_bootstrap_servers:
    logger.info(f'检测到 Kafka 配置使用容器名，强制覆盖为 localhost:9092（realtime_algorithm_service 使用 host 网络模式）')
    kafka_bootstrap_servers = 'localhost:9092'
```

### 2. `alert_hook_service.py` - Kafka Producer 配置

**文件**：`VIDEO/app/services/alert_hook_service.py`

**修复内容**：
- 在 `get_kafka_producer()` 函数中添加容器名检测
- 无论从 Flask 配置还是环境变量获取，都会检测并转换容器名

```python
# 重要：realtime_algorithm_service 使用 host 网络模式，必须使用 localhost 访问 Kafka
# 如果配置中包含容器名（Kafka 或 kafka-server），强制使用 localhost
if 'Kafka' in bootstrap_servers or 'kafka-server' in bootstrap_servers:
    logger.warning(f'检测到 Kafka 配置使用容器名 "{bootstrap_servers}"，强制覆盖为 localhost:9092（realtime_algorithm_service 使用 host 网络模式）')
    bootstrap_servers = 'localhost:9092'
```

### 3. `algorithm_task_daemon.py` - 环境变量设置

**文件**：`VIDEO/app/services/algorithm_task_daemon.py`

**修复内容**：
- 在启动 `realtime_algorithm_service` 时，检测并转换 Kafka 配置
- 确保传递给子进程的环境变量使用 `localhost:9092`

```python
# 重要：realtime_algorithm_service 使用 host 网络模式，必须使用 localhost 访问 Kafka
# 如果环境变量中配置了容器名（如 Kafka:9092），需要强制覆盖为 localhost:9092
kafka_bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
# 如果配置中包含容器名（Kafka 或 kafka-server），强制使用 localhost
if 'Kafka' in kafka_bootstrap_servers or 'kafka-server' in kafka_bootstrap_servers:
    self._log(f'检测到 Kafka 配置使用容器名，强制覆盖为 localhost:9092（realtime_algorithm_service 使用 host 网络模式）', 'INFO')
    env['KAFKA_BOOTSTRAP_SERVERS'] = 'localhost:9092'
```

## 验证方法

### 1. 运行测试脚本

```bash
cd /opt/projects/easyaiot/VIDEO
python3 test_kafka_config.py
```

### 2. 检查日志

重启 `realtime_algorithm_service` 后，查看日志应该显示：
- 如果检测到容器名，会输出：`检测到 Kafka 配置使用容器名，强制覆盖为 localhost:9092`
- Kafka 连接应该使用 `localhost:9092`，而不是 `Kafka:9092`

### 3. 验证连接

检查日志中不再出现 `socket disconnected` 错误，Kafka 连接应该正常。

## 注意事项

1. **重启服务**：修复后需要重启 `realtime_algorithm_service` 才能生效
2. **环境变量**：虽然代码会自动转换，但建议在环境变量配置中直接使用 `localhost:9092`
3. **网络模式**：`realtime_algorithm_service` 使用 `host` 网络模式，所有服务都应该通过 `localhost` 访问

## 修复文件清单

1. `VIDEO/services/realtime_algorithm_service/run_deploy.py`
2. `VIDEO/app/services/alert_hook_service.py`
3. `VIDEO/app/services/algorithm_task_daemon.py`

## 测试文件

- `VIDEO/test_kafka_config.py` - 验证修复是否生效的测试脚本

