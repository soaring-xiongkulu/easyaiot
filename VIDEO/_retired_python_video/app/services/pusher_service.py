"""
推送器管理服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import uuid
import json
from datetime import datetime
from typing import Optional

from models import db, Pusher

logger = logging.getLogger(__name__)


def create_pusher(pusher_name: str,
                  video_stream_enabled: bool = False,
                  video_stream_url: Optional[str] = None,
                  device_rtmp_mapping: Optional[dict] = None,
                  video_stream_format: str = 'rtmp',
                  video_stream_quality: str = 'high',
                  event_alert_enabled: bool = False,
                  event_alert_url: Optional[str] = None,
                  event_alert_method: str = 'http',
                  event_alert_format: str = 'json',
                  event_alert_headers: Optional[str] = None,
                  event_alert_template: Optional[str] = None,
                  description: Optional[str] = None,
                  is_enabled: bool = True) -> Pusher:
    """创建推送器"""
    try:
        # 生成唯一编号
        pusher_code = f"PUSHER_{uuid.uuid4().hex[:8].upper()}"
        
        # 验证并格式化请求头
        headers_json = None
        if event_alert_headers:
            try:
                if isinstance(event_alert_headers, str):
                    json.loads(event_alert_headers)  # 验证JSON格式
                    headers_json = event_alert_headers
                else:
                    headers_json = json.dumps(event_alert_headers)
            except json.JSONDecodeError:
                raise ValueError("事件告警请求头必须是有效的JSON格式")
        
        # 验证并格式化模板
        template_json = None
        if event_alert_template:
            try:
                if isinstance(event_alert_template, str):
                    json.loads(event_alert_template)  # 验证JSON格式
                    template_json = event_alert_template
                else:
                    template_json = json.dumps(event_alert_template)
            except json.JSONDecodeError:
                raise ValueError("事件告警模板必须是有效的JSON格式")
        
        # 验证并格式化多摄像头RTMP映射
        device_rtmp_mapping_json = None
        if device_rtmp_mapping:
            try:
                if isinstance(device_rtmp_mapping, str):
                    json.loads(device_rtmp_mapping)  # 验证JSON格式
                    device_rtmp_mapping_json = device_rtmp_mapping
                else:
                    device_rtmp_mapping_json = json.dumps(device_rtmp_mapping)
            except json.JSONDecodeError:
                raise ValueError("多摄像头RTMP映射必须是有效的JSON格式")
        
        pusher = Pusher(
            pusher_name=pusher_name,
            pusher_code=pusher_code,
            video_stream_enabled=video_stream_enabled,
            video_stream_url=video_stream_url,
            device_rtmp_mapping=device_rtmp_mapping_json,
            video_stream_format=video_stream_format,
            video_stream_quality=video_stream_quality,
            event_alert_enabled=event_alert_enabled,
            event_alert_url=event_alert_url,
            event_alert_method=event_alert_method,
            event_alert_format=event_alert_format,
            event_alert_headers=headers_json,
            event_alert_template=template_json,
            description=description,
            is_enabled=is_enabled
        )
        
        db.session.add(pusher)
        db.session.commit()
        
        logger.info(f"创建推送器成功: pusher_id={pusher.id}, pusher_name={pusher_name}")
        return pusher
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建推送器失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建推送器失败: {str(e)}")


def update_pusher(pusher_id: int, **kwargs) -> Pusher:
    """更新推送器"""
    try:
        pusher = Pusher.query.get_or_404(pusher_id)
        
        # 处理JSON字段
        if 'event_alert_headers' in kwargs:
            headers = kwargs['event_alert_headers']
            if headers:
                try:
                    if isinstance(headers, str):
                        json.loads(headers)  # 验证JSON格式
                        kwargs['event_alert_headers'] = headers
                    else:
                        kwargs['event_alert_headers'] = json.dumps(headers)
                except json.JSONDecodeError:
                    raise ValueError("事件告警请求头必须是有效的JSON格式")
        
        if 'event_alert_template' in kwargs:
            template = kwargs['event_alert_template']
            if template:
                try:
                    if isinstance(template, str):
                        json.loads(template)  # 验证JSON格式
                        kwargs['event_alert_template'] = template
                    else:
                        kwargs['event_alert_template'] = json.dumps(template)
                except json.JSONDecodeError:
                    raise ValueError("事件告警模板必须是有效的JSON格式")
        
        # 处理多摄像头RTMP映射
        if 'device_rtmp_mapping' in kwargs:
            mapping = kwargs['device_rtmp_mapping']
            if mapping:
                try:
                    if isinstance(mapping, str):
                        json.loads(mapping)  # 验证JSON格式
                        kwargs['device_rtmp_mapping'] = mapping
                    else:
                        kwargs['device_rtmp_mapping'] = json.dumps(mapping)
                except json.JSONDecodeError:
                    raise ValueError("多摄像头RTMP映射必须是有效的JSON格式")
        
        updatable_fields = [
            'pusher_name', 'video_stream_enabled', 'video_stream_url',
            'device_rtmp_mapping', 'video_stream_format', 'video_stream_quality',
            'event_alert_enabled', 'event_alert_url', 'event_alert_method',
            'event_alert_format', 'event_alert_headers', 'event_alert_template',
            'description', 'is_enabled'
        ]
        
        for field in updatable_fields:
            if field in kwargs:
                setattr(pusher, field, kwargs[field])
        
        pusher.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"更新推送器成功: pusher_id={pusher_id}")
        return pusher
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新推送器失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"更新推送器失败: {str(e)}")


def delete_pusher(pusher_id: int):
    """删除推送器"""
    try:
        pusher = Pusher.query.get_or_404(pusher_id)
        db.session.delete(pusher)
        db.session.commit()
        
        logger.info(f"删除推送器成功: pusher_id={pusher_id}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除推送器失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"删除推送器失败: {str(e)}")


def get_pusher(pusher_id: int) -> Pusher:
    """获取推送器详情"""
    try:
        pusher = Pusher.query.get_or_404(pusher_id)
        return pusher
    except Exception as e:
        logger.error(f"获取推送器失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取推送器失败: {str(e)}")


def list_pushers(page_no: int = 1, page_size: int = 10,
                search: Optional[str] = None,
                is_enabled: Optional[bool] = None) -> dict:
    """查询推送器列表"""
    try:
        query = Pusher.query
        
        if search:
            query = query.filter(
                db.or_(
                    Pusher.pusher_name.like(f'%{search}%'),
                    Pusher.pusher_code.like(f'%{search}%')
                )
            )
        
        if is_enabled is not None:
            query = query.filter_by(is_enabled=is_enabled)
        
        total = query.count()
        
        # 分页
        offset = (page_no - 1) * page_size
        pushers = query.order_by(
            Pusher.created_at.desc()
        ).offset(offset).limit(page_size).all()
        
        return {
            'items': [pusher.to_dict() for pusher in pushers],
            'total': total
        }
    except Exception as e:
        logger.error(f"查询推送器列表失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"查询推送器列表失败: {str(e)}")

