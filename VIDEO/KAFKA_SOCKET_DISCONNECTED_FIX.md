# Kafka Socket Disconnected 问题修复

## 问题描述

日志显示 Kafka 连接不断重试，出现以下错误：
```
WARNING:kafka.client:Node 1 connection failed -- refreshing metadata
INFO:kafka.conn:<BrokerConnection ... host=Kafka:9092 <connecting> ...>: connecting to Kafka:9092
INFO:kafka.conn:<BrokerConnection ... host=Kafka:9092 <connected> ...>: Connection complete.
ERROR:kafka.conn:<BrokerConnection ... host=Kafka:9092 <connected> ...>: socket disconnected
ERROR:kafka.conn:<BrokerConnection ... host=Kafka:9092 <connected> ...>: Closing connection. KafkaConnectionError: socket disconnected
```

## 问题根本原因

1. **Kafka broker 元数据问题**：即使客户端使用 `localhost:9092` 作为 bootstrap_servers，Kafka broker 返回的元数据中可能包含 `Kafka:9092` 作为 advertised listener
2. **容器名解析失败**：客户端尝试连接到 `Kafka:9092`，但在 host 网络模式下无法解析容器名 `Kafka`
3. **连接建立后立即断开**：即使能够解析到 IP 地址（如 `198.18.0.31:9092`），连接建立后也会立即断开，因为 Kafka broker 可能没有在该地址上正确监听

## 修复方案

### 1. 代码层面修复（已完成）

#### `alert_hook_service.py` 和 `notification_service.py`
- ✅ 添加了更严格的容器名检测和转换逻辑
- ✅ 在创建 KafkaProducer 之前，确保 bootstrap_servers 不包含容器名
- ✅ 添加了详细的日志记录，便于调试
- ✅ 添加了错误处理，当检测到容器名时给出明确的提示

#### 关键修复点：
```python
# 1. 检测并转换容器名
original_bootstrap_servers = bootstrap_servers
if 'Kafka' in bootstrap_servers or 'kafka-server' in bootstrap_servers:
    logger.warning(f'⚠️  检测到 Kafka 配置使用容器名 "{bootstrap_servers}"，强制覆盖为 localhost:9092')
    bootstrap_servers = 'localhost:9092'

# 2. 在创建 KafkaProducer 之前再次清理
bootstrap_servers_list = bootstrap_servers.split(',') if isinstance(bootstrap_servers, str) else bootstrap_servers
bootstrap_servers_list = [s.strip() for s in bootstrap_servers_list if s.strip() and 'Kafka' not in s and 'kafka-server' not in s]
if not bootstrap_servers_list:
    bootstrap_servers_list = ['localhost:9092']

# 3. 添加详细的错误日志
if 'Kafka:9092' in error_msg or 'Kafka' in error_msg:
    logger.error(f"⚠️  检测到错误信息中包含容器名 'Kafka'，这通常是因为 Kafka broker 的 "
                f"KAFKA_ADVERTISED_LISTENERS 配置问题。请确保 Kafka broker 的配置包含 "
                f"PLAINTEXT://localhost:9092")
```

### 2. Kafka Broker 配置修复（需要手动操作）

**重要**：即使客户端代码已经修复，如果 Kafka broker 的 `KAFKA_ADVERTISED_LISTENERS` 配置不正确，问题仍然可能出现。

#### 检查 Kafka broker 配置：
```bash
# 进入 Kafka 容器
docker exec -it kafka-server bash

# 查看 Kafka 配置
cat /opt/kafka/config/server.properties | grep advertised.listeners
# 或
env | grep KAFKA_ADVERTISED_LISTENERS
```

#### 正确的配置应该是：
```properties
# 对于 host 网络模式的服务，必须包含 localhost:9092
KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092

# 或者同时支持容器名和 localhost（推荐）
KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://Kafka:9092,PLAINTEXT://localhost:9092
```

#### 修改 Kafka broker 配置：
1. **如果使用 Docker Compose**：
   ```yaml
   environment:
     KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092,PLAINTEXT://Kafka:9092
   ```

2. **如果使用环境变量文件**：
   ```bash
   # 在 Kafka 容器的环境变量中设置
   KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092,PLAINTEXT://Kafka:9092
   ```

3. **重启 Kafka 服务**：
   ```bash
   docker restart kafka-server
   ```

### 3. 环境变量检查

确保所有相关服务的环境变量都正确设置：

```bash
# 检查 VIDEO 服务的环境变量
cd /opt/projects/easyaiot/VIDEO
grep KAFKA_BOOTSTRAP_SERVERS .env .env.prod .env.docker

# 应该显示：
# KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

## 验证步骤

### 1. 检查代码修复是否生效
```bash
# 查看日志，应该看到：
# - "⚠️  检测到 Kafka 配置使用容器名..."（如果配置中有容器名）
# - "✅ Kafka生产者初始化成功: bootstrap_servers=['localhost:9092']"
# - 不再出现 "connecting to Kafka:9092" 的日志
```

### 2. 检查 Kafka broker 配置
```bash
# 检查 Kafka broker 的 advertised listeners
docker exec kafka-server /opt/kafka/bin/kafka-broker-api-versions.sh \
  --bootstrap-server localhost:9092 \
  --command-config /opt/kafka/config/client.properties
```

### 3. 测试连接
```python
# 使用 Python 测试 Kafka 连接
from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
# 应该能够成功创建，不会出现 socket disconnected 错误
```

### 4. 监控日志
重启服务后，监控日志应该显示：
- ✅ 连接地址是 `localhost:9092`，不再是 `Kafka:9092`
- ✅ 不再出现 `socket disconnected` 错误
- ✅ 不再出现连接循环重试

## 如果问题仍然存在

### 1. 检查网络配置
```bash
# 检查 localhost:9092 是否可访问
telnet localhost 9092
# 或
nc -zv localhost 9092
```

### 2. 检查 Kafka 服务状态
```bash
# 检查 Kafka 是否正常运行
docker ps | grep kafka
docker logs kafka-server --tail 50
```

### 3. 检查防火墙规则
```bash
# 确保 9092 端口没有被防火墙阻止
sudo ufw status
sudo iptables -L -n | grep 9092
```

### 4. 查看详细日志
```bash
# 启用 Kafka 客户端的详细日志
export KAFKA_LOG_LEVEL=DEBUG
# 然后重启服务，查看详细日志
```

## 总结

1. **代码层面**：已经修复，确保客户端强制使用 `localhost:9092`
2. **Kafka broker 配置**：需要确保 `KAFKA_ADVERTISED_LISTENERS` 包含 `PLAINTEXT://localhost:9092`
3. **环境变量**：确保所有服务的 `KAFKA_BOOTSTRAP_SERVERS` 设置为 `localhost:9092`

修复后，Kafka 连接应该能够正常工作，不再出现 socket disconnected 错误。
