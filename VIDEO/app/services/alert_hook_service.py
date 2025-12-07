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
            AlgorithmTask.alert_event_enabled == True,
            AlgorithmTask.alert_notification_enabled == True,
            AlgorithmTask.is_enabled == True
        ).all()
        
        # 如果找到开启告警事件和告警通知的算法任务，检查是否有通知配置
        if algorithm_tasks:
            task = algorithm_tasks[0]
            # 检查是否有通知配置
            if not task.alert_notification_config:
                logger.debug(f"找到开启告警事件和告警通知的算法任务，但未配置通知渠道和模板: device_id={device_id}")
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
            if task.alert_notification_config:
                try:
                    notification_config_data = json.loads(task.alert_notification_config) if isinstance(task.alert_notification_config, str) else task.alert_notification_config
                except:
                    logger.warning(f"解析告警通知配置失败: {task.alert_notification_config}")
            
            # 组装通知配置
            config = {
                'task_id': task.id,
                'task_name': task.task_name,
                'alert_notification_config': notification_config_data,
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
    
    注意：告警通知使用的是系统通知模板（NotifyTemplate），而不是消息模板（TMsgMail等）。
    系统通知模板不包含通知人信息，通知人信息应该从消息模板中获取。
    但是，由于告警通知使用的是系统通知模板，我们需要通过其他方式获取通知人信息。
    
    Args:
        channels: 通知渠道列表，格式：[{"method": "sms", "template_id": "xxx", "template_name": "xxx"}, ...]
    
    Returns:
        list: 通知人列表，格式：[{"phone": "xxx"}, {"email": "xxx"}, ...]
    """
    notify_users = []
    if not channels:
        return notify_users
    
    # 注意：告警通知使用的是系统通知模板（NotifyTemplate），而不是消息模板（TMsgMail等）。
    # 系统通知模板不包含通知人信息，所以这里暂时返回空列表。
    # 通知人信息应该在配置告警通知时，从消息模板中获取并存储在 alert_notification_config 中。
    # 或者，我们需要通过API调用消息服务来获取消息模板的通知人信息。
    # 但是，由于告警通知使用的是系统通知模板，我们需要知道系统通知模板和消息模板的映射关系。
    logger.debug(f"尝试从消息模板获取通知人，但告警通知使用的是系统通知模板，不包含通知人信息: channels={channels}")
    
    return notify_users




def process_alert_hook(alert_data: Dict) -> Dict:
    """
    处理告警Hook请求：仅发送到Kafka（Java端统一处理消息，包括存储到数据库）
    
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
    global _producer
    try:
        # 查询告警通知配置
        device_id = alert_data.get('device_id')
        notification_config = None
        if device_id:
            notification_config = _query_alert_notification_config(device_id)
        
        # 构建告警消息（直接发送原始告警数据，Java端会处理）
        # 如果开启了告警通知，发送到Kafka
        if notification_config:
            producer = get_kafka_producer()
            if producer is not None:
                try:
                    # 构建通知消息（使用原始alert_data，不依赖数据库记录）
                    notification_message = _build_notification_message_for_kafka(alert_data, notification_config)
                    
                    # 如果通知消息为None，说明通知人列表为空，跳过发送
                    if notification_message is None:
                        logger.warning(f"告警通知消息构建失败（通知人列表为空），跳过发送: device_id={device_id}")
                        return {'status': 'skipped', 'reason': 'no_notify_users'}
                    
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
                        logger.info(f"告警消息发送到Kafka成功: device_id={device_id}, "
                                   f"topic={record_metadata.topic}, partition={record_metadata.partition}, "
                                   f"offset={record_metadata.offset}")
                        return {
                            'status': 'success',
                            'topic': record_metadata.topic,
                            'partition': record_metadata.partition,
                            'offset': record_metadata.offset
                        }
                    except Exception as e:
                        # 发送失败，但不影响主流程，只记录警告
                        logger.warning(f"告警消息发送到Kafka失败: device_id={device_id}, error={str(e)}")
                        # 如果连接失败，重置生产者，下次重新初始化
                        if isinstance(e, (KafkaError, ConnectionError, TimeoutError)):
                            try:
                                _producer.close(timeout=0.5)
                            except:
                                pass
                            _producer = None
                        return {'status': 'failed', 'error': str(e)}
                except Exception as e:
                    # 发送异常，但不影响主流程
                    logger.warning(f"发送告警消息到Kafka异常: {str(e)}")
                    # 如果连接失败，重置生产者
                    if isinstance(e, (KafkaError, ConnectionError, TimeoutError)):
                        try:
                            _producer.close(timeout=0.5)
                        except:
                            pass
                        _producer = None
                    return {'status': 'failed', 'error': str(e)}
            else:
                logger.warning(f"Kafka不可用，跳过告警消息发送: device_id={device_id}")
                return {'status': 'failed', 'error': 'Kafka不可用'}
        else:
            # 没有通知配置，也发送到Kafka（Java端可能需要处理）
            producer = get_kafka_producer()
            if producer is not None:
                try:
                    # 构建简单的告警消息（不包含通知配置）
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
                            'time': alert_data.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        },
                        'timestamp': datetime.now().isoformat()
                    }
                    
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
                        value=simple_message
                    )
                    
                    # 异步发送，不阻塞
                    try:
                        record_metadata = future.get(timeout=2)
                        logger.info(f"告警消息发送到Kafka成功（无通知配置）: device_id={device_id}, "
                                   f"topic={record_metadata.topic}, partition={record_metadata.partition}, "
                                   f"offset={record_metadata.offset}")
                        return {
                            'status': 'success',
                            'topic': record_metadata.topic,
                            'partition': record_metadata.partition,
                            'offset': record_metadata.offset
                        }
                    except Exception as e:
                        logger.warning(f"告警消息发送到Kafka失败: device_id={device_id}, error={str(e)}")
                        if isinstance(e, (KafkaError, ConnectionError, TimeoutError)):
                            try:
                                _producer.close(timeout=0.5)
                            except:
                                pass
                            _producer = None
                        return {'status': 'failed', 'error': str(e)}
                except Exception as e:
                    logger.warning(f"发送告警消息到Kafka异常: {str(e)}")
                    if isinstance(e, (KafkaError, ConnectionError, TimeoutError)):
                        try:
                            _producer.close(timeout=0.5)
                        except:
                            pass
                        _producer = None
                    return {'status': 'failed', 'error': str(e)}
            else:
                logger.warning(f"Kafka不可用，跳过告警消息发送: device_id={device_id}")
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
    # 从通知配置中提取渠道信息
    alert_notification_config = notification_config.get('alert_notification_config')
    channels = []
    if alert_notification_config and isinstance(alert_notification_config, dict):
        channels = alert_notification_config.get('channels', [])
    
    # 提取通知方式和模板信息
    notify_methods = [ch.get('method') for ch in channels if ch.get('method')]
    
    # 解析通知人列表
    notify_users = []
    notify_users_raw = notification_config.get('notify_users')
    if notify_users_raw:
        try:
            if isinstance(notify_users_raw, str):
                notify_users = json.loads(notify_users_raw)
            elif isinstance(notify_users_raw, list):
                notify_users = notify_users_raw
        except Exception as e:
            logger.warning(f"解析通知人列表失败: {str(e)}")
    
    # 如果通知人列表为空，尝试从消息模板中获取（适用于AlgorithmTask）
    if not notify_users and channels:
        notify_users = _get_notify_users_from_message_templates(channels)
    
    # 如果通知人列表仍然为空，返回None
    if not notify_users:
        logger.error(f"告警通知消息中没有通知人，跳过发送: device_id={alert_data.get('device_id')}, "
                     f"task_id={notification_config.get('task_id')}, "
                     f"task_name={notification_config.get('task_name')}, "
                     f"channels={channels}, "
                     f"notification_config={notification_config}")
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
        'taskId': notification_config.get('task_id'),  # 驼峰命名
        'taskName': notification_config.get('task_name'),  # 驼峰命名
        'deviceId': alert_data.get('device_id'),  # 驼峰命名
        'deviceName': alert_data.get('device_name'),  # 驼峰命名
        'alert': {
            'object': alert_data.get('object'),
            'event': alert_data.get('event'),
            'region': alert_data.get('region'),
            'information': alert_data.get('information'),
            'imagePath': alert_data.get('image_path'),  # 驼峰命名
            'recordPath': alert_data.get('record_path'),  # 驼峰命名
            'time': alert_time
        },
        'channels': channels,  # 通知渠道和模板配置
        'notifyMethods': notify_methods,  # 通知方式列表（驼峰命名，兼容旧接口）
        'notifyUsers': notify_users,  # 通知人列表（驼峰命名）
        'timestamp': datetime.now().isoformat()
    }
    
    return message

