"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm.query import Query
from models import Alert, db

logger = logging.getLogger('alert')

# 库匹配告警：object 存匹配对象（人员姓名/车牌号），task_name 存任务名
LIBRARY_MATCH_EVENTS = frozenset({'face_library_match', 'plate_library_match'})

# 与 iot-sink parseAlertEventTime、算法告警 time 字段一致：东八区墙钟
from app.utils.service_urls import (
    SHANGHAI_TZ,
    LEGACY_PLAYBACK_TZ_OFFSET_SECONDS,
    ensure_shanghai_aware,
    normalize_to_shanghai_naive,
    parse_alert_time_str,
    score_playback_for_alert,
)


def is_minio_download_path(path: str) -> bool:
    """是否为 MinIO 对象下载 API 路径（与 image_url、playback.file_path 一致）。"""
    if not path or not isinstance(path, str):
        return False
    p = path.strip()
    return p.startswith('/api/v1/buckets/') and '/objects/download' in p


def _alert_to_dict(alert: Alert) -> dict:
    """将 Alert 对象转换为字典格式"""
    result = {
        'id': alert.id,
        'object': alert.object,
        'event': alert.event,
        'region': alert.region,
        'device_id': alert.device_id,
        'device_name': alert.device_name,
        'image_path': alert.image_path,
        'record_path': alert.record_path,
        'task_id': alert.task_id if hasattr(alert, 'task_id') else None,
        'task_name': alert.task_name if hasattr(alert, 'task_name') else None,
        'edge_node_id': getattr(alert, 'edge_node_id', None),
        'edge_node_name': getattr(alert, 'edge_node_name', None),
        'edge_node_host': getattr(alert, 'edge_node_host', None),
        'node_id': getattr(alert, 'node_id', None),
    }
    
    # 处理 information 字段（如果是 JSON 字符串则解析）
    information_dict = None
    if alert.information is not None:
        if isinstance(alert.information, str):
            try:
                information_dict = json.loads(alert.information)
                result['information'] = information_dict
            except (json.JSONDecodeError, TypeError):
                result['information'] = alert.information
        else:
            information_dict = alert.information
            result['information'] = alert.information
    else:
        result['information'] = None
    
    # 优先使用字段中的 task_type，如果没有则从 information 中提取（兼容旧数据）
    task_type = alert.task_type
    if not task_type:
        # 兼容旧数据：从 information 中提取 task_type
        if information_dict and isinstance(information_dict, dict):
            task_type = information_dict.get('task_type')
        elif alert.information and isinstance(alert.information, str):
            try:
                parsed_info = json.loads(alert.information)
                if isinstance(parsed_info, dict):
                    task_type = parsed_info.get('task_type')
            except (json.JSONDecodeError, TypeError):
                pass
    
    # 设置 task_type 字段（如果存在）
    if task_type:
        result['task_type'] = task_type
    else:
        # 默认值：如果没有找到 task_type，默认为 'realtime'
        result['task_type'] = 'realtime'
    
    # 处理 time 字段（东八区墙钟字符串，与算法上报 / 录像匹配一致）
    if alert.time is not None and hasattr(alert.time, 'strftime'):
        sh_time = normalize_to_shanghai_naive(alert.time)
        result['time'] = sh_time.strftime('%Y-%m-%d %H:%M:%S') if sh_time else alert.time
    else:
        result['time'] = alert.time
    
    # 处理 notify_users 字段（如果是 JSON 字符串则解析）
    if alert.notify_users is not None:
        if isinstance(alert.notify_users, str):
            try:
                result['notify_users'] = json.loads(alert.notify_users)
            except (json.JSONDecodeError, TypeError):
                result['notify_users'] = alert.notify_users
        else:
            result['notify_users'] = alert.notify_users
    else:
        result['notify_users'] = None
    
    # 处理 channels 字段（如果是 JSON 字符串则解析）
    if alert.channels is not None:
        if isinstance(alert.channels, str):
            try:
                result['channels'] = json.loads(alert.channels)
            except (json.JSONDecodeError, TypeError):
                result['channels'] = alert.channels
        else:
            result['channels'] = alert.channels
    else:
        result['channels'] = None
    
    # 处理 notification_sent 和 notification_sent_time 字段
    result['notification_sent'] = alert.notification_sent if hasattr(alert, 'notification_sent') else False
    if hasattr(alert, 'notification_sent_time') and alert.notification_sent_time is not None:
        if hasattr(alert.notification_sent_time, 'strftime'):
            result['notification_sent_time'] = alert.notification_sent_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            result['notification_sent_time'] = alert.notification_sent_time
    else:
        result['notification_sent_time'] = None

    # MinIO 图片下载路径（列表与前端展示优先使用）
    image_url = alert.image_url if hasattr(alert, 'image_url') else ''
    try:
        from app.utils.service_urls import (
            is_local_filesystem_path,
            minio_storage_enabled,
            build_alert_image_api_url,
        )
        if not minio_storage_enabled() and is_local_filesystem_path(image_url or ''):
            image_url = build_alert_image_api_url(image_url)
    except Exception:
        pass
    result['image_url'] = image_url or ''

    record_path = result.get('record_path') or ''
    try:
        from app.utils.service_urls import (
            is_local_filesystem_path,
            minio_storage_enabled,
        )
        if not minio_storage_enabled() and is_local_filesystem_path(record_path):
            from urllib.parse import quote
            result['record_path'] = f'/video/alert/record?path={quote(record_path, safe="")}'
    except Exception:
        pass

    business_tags = []
    if hasattr(alert, 'business_tags') and alert.business_tags:
        try:
            parsed = json.loads(alert.business_tags) if isinstance(alert.business_tags, str) else alert.business_tags
            if isinstance(parsed, list):
                business_tags = parsed
        except (json.JSONDecodeError, TypeError):
            business_tags = []
    result['business_tags'] = business_tags

    if hasattr(alert, 'correlation_id'):
        result['correlation_id'] = alert.correlation_id

    if alert.event == 'face_library_match' and alert.object:
        result['matched_person_name'] = alert.object

    if information_dict and isinstance(information_dict, dict):
        source_event = information_dict.get('source_event')
        if source_event:
            result['source_event'] = source_event
        matched_person_code = information_dict.get('matched_person_code')
        if matched_person_code:
            result['matched_person_code'] = matched_person_code
        library_name = information_dict.get('library_name')
        if library_name:
            result['library_name'] = library_name

    return result


def _get_alert_filter_query(args: dict) -> Query:
    """构建报警查询过滤器"""
    # 仅返回告警图已上传 MinIO 的记录；抓拍任务无 DVR，不要求 record_path
    query: Query = Alert.query.filter(
        Alert.image_url.isnot(None),
        db.func.trim(Alert.image_url) != '',
    )

    if 'object' in args and args['object']:
        object_value = args['object'].strip() if isinstance(args['object'], str) else args['object']
        if object_value:
            query = query.filter(Alert.object == object_value)

    if 'event' in args and args['event']:
        event_value = args['event'].strip() if isinstance(args['event'], str) else args['event']
        if event_value:
            query = query.filter(Alert.event == event_value)

    if 'device_id' in args and args['device_id']:
        device_id_value = args['device_id'].strip() if isinstance(args['device_id'], str) else args['device_id']
        if device_id_value:
            query = query.filter(Alert.device_id == device_id_value)

    correlation_id = args.get('correlation_id') or args.get('correlationId')
    if correlation_id:
        correlation_id = str(correlation_id).strip()
        if correlation_id:
            query = query.filter(Alert.correlation_id == correlation_id)

    if 'task_type' in args and args['task_type']:
        task_type_value = args['task_type'].strip() if isinstance(args['task_type'], str) else args['task_type']
        if task_type_value:
            query = query.filter(Alert.task_type == task_type_value)

    if 'task_id' in args and args['task_id']:
        try:
            task_id_value = int(args['task_id'])
            query = query.filter(Alert.task_id == task_id_value)
        except (ValueError, TypeError):
            logger.warning(f'无效的task_id参数: {args["task_id"]}')

    # 任务名称：对 task_name 做模糊匹配
    if 'task_name' in args and args['task_name']:
        task_name_value = args['task_name'].strip() if isinstance(args['task_name'], str) else args['task_name']
        if task_name_value:
            query = query.filter(Alert.task_name.like(f'%{task_name_value}%'))

    if 'business_tags' in args and args['business_tags']:
        tag_value = args['business_tags']
        tag_list = []
        if isinstance(tag_value, str):
            tag_value = tag_value.strip()
            if tag_value:
                try:
                    parsed = json.loads(tag_value)
                    tag_list = parsed if isinstance(parsed, list) else [tag_value]
                except json.JSONDecodeError:
                    tag_list = [t.strip() for t in tag_value.split(',') if t.strip()]
        elif isinstance(tag_value, list):
            tag_list = [str(t).strip() for t in tag_value if str(t).strip()]
        for tag in tag_list:
            query = query.filter(Alert.business_tags.ilike(f'%{tag}%'))

    if 'begin_datetime' in args and args['begin_datetime']:
        begin_datetime_value = args['begin_datetime'].strip() if isinstance(args['begin_datetime'], str) else str(
            args['begin_datetime'])
        if begin_datetime_value:
            try:
                begin_time = None
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
                    try:
                        begin_time = datetime.strptime(begin_datetime_value, fmt)
                        break
                    except ValueError:
                        continue
                if begin_time:
                    query = query.filter(Alert.time >= begin_time)
                else:
                    logger.warning(f'无法解析开始时间格式: {begin_datetime_value}')
            except Exception as e:
                logger.warning(f'解析开始时间失败: {begin_datetime_value}, 错误: {str(e)}')

    if 'end_datetime' in args and args['end_datetime']:
        end_datetime_value = args['end_datetime'].strip() if isinstance(args['end_datetime'], str) else str(
            args['end_datetime'])
        if end_datetime_value:
            try:
                end_time = None
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
                    try:
                        end_time = datetime.strptime(end_datetime_value, fmt)
                        break
                    except ValueError:
                        continue
                if end_time:
                    query = query.filter(Alert.time <= end_time)
                else:
                    logger.warning(f'无法解析结束时间格式: {end_datetime_value}')
            except Exception as e:
                logger.warning(f'解析结束时间失败: {end_datetime_value}, 错误: {str(e)}')

    return query


def _should_skip_backfill(args: dict) -> bool:
    val = args.get('skip_backfill')
    if val is None:
        return False
    return str(val).lower() in ('1', 'true', 'yes')


def get_alert_list(args: dict) -> dict:
    """获取报警列表（仅返回 image_url 已写入 MinIO 的记录；record_path 可选）

    Args:
        args: 查询参数字典，支持以下参数：
            - pageNo: 页码（可选）
            - pageSize: 每页数量（可选，如果提供则启用分页）
            - object: 对象类型过滤（可选）
            - event: 事件类型过滤（可选）
            - device_id: 设备ID过滤（可选）
            - task_type: 任务类型过滤（可选，'realtime'或'snap'）
            - task_id: 任务ID过滤（可选）
            - task_name: 任务名称模糊匹配（过滤 object 字段，可选）
            - begin_datetime: 开始时间过滤（可选，多种 ISO 格式）
            - end_datetime: 结束时间过滤（可选）

    Returns:
        dict: 包含 alert_list 和 total 的字典
    """
    query = _get_alert_filter_query(args).order_by(Alert.time.desc())

    if 'pageSize' in args and args['pageSize']:
        try:
            page_no = int(args.get('pageNo') or 1)
            page_size = int(args['pageSize'])
            paginate = query.paginate(page=page_no, per_page=page_size, error_out=False)
            if not _should_skip_backfill(args):
                backfill_alert_records_for_list(paginate.items)
            return {
                'alert_list': [_alert_to_dict(alert) for alert in paginate.items],
                'total': paginate.total
            }
        except ValueError as e:
            logger.error(f'分页查询失败: {str(e)}')
            return {'alert_list': [], 'total': 0}
    else:
        alerts = query.all()
        if not _should_skip_backfill(args):
            backfill_alert_records_for_list(alerts)
        return {
            'alert_list': [_alert_to_dict(alert) for alert in alerts],
            'total': len(alerts)
        }


def get_correlation_events(correlation_id: str) -> dict:
    """按 correlation_id 聚合查询同一帧的算法告警、人脸匹配、车牌匹配记录。"""
    from models import FaceMatchRecord, PlateMatchRecord

    cid = str(correlation_id or '').strip()
    if not cid:
        raise ValueError('correlation_id 不能为空')

    alerts = Alert.query.filter(Alert.correlation_id == cid).order_by(Alert.id.asc()).all()
    face_records = (
        FaceMatchRecord.query.filter(FaceMatchRecord.correlation_id == cid)
        .order_by(FaceMatchRecord.id.asc())
        .all()
    )
    plate_records = (
        PlateMatchRecord.query.filter(PlateMatchRecord.correlation_id == cid)
        .order_by(PlateMatchRecord.id.asc())
        .all()
    )
    return {
        'correlation_id': cid,
        'alerts': [_alert_to_dict(a) for a in alerts],
        'face_match_records': [r.to_dict() for r in face_records],
        'plate_match_records': [r.to_dict() for r in plate_records],
    }


def get_alert_count(args: dict) -> dict:
    """获取报警统计（与列表一致：仅统计 image_url 已写入 MinIO 的记录，筛选条件同 get_alert_list）"""
    query = _get_alert_filter_query(args)

    if 'group' in args and args['group']:
        group_type = args['group']

        if group_type == 'date':
            group = db.func.DATE(Alert.time)
        elif group_type == 'device':
            group = Alert.device_id
        elif group_type == 'object':
            group = Alert.object
        else:
            logger.warning(f'不支持的 group 参数: {group_type}')
            return {'count_list': [], 'total_count': 0}

        count_list = []
        try:
            results = query.with_entities(group, db.func.count()).group_by(group).all()
            for col in results:
                value = col[0]
                # 处理日期类型
                if group_type == 'date' and hasattr(value, 'strftime'):
                    value = value.strftime('%Y-%m-%d')
                count_list.append({
                    'value': value,
                    'count': col[1]
                })

            total_count = sum(item['count'] for item in count_list)
            return {'count_list': count_list, 'total_count': total_count}
        except Exception as e:
            logger.error(f'分组统计失败: {str(e)}')
            return {'count_list': [], 'total_count': 0}
    else:
        try:
            total_count = query.count()
            return {'count_list': None, 'total_count': total_count}
        except Exception as e:
            logger.error(f'统计总数失败: {str(e)}')
            return {'count_list': None, 'total_count': 0}


def create_alert(alert_data: dict) -> dict:
    """创建报警记录
    
    Args:
        alert_data: 报警数据字典，包含以下字段：
            - object: 对象类型（必填）
            - event: 事件类型（必填）
            - device_id: 设备ID（必填）
            - device_name: 设备名称（必填）
            - region: 区域（可选）
            - information: 详细信息，可以是字符串或字典（可选）
            - time: 报警时间，格式：'YYYY-MM-DD HH:MM:SS'（可选，默认当前时间）
            - image_path: 图片路径（可选）
            - record_path: 录像路径（可选）
            - notify_users: 通知人列表（可选，JSON格式或列表）
            - channels: 通知渠道配置（可选，JSON格式或列表）
    
    Returns:
        dict: 创建的报警记录字典
    """
    try:
        # 验证必填字段
        required_fields = ['object', 'event', 'device_id', 'device_name']
        for field in required_fields:
            if field not in alert_data or not alert_data[field]:
                raise ValueError(f'必填字段 {field} 不能为空')
        
        # 处理时间字段（东八区墙钟，与 patch_alerts_record / on_dvr 一致）
        if 'time' in alert_data and alert_data['time']:
            if isinstance(alert_data['time'], str):
                alert_time = datetime.strptime(alert_data['time'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=SHANGHAI_TZ)
            elif getattr(alert_data['time'], 'tzinfo', None) is None:
                alert_time = alert_data['time'].replace(tzinfo=SHANGHAI_TZ)
            else:
                alert_time = alert_data['time'].astimezone(SHANGHAI_TZ)
        else:
            alert_time = datetime.now(SHANGHAI_TZ)
        
        # 处理 information 字段（如果是字典则转换为JSON字符串）
        information = alert_data.get('information')
        if information is not None:
            if isinstance(information, dict):
                # 如果 information 是字典，移除 task_type（因为已经单独存储到字段中）
                information = information.copy()
                information.pop('task_type', None)  # 移除task_type，避免冗余
                information = json.dumps(information, ensure_ascii=False) if information else None
            elif isinstance(information, str):
                # 如果 information 是字符串，尝试解析并移除 task_type
                try:
                    info_dict = json.loads(information)
                    if isinstance(info_dict, dict):
                        info_dict.pop('task_type', None)  # 移除task_type，避免冗余
                        information = json.dumps(info_dict, ensure_ascii=False) if info_dict else None
                except (json.JSONDecodeError, TypeError):
                    # 如果解析失败，保持原样
                    pass
        
        # 获取 task_type（优先从 alert_data 中获取，如果没有则默认为 'realtime'）
        task_type = alert_data.get('task_type', 'realtime')
        # 兼容 'snapshot' 值，统一转换为 'snap'
        if task_type == 'snapshot':
            task_type = 'snap'
        
        # 处理 notify_users 字段
        notify_users = alert_data.get('notify_users')
        if notify_users is not None:
            if isinstance(notify_users, (dict, list)):
                notify_users = json.dumps(notify_users, ensure_ascii=False)
            elif isinstance(notify_users, str):
                # 如果已经是字符串，验证是否为有效的JSON
                try:
                    json.loads(notify_users)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f'notify_users 不是有效的JSON格式: {notify_users}')
                    notify_users = None
        else:
            notify_users = None
        
        # 处理 channels 字段
        channels = alert_data.get('channels')
        if channels is not None:
            if isinstance(channels, (dict, list)):
                channels = json.dumps(channels, ensure_ascii=False)
            elif isinstance(channels, str):
                # 如果已经是字符串，验证是否为有效的JSON
                try:
                    json.loads(channels)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f'channels 不是有效的JSON格式: {channels}')
                    channels = None
        else:
            channels = None

        business_tags = alert_data.get('business_tags')
        if business_tags is not None:
            if isinstance(business_tags, list):
                business_tags = json.dumps(business_tags, ensure_ascii=False)
            elif isinstance(business_tags, str):
                try:
                    json.loads(business_tags)
                except (json.JSONDecodeError, TypeError):
                    business_tags = json.dumps([business_tags], ensure_ascii=False)
        else:
            business_tags = None

        task_id = alert_data.get('task_id')
        task_name = alert_data.get('task_name')
        correlation_id = alert_data.get('correlation_id') or alert_data.get('correlationId')
        if correlation_id:
            correlation_id = str(correlation_id).strip() or None

        # 非库匹配告警：task_name 写入 object（任务展示名）；库匹配告警 object 保留匹配对象
        object_value = alert_data['object']
        if task_name and alert_data['event'] not in LIBRARY_MATCH_EVENTS:
            object_value = task_name

        # 创建报警记录
        alert = Alert(
            object=object_value,
            event=alert_data['event'],
            device_id=alert_data['device_id'],
            device_name=alert_data['device_name'],
            region=alert_data.get('region'),
            information=information,
            time=alert_time,
            image_path=alert_data.get('image_path'),
            image_url=alert_data.get('image_url'),
            record_path=alert_data.get('record_path'),
            task_type=task_type,
            task_id=task_id,
            task_name=task_name,
            notify_users=notify_users,
            channels=channels,
            business_tags=business_tags,
            correlation_id=correlation_id,
            edge_node_id=alert_data.get('edge_node_id') or alert_data.get('edgeNodeId'),
            edge_node_name=alert_data.get('edge_node_name') or alert_data.get('edgeNodeName'),
            edge_node_host=alert_data.get('edge_node_host') or alert_data.get('edgeNodeHost'),
            node_id=alert_data.get('node_id') or alert_data.get('nodeId'),
        )
        
        db.session.add(alert)
        db.session.commit()

        if not (alert.record_path or '').strip() and task_type != 'snap':
            try:
                try_backfill_alert_record_from_playback(alert)
            except Exception as backfill_err:
                logger.debug(
                    'Playback 回填 record_path 跳过 alert_id=%s: %s',
                    alert.id,
                    backfill_err,
                )

        return _alert_to_dict(alert)
    except ValueError as e:
        logger.error(f'创建报警记录参数错误: {str(e)}')
        db.session.rollback()
        raise
    except Exception as e:
        logger.error(f'创建报警记录失败: {str(e)}')
        db.session.rollback()
        raise


def _normalize_to_shanghai_naive(value):
    return normalize_to_shanghai_naive(value)


def find_playback_for_alert(device_id: str, alert_time, time_range: int = 300):
    """查找与告警时间最匹配的 Playback 记录。"""
    from models import Playback

    alert_sh = ensure_shanghai_aware(alert_time)
    extended_range = max(time_range + 120, 300) + LEGACY_PLAYBACK_TZ_OFFSET_SECONDS
    start_time = alert_sh - timedelta(seconds=extended_range)
    end_time = alert_sh + timedelta(seconds=extended_range)

    candidates = Playback.query.filter(
        Playback.device_id == device_id,
        Playback.event_time >= start_time,
        Playback.event_time <= end_time,
    ).all()

    matched = []
    for playback in candidates:
        score = score_playback_for_alert(playback, alert_time, time_range)
        if score is not None:
            matched.append((playback, score))

    if matched:
        matched.sort(key=lambda x: x[1])
        return matched[0][0]
    return None


def find_record_file_for_alert(device_id: str, alert_time, time_range: int = 300):
    """在 RecordFile 元数据中查找与告警时间最匹配的录像片段（Playback 未命中时的兜底）。"""
    from models import RecordFile, RecordSpace

    alert_naive = normalize_to_shanghai_naive(alert_time)
    if not alert_naive:
        return None

    space = RecordSpace.query.filter_by(device_id=device_id).first()
    if not space:
        return None

    extended_range = max(time_range + 120, 300)
    start_time = alert_naive - timedelta(seconds=extended_range)
    end_time = alert_naive + timedelta(seconds=extended_range)

    candidates = (
        RecordFile.query.filter(
            RecordFile.device_id == device_id,
            RecordFile.space_id == space.id,
            RecordFile.event_time >= start_time,
            RecordFile.event_time <= end_time,
        )
        .order_by(RecordFile.event_time.asc())
        .all()
    )

    best = None
    best_score = None
    for record in candidates:
        duration = int(record.duration or 30)
        seg_start = record.event_time
        legacy_start = seg_start - timedelta(seconds=duration)
        seg_end = seg_start + timedelta(seconds=duration)
        if legacy_start <= alert_naive <= seg_end:
            score = 0.0
        else:
            center = seg_start + timedelta(seconds=duration / 2)
            score = abs((center - alert_naive).total_seconds())
            if score > time_range:
                continue
        if best_score is None or score < best_score:
            best = record
            best_score = score
    return best


def _record_path_playback_payload(record_path: str, device_id: str) -> dict:
    """将 alert.record_path 转为可播放响应。"""
    from urllib.parse import quote

    from app.utils.service_urls import is_local_filesystem_path, minio_storage_enabled

    record_path = (record_path or '').strip()
    if not record_path:
        return {}
    if is_minio_download_path(record_path):
        return {
            'video_url': record_path,
            'file_path': record_path,
            'device_id': device_id,
            'source': 'alert_record_path',
        }
    if not minio_storage_enabled() and is_local_filesystem_path(record_path):
        from app.utils.service_urls import build_alert_record_api_url
        api_path = build_alert_record_api_url(record_path)
        return {
            'video_url': api_path,
            'file_path': record_path,
            'device_id': device_id,
            'source': 'alert_record_path',
        }
    return {}


def resolve_alert_record_video(
    device_id: str,
    alert_time,
    time_range: int = 300,
    alert_id=None,
) -> Optional[dict]:
    """解析告警录像播放地址：record_path → Playback → RecordFile。"""
    alert_row = None
    if alert_id is not None:
        try:
            alert_row = Alert.query.get(int(alert_id))
        except (TypeError, ValueError):
            alert_row = None

    if alert_row:
        device_id = device_id or alert_row.device_id
        if alert_row.time is not None:
            alert_time = alert_row.time
        if not (alert_row.record_path or '').strip():
            try:
                try_backfill_alert_record_from_playback(alert_row)
            except Exception as exc:
                logger.debug('查询前回填 record_path 跳过 alert_id=%s: %s', alert_row.id, exc)
        payload = _record_path_playback_payload(alert_row.record_path, alert_row.device_id)
        if payload:
            return payload

    if not device_id or alert_time is None:
        return None

    playback = find_playback_for_alert(device_id, alert_time, time_range)
    if playback and (playback.file_path or '').strip():
        from app.utils.service_urls import resolve_playback_display_url
        file_path = playback.file_path.strip()
        return {
            'playback_id': playback.id,
            'file_path': file_path,
            'video_url': resolve_playback_display_url(file_path),
            'event_time': playback.event_time.isoformat() if playback.event_time else None,
            'duration': playback.duration,
            'device_id': playback.device_id,
            'device_name': playback.device_name,
            'source': 'playback_match',
        }

    record_file = find_record_file_for_alert(device_id, alert_time, time_range)
    if record_file:
        item = record_file.to_list_item()
        file_path = (item.get('url') or record_file.url or '').strip()
        if file_path:
            return {
                'record_file_id': record_file.id,
                'file_path': file_path,
                'video_url': file_path,
                'event_time': record_file.event_time.isoformat() if record_file.event_time else None,
                'duration': record_file.duration,
                'device_id': record_file.device_id,
                'source': 'record_file_match',
            }
    return None


def _find_playback_for_alert(device_id: str, alert_time, time_range: int = 300):
    return find_playback_for_alert(device_id, alert_time, time_range)


def backfill_alert_records_for_list(alerts) -> None:
    """列表展示前为缺失 record_path 的实时告警尝试回填。"""
    for alert in alerts:
        if (alert.record_path or '').strip() or alert.task_type == 'snap':
            continue
        try:
            try_backfill_alert_record_from_playback(alert)
        except Exception as exc:
            logger.debug('列表回填 record_path 跳过 alert_id=%s: %s', alert.id, exc)


def try_backfill_alert_record_from_playback(alert: Alert) -> bool:
    """告警落库后从 Playback 回填 record_path（DVR 已落盘但 patch 尚未命中时使用）。"""
    if (alert.record_path or '').strip():
        return False
    if alert.task_type == 'snap':
        return False

    playback = _find_playback_for_alert(alert.device_id, alert.time)
    if not playback or not (playback.file_path or '').strip():
        return False

    file_path = playback.file_path.strip()
    is_mini = False
    try:
        from app.utils.service_urls import is_mini_deploy_profile

        is_mini = is_mini_deploy_profile()
    except Exception:
        is_mini = False

    if not is_minio_download_path(file_path) and not is_mini:
        return False

    alert.record_path = file_path
    db.session.commit()
    logger.info('告警 %s 已从 Playback 回填 record_path: %s', alert.id, file_path[:120])
    return True


def patch_alerts_record(dvr_info: dict):
    """更新报警记录的录像路径。

    - 标准/完整形态：仅写入 MinIO 下载地址（禁止宿主机本地路径）。
      与 door-god on_dvr 一致：file_path 为
      ``/api/v1/buckets/{bucket}/objects/download?prefix=...``，非 ``/data/playbacks/...``。
    - mini 形态：不部署 MinIO，允许将本地录像路径直接写入 record_path（如 ``/data/playbacks/...``）。

    Args:
        dvr_info: DVR信息字典，包含以下字段：
            - event_time: 事件时间，格式：'YYYY-MM-DD HH:MM:SS'
            - duration: 持续时间（秒）
            - device_id: 设备ID
            - file_path: 录像路径（MinIO 下载 API 或本地路径，取决于部署形态）
    """
    try:
        file_path = (dvr_info.get('file_path') or '').strip()

        # 非 mini 形态严格要求 MinIO 下载地址；mini 形态允许本地路径
        is_mini = False
        try:
            from app.utils.service_urls import is_mini_deploy_profile

            is_mini = is_mini_deploy_profile()
        except Exception:
            is_mini = False

        if not is_minio_download_path(file_path) and not is_mini:
            logger.warning(
                '跳过回写告警 record_path：非 MinIO 下载地址 file_path=%s device_id=%s',
                file_path,
                dvr_info.get('device_id'),
            )
            return

        begin_time = datetime.strptime(dvr_info['event_time'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=SHANGHAI_TZ)
        duration = int(dvr_info.get('duration') or 1)
        # 兼容 event_time 为片段结束时刻（mtime）的旧数据：向前扩展一个 duration
        legacy_start = begin_time - timedelta(seconds=duration)
        end_time = begin_time + timedelta(seconds=duration)
        device_id = dvr_info['device_id']

        alerts = Alert.query.filter(
            Alert.time >= legacy_start,
            Alert.time <= end_time,
            Alert.device_id == device_id,
            db.or_(Alert.record_path.is_(None), db.func.trim(Alert.record_path) == ''),
        ).all()

        if alerts:
            for alert in alerts:
                alert.record_path = file_path
            db.session.commit()
            logger.info(
                '成功更新 %s 条告警 record_path（MinIO）device_id=%s path=%s',
                len(alerts), device_id, file_path[:120],
            )
        else:
            logger.debug(
                '未匹配到需回写 record_path 的告警 device_id=%s event_time=%s duration=%s',
                device_id, dvr_info.get('event_time'), dvr_info.get('duration'),
            )
    except Exception as e:
        logger.error(f'更新报警记录失败: {str(e)}')
        db.session.rollback()
        raise


def get_dashboard_statistics() -> dict:
    """获取仪表板统计信息
    
    Returns:
        dict: 包含以下统计信息的字典：
            - alarm_count: 告警总数
            - today_alarm_count: 今日告警数
            - camera_count: 摄像头数量
            - algorithm_count: 算法数量
            - model_count: 模型数量（如果AI服务可用则返回实际值，否则返回0）
    """
    try:
        from models import Device, AlgorithmTask
        
        # 统计告警总数
        alarm_count = Alert.query.count()
        
        # 统计今日告警数（从今天00:00:00开始，使用北京时区）
        from datetime import timezone
        import pytz
        
        # 获取北京时区的当前时间
        beijing_tz = pytz.timezone('Asia/Shanghai')
        beijing_now = datetime.now(beijing_tz)
        today_start = beijing_now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 由于Alert.time是带时区的，需要确保时区一致
        today_alarm_count = Alert.query.filter(Alert.time >= today_start).count()
        
        # 统计摄像头数量
        camera_count = Device.query.count()
        
        # 统计算法数量（算法任务数量）
        algorithm_count = AlgorithmTask.query.count()
        
        # 统计模型数量（通过DEVICE网关访问AI服务，如果失败则返回0）
        model_count = 0
        try:
            import os
            import requests
            
            # 从环境变量获取DEVICE网关地址，如果没有则使用默认值
            # 网关端口是48080，AI服务路由前缀是 /admin-api/model
            gateway_url = os.environ.get('DEVICE_GATEWAY_URL', 'http://localhost:48080')
            # 通过网关访问AI服务的模型列表接口
            # 网关路由配置：/admin-api/model/** -> model-server，StripPrefix=1
            # 所以完整路径是：http://网关:48080/admin-api/model/list
            ai_api_url = f"{gateway_url.rstrip('/')}/admin-api/model/list"
            
            # 调用AI服务的模型列表接口（只获取第一页，用于统计总数）
            response = requests.get(
                ai_api_url,
                params={'pageNo': 1, 'pageSize': 1},
                timeout=2  # 2秒超时，避免阻塞
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    model_count = data.get('total', 0)
        except Exception as e:
            # 如果AI服务不可用，记录日志但不影响其他统计
            logger.debug(f'无法获取模型数量（AI服务可能不可用）: {str(e)}')
            model_count = 0
        
        return {
            'alarm_count': alarm_count,
            'today_alarm_count': today_alarm_count,
            'camera_count': camera_count,
            'algorithm_count': algorithm_count,
            'model_count': model_count
        }
    except Exception as e:
        logger.error(f'获取仪表板统计信息失败: {str(e)}')
        # 返回默认值，避免前端报错
        return {
            'alarm_count': 0,
            'today_alarm_count': 0,
            'camera_count': 0,
            'algorithm_count': 0,
            'model_count': 0
        }


def clear_all_alerts() -> dict:
    """清空所有告警记录

    Returns:
        dict: 包含删除数量的字典
    """
    alerts = Alert.query.all()
    delete_count = len(alerts)

    for alert in alerts:
        db.session.delete(alert)

    db.session.commit()
    logger.info(f'清空所有告警成功: deleted_count={delete_count}')

    return {
        'deleted_count': delete_count,
    }


def clear_alerts_by_task_name(task_name: str) -> dict:
    """按任务名称清空告警记录

    说明：当前工程中 task_name 对应告警表的 object 字段。
    """
    task_name = (task_name or '').strip()
    if not task_name:
        raise ValueError('task_name参数不能为空')

    alerts = Alert.query.filter(Alert.object == task_name).all()
    delete_count = len(alerts)

    for alert in alerts:
        db.session.delete(alert)

    db.session.commit()
    logger.info(f'清空任务告警成功: task_name={task_name}, deleted_count={delete_count}')

    return {
        'deleted_count': delete_count,
        'task_name': task_name,
    }
