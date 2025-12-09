# Kafka 连接问题最终修复方案

## 问题根源

问题的根本原因是：**Kafka 服务器的 `KAFKA_ADVERTISED_LISTENERS` 配置为 `PLAINTEXT://Kafka:9092`**。

当客户端使用 `localhost:9092` 连接到 Kafka 时：
1. 客户端成功连接到 Kafka 服务器
2. Kafka 服务器返回元数据，其中包含 `Kafka:9092` 作为 advertised listener
3. 客户端尝试使用 `Kafka:9092` 连接 broker
4. 由于 `realtime_algorithm_service` 使用 host 网络模式，无法解析 `Kafka` 容器名
5. 连接失败，出现 `socket disconnected` 错误

## 修复方案

### 1. 修改 Kafka 配置（已完成）

修改 `.scripts/docker/docker-compose.yml` 中的 Kafka 配置：

```yaml
- KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://Kafka:9092,PLAINTEXT://localhost:9092
```

这样配置后，Kafka 会同时返回两个 advertised listener：
- `Kafka:9092` - 用于 Docker 网络内的服务（如 DEVICE 服务）
- `localhost:9092` - 用于 host 网络模式的服务（如 VIDEO 服务）

### 2. 客户端代码修复（已完成）

已在以下文件中添加容器名检测和转换逻辑：
- `VIDEO/services/realtime_algorithm_service/run_deploy.py`
- `VIDEO/app/services/alert_hook_service.py`
- `VIDEO/app/services/notification_service.py`
- `VIDEO/app/services/algorithm_task_daemon.py`
- `VIDEO/run.py`

### 3. 配置文件修复（已完成）

- `VIDEO/.env.prod` - 已更新为 `localhost:9092`

## 重要：需要重启 Kafka 服务

**⚠️ 必须重启 Kafka 容器才能使配置生效！**

```bash
# 重启 Kafka 容器
cd /opt/projects/easyaiot/.scripts/docker
docker-compose restart Kafka

# 或者如果使用其他方式启动的 Kafka
docker restart kafka-server
```

## 验证步骤

### 1. 检查 Kafka 配置

```bash
# 进入 Kafka 容器
docker exec -it kafka-server bash

# 检查配置
cat /opt/kafka/config/kraft/server.properties | grep advertised.listeners
# 应该显示：advertised.listeners=PLAINTEXT://Kafka:9092,PLAINTEXT://localhost:9092
```

### 2. 重启 Kafka 服务

```bash
docker restart kafka-server
```

### 3. 等待 Kafka 启动完成

```bash
# 检查 Kafka 是否正常运行
docker logs kafka-server | tail -20
```

### 4. 重启 VIDEO 服务

```bash
# 重启 VIDEO 容器
docker restart video-service

# 或者重启 realtime_algorithm_service 进程
```

### 5. 检查日志

重启后，查看日志应该显示：
- ✅ `Kafka生产者初始化成功: localhost:9092`
- ✅ 连接地址应该是 `localhost:9092`，不再是 `Kafka:9092`
- ✅ 不再出现 `socket disconnected` 错误
- ✅ 不再出现 `KafkaTimeoutError` 错误

## 如果问题仍然存在

### 检查 Kafka 元数据

```bash
# 使用 kafka-console-producer 测试连接
docker exec -it kafka-server /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic test-topic

# 在另一个终端检查元数据
docker exec -it kafka-server /opt/kafka/bin/kafka-broker-api-versions.sh \
  --bootstrap-server localhost:9092
```

### 检查网络连接

```bash
# 在 VIDEO 容器内测试连接
docker exec -it video-service bash
telnet localhost 9092
# 或
nc -zv localhost 9092
```

### 检查环境变量

```bash
# 在 realtime_algorithm_service 进程中检查
ps aux | grep run_deploy
# 查看进程的环境变量
cat /proc/<PID>/environ | tr '\0' '\n' | grep KAFKA
```

## 注意事项

1. **Kafka 配置更改需要重启**：修改 `KAFKA_ADVERTISED_LISTENERS` 后，必须重启 Kafka 容器才能生效
2. **多个 advertised listeners**：Kafka 会同时返回多个 advertised listener，客户端会选择可用的地址
3. **网络模式**：`realtime_algorithm_service` 使用 host 网络模式，必须使用 `localhost:9092` 连接
4. **Docker 网络**：DEVICE 服务使用 Docker 网络模式，可以使用 `Kafka:9092` 连接

## 修复文件清单

1. ✅ `.scripts/docker/docker-compose.yml` - Kafka 配置
2. ✅ `VIDEO/.env.prod` - 环境变量配置
3. ✅ `VIDEO/services/realtime_algorithm_service/run_deploy.py` - 代码修复
4. ✅ `VIDEO/app/services/alert_hook_service.py` - 代码修复
5. ✅ `VIDEO/app/services/notification_service.py` - 代码修复
6. ✅ `VIDEO/app/services/algorithm_task_daemon.py` - 代码修复
7. ✅ `VIDEO/run.py` - 代码修复

