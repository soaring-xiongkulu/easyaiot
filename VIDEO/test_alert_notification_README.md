# 告警通知流程测试脚本

## 功能说明

此脚本用于测试告警通知流程的畅通性，完整流程如下：

1. **模拟产生告警** - 通过VIDEO服务的 `/video/alert/hook` 接口发送测试告警
2. **存储到数据库** - 告警信息存储到PostgreSQL数据库的 `alert` 表
3. **投递到Kafka** - 如果设备配置了告警通知，告警消息会发送到Kafka主题 `iot-alert-notification`
4. **DEVICE服务订阅** - DEVICE的message服务通过 `AlertNotificationConsumer` 订阅Kafka消息
5. **发送通知** - 根据配置的通知方式（邮件、Webhook等）发送告警通知到用户

## 前置条件

1. **VIDEO服务运行中** - 确保VIDEO服务已启动并可访问
2. **数据库连接正常** - 确保PostgreSQL数据库连接正常
3. **Kafka服务运行中** - 确保Kafka服务已启动（可选，如果Kafka不可用，告警仍会存储但不会发送通知）
4. **DEVICE服务运行中** - 确保DEVICE服务的message模块已启动并订阅Kafka（可选，用于完整测试）

## 使用方法

### 基本用法

```bash
# 测试邮件通知
python test_alert_notification.py --device-id camera_001 --email test@example.com

# 测试Webhook通知
python test_alert_notification.py --device-id camera_001 --webhook http://localhost:8080/webhook

# 同时测试邮件和Webhook
python test_alert_notification.py \
    --device-id camera_001 \
    --email test@example.com \
    --webhook http://localhost:8080/webhook
```

### 参数说明

- `--device-id` (必填): 设备ID，用于关联告警和通知配置
- `--device-name` (可选): 设备名称，如果不提供会使用默认名称
- `--email` (可选): 测试邮箱地址，用于邮件通知测试
- `--webhook` (可选): 测试Webhook URL，用于Webhook通知测试
- `--service-url` (可选): VIDEO服务URL，默认为 `http://localhost:6000`

**注意**: 至少需要配置一种通知方式（`--email` 或 `--webhook`）

### 示例

#### 示例1: 测试邮件通知

```bash
python test_alert_notification.py \
    --device-id test_camera_001 \
    --email admin@example.com
```

#### 示例2: 测试Webhook通知

```bash
python test_alert_notification.py \
    --device-id test_camera_001 \
    --webhook http://localhost:8080/api/webhook/alert
```

#### 示例3: 同时测试邮件和Webhook

```bash
python test_alert_notification.py \
    --device-id test_camera_001 \
    --email admin@example.com \
    --webhook http://localhost:8080/api/webhook/alert \
    --device-name "测试摄像头1"
```

#### 示例4: 指定VIDEO服务地址

```bash
python test_alert_notification.py \
    --device-id test_camera_001 \
    --email admin@example.com \
    --service-url http://192.168.1.100:6000
```

## 测试流程

脚本执行时会自动完成以下步骤：

1. **检查服务可用性** - 验证VIDEO服务是否可访问
2. **准备测试环境** - 自动创建或获取测试设备、抓拍空间和告警任务
3. **发送测试告警** - 通过Hook接口发送测试告警数据
4. **验证告警存储** - 检查告警是否成功存储到数据库
5. **检查Kafka消息** - 提示查看Kafka消息投递日志
6. **检查DEVICE服务** - 提示查看DEVICE服务处理日志

## 测试数据

脚本会创建以下测试数据：

- **告警对象类型**: `person`
- **告警事件类型**: `intrusion`
- **告警区域**: `测试区域A`
- **告警信息**: 包含置信度、边界框等测试数据

## 验证结果

### 1. 告警存储验证

脚本会自动验证告警是否成功存储到数据库，并显示告警的详细信息。

### 2. Kafka消息验证

查看VIDEO服务日志，查找以下日志信息：

```
告警通知消息发送到Kafka成功: alert_id=xxx, topic=iot-alert-notification, partition=0, offset=xxx
```

如果Kafka不可用，会看到警告日志：

```
Kafka不可用，跳过告警通知发送: alert_id=xxx
```

### 3. DEVICE服务处理验证

查看DEVICE服务的message模块日志，查找以下日志信息：

```
告警通知Kafka消费者 - 收到告警通知消息: topic=iot-alert-notification, partition=0, offset=xxx, alertId=xxx
处理告警通知: alertId=xxx
发送告警通知: method=email/webhook, alertId=xxx
```

### 4. 邮件通知验证

如果配置了邮件通知，请检查：

- 测试邮箱是否收到告警通知邮件
- 邮件内容是否包含告警信息（设备名称、对象类型、事件类型等）
- DEVICE服务日志中是否有邮件发送成功的记录

### 5. Webhook通知验证

如果配置了Webhook通知，请检查：

- Webhook URL是否收到HTTP POST请求
- 请求体是否包含告警信息（JSON格式）
- HTTP响应状态码是否为200
- DEVICE服务日志中是否有Webhook发送成功的记录

**注意**: Webhook通知需要在DEVICE服务的消息配置中正确配置HTTP消息的URL。如果Webhook URL未正确配置，可能需要在DEVICE服务的消息管理界面中配置HTTP消息模板，或者确保告警通知服务能够从用户信息中获取Webhook URL。

## 常见问题

### 1. VIDEO服务不可用

**错误信息**: `VIDEO服务不可用: http://localhost:6000`

**解决方法**:
- 检查VIDEO服务是否已启动
- 检查服务URL是否正确
- 使用 `--service-url` 参数指定正确的服务地址

### 2. 设备不存在

**错误信息**: `设备不存在: xxx`

**解决方法**:
- 脚本会自动创建测试设备，如果创建失败，请检查数据库连接
- 或者手动在数据库中创建设备记录

### 3. Kafka消息未投递

**可能原因**:
- Kafka服务未启动
- Kafka连接配置错误
- 网络问题

**解决方法**:
- 检查Kafka服务状态
- 检查VIDEO服务的Kafka配置（`KAFKA_BOOTSTRAP_SERVERS`）
- 查看VIDEO服务日志中的Kafka错误信息

### 4. DEVICE服务未处理消息

**可能原因**:
- DEVICE服务未启动
- Kafka消费者未正确订阅
- 消息格式不匹配

**解决方法**:
- 检查DEVICE服务是否运行
- 检查Kafka消费者配置
- 查看DEVICE服务日志中的错误信息

### 5. 邮件未发送

**可能原因**:
- 邮件服务器配置错误
- SMTP服务不可用
- 邮件地址无效

**解决方法**:
- 检查DEVICE服务的邮件配置（SMTP服务器、端口、用户名、密码等）
- 查看DEVICE服务日志中的邮件发送错误信息
- 验证邮件地址格式是否正确

### 6. Webhook未收到请求

**可能原因**:
- Webhook URL不可访问
- 网络问题
- HTTP请求格式错误
- HTTP消息配置中未设置URL

**解决方法**:
- 检查Webhook URL是否可访问（可以使用curl测试）
- 查看DEVICE服务日志中的Webhook发送错误信息
- 检查Webhook服务器的日志
- 确保在DEVICE服务的消息配置中正确配置了HTTP消息的URL
- 检查 `TMsgHttp` 表中的消息记录，确认URL字段是否已设置

## 注意事项

1. **告警抑制时间**: 脚本会自动将告警抑制时间设置为0，确保可以立即发送通知。实际生产环境中，建议设置合理的抑制时间（如300秒）以避免频繁通知。

2. **测试数据清理**: 脚本创建的测试数据（设备、空间、任务）不会自动清理，如果需要清理，请手动删除。

3. **Kafka主题**: 确保Kafka主题 `iot-alert-notification` 已创建，或者Kafka配置为自动创建主题。

4. **通知配置格式**: 
   - 通知方式: `email,webhook` (多个用逗号分隔)
   - 通知人列表: JSON格式，例如: `[{"email": "test@example.com", "name": "测试用户"}]`

5. **日志查看**: 建议同时查看VIDEO服务和DEVICE服务的日志，以便完整追踪告警通知流程。

## 相关文件

- `VIDEO/app/blueprints/alert.py` - 告警Hook接口
- `VIDEO/app/services/alert_hook_service.py` - 告警Hook服务（处理告警并发送到Kafka）
- `DEVICE/iot-message/iot-message-biz/src/main/java/com/basiclab/iot/message/consumer/AlertNotificationConsumer.java` - Kafka消费者
- `DEVICE/iot-message/iot-message-biz/src/main/java/com/basiclab/iot/message/service/impl/AlertNotificationServiceImpl.java` - 告警通知服务实现

## 作者

翱翔的雄库鲁
- Email: andywebjava@163.com
- WeChat: EasyAIoT2025

