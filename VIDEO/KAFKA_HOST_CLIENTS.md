# Kafka — 宿主机客户端连通（FR-B24）

## 问题

本地 Docker Kafka（`kafka-server`）常见配置：

```text
KAFKA_ADVERTISED_LISTENERS=INTERNAL://Kafka:9092,EXTERNAL://localhost:9094
```

宿主机客户端连接 `127.0.0.1:9092` 时，broker 元数据返回 `Kafka:9092`。若 hosts 未解析 `Kafka`，则 Python `kafka-python` / Java `KafkaConsumer` 均报 **DNS Resolution failure**（FR-B23 证据）。

容器内服务仍应使用 `Kafka:9092`（Docker 网络别名），**不要**全局改主 compose 的 INTERNAL 监听器。

## 推荐修复（本地开发）

在 **宿主机** `hosts` 增加一行（需管理员权限）：

```text
127.0.0.1 Kafka
```

Windows：`C:\Windows\System32\drivers\etc\hosts`  
Linux/macOS：`/etc/hosts`

验证：

```bash
python -c "from kafka import KafkaAdminClient; c=KafkaAdminClient(bootstrap_servers=['127.0.0.1:9092'], request_timeout_ms=8000); print(len(c.list_topics())); c.close()"
```

## 客户端 bootstrap

与 Python `media_kafka_service._bootstrap_servers()` 一致，Java `DvrUploadKafkaConsumerRunner` / `SnapUploadKafkaConsumerRunner` 在环境变量含 `Kafka` 或 `kafka-server` 时回退 `localhost:9092`。

本地 profile 推荐：

```yaml
video:
  kafka:
    bootstrap-servers: 127.0.0.1:9092
```

## 新栈可选 override

若从零拉起 Kafka 且需同时服务容器与宿主机，可用 `VIDEO/docker-compose.kafka-host.override.example.yaml`（示例，不自动应用）将 INTERNAL advertised 改为 `127.0.0.1:9092`。**仅用于独立本地栈**；与现有 `easyaiot-network` 混跑时优先 hosts 方案。

## 取证

```bash
python tools/video_java/fr_b24_kafka_e2e.py --java-log logs/fr-b24-java-soak.log
```

产物：`logs/fr-b24-kafka-e2e.{json,md}`
