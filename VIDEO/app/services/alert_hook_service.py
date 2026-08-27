"""
告警Hook服务：处理实时分析中的告警信息，仅发送到Kafka（Java端统一处理消息）
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
import hashlib
import logging
import os
import threading
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

from flask import current_app
from kafka import KafkaProducer
from kafka.errors import KafkaError
from models import db, AlgorithmTask, AlgorithmTaskNotificationState, Device
from app.utils.algorithm_task_identity import (
    AmbiguousAlgorithmTaskError,
    build_alert_suppression_key,
    normalize_algorithm_task_type,
    resolve_alert_event_identity,
    select_unique_legacy_alert_task,
)
from app.utils.service_urls import (
    SHANGHAI_TZ,
    now_shanghai_time_str,
    parse_alert_time_str,
    shanghai_isoformat,
    shanghai_time_str_from_epoch,
)

logger = logging.getLogger(__name__)

# HTTP/Webhook 渠道不依赖 notify_users（URL 在消息模板中）
_USERLESS_NOTIFY_METHODS = frozenset({'http', 'webhook'})

_producer = None
_producer_init_failed = False
_last_init_attempt_time = 0
_init_retry_interval = 60  # 初始化失败后，60秒内不再重试
# 警告抑制：记录上次输出 Kafka 不可用警告的时间，避免日志刷屏
_last_kafka_unavailable_warning_time = 0
_kafka_unavailable_warning_interval = 300  # 每5分钟最多输出一次警告
# 告警事件 Kafka 投递抑制（与算法进程内抑制互补，防止抓拍等路径仍刷 Kafka）
_last_alert_event_kafka_time: Dict[Tuple[str, ...], float] = {}
_alert_event_kafka_lock = threading.Lock()


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
            # 批量发送配置（提高性能，配合 64 分区分散写入）
            batch_size=65536,  # 64KB
            linger_ms=5,  # 等待5ms以批量发送
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


def _kafka_topic_for_alert_task_type(task_type: str) -> str:
    """根据算法任务类型解析 Kafka 告警主题（与下方分发逻辑一致）。"""
    tt = task_type or 'realtime'
    if tt == 'snapshot':
        tt = 'snap'
    try:
        if tt == 'snap':
            return current_app.config.get('KAFKA_SNAPSHOT_ALERT_TOPIC', 'iot-snapshot-alert')
        return current_app.config.get('KAFKA_ALERT_NOTIFICATION_TOPIC', 'iot-alert-notification')
    except RuntimeError:
        import os
        if tt == 'snap':
            return os.getenv('KAFKA_SNAPSHOT_ALERT_TOPIC', 'iot-snapshot-alert')
        return os.getenv('KAFKA_ALERT_NOTIFICATION_TOPIC', 'iot-alert-notification')


def _task_event_config(task) -> Dict:
    """将算法任务转换为告警事件所需的稳定配置。"""
    model_ids = []
    raw_model_ids = getattr(task, 'model_ids', None)
    if raw_model_ids:
        try:
            parsed_model_ids = json.loads(raw_model_ids) if isinstance(raw_model_ids, str) else raw_model_ids
            model_ids = sorted({int(value) for value in (parsed_model_ids or [])})
        except (TypeError, ValueError, json.JSONDecodeError):
            model_ids = []
    return {
        'task_id': task.id,
        'task_name': task.task_name,
        'task_type': task.task_type,
        'face_detection_enabled': bool(task.face_detection_enabled),
        'plate_detection_enabled': bool(task.plate_detection_enabled),
        'face_matching_enabled': bool(getattr(task, 'face_matching_enabled', False)),
        'face_library_ids': AlgorithmTask._parse_library_ids(
            getattr(task, 'face_library_ids', None)
        ),
        'face_matching_threshold': getattr(task, 'face_matching_threshold', None),
        'plate_matching_enabled': bool(getattr(task, 'plate_matching_enabled', False)),
        'plate_library_ids': AlgorithmTask._parse_library_ids(
            getattr(task, 'plate_library_ids', None)
        ),
        'alert_event_suppress_time': task.alert_event_suppress_time,
        'alert_class_names': getattr(task, 'alert_class_names', None),
        'model_ids': model_ids,
    }


def _normalize_event_model_ids(alert_data: Dict) -> set[int]:
    """汇总事件顶层和检测明细中的模型ID。"""
    values = alert_data.get('model_ids') or alert_data.get('modelIds') or []
    if not isinstance(values, (list, tuple, set)):
        values = [values]
    for detection in alert_data.get('detections') or []:
        if isinstance(detection, dict):
            model_id = detection.get('model_id') or detection.get('modelId')
            if model_id is not None:
                values = [*values, model_id]
    normalized = set()
    for value in values:
        try:
            if value is not None and str(value).strip():
                normalized.add(int(value))
        except (TypeError, ValueError):
            continue
    return normalized


def _maybe_dispatch_face_matching_from_alert(alert_data: Dict, task_info: Optional[Dict]) -> None:
    """RUNTIME（C++ 执行器）告警接入人脸链路。

    RUNTIME 告警携带整帧截图（image_path）与检测框（information.detections[].bbox），
    任务启用 face_matching 时：把告警帧送入人脸抓取队列（face_det.onnx 检测→裁剪），
    由队列 Worker 投递匹配（publish_url → Kafka → iot-sink → /matching/process），
    匹配记录经 correlation_id 与告警自动关联，前端人脸弹框/轨迹直接可用。
    """
    if not task_info:
        return
    if not task_info.get('face_matching_enabled'):
        return
    library_ids = task_info.get('face_library_ids') or []
    if not library_ids:
        return

    image_path = (alert_data.get('image_path') or '').strip()
    if not image_path or not os.path.isfile(image_path):
        logger.debug('RUNTIME 人脸匹配跳过：告警图片不存在 image_path=%s', image_path)
        return

    try:
        import cv2
        frame = cv2.imread(image_path)
        if frame is None or frame.size == 0:
            logger.warning('RUNTIME 人脸匹配跳过：告警图片读取失败 %s', image_path)
            return
    except Exception as exc:
        logger.warning('RUNTIME 人脸匹配跳过：图片读取异常 %s: %s', image_path, exc)
        return

    try:
        from app.utils.face_capture_queue_service import enqueue_face_capture
        from app.utils.service_urls import resolve_face_matching_publish_url

        task_id = task_info.get('task_id')
        correlation_id = (
            (alert_data.get('correlation_id') or alert_data.get('correlationId') or '')
            .strip() or None
        )
        ok = enqueue_face_capture(
            frame=frame,
            device_id=(alert_data.get('device_id') or '').strip(),
            device_name=(alert_data.get('device_name') or '').strip() or None,
            frame_number=0,
            task_id=int(task_id) if task_id else 0,
            task_name=task_info.get('task_name') or '',
            task_type='realtime',
            library_ids=library_ids,
            threshold=task_info.get('face_matching_threshold'),
            publish_url=resolve_face_matching_publish_url(),
            correlation_id=correlation_id,
            source_event=task_info.get('task_name') or '',
        )
        if ok:
            logger.info(
                'RUNTIME 告警已投递人脸匹配: device=%s task=%s corr=%s',
                alert_data.get('device_id'),
                task_id,
                correlation_id,
            )
    except Exception as exc:
        logger.warning('RUNTIME 人脸匹配投递异常: %s', exc, exc_info=True)


def _maybe_dispatch_plate_matching_from_alert(alert_data: Dict, task_info: Optional[Dict]) -> None:
    """RUNTIME（C++ 执行器）告警接入车牌链路。

    与 _maybe_dispatch_face_matching_from_alert 对称：任务启用 plate_matching 时，
    把告警整帧截图送入车牌抓取队列（plate_detect+plate_rec 检测→识别→裁剪），
    由队列 Worker 投递匹配（publish_url → Kafka → iot-sink → /matching/process），
    匹配记录经 correlation_id 与告警自动关联，前端车牌弹框/轨迹直接可用。
    """
    if not task_info:
        return
    if not task_info.get('plate_matching_enabled'):
        return
    library_ids = task_info.get('plate_library_ids') or []
    if not library_ids:
        return

    image_path = (alert_data.get('image_path') or '').strip()
    if not image_path or not os.path.isfile(image_path):
        logger.debug('RUNTIME 车牌匹配跳过：告警图片不存在 image_path=%s', image_path)
        return

    try:
        import cv2
        frame = cv2.imread(image_path)
        if frame is None or frame.size == 0:
            logger.warning('RUNTIME 车牌匹配跳过：告警图片读取失败 %s', image_path)
            return
    except Exception as exc:
        logger.warning('RUNTIME 车牌匹配跳过：图片读取异常 %s: %s', image_path, exc)
        return

    try:
        from app.utils.plate_capture_queue_service import enqueue_plate_capture
        from app.utils.service_urls import resolve_plate_matching_publish_url

        task_id = task_info.get('task_id')
        correlation_id = (
            (alert_data.get('correlation_id') or alert_data.get('correlationId') or '')
            .strip() or None
        )
        ok = enqueue_plate_capture(
            frame=frame,
            device_id=(alert_data.get('device_id') or '').strip(),
            device_name=(alert_data.get('device_name') or '').strip() or None,
            frame_number=0,
            task_id=int(task_id) if task_id else 0,
            task_name=task_info.get('task_name') or '',
            task_type='realtime',
            library_ids=library_ids,
            publish_url=resolve_plate_matching_publish_url(),
            correlation_id=correlation_id,
        )
        if ok:
            logger.info(
                'RUNTIME 告警已投递车牌匹配: device=%s task=%s corr=%s',
                alert_data.get('device_id'),
                task_id,
                correlation_id,
            )
    except Exception as exc:
        logger.warning('RUNTIME 车牌匹配投递异常: %s', exc, exc_info=True)


def _process_runtime_feed_only_alert(alert_data: Dict) -> Dict:
    """RUNTIME（C++）MQTT/InferEvent 主告警路径补投的告警：仅做库匹配投递。

    主告警仍按原链路（MQTT → iot-sink）落库；此处只把整帧截图送入人脸/车牌抓取队列，
    匹配记录经 correlation_id 与主告警自动关联，不重复落库/通知/抑制。
    """
    device_id = alert_data.get('device_id')
    task_type = normalize_algorithm_task_type(alert_data.get('task_type'))
    request_task_id = alert_data.get('task_id') or alert_data.get('taskId')
    task_info = None
    if device_id:
        try:
            task_info = _query_alert_event_task(device_id, task_type, request_task_id)
        except (AmbiguousAlgorithmTaskError, ValueError):
            task_info = None
        except Exception:
            task_info = None
    try:
        # 按 RUNTIME 补投标志分别投递：face_feed_only → 仅人脸，plate_feed_only → 仅车牌
        if alert_data.get('face_feed_only'):
            _maybe_dispatch_face_matching_from_alert(alert_data, task_info)
        if alert_data.get('plate_feed_only'):
            _maybe_dispatch_plate_matching_from_alert(alert_data, task_info)
    except Exception as exc:
        logger.warning('RUNTIME 库匹配 feed_only 处理失败: %s', exc, exc_info=True)
    return {'status': 'accepted', 'mode': 'runtime_feed_only'}


def _validate_alert_model_ownership(alert_data: Dict, task_config: Dict) -> Optional[Dict]:
    """校验 v2 告警中的模型均属于指定任务。"""
    try:
        schema_version = int(alert_data.get('schema_version') or alert_data.get('schemaVersion') or 1)
    except (TypeError, ValueError):
        schema_version = 1
    if schema_version < 2:
        return None
    event_model_ids = _normalize_event_model_ids(alert_data)
    if not event_model_ids:
        return {
            'status': 'rejected',
            'reason': 'missing_model_ids',
            'error': 'schema_version=2 告警必须携带 model_ids 或 detections[].model_id',
        }
    task_model_ids = {int(value) for value in (task_config.get('model_ids') or [])}
    foreign_model_ids = sorted(event_model_ids - task_model_ids)
    if foreign_model_ids:
        return {
            'status': 'rejected',
            'reason': 'foreign_model',
            'error': f'模型不属于任务: {foreign_model_ids}',
            'foreign_model_ids': foreign_model_ids,
        }
    return None


def _query_alert_event_task(
        device_id: str,
        task_type: str = None,
        task_id=None,
) -> Optional[Dict]:
    """
    查询设备的告警事件任务配置（仅需 alert_event_enabled，不要求告警通知）。
    """
    if not device_id:
        return None
    try:
        tt = normalize_algorithm_task_type(task_type)

        filter_conditions = [
            AlgorithmTask.devices.any(Device.id == device_id),
            AlgorithmTask.alert_event_enabled == True,
            AlgorithmTask.is_enabled == True,
        ]
        if tt:
            filter_conditions.append(AlgorithmTask.task_type == tt)

        if task_id is not None and str(task_id).strip():
            try:
                normalized_task_id = int(task_id)
            except (TypeError, ValueError) as exc:
                raise ValueError('task_id 必须是正整数') from exc
            if normalized_task_id <= 0:
                raise ValueError('task_id 必须是正整数')
            task = AlgorithmTask.query.filter(
                *filter_conditions,
                AlgorithmTask.id == normalized_task_id,
            ).first()
            return _task_event_config(task) if task else None

        candidates = AlgorithmTask.query.filter(*filter_conditions).order_by(AlgorithmTask.id.asc()).all()
        task = select_unique_legacy_alert_task(candidates, device_id, tt)
        return _task_event_config(task) if task else None
    except (AmbiguousAlgorithmTaskError, ValueError):
        raise
    except Exception as e:
        logger.error(f"查询告警事件任务失败: device_id={device_id}, error={e}", exc_info=True)
        return None


def _normalize_alert_wall_time_str(raw_time) -> str:
    """统一告警时间为东八区墙钟字符串（与 iot-sink parseAlertEventTime 一致）。"""
    if raw_time is None or (isinstance(raw_time, str) and not str(raw_time).strip()):
        return now_shanghai_time_str()
    if isinstance(raw_time, (int, float)):
        return shanghai_time_str_from_epoch(float(raw_time))
    if isinstance(raw_time, datetime):
        if raw_time.tzinfo is None:
            aware = raw_time.replace(tzinfo=SHANGHAI_TZ)
        else:
            aware = raw_time.astimezone(SHANGHAI_TZ)
        return aware.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(raw_time, str):
        parsed, _err = parse_alert_time_str(raw_time)
        if parsed is not None:
            return parsed.strftime('%Y-%m-%d %H:%M:%S')
    return now_shanghai_time_str()


def _shanghai_message_timestamp() -> str:
    return shanghai_isoformat(datetime.now(SHANGHAI_TZ))


def _build_minimal_alert_kafka_message(
        alert_data: Dict,
        detection_switches: Optional[Dict],
        alert_event_task: Optional[Dict] = None,
) -> Dict:
    """
    精简告警 Kafka 消息（无通知人配置时使用）。
    必须与 iot-sink AlertNotificationMessage / Python 驼峰字段一致，否则 sink 无法解析 imagePath、无法上传 MinIO。
    """
    sw = detection_switches or {}
    task_id = (
        alert_event_task.get('task_id')
        if alert_event_task else alert_data.get('task_id') or alert_data.get('taskId')
    )
    task_name = (
        alert_event_task.get('task_name')
        if alert_event_task else alert_data.get('task_name') or alert_data.get('taskName')
    )
    task_type = (
        alert_data.get('task_type')
        or (alert_event_task.get('task_type') if alert_event_task else None)
        or 'realtime'
    )
    message = {
        'deviceId': alert_data.get('device_id'),
        'deviceName': alert_data.get('device_name'),
        'taskId': task_id,
        'taskName': task_name,
        'alert': {
            'object': alert_data.get('object'),
            'event': alert_data.get('event'),
            'region': alert_data.get('region'),
            'information': alert_data.get('information'),
            'imagePath': alert_data.get('image_path'),
            'recordPath': alert_data.get('record_path'),
            'time': _normalize_alert_wall_time_str(alert_data.get('time')),
            'taskType': task_type,
        },
        'notifyUsers': None,
        'notifyMethods': None,
        'channels': None,
        'faceDetectionEnabled': bool(sw.get('face_detection_enabled', False)),
        'plateDetectionEnabled': bool(sw.get('plate_detection_enabled', False)),
        'shouldNotify': False,
        'timestamp': _shanghai_message_timestamp(),
    }
    correlation_id = alert_data.get('correlation_id') or alert_data.get('correlationId')
    if correlation_id:
        message['correlationId'] = correlation_id
    message['schemaVersion'] = alert_data.get('schema_version') or alert_data.get('schemaVersion') or 1
    message['eventId'] = alert_data.get('event_id') or alert_data.get('eventId') or correlation_id
    message['modelIds'] = sorted(_normalize_event_model_ids(alert_data))
    message['detections'] = alert_data.get('detections') or []
    return message


def _is_userless_notify_method(method: str) -> bool:
    return (method or '').lower() in _USERLESS_NOTIFY_METHODS


def _is_userless_channel(channel: dict) -> bool:
    if not channel:
        return False
    if channel.get('userless'):
        return True
    return _is_userless_notify_method(channel.get('method', ''))


def _has_userless_channel(channels: list) -> bool:
    return any(_is_userless_channel(ch) for ch in (channels or []))


def _notification_channel_key(channel: Dict) -> str:
    """生成不依赖渠道列表顺序的稳定抑制键。"""
    normalized = channel if isinstance(channel, dict) else {'method': str(channel or '')}
    method = str(normalized.get('method') or 'unknown').strip().lower()
    canonical = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    digest = hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:32]
    return f'{method}:{digest}'


def _filter_notification_channels(
        task_id: int,
        device_id: str,
        channels: list,
        suppress_seconds: int,
) -> Tuple[list, list]:
    """按任务、设备、渠道过滤仍在通知抑制窗口内的渠道。"""
    if not channels or suppress_seconds <= 0:
        return list(channels or []), []
    channel_by_key = {
        _notification_channel_key(channel): channel
        for channel in channels
        if isinstance(channel, dict)
    }
    states = AlgorithmTaskNotificationState.query.filter(
        AlgorithmTaskNotificationState.task_id == int(task_id),
        AlgorithmTaskNotificationState.device_id == str(device_id),
        AlgorithmTaskNotificationState.channel_key.in_(list(channel_by_key.keys())),
    ).all()
    state_by_key = {state.channel_key: state for state in states}
    now = datetime.utcnow()
    allowed = []
    suppressed = []
    for channel_key, channel in channel_by_key.items():
        state = state_by_key.get(channel_key)
        if (
                state
                and state.last_notify_time
                and (now - state.last_notify_time).total_seconds() < suppress_seconds
        ):
            suppressed.append(channel)
        else:
            allowed.append(channel)
    return allowed, suppressed


def _query_alert_notification_config(
        device_id: str,
        task_type: str = None,
        task_id=None,
) -> Optional[Dict]:
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
                
                # 组装通知配置
                config = {
                    'task_id': task.id,
                    'task_name': task.task_name,
                    'notify_users': task.notify_users,
                    'notify_methods': task.notify_methods,
                    'alarm_suppress_time': task.alarm_suppress_time,
                    # 旧版 SnapTask 不区分人脸/车牌开关，默认都关闭
                    'face_detection_enabled': False,
                    'plate_detection_enabled': False
                }

                # 检查抑制时间
                if task.last_notify_time:
                    suppress_seconds = task.alarm_suppress_time or 300
                    time_since_last_notify = (datetime.utcnow() - task.last_notify_time).total_seconds()
                    if time_since_last_notify < suppress_seconds:
                        logger.debug(
                            f"告警通知在抑制时间内，本轮不发送通知: device_id={device_id}, "
                            f"time_since_last_notify={time_since_last_notify:.0f}秒, "
                            f"suppress_seconds={suppress_seconds}"
                        )
                        config['notification_suppressed'] = True
                        return config
                logger.info(f"📋 SnapTask通知配置详情: device_id={device_id}, task_id={task.id}, "
                          f"notify_users类型={type(task.notify_users).__name__}, "
                          f"notify_methods={task.notify_methods}, "
                          f"notify_users长度={len(json.loads(task.notify_users)) if task.notify_users and isinstance(task.notify_users, str) else (len(task.notify_users) if isinstance(task.notify_users, list) else 0)}")
                
                return config
        
        # 查询 AlgorithmTask（算法任务）- 通过多对多关系，使用any()方法更标准
        filter_conditions = [
            AlgorithmTask.devices.any(Device.id == device_id),
            AlgorithmTask.alert_event_enabled == True,
            AlgorithmTask.alert_notification_enabled == True,
            AlgorithmTask.is_enabled == True
        ]
        if task_id is not None and str(task_id).strip():
            filter_conditions.append(AlgorithmTask.id == int(task_id))
        
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
            
            # 解析通知配置（抑制判断前解析，避免抑制窗口被误报为「未找到配置」）
            notification_config_data = None
            notify_users_from_config = None
            if task.alert_notification_config:
                try:
                    notification_config_data = json.loads(task.alert_notification_config) if isinstance(task.alert_notification_config, str) else task.alert_notification_config
                    logger.debug(f"解析alert_notification_config成功: device_id={device_id}, task_id={task.id}, config_keys={list(notification_config_data.keys()) if isinstance(notification_config_data, dict) else 'not_dict'}")
                    
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

            channels = (
                notification_config_data.get('channels', [])
                if isinstance(notification_config_data, dict)
                else []
            )
            allowed_channels, suppressed_channels = _filter_notification_channels(
                task.id,
                device_id,
                channels,
                int(task.alarm_suppress_time or 0),
            )
            if isinstance(notification_config_data, dict):
                notification_config_data = dict(notification_config_data)
                notification_config_data['channels'] = allowed_channels
            
            # 组装通知配置
            config = {
                'task_id': task.id,
                'task_name': task.task_name,
                'alert_notification_config': notification_config_data,
                'notify_users': notify_users_from_config,
                'alarm_suppress_time': task.alarm_suppress_time,
                'face_detection_enabled': bool(task.face_detection_enabled),
                'plate_detection_enabled': bool(task.plate_detection_enabled),
                'task_type': task.task_type or task_type or 'realtime',
                'notification_suppressed': bool(channels and not allowed_channels),
                'suppressed_channel_count': len(suppressed_channels),
            }
            
            return config
        
        return None
        
    except Exception as e:
        logger.error(f"查询告警通知配置失败: device_id={device_id}, error={str(e)}", exc_info=True)
        return None


def _mark_task_notification_sent(
        notification_config: Dict,
        device_id: str,
        event_id: Optional[str] = None,
        task_type: str = 'realtime',
) -> None:
    """告警通知消息成功投递 Kafka 后更新抑制时间戳（避免查询阶段提前写入导致误抑制）。"""
    task_id = notification_config.get('task_id')
    if not task_id:
        return
    try:
        from models import SnapTask

        resolved_type = notification_config.get('task_type') or task_type
        if resolved_type is None:
            task = SnapTask.query.get(task_id)
        else:
            task = AlgorithmTask.query.get(task_id)
        if not task:
            return
        now = datetime.utcnow()
        task.last_notify_time = now
        if resolved_type is not None:
            channel_config = notification_config.get('alert_notification_config') or {}
            channels = channel_config.get('channels', []) if isinstance(channel_config, dict) else []
            for channel in channels:
                channel_key = _notification_channel_key(channel)
                state = AlgorithmTaskNotificationState.query.filter_by(
                    task_id=int(task_id),
                    device_id=str(device_id),
                    channel_key=channel_key,
                ).first()
                if state is None:
                    state = AlgorithmTaskNotificationState(
                        task_id=int(task_id),
                        device_id=str(device_id),
                        channel_key=channel_key,
                    )
                    db.session.add(state)
                state.last_notify_time = now
                state.last_event_id = str(event_id or '')[:36] or None
                state.updated_at = now
        db.session.commit()
        logger.debug(
            f"已更新告警通知抑制时间: task_id={task_id}, task_type={resolved_type or 'snap'}"
        )
    except Exception as e:
        logger.warning(f"更新最后通知时间失败: task_id={task_id}, error={e}")
        db.session.rollback()


def _resolve_detection_switches_from_alert_data(
        alert_data: Dict,
        notification_config: Optional[Dict] = None,
        alert_event_task: Optional[Dict] = None,
) -> Dict:
    """
    从告警数据中提取人脸/车牌检测开关。
    优先使用 alert_data 透传值，不再额外查询数据库。
    """
    def _to_bool(value, default=False):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in ('1', 'true', 'yes', 'on')
        return default

    face_raw = alert_data.get('face_detection_enabled')
    if face_raw is None:
        face_raw = alert_data.get('faceDetectionEnabled')
    if face_raw is None and notification_config:
        face_raw = notification_config.get('face_detection_enabled')
    if face_raw is None and alert_event_task:
        face_raw = alert_event_task.get('face_detection_enabled')

    plate_raw = alert_data.get('plate_detection_enabled')
    if plate_raw is None:
        plate_raw = alert_data.get('plateDetectionEnabled')
    if plate_raw is None and notification_config:
        plate_raw = notification_config.get('plate_detection_enabled')
    if plate_raw is None and alert_event_task:
        plate_raw = alert_event_task.get('plate_detection_enabled')

    return {
        'face_detection_enabled': _to_bool(face_raw, False),
        'plate_detection_enabled': _to_bool(plate_raw, False),
    }


def _get_notify_users_from_message_templates(channels: list) -> list:
    """告警触发时从消息模板提取通知人（与保存任务时逻辑一致）。"""
    if not channels:
        return []
    try:
        from app.services.algorithm_task_service import _extract_notify_users_from_templates
        notify_users = _extract_notify_users_from_templates(channels)
        if notify_users:
            logger.info(f"✅ 告警触发时从消息模板提取到 {len(notify_users)} 个通知人")
        else:
            logger.warning(
                "⚠️  告警触发时未能从消息模板提取通知人，"
                "请检查模板是否绑定用户分组及 MESSAGE_SERVICE_URL 配置"
            )
        return notify_users
    except Exception as e:
        logger.error(f"从消息模板获取通知人异常: {str(e)}", exc_info=True)
        return []


def _is_robot_fallback_channel(channel: dict) -> bool:
    """判断渠道是否可在无 notify_users 时兜底发送（仅 HTTP/Webhook 与群机器人）。"""
    if not channel or not channel.get('template_id'):
        return False
    method = (channel.get('method') or '').lower()
    if method in ('http', 'webhook'):
        return True
    if method not in ('wxcp', 'wechat', 'weixin', 'ding', 'dingtalk', 'feishu', 'lark'):
        return False
    if channel.get('userless'):
        return True
    try:
        from app.services.algorithm_task_service import _fetch_message_template_meta
        template_meta = _fetch_message_template_meta(method, channel.get('template_id'))
        if template_meta and (
            template_meta.get('radioType') == '群机器人消息'
            or template_meta.get('webHook')
        ):
            return True
    except Exception as e:
        logger.debug(f"查询模板元数据失败，不视为群机器人渠道: method={method}, error={e}")
    return False






def _resolve_alert_event_suppress_seconds(
        device_id: str,
        task_type: str,
        task_id=None,
) -> int:
    """查询设备关联算法任务的告警事件抑制时间（秒）。"""
    if not device_id:
        return 5
    try:
        tt = task_type or 'realtime'
        if tt == 'snapshot':
            tt = 'snap'
        query = AlgorithmTask.query.filter(
            AlgorithmTask.devices.any(Device.id == device_id),
            AlgorithmTask.alert_event_enabled == True,
            AlgorithmTask.is_enabled == True,
        )
        if tt:
            query = query.filter(AlgorithmTask.task_type == tt)
        if task_id is not None and str(task_id).strip():
            query = query.filter(AlgorithmTask.id == int(task_id))
        task = query.order_by(AlgorithmTask.id.asc()).first()
        if task and task.alert_event_suppress_time is not None:
            return max(0, int(task.alert_event_suppress_time))
    except Exception as e:
        logger.warning(f"查询告警事件抑制时间失败: device_id={device_id}, error={e}")
    return 5


def _should_suppress_alert_event_kafka(
        task_id,
        device_id: str,
        task_type: str,
        suppress_seconds: int,
        event_identity: Optional[str] = None,
) -> bool:
    """同一任务、设备及事件在抑制窗口内不再向 Kafka 投递。"""
    if not device_id or suppress_seconds <= 0:
        return False
    key = build_alert_suppression_key(
        task_id,
        device_id,
        task_type,
        event_identity=event_identity,
    )
    now = time.time()
    with _alert_event_kafka_lock:
        last = _last_alert_event_kafka_time.get(key, 0)
        if now - last < suppress_seconds:
            return True
        _last_alert_event_kafka_time[key] = now
    return False


def _should_use_direct_alert_persist() -> bool:
    """mini 形态或未部署 Kafka 消费链时，告警直接写入 VIDEO 库（不经 Kafka/iot-sink）。"""
    import os
    explicit = (os.getenv('ALERT_USE_DIRECT_PERSIST') or '').strip().lower()
    if explicit in ('1', 'true', 'yes', 'on'):
        return True
    if explicit in ('0', 'false', 'no', 'off'):
        return False
    try:
        from app.utils.service_urls import is_mini_deploy_profile
        return is_mini_deploy_profile()
    except Exception:
        return False


def _persist_alert_directly(
    alert_data: Dict,
    alert_event_task: Optional[Dict],
    detection_switches: Optional[Dict] = None,
) -> Dict:
    """将告警直接写入 VIDEO 数据库。

    - mini 形态：不依赖 MinIO，直接使用本地 image_path 作为 image_url。
    - 非 mini 形态：异步上传图片到 MinIO，并回写 image_url。
    """
    from app.services.alert_service import create_alert
    from app.services.alert_consumer_service import upload_image_to_minio
    from models import Alert

    device_id = alert_data.get('device_id')
    task_id = alert_event_task.get('task_id') if alert_event_task else None
    task_name = (alert_event_task.get('task_name') if alert_event_task else None) or alert_data.get('event')

    persist_data = dict(alert_data)
    persist_data['task_id'] = task_id
    persist_data['task_name'] = task_name
    if detection_switches:
        persist_data.setdefault(
            'face_detection_enabled',
            bool(detection_switches.get('face_detection_enabled', False)),
        )
        persist_data.setdefault(
            'plate_detection_enabled',
            bool(detection_switches.get('plate_detection_enabled', False)),
        )

    row = create_alert(persist_data)
    alert_id = row.get('id')
    image_path = alert_data.get('image_path')

    if alert_id and image_path:
        # mini 形态：不启用 MinIO，直接使用本地路径
        is_mini = False
        try:
            from app.utils.service_urls import is_mini_deploy_profile

            is_mini = is_mini_deploy_profile()
        except Exception:
            is_mini = False

        is_edge_local = (os.getenv('RECORDING_STORAGE_MODE') or '').strip().lower() == 'edge_local'
        if is_mini or is_edge_local:
            try:
                from app.utils.service_urls import build_alert_image_api_url

                alert = Alert.query.get(alert_id)
                if alert:
                    edge_asset_id = alert_data.get('_edge_image_asset_id')
                    alert.image_asset_id = edge_asset_id
                    alert.image_url = (
                        f'/video/media/assets/{edge_asset_id}/content'
                        if edge_asset_id else build_alert_image_api_url(image_path)
                    )
                    db.session.commit()
                    logger.info(
                        'mini 形态告警图片使用本地路径: alertId=%s, deviceId=%s, image_url=%s',
                        alert_id,
                        device_id,
                        alert.image_url,
                    )
            except Exception as exc:
                logger.warning('mini 形态更新告警 %s image_url 失败: %s', alert_id, exc, exc_info=True)
                try:
                    db.session.rollback()
                except Exception:
                    pass
        else:
            # 非 mini：保持原有异步 MinIO 上传逻辑
            app = current_app._get_current_object()

            def _upload():
                try:
                    with app.app_context():
                        minio_path = upload_image_to_minio(image_path, alert_id, device_id)
                        if not minio_path:
                            return
                        alert = Alert.query.get(alert_id)
                        if alert:
                            alert.image_url = minio_path
                            db.session.commit()
                            logger.info('告警 %s 图片已上传 MinIO: %s', alert_id, minio_path)
                except Exception as exc:
                    logger.warning('告警 %s 图片上传失败: %s', alert_id, exc)
                    try:
                        with app.app_context():
                            db.session.rollback()
                    except Exception:
                        pass

            threading.Thread(target=_upload, daemon=True, name=f'alert-img-%s' % alert_id).start()

    logger.info(
        '✅ 告警已直接落库(mini): alertId=%s, deviceId=%s, object=%s',
        alert_id,
        device_id,
        alert_data.get('object'),
    )
    return {'status': 'success', 'alert_id': alert_id, 'mode': 'direct_persist'}


def _fallback_persist_on_kafka_failure(
    alert_data: Dict,
    alert_event_task: Optional[Dict],
    detection_switches: Optional[Dict],
    kafka_error: str,
) -> Dict:
    """Kafka 投递失败时尝试直连落库，避免告警丢失。"""
    logger.warning(
        'Kafka 投递失败，尝试告警直连落库: device_id=%s, error=%s',
        alert_data.get('device_id'),
        kafka_error,
    )
    try:
        return _persist_alert_directly(alert_data, alert_event_task, detection_switches)
    except Exception as persist_exc:
        logger.error(
            '告警直连落库失败: device_id=%s, error=%s',
            alert_data.get('device_id'),
            persist_exc,
            exc_info=True,
        )
        return {'status': 'failed', 'error': kafka_error}


def _apply_alert_class_filter(alert_data: Dict, alert_event_task: Optional[Dict]) -> Optional[Dict]:
    """按任务 alert_class_names 过滤 detections；无匹配时返回 skip 结果。"""
    if not alert_event_task:
        return None
    raw_names = alert_event_task.get('alert_class_names')
    if not raw_names:
        return None
    try:
        from app.utils.alert_class_filter import filter_detections_for_alert, parse_alert_class_names
        import json as _json
    except Exception:
        return None

    allowed = parse_alert_class_names(raw_names)
    if not allowed:
        return None

    info = alert_data.get('information')
    if isinstance(info, str):
        try:
            info = _json.loads(info)
        except Exception:
            info = None
    if not isinstance(info, dict):
        return None
    detections = info.get('detections')
    if not isinstance(detections, list) or not detections:
        return None

    filtered = filter_detections_for_alert(detections, allowed)
    if not filtered:
        return {'status': 'skipped', 'reason': 'alert_class_filtered'}

    info = dict(info)
    info['detections'] = filtered
    info['detection_count'] = len(filtered)
    alert_data['information'] = _json.dumps(info, ensure_ascii=False, separators=(',', ':'))
    primary = filtered[0].get('class_name') if isinstance(filtered[0], dict) else None
    if primary:
        alert_data['object'] = primary
    return None


def process_alert_hook(alert_data: Dict) -> Dict:
    """
    HTTP 告警入口（edge/mini：直连落库；其它形态可兼容转发）。

    正式 full/standard 主路径仍为 MQTT → iot-sink；edge 无 EMQX 时由 RUNTIME HTTP 调用本接口。
    """
    global _producer, _last_kafka_unavailable_warning_time, _kafka_unavailable_warning_interval
    try:
        if 'time' in alert_data:
            alert_data['time'] = _normalize_alert_wall_time_str(alert_data.get('time'))

        device_id = alert_data.get('device_id')
        task_type = normalize_algorithm_task_type(alert_data.get('task_type'))
        request_task_id = alert_data.get('task_id') or alert_data.get('taskId')

        # RUNTIME 人脸/车牌链路桥：MQTT/InferEvent 主告警路径下 C++ 补投的 feed_only 告警，
        # 仅做库匹配投递（主告警已由 iot-sink 落库），避免重复落库/通知/抑制。
        if alert_data.get('face_feed_only') or alert_data.get('plate_feed_only'):
            return _process_runtime_feed_only_alert(alert_data)

        use_direct_persist = _should_use_direct_alert_persist()

        alert_event_task = None
        if device_id:
            try:
                alert_event_task = _query_alert_event_task(
                    device_id,
                    task_type,
                    request_task_id,
                )
            except AmbiguousAlgorithmTaskError as exc:
                logger.warning('拒绝缺少任务身份的歧义告警: %s', exc)
                return {'status': 'rejected', 'reason': 'ambiguous_task', 'error': str(exc)}
            except ValueError as exc:
                return {'status': 'rejected', 'reason': 'invalid_task_id', 'error': str(exc)}
            if not alert_event_task:
                logger.info(
                    '未找到匹配且已启用的告警事件任务，跳过: task_id=%s, device_id=%s, task_type=%s',
                    request_task_id,
                    device_id,
                    task_type,
                )
                return {'status': 'skipped', 'reason': 'alert_event_disabled'}

        resolved_task_id = alert_event_task.get('task_id') if alert_event_task else request_task_id

        if alert_event_task:
            model_validation_error = _validate_alert_model_ownership(alert_data, alert_event_task)
            if model_validation_error:
                logger.warning(
                    '拒绝模型归属不匹配的告警: task_id=%s device_id=%s reason=%s',
                    resolved_task_id,
                    device_id,
                    model_validation_error.get('reason'),
                )
                return model_validation_error

        filtered = _apply_alert_class_filter(alert_data, alert_event_task)
        if filtered is not None:
            logger.info(
                '告警类别过滤跳过: device_id=%s, allowed=%s',
                device_id,
                (alert_event_task or {}).get('alert_class_names'),
            )
            return filtered

        # RUNTIME 告警接入人脸链路：任务启用人脸匹配时投递人脸抓取匹配
        try:
            _maybe_dispatch_face_matching_from_alert(alert_data, alert_event_task)
        except Exception as face_exc:
            logger.warning('RUNTIME 人脸匹配投递失败: %s', face_exc, exc_info=True)

        # RUNTIME 告警接入车牌链路：任务启用车牌匹配时投递车牌抓取匹配
        try:
            _maybe_dispatch_plate_matching_from_alert(alert_data, alert_event_task)
        except Exception as plate_exc:
            logger.warning('RUNTIME 车牌匹配投递失败: %s', plate_exc, exc_info=True)

        # Kafka 抑制仅作用于投递 Kafka；mini 直连落库由算法侧抑制，hook 不再二次拦截。
        if device_id and resolved_task_id and not use_direct_persist:
            suppress_seconds = _resolve_alert_event_suppress_seconds(
                device_id,
                task_type,
                resolved_task_id,
            )
            event_identity = resolve_alert_event_identity(alert_data)
            if _should_suppress_alert_event_kafka(
                    resolved_task_id,
                    device_id,
                    task_type,
                    suppress_seconds,
                    event_identity,
            ):
                logger.debug(
                    '告警事件 Kafka 抑制: task_id=%s, device_id=%s, task_type=%s, '
                    'event_identity=%s, interval=%ss',
                    resolved_task_id,
                    device_id,
                    task_type,
                    event_identity,
                    suppress_seconds,
                )
                return {'status': 'suppressed', 'reason': 'alert_event_suppress_interval'}

        notification_config = None
        if device_id:
            logger.info(
                '🔍 查询告警通知配置: task_id=%s, device_id=%s, task_type=%s',
                resolved_task_id,
                device_id,
                task_type,
            )
            notification_config = _query_alert_notification_config(
                device_id,
                task_type,
                resolved_task_id,
            )
            if notification_config:
                logger.info(f"✅ 找到告警通知配置: device_id={device_id}, task_id={notification_config.get('task_id')}, "
                          f"task_name={notification_config.get('task_name')}, "
                          f"notify_users={notification_config.get('notify_users') is not None}, "
                          f"notify_methods={notification_config.get('notify_methods')}")
            else:
                logger.info(
                    f"未配置告警通知（仅落库告警事件）: device_id={device_id}, task_type={task_type}, "
                    f"alert_task_id={alert_event_task.get('task_id') if alert_event_task else None}"
                )

        detection_switches = _resolve_detection_switches_from_alert_data(
            alert_data, notification_config, alert_event_task
        )

        if (os.getenv('RECORDING_STORAGE_MODE') or '').strip().lower() == 'edge_local':
            try:
                from app.services.edge_event_media_service import prepare_edge_event_media
                prepare_edge_event_media(alert_data)
                # 边缘绝对路径不能交给中心 iot-sink 读取；图片由上面的短期凭证队列独立补传。
                if not use_direct_persist:
                    alert_data['image_path'] = ''
            except Exception as media_exc:
                logger.warning('边缘事件媒体调度失败，事件仍继续落库: %s', media_exc, exc_info=True)

        # mini 形态：直连落库，避免 Kafka/iot-sink 未就绪导致告警丢失
        if use_direct_persist:
            logger.info(
                'ℹ️  mini 形态告警直连落库: device_id=%s, task_type=%s',
                device_id,
                task_type,
            )
            return _persist_alert_directly(alert_data, alert_event_task, detection_switches)
        
        # 构建告警消息（直接发送原始告警数据，Java端会处理）
        # 如果开启了告警通知，发送到Kafka
        if notification_config:
            if notification_config.get('notification_suppressed'):
                logger.info(
                    f"告警通知处于抑制窗口，仅落库不推送: device_id={device_id}, "
                    f"task_id={notification_config.get('task_id')}, "
                    f"suppress_seconds={notification_config.get('alarm_suppress_time') or 300}"
                )
            else:
                logger.info(f"📨 找到通知配置，开始处理告警通知: device_id={device_id}, "
                           f"task_id={notification_config.get('task_id')}, "
                           f"task_name={notification_config.get('task_name')}")
            
            producer = get_kafka_producer()
            if producer is not None:
                try:
                    if notification_config.get('notification_suppressed'):
                        notification_message = _build_minimal_alert_kafka_message(
                            alert_data, detection_switches, alert_event_task
                        )
                    else:
                        notification_message = _build_notification_message_for_kafka(
                            alert_data,
                            notification_config,
                            detection_switches
                        )
                        
                        if notification_message is None:
                            logger.warning(
                                f"⚠️  告警通知消息构建失败，"
                                f"将发送精简消息以保证 iot-sink 落库与 MinIO: device_id={device_id}"
                            )
                            notification_message = _build_minimal_alert_kafka_message(
                                alert_data, detection_switches, alert_event_task
                            )
                    
                    kafka_topic = _kafka_topic_for_alert_task_type(
                        alert_data.get('task_type', 'realtime')
                    )
                    
                    # 记录发送信息
                    should_notify = notification_message.get('shouldNotify', False)
                    _nu = notification_message.get('notifyUsers')
                    notify_users_count = len(_nu) if _nu else 0
                    _ch = notification_message.get('channels')
                    channels_count = len(_ch) if _ch else 0
                    logger.info(f"📤 准备发送告警通知消息到Kafka: device_id={device_id}, topic={kafka_topic}, "
                               f"shouldNotify={should_notify}, notifyUsers数量={notify_users_count}, "
                               f"notifyMethods={notification_message.get('notifyMethods')}, "
                               f"channels数量={channels_count}")
                    
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
                        if should_notify and notification_config:
                            _mark_task_notification_sent(
                                notification_config,
                                device_id,
                                alert_data.get('event_id')
                                or alert_data.get('eventId')
                                or alert_data.get('correlation_id')
                                or alert_data.get('correlationId'),
                                alert_data.get('task_type', 'realtime'),
                            )
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
                        return _fallback_persist_on_kafka_failure(
                            alert_data, alert_event_task, detection_switches, str(e)
                        )
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
                        return _fallback_persist_on_kafka_failure(
                            alert_data, alert_event_task, detection_switches, str(e)
                        )
            else:
                # 警告抑制：避免日志刷屏，每5分钟最多输出一次警告
                current_time = time.time()
                if (current_time - _last_kafka_unavailable_warning_time) >= _kafka_unavailable_warning_interval:
                    logger.warning(f"⚠️  Kafka不可用，跳过告警消息发送: device_id={device_id}（将在 {_kafka_unavailable_warning_interval} 秒后再次提醒）")
                    _last_kafka_unavailable_warning_time = current_time
                else:
                    logger.debug(f"Kafka不可用，跳过告警消息发送: device_id={device_id}")
                return _fallback_persist_on_kafka_failure(
                    alert_data, alert_event_task, detection_switches, 'Kafka不可用'
                )
        else:
            # 没有通知配置，也发送到Kafka（Java端可能需要处理），但标记为不需要通知
            logger.info(f"ℹ️  未找到通知配置，发送告警消息（不包含通知信息）: device_id={device_id}, task_type={task_type}")
            
            producer = get_kafka_producer()
            if producer is not None:
                try:
                    simple_message = _build_minimal_alert_kafka_message(
                        alert_data, detection_switches, alert_event_task
                    )

                    kafka_topic = _kafka_topic_for_alert_task_type(
                        alert_data.get('task_type', 'realtime')
                    )
                    
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
                        return _fallback_persist_on_kafka_failure(
                            alert_data, alert_event_task, detection_switches, str(e)
                        )
                except Exception as e:
                    logger.error(f"❌ 发送告警消息到Kafka异常: device_id={device_id}, error={str(e)}", exc_info=True)
                    if isinstance(e, (KafkaError, ConnectionError, TimeoutError)) or 'socket disconnected' in str(e).lower():
                        try:
                            _producer.close(timeout=1)
                        except:
                            pass
                        _producer = None
                        logger.info(f"已重置Kafka生产者，将在下次发送时重新初始化")
                        return _fallback_persist_on_kafka_failure(
                            alert_data, alert_event_task, detection_switches, str(e)
                        )
            else:
                # 警告抑制：避免日志刷屏，每5分钟最多输出一次警告
                current_time = time.time()
                if (current_time - _last_kafka_unavailable_warning_time) >= _kafka_unavailable_warning_interval:
                    logger.warning(f"⚠️  Kafka不可用，跳过告警消息发送: device_id={device_id}（将在 {_kafka_unavailable_warning_interval} 秒后再次提醒）")
                    _last_kafka_unavailable_warning_time = current_time
                else:
                    logger.debug(f"Kafka不可用，跳过告警消息发送: device_id={device_id}")
                return _fallback_persist_on_kafka_failure(
                    alert_data, alert_event_task, detection_switches, 'Kafka不可用'
                )
        
    except Exception as e:
        logger.error(f"处理告警Hook失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"处理告警Hook失败: {str(e)}")


def _build_notification_message_for_kafka(alert_data: Dict, notification_config: Dict,
                                          detection_switches: Optional[Dict] = None) -> Optional[Dict]:
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

    if channels:
        try:
            from app.services.algorithm_task_service import _enrich_channels_userless_flags
            channels = _enrich_channels_userless_flags(channels)
        except Exception as e:
            logger.debug(f"补充 userless 渠道标记失败: {e}")
    
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
    has_channels = bool(channels or notify_methods)
    has_users = bool(notify_users)
    has_userless = _has_userless_channel(channels)
    # HTTP/Webhook 只需 channels（URL 在模板中），不强制 notify_users
    should_notify = has_channels and (has_users or has_userless)
    if has_users and not should_notify:
        logger.warning(f"⚠️  有通知人但没有通知方式: device_id={device_id}, task_id={task_id}, "
                      f"notify_users数量={len(notify_users)}, channels数量={len(channels)}, "
                      f"notify_methods={notify_methods}")
    
    # 记录通知配置信息
    logger.info(f"📊 通知配置信息: device_id={device_id}, task_id={task_id}, "
                f"channels数量={len(channels)}, notify_methods={notify_methods}, "
                f"notify_users数量={len(notify_users)}, has_userless_channel={has_userless}, "
                f"shouldNotify={should_notify}")

    if not should_notify and has_channels and not has_users and not has_userless:
        # 仅群机器人 / HTTP Webhook 可在无 notify_users 时兜底；工作通知必须带通知人
        robot_channels = [ch for ch in channels if _is_robot_fallback_channel(ch)]
        if robot_channels:
            should_notify = True
            for ch in robot_channels:
                ch['userless'] = True
            has_userless = True
            logger.info(
                f"ℹ️  按群机器人/Webhook 渠道兜底启用通知: device_id={device_id}, "
                f"task_id={task_id}, robot_channels={len(robot_channels)}"
            )

    if notification_config.get('notification_suppressed'):
        should_notify = False
        logger.info(
            f"告警通知处于抑制窗口，本轮不发送通知: device_id={device_id}, task_id={task_id}"
        )

    if not should_notify:
        if not has_channels:
            logger.warning(
                f"⚠️  告警通知无有效渠道，跳过发送: device_id={device_id}, "
                f"task_id={task_id}, task_name={task_name}"
            )
            return None
        if not has_users and not has_userless:
            wxcp_methods = frozenset({'wxcp', 'wechat', 'weixin'})
            has_wxcp_work = any(
                (ch.get('method') or '').lower() in wxcp_methods and not _is_robot_fallback_channel(ch)
                for ch in (channels or [])
            )
            if has_wxcp_work:
                logger.warning(
                    f"⚠️  企业微信工作通知缺少通知人(notify_users)，无法推送: "
                    f"device_id={device_id}, task_id={task_id}, task_name={task_name}. "
                    f"请确认「办公室告警」模板已绑定用户分组，并重新保存算法任务"
                )
            else:
                logger.warning(
                    f"⚠️  告警通知消息中没有通知人且无群机器人/Webhook 渠道，跳过发送: "
                    f"device_id={device_id}, task_id={task_id}, task_name={task_name}, "
                    f"channels={channels}"
                )
            return None
    
    alert_time = _normalize_alert_wall_time_str(alert_data.get('time'))
    
    # 构建通知消息（使用驼峰命名以匹配 Java 端的 AlertNotificationMessage）
    face_enabled = bool(
        detection_switches.get('face_detection_enabled', False)
    ) if detection_switches else bool(notification_config.get('face_detection_enabled', False))
    plate_enabled = bool(
        detection_switches.get('plate_detection_enabled', False)
    ) if detection_switches else bool(notification_config.get('plate_detection_enabled', False))

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
        'faceDetectionEnabled': face_enabled,
        'plateDetectionEnabled': plate_enabled,
        'shouldNotify': should_notify,  # 是否需要发送通知
        'timestamp': _shanghai_message_timestamp(),
    }
    correlation_id = alert_data.get('correlation_id') or alert_data.get('correlationId')
    if correlation_id:
        message['correlationId'] = correlation_id
    message['schemaVersion'] = alert_data.get('schema_version') or alert_data.get('schemaVersion') or 1
    message['eventId'] = alert_data.get('event_id') or alert_data.get('eventId') or correlation_id
    message['modelIds'] = sorted(_normalize_event_model_ids(alert_data))
    message['detections'] = alert_data.get('detections') or []
    
    logger.info(f"✅ 告警通知消息构建成功: device_id={device_id}, task_id={task_id}, "
                f"shouldNotify={should_notify}, notifyUsers数量={len(notify_users)}, "
                f"notifyMethods={notify_methods}, channels数量={len(channels)}")
    
    return message
