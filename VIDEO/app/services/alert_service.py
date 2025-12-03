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
    if alert.information is not None:
        if isinstance(alert.information, str):
            try:
                result['information'] = json.loads(alert.information)
            except (json.JSONDecodeError, TypeError):
                result['information'] = alert.information
        else:
            result['information'] = alert.information
    else:
        result['information'] = None
    
    # 处理 time 字段（转换为字符串格式）
    if alert.time is not None and hasattr(alert.time, 'strftime'):
        result['time'] = alert.time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        result['time'] = alert.time
    
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
                information = json.dumps(information, ensure_ascii=False)
        
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
            record_path=alert_data.get('record_path')
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
