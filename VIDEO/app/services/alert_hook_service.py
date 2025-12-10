"""
告警Hook服务：处理实时分析中的告警信息，仅发送到Kafka（Java端统一处理消息）
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
import logging
import time
from datetime import datetime
from typing import Dict, Optional

from flask import current_app
from kafka import KafkaProducer
from kafka.errors import KafkaError
from models import db

logger = logging.getLogger(__name__)

_producer = None
_producer_init_failed = False
_last_init_attempt_time = 0
_init_retry_interval = 60  # 初始化失败后，60秒内不再重试
# 警告抑制：记录上次输出 Kafka 不可用警告的时间，避免日志刷屏
_last_kafka_unavailable_warning_time = 0
_kafka_unavailable_warning_interval = 300  # 每5分钟最多输出一次警告


def get_kafka_producer():
    """获取Kafka生产者实例（单例，带错误处理和重试限制）"""
    global _producer, _producer_init_failed, _last_init_attempt_time
    
    # 从Flask配置中获取Kafka配置
    try:
        bootstrap_servers = current_app.config.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        request_timeout_ms = current_app.config.get('KAFKA_REQUEST_TIMEOUT_MS', 30000)  # 增加到30秒
        retries = current_app.config.get('KAFKA_RETRIES', 3)  # 增加到3次
        retry_backoff_ms = current_app.config.get('KAFKA_RETRY_BACKOFF_MS', 1000)  # 增加到1秒
        metadata_max_age_ms = current_app.config.get('KAFKA_METADATA_MAX_AGE_MS', 300000)
        init_retry_interval = current_app.config.get('KAFKA_INIT_RETRY_INTERVAL', 60)
        max_block_ms = current_app.config.get('KAFKA_MAX_BLOCK_MS', 60000)  # 最大阻塞时间60秒
        delivery_timeout_ms = current_app.config.get('KAFKA_DELIVERY_TIMEOUT_MS', 120000)  # 消息传递超时120秒
    except RuntimeError:
        # 不在Flask应用上下文中，使用环境变量作为后备
        import os
        bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        request_timeout_ms = int(os.getenv('KAFKA_REQUEST_TIMEOUT_MS', '30000'))  # 增加到30秒
        retries = int(os.getenv('KAFKA_RETRIES', '3'))  # 增加到3次
        retry_backoff_ms = int(os.getenv('KAFKA_RETRY_BACKOFF_MS', '1000'))  # 增加到1秒
        metadata_max_age_ms = int(os.getenv('KAFKA_METADATA_MAX_AGE_MS', '300000'))
        init_retry_interval = int(os.getenv('KAFKA_INIT_RETRY_INTERVAL', '60'))
        max_block_ms = int(os.getenv('KAFKA_MAX_BLOCK_MS', '60000'))
        delivery_timeout_ms = int(os.getenv('KAFKA_DELIVERY_TIMEOUT_MS', '120000'))
    
    # 重要：VIDEO服务使用 host 网络模式，必须使用 localhost 访问 Kafka
    # 如果配置中包含容器名（Kafka 或 kafka-server），强制使用 localhost
    # 这样可以避免在 host 网络模式下尝试解析容器名导致的连接失败
    original_bootstrap_servers = bootstrap_servers
    if 'Kafka' in bootstrap_servers or 'kafka-server' in bootstrap_servers:
        logger.warning(f'⚠️  检测到 Kafka 配置使用容器名 "{bootstrap_servers}"，强制覆盖为 localhost:9092（VIDEO服务使用 host 网络模式）')
        bootstrap_servers = 'localhost:9092'
    
    # 记录最终使用的 bootstrap_servers（用于调试）
    logger.debug(f'Kafka bootstrap_servers: {bootstrap_servers} (原始值: {original_bootstrap_servers})')
    
    # 如果已经初始化成功，检查连接健康状态
    if _producer is not None:
        try:
            # 尝试获取元数据来检查连接是否健康
            # 注意：某些版本的 kafka-python 可能没有 list_topics 方法
            # 使用更通用的方法检查连接
            if hasattr(_producer, 'list_topics'):
                _producer.list_topics(timeout=1)
            else:
                # 如果没有 list_topics 方法，尝试发送一个空的 Future 来检查连接
                # 或者直接返回，让后续的 send 操作来验证连接
                pass
            return _producer
        except Exception as e:
            # 连接已断开，重置生产者
            logger.warning(f"Kafka生产者连接已断开，将重新初始化: {str(e)}")
            try:
                _producer.close(timeout=1)
            except:
                pass
            _producer = None
    
    # 如果之前初始化失败，且距离上次尝试时间不足，不再重试
    current_time = time.time()
    if _producer_init_failed and (current_time - _last_init_attempt_time) < init_retry_interval:
        return None
    
    # 尝试初始化
    try:
        # 确保 bootstrap_servers 是列表格式
        bootstrap_servers_list = bootstrap_servers.split(',') if isinstance(bootstrap_servers, str) else bootstrap_servers
        # 再次检查并清理，确保不包含容器名
        bootstrap_servers_list = [s.strip() for s in bootstrap_servers_list if s.strip() and 'Kafka' not in s and 'kafka-server' not in s]
        if not bootstrap_servers_list:
            bootstrap_servers_list = ['localhost:9092']
        
        logger.info(f"正在初始化 Kafka 生产者: bootstrap_servers={bootstrap_servers_list}")
        
        _producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers_list,
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            # 连接超时和重试配置
            request_timeout_ms=request_timeout_ms,
            connections_max_idle_ms=300000,  # 连接最大空闲时间5分钟
            retries=retries,
            retry_backoff_ms=retry_backoff_ms,
            # 减少元数据刷新频率，避免频繁连接
            metadata_max_age_ms=metadata_max_age_ms,
            # 最大阻塞时间（用于send等操作）
            max_block_ms=max_block_ms,
            # 消息传递超时
            delivery_timeout_ms=delivery_timeout_ms,
            # 指定API版本，避免版本探测（使用 (2, 5) 而不是 (2, 5, 0)）
            api_version=(2, 5),
            # 启用幂等性，确保消息不重复
            enable_idempotence=True,
            # 批量发送配置（提高性能）
            batch_size=16384,  # 16KB
            linger_ms=10,  # 等待10ms以批量发送
            # 客户端ID，便于在日志中识别
            client_id='video-alert-producer',
        )
        # KafkaProducer在创建时会自动尝试连接
        # 如果连接失败，构造函数会抛出异常，这会被外层的try-except捕获
        # 这里我们只需要记录成功日志
        logger.info(f"✅ Kafka生产者初始化成功: bootstrap_servers={bootstrap_servers_list}, "
                   f"request_timeout_ms={request_timeout_ms}, retries={retries}, "
                   f"retry_backoff_ms={retry_backoff_ms}")
        _producer_init_failed = False
    except Exception as e:
        _producer = None
        _producer_init_failed = True
        _last_init_attempt_time = current_time
        # 记录详细错误信息，包括 bootstrap_servers 的值
        error_msg = str(e)
        logger.error(f"❌ Kafka生产者初始化失败: bootstrap_servers={bootstrap_servers}, error={error_msg}")
        # 如果错误信息中包含 'Kafka:9092'，说明 broker 返回了容器名，需要检查 Kafka broker 配置
        if 'Kafka:9092' in error_msg or 'Kafka' in error_msg:
            logger.error(f"⚠️  检测到错误信息中包含容器名 'Kafka'，这通常是因为 Kafka broker 的 "
                        f"KAFKA_ADVERTISED_LISTENERS 配置问题。请确保 Kafka broker 的配置包含 "
                        f"PLAINTEXT://localhost:9092")
        # 只记录警告，不抛出异常，避免影响主功能
        logger.warning(f"Kafka生产者初始化失败，将在 {init_retry_interval} 秒后重试")
        return None
    
    return _producer


def _query_alert_notification_config(device_id: str, task_type: str = None) -> Optional[Dict]:
    """
    查询设备的告警通知配置
    
    Args:
        device_id: 设备ID
        task_type: 任务类型（'realtime' 或 'snap'/'snapshot'），用于区分实时算法任务和抓拍算法任务
    
    Returns:
        dict: 告警通知配置，包含以下字段：
            - notify_users: 通知人列表（JSON格式）
            - notify_methods: 通知方式（逗号分隔，支持：sms,email,wxcp,http,ding,feishu）
            - alert_notification_config: 告警通知配置（JSON格式，包含channels和notify_users）
        如果未找到配置或未开启告警，返回None
    """
    try:
        from models import SnapTask, AlgorithmTask, Device
        
        # 统一task_type格式（snapshot -> snap）
        if task_type == 'snapshot':
            task_type = 'snap'
        
        # 注意：抓拍算法任务（task_type='snap'）应该使用 AlgorithmTask 表，而不是 SnapTask 表
        # SnapTask 是旧的抓拍任务表，新的抓拍算法任务统一使用 AlgorithmTask 表（task_type='snap'）
        # 因此，当 task_type='snap' 时，跳过 SnapTask 表的查询，直接查询 AlgorithmTask 表
        
        # 先查询 SnapTask（抓拍任务）- 仅当task_type为None时查询（兼容旧系统）
        if task_type is None:
            snap_tasks = SnapTask.query.filter(
                SnapTask.device_id == device_id,
                SnapTask.alarm_enabled == True,
                SnapTask.is_enabled == True
            ).all()
            logger.debug(f"查询SnapTask: device_id={device_id}, task_type={task_type}, 找到{len(snap_tasks)}个任务")
            
            # 如果找到开启告警的抓拍任务，使用第一个任务的配置
            if snap_tasks:
                task = snap_tasks[0]
                logger.info(f"📋 找到SnapTask配置: device_id={device_id}, task_id={task.id}, task_name={task.task_name}, "
                          f"notify_users={task.notify_users is not None}, notify_methods={task.notify_methods}")
                
                # 检查抑制时间
                if task.last_notify_time:
                    suppress_seconds = task.alarm_suppress_time or 300
                    time_since_last_notify = (datetime.utcnow() - task.last_notify_time).total_seconds()
                    if time_since_last_notify < suppress_seconds:
                        logger.debug(f"告警通知在抑制时间内，跳过发送: device_id={device_id}, "
                                   f"time_since_last_notify={time_since_last_notify:.0f}秒")
                        return None
                
                # 组装通知配置
                config = {
                    'task_id': task.id,
                    'task_name': task.task_name,
                    'notify_users': task.notify_users,
                    'notify_methods': task.notify_methods,
                    'alarm_suppress_time': task.alarm_suppress_time
                }
                logger.info(f"📋 SnapTask通知配置详情: device_id={device_id}, task_id={task.id}, "
                          f"notify_users类型={type(task.notify_users).__name__}, "
                          f"notify_methods={task.notify_methods}, "
                          f"notify_users长度={len(json.loads(task.notify_users)) if task.notify_users and isinstance(task.notify_users, str) else (len(task.notify_users) if isinstance(task.notify_users, list) else 0)}")
                
                # 更新最后通知时间
                try:
                    task.last_notify_time = datetime.utcnow()
                    db.session.commit()
                except Exception as e:
                    logger.warning(f"更新最后通知时间失败: {str(e)}")
                    db.session.rollback()
                
                return config
        
        # 查询 AlgorithmTask（算法任务）- 通过多对多关系，使用any()方法更标准
        filter_conditions = [
            AlgorithmTask.devices.any(Device.id == device_id),
            AlgorithmTask.alert_event_enabled == True,
            AlgorithmTask.alert_notification_enabled == True,
            AlgorithmTask.is_enabled == True
        ]
        
        # 如果指定了task_type，添加过滤条件
        if task_type:
            filter_conditions.append(AlgorithmTask.task_type == task_type)
            logger.debug(f"查询AlgorithmTask: device_id={device_id}, task_type={task_type}")
        else:
            logger.debug(f"查询AlgorithmTask: device_id={device_id}, task_type=所有类型")
        
        algorithm_tasks = AlgorithmTask.query.filter(*filter_conditions).all()
        
        logger.info(f"🔍 查询AlgorithmTask结果: device_id={device_id}, task_type={task_type}, 找到{len(algorithm_tasks)}个任务")
        
        # 如果找到开启告警事件和告警通知的算法任务，检查是否有通知配置
        if algorithm_tasks:
            task = algorithm_tasks[0]
            logger.info(f"📋 找到AlgorithmTask配置: device_id={device_id}, task_id={task.id}, task_name={task.task_name}, task_type={task.task_type}, "
                      f"alert_event_enabled={task.alert_event_enabled}, alert_notification_enabled={task.alert_notification_enabled}, "
                      f"is_enabled={task.is_enabled}, alert_notification_config={task.alert_notification_config is not None}")
            
            # 检查是否有通知配置
            if not task.alert_notification_config:
                logger.warning(f"⚠️  找到开启告警事件和告警通知的算法任务，但未配置通知渠道和模板: device_id={device_id}, task_id={task.id}, task_name={task.task_name}, task_type={task.task_type}")
                return None
            
            # 检查抑制时间
            if task.last_notify_time:
                suppress_seconds = task.alarm_suppress_time or 300
                time_since_last_notify = (datetime.utcnow() - task.last_notify_time).total_seconds()
                if time_since_last_notify < suppress_seconds:
                    logger.debug(f"告警通知在抑制时间内，跳过发送: device_id={device_id}, "
                               f"time_since_last_notify={time_since_last_notify:.0f}秒")
                    return None
            
            # 解析通知配置
            notification_config_data = None
            notify_users_from_config = None
            if task.alert_notification_config:
                try:
                    notification_config_data = json.loads(task.alert_notification_config) if isinstance(task.alert_notification_config, str) else task.alert_notification_config
                    logger.debug(f"解析alert_notification_config成功: device_id={device_id}, task_id={task.id}, config_keys={list(notification_config_data.keys()) if isinstance(notification_config_data, dict) else 'not_dict'}")
                    
                    # 从配置中提取通知人信息（如果已保存）
                    if isinstance(notification_config_data, dict):
                        notify_users_from_config = notification_config_data.get('notify_users')
                        channels = notification_config_data.get('channels', [])
                        logger.info(f"📊 从alert_notification_config提取: device_id={device_id}, task_id={task.id}, "
                                  f"channels数量={len(channels) if isinstance(channels, list) else 0}, "
                                  f"notify_users数量={len(notify_users_from_config) if isinstance(notify_users_from_config, list) else 0}")
                        if notify_users_from_config:
                            logger.debug(f"从alert_notification_config中获取到通知人: {len(notify_users_from_config)}个")
                except Exception as e:
                    logger.error(f"❌ 解析告警通知配置失败: device_id={device_id}, task_id={task.id}, error={str(e)}, config={task.alert_notification_config[:200] if task.alert_notification_config else None}")
            
            # 组装通知配置
            config = {
                'task_id': task.id,
                'task_name': task.task_name,
                'alert_notification_config': notification_config_data,
                'notify_users': notify_users_from_config,  # 添加通知人信息
                'alarm_suppress_time': task.alarm_suppress_time
            }
            
            # 更新最后通知时间
            try:
                task.last_notify_time = datetime.utcnow()
                db.session.commit()
            except Exception as e:
                logger.warning(f"更新最后通知时间失败: {str(e)}")
                db.session.rollback()
            
            return config
        
        return None
        
    except Exception as e:
        logger.error(f"查询告警通知配置失败: device_id={device_id}, error={str(e)}", exc_info=True)
        return None


def _get_notify_users_from_message_templates(channels: list) -> list:
    """
    从消息模板中获取通知人信息
    
    注意：告警通知配置中的template_id是消息模板（TMsgMail、TMsgSms等）的ID。
    消息模板中包含userGroupId字段，通知人信息应该从用户组中获取。
    
    实现方式：通过HTTP API调用消息服务来获取消息模板的详细信息，然后从用户组中获取通知人信息。
    
    Args:
        channels: 通知渠道列表，格式：[{"method": "sms", "template_id": "xxx", "template_name": "xxx"}, ...]
    
    Returns:
        list: 通知人列表，格式：[{"phone": "xxx"}, {"email": "xxx"}, ...]
    """
    notify_users = []
    if not channels:
        return notify_users
    
    try:
        import os
        import requests
        
        # 获取消息服务API地址（从环境变量或配置中获取）
        try:
            message_service_url = current_app.config.get('MESSAGE_SERVICE_URL', 'http://localhost:48080')
        except RuntimeError:
            message_service_url = os.getenv('MESSAGE_SERVICE_URL', 'http://localhost:48080')
        
        # 消息类型映射
        method_to_msg_type = {
            'sms': 1,  # 短信（阿里云/腾讯云）
            'email': 3,  # 邮件
            'mail': 3,  # 邮件（别名）
            'wxcp': 4,  # 企业微信
            'wechat': 4,  # 企业微信（别名）
            'weixin': 4,  # 企业微信（别名）
            'http': 5,  # HTTP
            'webhook': 5,  # HTTP（别名）
            'ding': 6,  # 钉钉
            'dingtalk': 6,  # 钉钉（别名）
            'feishu': 7,  # 飞书
            'lark': 7,  # 飞书（别名）
        }
        
        # 遍历所有渠道，收集通知人信息
        all_notify_users = {}  # 使用字典去重，key为phone或email
        
        for channel in channels:
            method = channel.get('method', '').lower()
            template_id = channel.get('template_id')
            
            if not template_id:
                continue
            
            msg_type = method_to_msg_type.get(method)
            if not msg_type:
                logger.warning(f"不支持的通知方式: {method}")
                continue
            
            try:
                # 调用消息服务API获取模板详情
                # 注意：这里需要根据实际的消息服务API接口调整
                # 由于消息服务可能没有直接提供获取模板详情的公开API，这里采用简化方案
                # 实际应该调用：/api/message/template/get?id={template_id}
                # 或者通过消息服务的内部API获取模板信息
                
                # 简化实现：尝试从消息服务获取模板信息
                # 如果消息服务提供了相关API，可以在这里调用
                # 否则，返回空列表，依赖配置时存储的通知人信息
                
                logger.debug(f"尝试从消息模板获取通知人: method={method}, template_id={template_id}, msg_type={msg_type}")
                
                # 注意：由于消息服务的API可能不可用或需要认证，这里暂时跳过
                # 实际部署时，如果消息服务提供了相关API，可以在这里实现
                # 当前建议：在配置告警通知时，从消息模板中提取通知人信息并存储
                
            except Exception as e:
                logger.warning(f"从消息模板获取通知人失败: method={method}, template_id={template_id}, error={str(e)}")
                continue
        
        # 将字典转换为列表
        notify_users = list(all_notify_users.values())
        
        if not notify_users:
            logger.warning(f"从消息模板获取通知人失败，返回空列表: channels={channels}")
            logger.warning(f"建议：在配置告警通知时，从消息模板中提取通知人信息并存储在alert_notification_config中")
        
    except Exception as e:
        logger.error(f"从消息模板获取通知人异常: {str(e)}", exc_info=True)
    
    return notify_users






def process_alert_hook(alert_data: Dict) -> Dict:
    """
    处理告警Hook请求：仅发送到Kafka（Java端统一处理消息，包括区域比对、布防时段判断、存储到数据库）
    
    Args:
        alert_data: 告警数据字典，包含以下字段：
            - object: 对象类型（必填）
            - event: 事件类型（必填）
            - device_id: 设备ID（必填）
            - device_name: 设备名称（必填）
            - region: 区域（可选）
            - information: 详细信息，可以是字符串或字典（可选）
            - time: 报警时间，格式：'YYYY-MM-DD HH:MM:SS'（可选，默认当前时间）
            - image_path: 图片路径（可选，不直接传输图片，而是传输图片所在磁盘路径）
            - record_path: 录像路径（可选）
    
    Returns:
        dict: 发送到Kafka的消息字典
    """
    global _producer, _last_kafka_unavailable_warning_time, _kafka_unavailable_warning_interval
    try:
        # 查询告警通知配置
        device_id = alert_data.get('device_id')
        task_type = alert_data.get('task_type', 'realtime')  # 默认为实时算法任务
        # 统一task_type格式（snapshot -> snap）
        if task_type == 'snapshot':
            task_type = 'snap'
        
        notification_config = None
        if device_id:
            logger.info(f"🔍 查询告警通知配置: device_id={device_id}, task_type={task_type}")
            notification_config = _query_alert_notification_config(device_id, task_type)
            if notification_config:
                logger.info(f"✅ 找到告警通知配置: device_id={device_id}, task_id={notification_config.get('task_id')}, "
                          f"task_name={notification_config.get('task_name')}, "
                          f"notify_users={notification_config.get('notify_users') is not None}, "
                          f"notify_methods={notification_config.get('notify_methods')}")
            else:
                logger.warning(f"⚠️  未找到告警通知配置: device_id={device_id}, task_type={task_type}。"
                             f"请检查：1) SnapTask或AlgorithmTask是否存在 2) alarm_enabled是否为True "
                             f"3) is_enabled是否为True 4) 设备ID是否匹配")
        
        # 构建告警消息（直接发送原始告警数据，Java端会处理）
        # 如果开启了告警通知，发送到Kafka
        if notification_config:
            logger.info(f"📨 找到通知配置，开始处理告警通知: device_id={device_id}, "
                       f"task_id={notification_config.get('task_id')}, "
                       f"task_name={notification_config.get('task_name')}")
            
            producer = get_kafka_producer()
            if producer is not None:
                try:
                    # 构建通知消息（使用原始alert_data，不依赖数据库记录）
                    notification_message = _build_notification_message_for_kafka(alert_data, notification_config)
                    
                    # 如果通知消息为None，说明通知人列表为空，跳过发送
                    if notification_message is None:
                        logger.warning(f"⚠️  告警通知消息构建失败（通知人列表为空），跳过发送: device_id={device_id}")
                        return {'status': 'skipped', 'reason': 'no_notify_users'}
                    
                    # 从Flask配置中获取Kafka主题（根据任务类型选择不同的topic）
                    task_type = alert_data.get('task_type', 'realtime')  # 默认为实时算法任务
                    # 兼容 'snapshot' 值，统一转换为 'snap'
                    if task_type == 'snapshot':
                        task_type = 'snap'
                    try:
                        if task_type == 'snap':
                            # 抓拍算法任务使用单独的topic
                            kafka_topic = current_app.config.get('KAFKA_SNAPSHOT_ALERT_TOPIC', 'iot-snapshot-alert')
                        else:
                            # 实时算法任务使用原有topic
                            kafka_topic = current_app.config.get('KAFKA_ALERT_NOTIFICATION_TOPIC', 'iot-alert-notification')
                    except RuntimeError:
                        import os
                        if task_type == 'snap':
                            kafka_topic = os.getenv('KAFKA_SNAPSHOT_ALERT_TOPIC', 'iot-snapshot-alert')
                        else:
                            kafka_topic = os.getenv('KAFKA_ALERT_NOTIFICATION_TOPIC', 'iot-alert-notification')
                    
                    # 记录发送信息
                    should_notify = notification_message.get('shouldNotify', False)
                    notify_users_count = len(notification_message.get('notifyUsers', []))
                    logger.info(f"📤 准备发送告警通知消息到Kafka: device_id={device_id}, topic={kafka_topic}, "
                               f"shouldNotify={should_notify}, notifyUsers数量={notify_users_count}, "
                               f"notifyMethods={notification_message.get('notifyMethods')}, "
                               f"channels数量={len(notification_message.get('channels', []))}")
                    
                    # 使用device_id作为key，确保同一设备的告警消息有序
                    future = producer.send(
                        kafka_topic,
                        key=str(device_id),
                        value=notification_message
                    )
                    
                    # 异步发送，等待结果（增加超时时间以提高成功率）
                    try:
                        record_metadata = future.get(timeout=10)  # 增加到10秒，给连接更多时间
                        logger.info(f"✅ 告警通知消息发送到Kafka成功: device_id={device_id}, "
                                   f"topic={record_metadata.topic}, partition={record_metadata.partition}, "
                                   f"offset={record_metadata.offset}, shouldNotify={should_notify}, "
                                   f"notifyUsers数量={notify_users_count}")
                        return {
                            'status': 'success',
                            'topic': record_metadata.topic,
                            'partition': record_metadata.partition,
                            'offset': record_metadata.offset
                        }
                    except Exception as e:
                        # 发送失败，但不影响主流程，只记录警告
                        logger.error(f"❌ 告警通知消息发送到Kafka失败: device_id={device_id}, error={str(e)}")
                        # 如果连接失败，重置生产者，下次重新初始化
                        if isinstance(e, (KafkaError, ConnectionError, TimeoutError)) or 'socket disconnected' in str(e).lower():
                            try:
                                _producer.close(timeout=1)
                            except:
                                pass
                            _producer = None
                            logger.info(f"已重置Kafka生产者，将在下次发送时重新初始化")
                        return {'status': 'failed', 'error': str(e)}
                except Exception as e:
                    # 发送异常，但不影响主流程
                    logger.error(f"❌ 发送告警通知消息到Kafka异常: device_id={device_id}, error={str(e)}", exc_info=True)
                    # 如果连接失败，重置生产者
                    if isinstance(e, (KafkaError, ConnectionError, TimeoutError)) or 'socket disconnected' in str(e).lower():
                        try:
                            _producer.close(timeout=1)
                        except:
                            pass
                        _producer = None
                        logger.info(f"已重置Kafka生产者，将在下次发送时重新初始化")
                        return {'status': 'failed', 'error': str(e)}
            else:
                # 警告抑制：避免日志刷屏，每5分钟最多输出一次警告
                current_time = time.time()
                if (current_time - _last_kafka_unavailable_warning_time) >= _kafka_unavailable_warning_interval:
                    logger.warning(f"⚠️  Kafka不可用，跳过告警消息发送: device_id={device_id}（将在 {_kafka_unavailable_warning_interval} 秒后再次提醒）")
                    _last_kafka_unavailable_warning_time = current_time
                else:
                    logger.debug(f"Kafka不可用，跳过告警消息发送: device_id={device_id}")
                return {'status': 'failed', 'error': 'Kafka不可用'}
        else:
            # 没有通知配置，也发送到Kafka（Java端可能需要处理），但标记为不需要通知
            logger.info(f"ℹ️  未找到通知配置，发送告警消息（不包含通知信息）: device_id={device_id}, task_type={task_type}")
            
            producer = get_kafka_producer()
            if producer is not None:
                try:
                    # 构建简单的告警消息（不包含通知配置，但标记为不需要通知）
                    simple_message = {
                        'deviceId': alert_data.get('device_id'),
                        'deviceName': alert_data.get('device_name'),
                        'alert': {
                            'object': alert_data.get('object'),
                            'event': alert_data.get('event'),
                            'region': alert_data.get('region'),
                            'information': alert_data.get('information'),
                            'imagePath': alert_data.get('image_path'),
                            'recordPath': alert_data.get('record_path'),
                            'time': alert_data.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                            'taskType': alert_data.get('task_type', 'realtime')
                        },
                        'notifyUsers': None,  # 明确标记为null
                        'notifyMethods': None,  # 明确标记为null
                        'channels': None,  # 明确标记为null
                        'shouldNotify': False,  # 明确标记为不需要通知
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # 从Flask配置中获取Kafka主题（根据任务类型选择不同的topic）
                    task_type = alert_data.get('task_type', 'realtime')  # 默认为实时算法任务
                    # 兼容 'snapshot' 值，统一转换为 'snap'
                    if task_type == 'snapshot':
                        task_type = 'snap'
                    try:
                        if task_type == 'snap':
                            # 抓拍算法任务使用单独的topic
                            kafka_topic = current_app.config.get('KAFKA_SNAPSHOT_ALERT_TOPIC', 'iot-snapshot-alert')
                        else:
                            # 实时算法任务使用原有topic
                            kafka_topic = current_app.config.get('KAFKA_ALERT_NOTIFICATION_TOPIC', 'iot-alert-notification')
                    except RuntimeError:
                        import os
                        if task_type == 'snap':
                            kafka_topic = os.getenv('KAFKA_SNAPSHOT_ALERT_TOPIC', 'iot-snapshot-alert')
                        else:
                            kafka_topic = os.getenv('KAFKA_ALERT_NOTIFICATION_TOPIC', 'iot-alert-notification')
                    
                    logger.info(f"📤 准备发送告警消息（无通知配置）到Kafka: device_id={device_id}, topic={kafka_topic}, shouldNotify=False")
                    
                    # 使用device_id作为key，确保同一设备的告警消息有序
                    future = producer.send(
                        kafka_topic,
                        key=str(device_id),
                        value=simple_message
                    )
                    
                    # 异步发送，等待结果（增加超时时间以提高成功率）
                    try:
                        record_metadata = future.get(timeout=10)  # 增加到10秒
                        logger.info(f"✅ 告警消息发送到Kafka成功（无通知配置）: device_id={device_id}, "
                                   f"topic={record_metadata.topic}, partition={record_metadata.partition}, "
                                   f"offset={record_metadata.offset}, shouldNotify=False")
                        return {
                            'status': 'success',
                            'topic': record_metadata.topic,
                            'partition': record_metadata.partition,
                            'offset': record_metadata.offset
                        }
                    except Exception as e:
                        logger.error(f"❌ 告警消息发送到Kafka失败: device_id={device_id}, error={str(e)}")
                        if isinstance(e, (KafkaError, ConnectionError, TimeoutError)) or 'socket disconnected' in str(e).lower():
                            try:
                                _producer.close(timeout=1)
                            except:
                                pass
                            _producer = None
                            logger.info(f"已重置Kafka生产者，将在下次发送时重新初始化")
                        return {'status': 'failed', 'error': str(e)}
                except Exception as e:
                    logger.error(f"❌ 发送告警消息到Kafka异常: device_id={device_id}, error={str(e)}", exc_info=True)
                    if isinstance(e, (KafkaError, ConnectionError, TimeoutError)) or 'socket disconnected' in str(e).lower():
                        try:
                            _producer.close(timeout=1)
                        except:
                            pass
                        _producer = None
                        logger.info(f"已重置Kafka生产者，将在下次发送时重新初始化")
                    return {'status': 'failed', 'error': str(e)}
            else:
                # 警告抑制：避免日志刷屏，每5分钟最多输出一次警告
                current_time = time.time()
                if (current_time - _last_kafka_unavailable_warning_time) >= _kafka_unavailable_warning_interval:
                    logger.warning(f"⚠️  Kafka不可用，跳过告警消息发送: device_id={device_id}（将在 {_kafka_unavailable_warning_interval} 秒后再次提醒）")
                    _last_kafka_unavailable_warning_time = current_time
                else:
                    logger.debug(f"Kafka不可用，跳过告警消息发送: device_id={device_id}")
                return {'status': 'failed', 'error': 'Kafka不可用'}
        
    except Exception as e:
        logger.error(f"处理告警Hook失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"处理告警Hook失败: {str(e)}")


def _build_notification_message_for_kafka(alert_data: Dict, notification_config: Dict) -> Optional[Dict]:
    """
    构建告警通知消息（用于发送到Kafka，不依赖数据库记录）
    
    Args:
        alert_data: 原始告警数据字典
        notification_config: 通知配置字典
    
    Returns:
        dict: 通知消息字典，如果通知人列表为空返回None
    """
    device_id = alert_data.get('device_id')
    task_id = notification_config.get('task_id')
    task_name = notification_config.get('task_name')
    
    logger.info(f"📋 开始构建告警通知消息: device_id={device_id}, task_id={task_id}, task_name={task_name}")
    
    # 从通知配置中提取渠道信息
    alert_notification_config = notification_config.get('alert_notification_config')
    channels = []
    if alert_notification_config and isinstance(alert_notification_config, dict):
        channels = alert_notification_config.get('channels', [])
        logger.debug(f"从alert_notification_config获取channels: {channels}")
    
    # 提取通知方式和模板信息
    notify_methods = [ch.get('method') for ch in channels if ch.get('method')]
    logger.debug(f"提取的通知方式: {notify_methods}")
    
    # 如果channels为空，尝试从notify_methods构建channels（适用于SnapTask，它没有alert_notification_config）
    if not channels:
        notify_methods_raw = notification_config.get('notify_methods')
        if notify_methods_raw:
            # notify_methods可能是字符串（逗号分隔）或列表
            if isinstance(notify_methods_raw, str):
                method_list = [m.strip() for m in notify_methods_raw.split(',') if m.strip()]
            elif isinstance(notify_methods_raw, list):
                method_list = [str(m).strip() for m in notify_methods_raw if m]
            else:
                method_list = []
            
            # 为每个通知方式构建一个简单的channel（没有template_id，适用于SnapTask的旧配置）
            channels = [{'method': method} for method in method_list]
            notify_methods = method_list
            logger.info(f"从notify_methods构建channels: device_id={device_id}, notify_methods={notify_methods_raw}, channels数量={len(channels)}")
    
    # 解析通知人列表（优先使用配置中保存的通知人信息）
    notify_users = []
    notify_users_raw = notification_config.get('notify_users')
    if notify_users_raw:
        try:
            if isinstance(notify_users_raw, str):
                notify_users = json.loads(notify_users_raw)
            elif isinstance(notify_users_raw, list):
                notify_users = notify_users_raw
            logger.debug(f"从notification_config获取通知人: {len(notify_users)}个")
        except Exception as e:
            logger.warning(f"解析通知人列表失败: {str(e)}")
    
    # 如果通知人列表为空，尝试从alert_notification_config中获取（如果配置中已保存）
    if not notify_users:
        alert_notification_config = notification_config.get('alert_notification_config')
        if alert_notification_config and isinstance(alert_notification_config, dict):
            notify_users_from_config = alert_notification_config.get('notify_users')
            if notify_users_from_config:
                try:
                    if isinstance(notify_users_from_config, str):
                        notify_users = json.loads(notify_users_from_config)
                    elif isinstance(notify_users_from_config, list):
                        notify_users = notify_users_from_config
                    logger.debug(f"从alert_notification_config获取通知人: {len(notify_users)}个")
                except Exception as e:
                    logger.warning(f"解析alert_notification_config中的通知人列表失败: {str(e)}")
    
    # 如果通知人列表仍为空，尝试从消息模板中获取（适用于AlgorithmTask，作为后备方案）
    if not notify_users and channels:
        logger.debug(f"通知人列表为空，尝试从消息模板获取: channels={channels}")
        notify_users = _get_notify_users_from_message_templates(channels)
        if notify_users:
            logger.debug(f"从消息模板获取到通知人: {len(notify_users)}个")
    
    # 判断是否需要通知
    # 如果有通知人，并且有通知方式（channels或notify_methods），则需要通知
    # 注意：即使没有channels，只要有notify_users和notify_methods，也应该通知（适用于SnapTask）
    should_notify = bool(notify_users and (channels or notify_methods))
    if notify_users and not should_notify:
        # 如果有通知人但没有通知方式，记录警告
        logger.warning(f"⚠️  有通知人但没有通知方式: device_id={device_id}, task_id={task_id}, "
                      f"notify_users数量={len(notify_users)}, channels数量={len(channels)}, "
                      f"notify_methods={notify_methods}")
    
    # 记录通知配置信息
    logger.info(f"📊 通知配置信息: device_id={device_id}, task_id={task_id}, "
                f"channels数量={len(channels)}, notify_methods={notify_methods}, "
                f"notify_users数量={len(notify_users)}, shouldNotify={should_notify}")
    
    # 如果通知人列表为空，返回None
    if not notify_users:
        logger.warning(f"⚠️  告警通知消息中没有通知人，跳过发送: device_id={device_id}, "
                     f"task_id={task_id}, task_name={task_name}, "
                     f"channels={channels}, notification_config={notification_config}")
        return None
    
    # 处理告警时间格式
    alert_time = alert_data.get('time')
    if alert_time:
        if isinstance(alert_time, datetime):
            alert_time = alert_time.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(alert_time, str):
            # 如果已经是字符串，尝试格式化
            try:
                dt = datetime.strptime(alert_time, '%Y-%m-%d %H:%M:%S')
                alert_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
    else:
        alert_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 构建通知消息（使用驼峰命名以匹配 Java 端的 AlertNotificationMessage）
    message = {
        'taskId': task_id,  # 驼峰命名
        'taskName': task_name,  # 驼峰命名
        'deviceId': device_id,  # 驼峰命名
        'deviceName': alert_data.get('device_name'),  # 驼峰命名
        'alert': {
            'object': alert_data.get('object'),
            'event': alert_data.get('event'),
            'region': alert_data.get('region'),
            'information': alert_data.get('information'),
            'imagePath': alert_data.get('image_path'),  # 驼峰命名
            'recordPath': alert_data.get('record_path'),  # 驼峰命名
            'time': alert_time,
            'taskType': alert_data.get('task_type', 'realtime')  # 添加task_type字段（驼峰命名）
        },
        'channels': channels,  # 通知渠道和模板配置
        'notifyMethods': notify_methods,  # 通知方式列表（驼峰命名，兼容旧接口）
        'notifyUsers': notify_users,  # 通知人列表（驼峰命名）
        'shouldNotify': should_notify,  # 是否需要发送通知
        'timestamp': datetime.now().isoformat()
    }
    
    logger.info(f"✅ 告警通知消息构建成功: device_id={device_id}, task_id={task_id}, "
                f"shouldNotify={should_notify}, notifyUsers数量={len(notify_users)}, "
                f"notifyMethods={notify_methods}, channels数量={len(channels)}")
    
    return message

