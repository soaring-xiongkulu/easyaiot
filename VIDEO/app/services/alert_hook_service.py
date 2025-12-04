"""
告警Hook服务：处理实时分析中的告警信息，存储到数据库并发送到Kafka
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
from models import db, Alert
from app.services.alert_service import create_alert

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
    
    # 如果已经初始化成功，直接返回
    if _producer is not None:
        return _producer
    
    # 如果之前初始化失败，且距离上次尝试时间不足，不再重试
    current_time = time.time()
    if _producer_init_failed and (current_time - _last_init_attempt_time) < init_retry_interval:
        return None
    
    # 尝试初始化
    try:
        _producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers.split(','),
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
            api_version=(2, 5, 0),  # 指定API版本，避免版本探测
        )
        # KafkaProducer在创建时会自动尝试连接
        # 如果连接失败，构造函数会抛出异常，这会被外层的try-except捕获
        # 这里我们只需要记录成功日志
        logger.info(f"Kafka生产者初始化成功: {bootstrap_servers}")
        _producer_init_failed = False
    except Exception as e:
        _producer = None
        _producer_init_failed = True
        _last_init_attempt_time = current_time
        # 只记录警告，不抛出异常，避免影响主功能
        logger.warning(f"Kafka生产者初始化失败: {str(e)}，将在 {init_retry_interval} 秒后重试")
        return None
    
    return _producer


def _query_alert_notification_config(device_id: str) -> Optional[Dict]:
    """
    查询设备的告警通知配置
    
    Args:
        device_id: 设备ID
    
    Returns:
        dict: 告警通知配置，包含以下字段：
            - notify_users: 通知人列表（JSON格式）
            - notify_methods: 通知方式（逗号分隔，支持：sms,email,wxcp,http,ding,feishu）
            - phone_number: 手机号（兼容旧字段）
            - email: 邮箱（兼容旧字段）
            - alarm_type: 告警类型（兼容旧字段）
        如果未找到配置或未开启告警，返回None
    """
    try:
        from models import SnapTask, AlgorithmTask, Device
        
        # 先查询 SnapTask（抓拍任务）
        snap_tasks = SnapTask.query.filter(
            SnapTask.device_id == device_id,
            SnapTask.alarm_enabled == True,
            SnapTask.is_enabled == True
        ).all()
        
        # 如果找到开启告警的抓拍任务，使用第一个任务的配置
        if snap_tasks:
            task = snap_tasks[0]
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
                'phone_number': task.phone_number,  # 兼容旧字段
                'email': task.email,  # 兼容旧字段
                'alarm_type': task.alarm_type,  # 兼容旧字段
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
        
        # 查询 AlgorithmTask（算法任务）- 通过多对多关系
        algorithm_tasks = AlgorithmTask.query.join(
            AlgorithmTask.devices
        ).filter(
            Device.id == device_id,
            AlgorithmTask.alert_hook_enabled == True,
            AlgorithmTask.is_enabled == True
        ).all()
        
        # 如果找到开启告警Hook的算法任务，检查是否有通知配置
        if algorithm_tasks:
            task = algorithm_tasks[0]
            # 检查是否有通知配置
            if not task.notify_users and not task.notify_methods:
                logger.debug(f"找到开启告警Hook的算法任务，但未配置通知: device_id={device_id}")
                return None
            
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


def _build_notification_message(alert_record: Dict, alert_data: Dict, notification_config: Dict) -> Dict:
    """
    构建告警通知消息
    
    Args:
        alert_record: 告警记录字典
        alert_data: 原始告警数据字典
        notification_config: 通知配置字典
    
    Returns:
        dict: 通知消息字典
    """
    # 解析通知人列表
    notify_users = []
    if notification_config.get('notify_users'):
        try:
            notify_users = json.loads(notification_config['notify_users']) if isinstance(notification_config['notify_users'], str) else notification_config['notify_users']
        except:
            logger.warning(f"解析通知人列表失败: {notification_config.get('notify_users')}")
    
    # 解析通知方式
    notify_methods = []
    if notification_config.get('notify_methods'):
        notify_methods = [m.strip() for m in notification_config['notify_methods'].split(',') if m.strip()]
    
    # 兼容旧字段：如果没有配置通知人和通知方式，使用旧的phone_number和email
    if not notify_users and not notify_methods:
        alarm_type = notification_config.get('alarm_type', 0)
        if alarm_type == 0 or alarm_type == 2:  # 短信告警或短信+邮箱
            if notification_config.get('phone_number'):
                notify_methods.append('sms')
                notify_users.extend([{'phone': phone.strip()} for phone in notification_config['phone_number'].split(',')])
        if alarm_type == 1 or alarm_type == 2:  # 邮箱告警或短信+邮箱
            if notification_config.get('email'):
                notify_methods.append('email')
                notify_users.extend([{'email': email.strip()} for email in notification_config['email'].split(',')])
    
    # 构建通知消息
    message = {
        'alert_id': alert_record.get('id'),
        'task_id': notification_config.get('task_id'),
        'task_name': notification_config.get('task_name'),
        'device_id': alert_data.get('device_id'),
        'device_name': alert_data.get('device_name'),
        'alert': {
            'object': alert_data.get('object'),
            'event': alert_data.get('event'),
            'region': alert_data.get('region'),
            'information': alert_data.get('information'),
            'image_path': alert_data.get('image_path'),
            'record_path': alert_data.get('record_path'),
            'time': alert_record.get('time')
        },
        'notify_users': notify_users,
        'notify_methods': notify_methods,
        'timestamp': datetime.now().isoformat()
    }
    
    return message


def process_alert_hook(alert_data: Dict) -> Dict:
    """
    处理告警Hook请求：存储到数据库并发送到Kafka
    
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
        dict: 创建的报警记录字典
    """
    global _producer
    try:
        # 先存储到数据库
        alert_record = create_alert(alert_data)
        
        # 查询告警通知配置
        device_id = alert_data.get('device_id')
        notification_config = None
        if device_id:
            notification_config = _query_alert_notification_config(device_id)
        
        # 如果开启了告警通知，发送到Kafka
        if notification_config:
            producer = get_kafka_producer()
            if producer is not None:
                try:
                    # 构建通知消息
                    notification_message = _build_notification_message(alert_record, alert_data, notification_config)
                    
                    # 从Flask配置中获取Kafka主题
                    try:
                        kafka_topic = current_app.config.get('KAFKA_ALERT_NOTIFICATION_TOPIC', 'iot-alert-notification')
                    except RuntimeError:
                        import os
                        kafka_topic = os.getenv('KAFKA_ALERT_NOTIFICATION_TOPIC', 'iot-alert-notification')
                    
                    # 使用device_id作为key，确保同一设备的告警消息有序
                    future = producer.send(
                        kafka_topic,
                        key=str(device_id),
                        value=notification_message
                    )
                    
                    # 异步发送，不阻塞（减少超时时间）
                    try:
                        record_metadata = future.get(timeout=2)  # 减少超时时间到2秒
                        logger.info(f"告警通知消息发送到Kafka成功: alert_id={alert_record.get('id')}, "
                                   f"topic={record_metadata.topic}, partition={record_metadata.partition}, "
                                   f"offset={record_metadata.offset}")
                    except Exception as e:
                        # 发送失败，但不影响主流程，只记录警告
                        logger.warning(f"告警通知消息发送到Kafka失败: alert_id={alert_record.get('id')}, error={str(e)}")
                        # 如果连接失败，重置生产者，下次重新初始化
                        if isinstance(e, (KafkaError, ConnectionError, TimeoutError)):
                            try:
                                _producer.close(timeout=0.5)
                            except:
                                pass
                            _producer = None
                except Exception as e:
                    # 发送异常，但不影响主流程
                    logger.warning(f"发送告警通知消息到Kafka异常: {str(e)}")
                    # 如果连接失败，重置生产者
                    if isinstance(e, (KafkaError, ConnectionError, TimeoutError)):
                        try:
                            _producer.close(timeout=0.5)
                        except:
                            pass
                        _producer = None
            else:
                logger.warning(f"Kafka不可用，跳过告警通知发送: alert_id={alert_record.get('id')}")
        
        return alert_record
        
    except Exception as e:
        logger.error(f"处理告警Hook失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"处理告警Hook失败: {str(e)}")

