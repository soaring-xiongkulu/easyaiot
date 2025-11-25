"""
告警通知服务（通过Kafka发送）
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from kafka import KafkaProducer
from models import db, SnapTask

logger = logging.getLogger(__name__)

# Kafka配置
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_ALERT_TOPIC = os.getenv('KAFKA_ALERT_TOPIC', 'iot-alert-notification')

_producer = None


def get_kafka_producer():
    """获取Kafka生产者实例（单例）"""
    global _producer
    if _producer is None:
        try:
            _producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            logger.info(f"Kafka生产者初始化成功: {KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Kafka生产者初始化失败: {str(e)}", exc_info=True)
            raise RuntimeError(f"Kafka生产者初始化失败: {str(e)}")
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
        
        # 发送到Kafka
        producer = get_kafka_producer()
        future = producer.send(
            KAFKA_ALERT_TOPIC,
            key=str(task.id),
            value=message
        )
        
        # 等待发送结果（可选，根据需求决定是否同步等待）
        try:
            record_metadata = future.get(timeout=10)
            logger.info(f"告警通知发送成功: task_id={task.id}, topic={record_metadata.topic}, "
                       f"partition={record_metadata.partition}, offset={record_metadata.offset}")
            
            # 更新最后通知时间
            task.last_notify_time = datetime.utcnow()
            db.session.commit()
            
            return True
        except Exception as e:
            logger.error(f"告警通知发送失败: task_id={task.id}, error={str(e)}", exc_info=True)
            return False
        
    except Exception as e:
        logger.error(f"发送告警通知异常: task_id={task.id}, error={str(e)}", exc_info=True)
        return False

