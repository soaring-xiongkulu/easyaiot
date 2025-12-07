"""
设备区域检测服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

from models import db, DeviceDetectionRegion, Device, Image

logger = logging.getLogger(__name__)


def get_device_regions(device_id: str) -> List[DeviceDetectionRegion]:
    """获取设备的所有检测区域"""
    try:
        regions = DeviceDetectionRegion.query.filter_by(device_id=device_id).order_by(DeviceDetectionRegion.sort_order).all()
        return regions
    except Exception as e:
        logger.error(f"获取设备检测区域失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取设备检测区域失败: {str(e)}")


def create_device_region(device_id: str, region_name: str, region_type: str, points: List[Dict],
                        image_id: Optional[int] = None, color: str = '#FF5252', opacity: float = 0.3,
                        is_enabled: bool = True, sort_order: int = 0, model_ids: Optional[List[int]] = None) -> DeviceDetectionRegion:
    """创建设备检测区域"""
    try:
        # 验证设备是否存在
        device = Device.query.get(device_id)
        if not device:
            raise ValueError(f"设备不存在: {device_id}")
        
        # 验证图片是否存在（如果提供了image_id）
        if image_id:
            image = Image.query.get(image_id)
            if not image:
                raise ValueError(f"图片不存在: {image_id}")
        
        # 将points转换为JSON字符串
        points_json = json.dumps(points)
        
        # 处理 model_ids
        model_ids_json = None
        if model_ids:
            if isinstance(model_ids, list) and len(model_ids) > 0:
                model_ids_json = json.dumps(model_ids)
            elif isinstance(model_ids, str):
                # 如果已经是JSON字符串，验证格式
                try:
                    parsed = json.loads(model_ids)
                    if isinstance(parsed, list):
                        model_ids_json = model_ids
                except:
                    pass
        
        region = DeviceDetectionRegion(
            device_id=device_id,
            region_name=region_name,
            region_type=region_type,
            points=points_json,
            image_id=image_id,
            color=color,
            opacity=opacity,
            is_enabled=is_enabled,
            sort_order=sort_order,
            model_ids=model_ids_json
        )
        
        db.session.add(region)
        db.session.commit()
        
        logger.info(f"创建设备检测区域成功: device_id={device_id}, region_name={region_name}")
        return region
    except ValueError as e:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建设备检测区域失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建设备检测区域失败: {str(e)}")


def update_device_region(region_id: int, **kwargs) -> DeviceDetectionRegion:
    """更新设备检测区域"""
    try:
        region = DeviceDetectionRegion.query.get(region_id)
        if not region:
            raise ValueError(f"检测区域不存在: {region_id}")
        
        # 更新字段
        if 'region_name' in kwargs:
            region.region_name = kwargs['region_name']
        if 'region_type' in kwargs:
            region.region_type = kwargs['region_type']
        if 'points' in kwargs:
            if isinstance(kwargs['points'], list):
                region.points = json.dumps(kwargs['points'])
            else:
                region.points = kwargs['points']
        if 'image_id' in kwargs:
            if kwargs['image_id']:
                image = Image.query.get(kwargs['image_id'])
                if not image:
                    raise ValueError(f"图片不存在: {kwargs['image_id']}")
            region.image_id = kwargs['image_id']
        if 'color' in kwargs:
            region.color = kwargs['color']
        if 'opacity' in kwargs:
            region.opacity = kwargs['opacity']
        if 'is_enabled' in kwargs:
            region.is_enabled = kwargs['is_enabled']
        if 'sort_order' in kwargs:
            region.sort_order = kwargs['sort_order']
        if 'model_ids' in kwargs:
            model_ids = kwargs['model_ids']
            if model_ids:
                if isinstance(model_ids, list) and len(model_ids) > 0:
                    region.model_ids = json.dumps(model_ids)
                elif isinstance(model_ids, str):
                    # 如果已经是JSON字符串，验证格式
                    try:
                        parsed = json.loads(model_ids)
                        if isinstance(parsed, list):
                            region.model_ids = model_ids
                        else:
                            region.model_ids = None
                    except:
                        region.model_ids = None
                else:
                    region.model_ids = None
            else:
                region.model_ids = None
        
        region.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"更新设备检测区域成功: region_id={region_id}")
        return region
    except ValueError as e:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新设备检测区域失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"更新设备检测区域失败: {str(e)}")


def delete_device_region(region_id: int) -> bool:
    """删除设备检测区域"""
    try:
        region = DeviceDetectionRegion.query.get(region_id)
        if not region:
            raise ValueError(f"检测区域不存在: {region_id}")
        
        db.session.delete(region)
        db.session.commit()
        
        logger.info(f"删除设备检测区域成功: region_id={region_id}")
        return True
    except ValueError as e:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除设备检测区域失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"删除设备检测区域失败: {str(e)}")


def update_device_cover_image(device_id: str, image_path: str) -> Device:
    """更新设备封面图"""
    try:
        device = Device.query.get(device_id)
        if not device:
            raise ValueError(f"设备不存在: {device_id}")
        
        device.cover_image_path = image_path
        device.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"更新设备封面图成功: device_id={device_id}, image_path={image_path}")
        return device
    except ValueError as e:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新设备封面图失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"更新设备封面图失败: {str(e)}")

