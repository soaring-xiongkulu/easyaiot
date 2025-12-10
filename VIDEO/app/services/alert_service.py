"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm.query import Query
from models import Alert, db

logger = logging.getLogger('alert')

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
    
    # 处理 time 字段（转换为字符串格式）
    if alert.time is not None and hasattr(alert.time, 'strftime'):
        result['time'] = alert.time.strftime('%Y-%m-%d %H:%M:%S')
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
    
    return result

def _get_alert_filter_query(args: dict) -> Query:
    """构建报警查询过滤器"""
    query: Query = Alert.query

    if 'object' in args and args['object']:
        query = query.filter(Alert.object == args['object'])
    if 'event' in args and args['event']:
        query = query.filter(Alert.event == args['event'])
    if 'device_id' in args and args['device_id']:
        query = query.filter(Alert.device_id == args['device_id'])
    if 'task_type' in args and args['task_type']:
        query = query.filter(Alert.task_type == args['task_type'])
    if 'begin_datetime' in args and args['begin_datetime']:
        query = query.filter(Alert.time >= datetime.strptime(args['begin_datetime'], '%Y-%m-%d %H:%M:%S'))
    if 'end_datetime' in args and args['end_datetime']:
        query = query.filter(Alert.time <= datetime.strptime(args['end_datetime'], '%Y-%m-%d %H:%M:%S'))

    return query


def get_alert_list(args: dict) -> dict:
    """获取报警列表
    
    Args:
        args: 查询参数字典，支持以下参数：
            - pageNo: 页码（可选）
            - pageSize: 每页数量（可选，如果提供则启用分页）
            - object: 对象类型过滤（可选）
            - event: 事件类型过滤（可选）
            - device_id: 设备ID过滤（可选）
            - task_type: 任务类型过滤（可选，'realtime'或'snap'）
            - begin_datetime: 开始时间过滤，格式：'YYYY-MM-DD HH:MM:SS'（可选）
            - end_datetime: 结束时间过滤，格式：'YYYY-MM-DD HH:MM:SS'（可选）
    
    Returns:
        dict: 包含 alert_list 和 total 的字典
    """
    query = _get_alert_filter_query(args).order_by(Alert.time.desc())

    if 'pageSize' in args and args['pageSize']:
        try:
            page_no = int(args.get('pageNo') or 1)
            page_size = int(args['pageSize'])
            paginate = query.paginate(page=page_no, per_page=page_size, error_out=False)
            return {
                'alert_list': [_alert_to_dict(alert) for alert in paginate.items],
                'total': paginate.total
            }
        except ValueError as e:
            logger.error(f'分页查询失败: {str(e)}')
            return {'alert_list': [], 'total': 0}
    else:
        alerts = query.all()
        return {
            'alert_list': [_alert_to_dict(alert) for alert in alerts],
            'total': len(alerts)
        }


def get_alert_count(args: dict) -> dict:
    """获取报警统计
    
    Args:
        args: 查询参数字典，支持以下参数：
            - group: 分组方式，可选值：'date'（按日期）、'device'（按设备）、'object'（按对象）
            - object: 对象类型过滤（可选）
            - event: 事件类型过滤（可选）
            - device_id: 设备ID过滤（可选）
            - begin_datetime: 开始时间过滤（可选）
            - end_datetime: 结束时间过滤（可选）
    
    Returns:
        dict: 包含 count_list 和 total_count 的字典
    """
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
        
        # 处理时间字段
        if 'time' in alert_data and alert_data['time']:
            if isinstance(alert_data['time'], str):
                alert_time = datetime.strptime(alert_data['time'], '%Y-%m-%d %H:%M:%S')
            else:
                alert_time = alert_data['time']
        else:
            alert_time = datetime.now()
        
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
        
        # 创建报警记录
        alert = Alert(
            object=alert_data['object'],
            event=alert_data['event'],
            device_id=alert_data['device_id'],
            device_name=alert_data['device_name'],
            region=alert_data.get('region'),
            information=information,
            time=alert_time,
            image_path=alert_data.get('image_path'),
            record_path=alert_data.get('record_path'),
            task_type=task_type,
            notify_users=notify_users,
            channels=channels
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return _alert_to_dict(alert)
    except ValueError as e:
        logger.error(f'创建报警记录参数错误: {str(e)}')
        db.session.rollback()
        raise
    except Exception as e:
        logger.error(f'创建报警记录失败: {str(e)}')
        db.session.rollback()
        raise


def patch_alerts_record(dvr_info: dict):
    """更新报警记录的录像路径
    
    Args:
        dvr_info: DVR信息字典，包含以下字段：
            - event_time: 事件时间，格式：'YYYY-MM-DD HH:MM:SS'
            - duration: 持续时间（秒）
            - device_id: 设备ID
            - file_path: 录像文件路径
    """
    try:
        begin_time = datetime.strptime(dvr_info['event_time'], '%Y-%m-%d %H:%M:%S')
        end_time = begin_time + timedelta(seconds=dvr_info['duration'])

        alerts = Alert.query.filter(
            Alert.time >= begin_time,
            Alert.time <= end_time,
            Alert.device_id == dvr_info['device_id'],
            Alert.record_path.is_(None)
        ).all()

        if alerts:
            dvr_path = dvr_info['file_path']
            for alert in alerts:
                alert.record_path = dvr_path
            db.session.commit()
            logger.info(f'成功更新 {len(alerts)} 条报警记录的录像路径')
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
