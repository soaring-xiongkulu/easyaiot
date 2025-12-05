# Kafka消费者组修复脚本使用说明

## 📋 问题描述

当Kafka日志出现以下错误时，说明消费者组出现了重平衡问题：
```
Preparing to rebalance group video-alert-consumer in state PreparingRebalance
```

这通常是由于：
- 消费者频繁重启
- 多个消费者实例同时运行
- 网络不稳定导致心跳超时
- 消费者组状态异常

## 🚀 快速修复步骤

### 方法一：一键快速修复（最简单，推荐！）

```bash
# 进入VIDEO目录
cd /opt/projects/easyaiot/VIDEO

# 运行一键修复脚本（会自动检查、停止服务、等待、修复）
bash fix_kafka_quick.sh
```

这个脚本会自动：
1. ✅ 检查并停止运行中的消费者服务
2. ✅ 等待30秒让Kafka清理状态
3. ✅ 检查消费者组问题
4. ✅ 执行修复（需要确认）

### 方法二：使用Shell脚本（手动控制）

```bash
# 1. 进入VIDEO目录
cd /opt/projects/easyaiot/VIDEO

# 2. 先检查问题（不执行修复）
bash fix_kafka_consumer_group.sh --check-only

# 3. 如果确认要修复，执行重置（会删除消费者组）
bash fix_kafka_consumer_group.sh --reset
```

### 方法三：使用Python脚本

```bash
# 1. 进入VIDEO目录
cd /opt/projects/easyaiot/VIDEO

# 2. 先检查问题（不执行修复）
python3 fix_kafka_consumer_group.py --check-only

# 3. 如果确认要修复，执行重置（会删除消费者组）
python3 fix_kafka_consumer_group.py --reset
```

## 📝 详细使用说明

### Shell脚本参数

```bash
bash fix_kafka_consumer_group.sh [选项]

选项：
  --reset              重置消费者组（删除组及其偏移量）
  --check-only         仅检查问题，不执行修复
  --group GROUP_ID     指定消费者组ID（默认: video-alert-consumer）
  --topic TOPIC        指定主题名称（默认: iot-alert-notification）
  --bootstrap-servers SERVERS  指定Kafka服务器（默认: localhost:9092）
  -h, --help           显示帮助信息
```

### Python脚本参数

```bash
python3 fix_kafka_consumer_group.py [选项]

选项：
  --reset              重置消费者组偏移量
  --check-only         仅检查问题，不执行修复
  --group GROUP_ID     指定消费者组ID（默认: video-alert-consumer）
  --topic TOPIC        指定主题名称（默认: iot-alert-notification）
  --bootstrap-servers SERVERS  指定Kafka服务器（默认: localhost:9092）
  --reset-to POSITION  重置偏移量到哪个位置（earliest/latest，默认: latest）
  -h, --help           显示帮助信息
```

## ⚙️ 配置说明

脚本会自动从以下位置读取配置（按优先级）：

1. **命令行参数**（最高优先级）
2. **环境变量**
   - `KAFKA_BOOTSTRAP_SERVERS` - Kafka服务器地址
   - `KAFKA_ALERT_CONSUMER_GROUP` - 消费者组ID
   - `KAFKA_ALERT_TOPIC` - 主题名称
3. **.env文件**（在VIDEO目录下）
4. **默认值**
   - 消费者组: `video-alert-consumer`
   - 主题: `iot-alert-notification`
   - Kafka服务器: `localhost:9092`

## 🔧 完整修复流程

### 步骤1：停止消费者服务

```bash
# 停止正在运行的video服务
# 如果是Docker环境：
docker-compose stop video-server

# 如果是直接运行：
# 找到运行中的进程并停止
ps aux | grep "run.py\|alert_consumer"
kill <进程ID>
```

### 步骤2：等待清理（重要！）

```bash
# 等待30秒，让Kafka完全清理消费者组
sleep 30
```

### 步骤3：检查问题

```bash
cd /opt/projects/easyaiot/VIDEO
bash fix_kafka_consumer_group.sh --check-only
```

### 步骤4：执行修复

```bash
# 执行重置（会提示确认）
bash fix_kafka_consumer_group.sh --reset
# 输入 yes 确认
```

### 步骤5：重启服务

```bash
# 重启video服务
# Docker环境：
docker-compose start video-server

# 直接运行：
python3 run.py
```

### 步骤6：监控日志

```bash
# 查看服务日志，确认不再出现重平衡错误
tail -f logs/app.log | grep -i "rebalance\|consumer"
```

## 🐳 Docker环境使用

如果Kafka在Docker容器中运行：

```bash
# 1. 进入Kafka容器执行修复
docker exec -it <kafka容器名> bash
cd /opt/kafka/bin
./kafka-consumer-groups.sh --bootstrap-server localhost:9092 --delete --group video-alert-consumer

# 2. 或者在宿主机上指定Kafka地址
cd /opt/projects/easyaiot/VIDEO
bash fix_kafka_consumer_group.sh --bootstrap-servers <kafka容器IP>:9092 --reset
```

## ⚠️ 注意事项

1. **重置操作会删除消费者组**：这意味着会丢失当前的消费偏移量，消费者重启后会从最新位置（或最早位置）开始消费
2. **确保服务已停止**：在执行重置前，必须停止所有运行中的消费者实例
3. **等待时间很重要**：停止服务后等待30秒，让Kafka完全清理消费者组状态
4. **备份重要数据**：如果担心丢失消息，可以先检查当前偏移量

## 🔍 常见问题

### Q1: 脚本找不到kafka-consumer-groups.sh

**A:** 脚本会自动查找，如果找不到，可以：
- 设置 `KAFKA_HOME` 环境变量
- 或者使用Python脚本（不依赖kafka-consumer-groups.sh）

### Q2: 连接Kafka失败

**A:** 检查：
- Kafka服务是否运行：`docker ps | grep kafka` 或 `systemctl status kafka`
- 服务器地址是否正确（检查.env文件）
- 网络连接是否正常

### Q3: 重置后问题仍然存在

**A:** 可能原因：
- 有多个服务实例在运行（检查进程）
- 消费者配置有问题（检查session_timeout_ms和heartbeat_interval_ms）
- Kafka集群本身有问题

### Q4: 如何查看当前消费者组状态？

```bash
# 使用kafka-consumer-groups.sh
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group video-alert-consumer --describe

# 或使用脚本检查
bash fix_kafka_consumer_group.sh --check-only
```

## 📞 技术支持

- 作者：翱翔的雄库鲁
- 邮箱：andywebjava@163.com
- 微信：EasyAIoT2025

