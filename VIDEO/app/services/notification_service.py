"""
告警通知服务（通过Kafka发送）
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from flask import current_app
from kafka import KafkaProducer
from kafka.errors import KafkaError
from models import db, SnapTask

logger = logging.getLogger(__name__)

_producer = None
_producer_init_failed = False
_last_init_attempt_time = 0
_init_retry_interval = 60  # 初始化失败后，60秒内不再重试


def get_kafka_producer():
    """获取Kafka生产者实例（单例，带错误处理和重试限制）"""
    global _producer, _producer_init_failed, _last_init_attempt_time
    
    # 从Flask配置中获取Kafka配置
    try:
        bootstrap_servers = current_app.config.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        request_timeout_ms = current_app.config.get('KAFKA_REQUEST_TIMEOUT_MS', 5000)
        retries = current_app.config.get('KAFKA_RETRIES', 1)
        retry_backoff_ms = current_app.config.get('KAFKA_RETRY_BACKOFF_MS', 100)
        metadata_max_age_ms = current_app.config.get('KAFKA_METADATA_MAX_AGE_MS', 300000)
        init_retry_interval = current_app.config.get('KAFKA_INIT_RETRY_INTERVAL', 60)
    except RuntimeError:
        # 不在Flask应用上下文中，使用环境变量作为后备
        import os
        bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        request_timeout_ms = int(os.getenv('KAFKA_REQUEST_TIMEOUT_MS', '5000'))
        retries = int(os.getenv('KAFKA_RETRIES', '1'))
        retry_backoff_ms = int(os.getenv('KAFKA_RETRY_BACKOFF_MS', '100'))
        metadata_max_age_ms = int(os.getenv('KAFKA_METADATA_MAX_AGE_MS', '300000'))
        init_retry_interval = int(os.getenv('KAFKA_INIT_RETRY_INTERVAL', '60'))
    
    # 重要：VIDEO服务使用 host 网络模式，必须使用 localhost 访问 Kafka
    # 如果配置中包含容器名（Kafka 或 kafka-server），强制使用 localhost
    # 这样可以避免在 host 网络模式下尝试解析容器名导致的连接失败
    original_bootstrap_servers = bootstrap_servers
    if 'Kafka' in bootstrap_servers or 'kafka-server' in bootstrap_servers:
        logger.warning(f'⚠️  检测到 Kafka 配置使用容器名 "{bootstrap_servers}"，强制覆盖为 localhost:9092（VIDEO服务使用 host 网络模式）')
        bootstrap_servers = 'localhost:9092'
    
    # 记录最终使用的 bootstrap_servers（用于调试）
    logger.debug(f'Kafka bootstrap_servers: {bootstrap_servers} (原始值: {original_bootstrap_servers})')
    
    # 如果已经初始化成功，直接返回
    if _producer is not None:
        return _producer
    
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
            # 添加连接超时和重试限制
            request_timeout_ms=request_timeout_ms,
            connections_max_idle_ms=300000,  # 连接最大空闲时间5分钟
            retries=retries,
            retry_backoff_ms=retry_backoff_ms,
            # 减少元数据刷新频率，避免频繁连接
            metadata_max_age_ms=metadata_max_age_ms,
            # 连接超时设置
            api_version=(2, 5),  # 指定API版本，避免版本探测（使用 (2, 5) 而不是 (2, 5, 0)）
            # 客户端ID，便于在日志中识别
            client_id='video-notification-producer',
        )
        # KafkaProducer在创建时会自动尝试连接
        # 如果连接失败，构造函数会抛出异常，这会被外层的try-except捕获
        # 这里我们只需要记录成功日志
        logger.info(f"✅ Kafka生产者初始化成功: bootstrap_servers={bootstrap_servers_list}")
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


def should_send_notification(task: SnapTask) -> bool:
    """判断是否应该发送通知（考虑抑制时间）"""
    if not task.alarm_enabled:
        return False
    
    if not task.last_notify_time:
        return True
    
    # 检查是否在抑制时间内
    suppress_seconds = task.alarm_suppress_time or 300
    time_since_last_notify = (datetime.utcnow() - task.last_notify_time).total_seconds()
    
    if time_since_last_notify < suppress_seconds:
        logger.debug(f"任务 {task.id} 在抑制时间内，跳过通知（距离上次通知 {time_since_last_notify:.0f}秒）")
        return False
    
    return True


def send_alert_notification(task: SnapTask, alert_data: Dict) -> bool:
    """发送告警通知到Kafka
    
    Args:
        task: 算法任务对象
        alert_data: 告警数据，包含以下字段：
            - object: 对象类型
            - event: 事件类型
            - device_id: 设备ID
            - device_name: 设备名称
            - region: 区域名称（可选）
            - information: 详细信息（可选）
            - image_path: 图片路径（可选）
            - record_path: 录像路径（可选）
    
    Returns:
        bool: 是否发送成功
    """
    try:
        # 检查是否应该发送通知
        if not should_send_notification(task):
            return False
        
        # 解析通知人列表
        notify_users = []
        if task.notify_users:
            try:
                notify_users = json.loads(task.notify_users) if isinstance(task.notify_users, str) else task.notify_users
            except:
                logger.warning(f"解析通知人列表失败: task_id={task.id}")
        
        # 解析通知方式
        notify_methods = []
        if task.notify_methods:
            notify_methods = [m.strip() for m in task.notify_methods.split(',') if m.strip()]
        
        # 如果没有配置通知人和通知方式，使用旧的phone_number和email
        if not notify_users and not notify_methods:
            if task.phone_number:
                notify_methods.append('sms')
                notify_users.extend([{'phone': phone.strip()} for phone in task.phone_number.split(',')])
            if task.email:
                notify_methods.append('email')
                notify_users.extend([{'email': email.strip()} for email in task.email.split(',')])
        
        # 构建通知消息
        message = {
            'task_id': task.id,
            'task_name': task.task_name,
            'device_id': alert_data.get('device_id'),
            'device_name': alert_data.get('device_name'),
            'alert': {
                'object': alert_data.get('object'),
                'event': alert_data.get('event'),
                'region': alert_data.get('region'),
                'information': alert_data.get('information'),
                'image_path': alert_data.get('image_path'),
                'record_path': alert_data.get('record_path'),
                'time': datetime.utcnow().isoformat()
            },
            'notify_users': notify_users,
            'notify_methods': notify_methods,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # 发送到Kafka（如果可用）
        producer = get_kafka_producer()
        if producer is None:
            logger.warning(f"Kafka不可用，跳过告警通知发送: task_id={task.id}")
            return False
        
        # 从Flask配置中获取Kafka主题
        try:
            kafka_topic = current_app.config.get('KAFKA_ALERT_TOPIC', 'iot-alert-notification')
        except RuntimeError:
            import os
            kafka_topic = os.getenv('KAFKA_ALERT_TOPIC', 'iot-alert-notification')
        
        try:
            future = producer.send(
                kafka_topic,
                key=str(task.id),
                value=message
            )
            
            # 等待发送结果（减少超时时间）
            try:
                record_metadata = future.get(timeout=2)  # 减少超时时间到2秒
                logger.info(f"告警通知发送成功: task_id={task.id}, topic={record_metadata.topic}, "
                           f"partition={record_metadata.partition}, offset={record_metadata.offset}")
                
                # 更新最后通知时间
                task.last_notify_time = datetime.utcnow()
                db.session.commit()
                
                return True
            except Exception as e:
                logger.warning(f"告警通知发送失败: task_id={task.id}, error={str(e)}")
                # 如果连接失败，重置生产者，下次重新初始化
                global _producer
                if isinstance(e, (KafkaError, ConnectionError, TimeoutError)):
                    try:
                        _producer.close(timeout=0.5)
                    except:
                        pass
                    _producer = None
                return False
        except Exception as e:
            logger.warning(f"发送告警通知异常: task_id={task.id}, error={str(e)}")
            # 如果连接失败，重置生产者
            global _producer
            if isinstance(e, (KafkaError, ConnectionError, TimeoutError)):
                try:
                    _producer.close(timeout=0.5)
                except:
                    pass
                _producer = None
            return False
        
    except Exception as e:
        logger.error(f"发送告警通知异常: task_id={task.id}, error={str(e)}", exc_info=True)
        return False

