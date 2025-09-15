# 系统要求

- Java 8 或更高版本
- 至少 4GB 内存
- 至少 10GB 可用磁盘空间
- Linux 或类 Unix 操作系统

## 安装步骤

### 1. 安装 Java

Kafka 需要 Java 环境支持，首先确保系统已安装 Java：

### 2. 下载 Kafka
访问 Apache Kafka 官网 获取最新版本的下载链接：
# 下载 Kafka (以 3.5.0 版本为例)
wget https://archive.apache.org/dist/kafka/3.5.0/kafka_2.13-3.5.0.tgz

# 解压文件
tar -xzf kafka_2.13-3.5.0.tgz
mv kafka_2.13-3.5.0 kafka

### 3. 配置 Kafka
Kafka 的主要配置文件位于 config/ 目录下：
cd kafka

# 编辑 server.properties
vim config/server.properties

主要配置项包括：
```
# broker.id 每个节点必须唯一
broker.id=0

# 监听地址
listeners=PLAINTEXT://:9092

# 广告地址（外网访问时需要配置）
advertised.listeners=PLAINTEXT://your.host.name:9092

# 日志目录
log.dirs=/tmp/kafka-logs

# Zookeeper 连接地址
zookeeper.connect=localhost:2181
```
### 4. 启动 Kafka
Kafka 依赖 Zookeeper，需要先启动 Zookeeper：
```
# 启动 Zookeeper
bin/zookeeper-server-start.sh -daemon config/zookeeper.properties

# 启动 Kafka
bin/kafka-server-start.sh -daemon config/server.properties
```

验证 Kafka 是否启动成功：
```
# 检查进程
jps | grep -i kafka

# 查看端口监听
netstat -tuln | grep 9092
```

### 5. 创建测试主题
```
# 创建主题
bin/kafka-topics.sh --create --topic test-topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# 查看主题列表
bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# 查看主题详情
bin/kafka-topics.sh --describe --topic test-topic --bootstrap-server localhost:9092
```

### 6. 测试消息发送和接收
打开两个终端分别进行生产和消费测试：
```
# 终端1：启动消费者
bin/kafka-console-consumer.sh --topic test-topic --bootstrap-server localhost:9092

# 终端2：启动生产者并发送消息
bin/kafka-console-producer.sh --topic test-topic --bootstrap-server localhost:9092
```
在生产者终端输入消息，观察消费者终端是否能接收到相同的消息。

### 常用管理命令
#### 主题管理
```
# 创建主题
bin/kafka-topics.sh --create --topic my-topic --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# 删除主题
bin/kafka-topics.sh --delete --topic my-topic --bootstrap-server localhost:9092

# 列出所有主题
bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# 查看主题详情
bin/kafka-topics.sh --describe --topic my-topic --bootstrap-server localhost:9092
```

#### 消费者组管理
```
# 列出所有消费者组
bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list

# 查看消费者组详情
bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group my-group
```

### 配置优化
#### JVM 参数优化
编辑 bin/kafka-server-start.sh 文件，调整 JVM 参数：
```
export KAFKA_HEAP_OPTS="-Xmx4g -Xms4g"
export KAFKA_JVM_PERFORMANCE_OPTS="-server -XX:+UseG1GC -XX:MaxGCPauseMillis=20 -XX:InitiatingHeapOccupancyPercent=35"
```

### Kafka 性能配置
#### 在 config/server.properties 中添加或修改以下配置：
```
# 网络线程数
num.network.threads=8

# IO线程数
num.io.threads=16

# Socket 服务发送缓冲区大小
socket.send.buffer.bytes=102400

# Socket 服务接收缓冲区大小
socket.receive.buffer.bytes=102400

# Socket 服务请求最大大小
socket.request.max.bytes=104857600

# 日志段文件大小
log.segment.bytes=1073741824

# 日志保留小时数
log.retention.hours=168

# 消息保留最大字节数
log.retention.bytes=1073741824

# 日志清理策略
log.cleanup.policy=delete
```
