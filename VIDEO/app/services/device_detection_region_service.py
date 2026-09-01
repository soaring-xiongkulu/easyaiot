"""
设备区域检测服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
import logging
import math
from typing import List, Dict, Optional
from datetime import datetime

from models import db, DeviceDetectionRegion, Device, Image, AlgorithmTask
from app.utils.region_hit_mode import normalize_region_hit_config

logger = logging.getLogger(__name__)


class RegionRevisionConflict(ValueError):
    """区域配置已被其他请求修改。"""


def _parse_model_ids(raw) -> List[int]:
    if not raw:
        return []
    try:
        values = json.loads(raw) if isinstance(raw, str) else list(raw)
        return sorted({int(value) for value in values if value is not None})
    except (TypeError, ValueError, json.JSONDecodeError):
        return []


def _segments_intersect(a, b, c, d) -> bool:
    def orient(p, q, r):
        return (q['x'] - p['x']) * (r['y'] - p['y']) - (q['y'] - p['y']) * (r['x'] - p['x'])

    def on_segment(p, q, r):
        eps = 1e-12
        return (
            min(p['x'], r['x']) - eps <= q['x'] <= max(p['x'], r['x']) + eps
            and min(p['y'], r['y']) - eps <= q['y'] <= max(p['y'], r['y']) + eps
        )

    eps = 1e-12
    o1, o2 = orient(a, b, c), orient(a, b, d)
    o3, o4 = orient(c, d, a), orient(c, d, b)
    if ((o1 > eps and o2 < -eps) or (o2 > eps and o1 < -eps)) and (
        (o3 > eps and o4 < -eps) or (o4 > eps and o3 < -eps)
    ):
        return True
    return (
        (abs(o1) <= eps and on_segment(a, c, b))
        or (abs(o2) <= eps and on_segment(a, d, b))
        or (abs(o3) <= eps and on_segment(c, a, d))
        or (abs(o4) <= eps and on_segment(c, b, d))
    )


def _validate_points(region_type: str, raw_points) -> List[Dict[str, float]]:
    if not isinstance(raw_points, list):
        raise ValueError('区域坐标点必须是数组')
    expected = {'line': 2, 'rectangle': 4}
    if region_type == 'polygon' and len(raw_points) < 3:
        raise ValueError('多边形区域至少需要3个点')
    if region_type in expected and len(raw_points) != expected[region_type]:
        raise ValueError(f'{region_type} 区域必须包含{expected[region_type]}个点')
    if len(raw_points) > 64:
        raise ValueError('单个区域最多支持64个点')
    points = []
    for raw in raw_points:
        if not isinstance(raw, dict) or 'x' not in raw or 'y' not in raw:
            raise ValueError('区域坐标点必须包含x、y')
        try:
            x, y = float(raw['x']), float(raw['y'])
        except (TypeError, ValueError):
            raise ValueError('区域坐标必须是数值')
        if not math.isfinite(x) or not math.isfinite(y) or not (0 <= x <= 1 and 0 <= y <= 1):
            raise ValueError('区域坐标必须位于0到1之间')
        points.append({'x': x, 'y': y})
    if region_type != 'line':
        area = abs(sum(
            points[i]['x'] * points[(i + 1) % len(points)]['y']
            - points[(i + 1) % len(points)]['x'] * points[i]['y']
            for i in range(len(points))
        )) / 2
        if area <= 1e-9:
            raise ValueError('区域面积必须大于0')
        n = len(points)
        for i in range(n):
            for j in range(i + 1, n):
                if j in (i, i + 1) or (i == 0 and j == n - 1):
                    continue
                if _segments_intersect(points[i], points[(i + 1) % n], points[j], points[(j + 1) % n]):
                    raise ValueError('区域边界不能自相交')
    return points


def _normalize_region_payload(data: Dict, task: AlgorithmTask, *, default_sort_order: int = 0) -> Dict:
    region_type = str(data.get('region_type') or 'polygon').strip().lower()
    if region_type not in ('polygon', 'rectangle', 'line'):
        raise ValueError('区域类型必须是 polygon、rectangle 或 line')
    region_name = str(data.get('region_name') or '').strip()
    if not region_name:
        raise ValueError('区域名称不能为空')
    points = _validate_points(region_type, data.get('points'))

    task_models = {model_id for model_id in _parse_model_ids(task.model_ids) if model_id != 0}
    model_scope = str(data.get('model_scope') or ('selected' if data.get('model_ids') else 'all')).lower()
    if model_scope not in ('all', 'selected'):
        raise ValueError('model_scope 必须是 all 或 selected')
    model_ids = [] if model_scope == 'all' else _parse_model_ids(data.get('model_ids'))
    if model_scope == 'selected' and not model_ids:
        raise ValueError('指定模型区域至少选择一个模型')
    foreign = sorted(set(model_ids) - task_models)
    if foreign:
        raise ValueError(f'区域模型不属于算法任务: {foreign}')
    if 0 in model_ids:
        raise ValueError('模型ID 0不是有效的业务模型ID')

    try:
        opacity = float(data.get('opacity', 0.3))
        sort_order = int(data.get('sort_order', default_sort_order))
    except (TypeError, ValueError):
        raise ValueError('透明度或排序值格式错误')
    if not 0 <= opacity <= 1:
        raise ValueError('区域透明度必须位于0到1之间')
    if sort_order < 0:
        raise ValueError('区域排序值不能小于0')

    hit_mode, min_overlap_ratio = normalize_region_hit_config(
        data.get('hit_mode'),
        data.get('min_overlap_ratio'),
    )

    image_id = data.get('image_id')
    if image_id:
        image = Image.query.get(image_id)
        if not image:
            raise ValueError(f'图片不存在: {image_id}')
        if getattr(image, 'device_id', None) and str(image.device_id) != str(data.get('device_id') or ''):
            # device_id is injected by the batch service below before validation.
            raise ValueError('参考图片不属于当前设备')
    return {
        'region_name': region_name,
        'region_type': region_type,
        'points': json.dumps(points, ensure_ascii=False),
        'image_id': image_id,
        'color': str(data.get('color') or '#FF5252'),
        'opacity': opacity,
        'is_enabled': bool(data.get('is_enabled', True)),
        'sort_order': sort_order,
        'model_ids': json.dumps(model_ids) if model_ids else None,
        'hit_mode': hit_mode,
        'min_overlap_ratio': min_overlap_ratio,
    }


def _bump_template_revision(task: AlgorithmTask) -> int:
    task.template_revision = int(getattr(task, 'template_revision', 1) or 1) + 1
    return task.template_revision


def replace_device_regions(device_id: str, task_id: int, regions_data: List[Dict],
                           expected_revision: int) -> tuple[List[DeviceDetectionRegion], int]:
    """原子替换任务设备的全部区域，并以任务模板版本做乐观锁。"""
    if not isinstance(regions_data, list):
        raise ValueError('regions 必须是数组')
    if len(regions_data) > 100:
        raise ValueError('单任务单设备最多支持100个区域')
    try:
        task = AlgorithmTask.query.filter_by(id=task_id).with_for_update().first()
        if not task:
            raise ValueError(f'算法任务不存在: {task_id}')
        _validate_task_device(task_id, device_id)
        current_revision = int(getattr(task, 'template_revision', 1) or 1)
        if int(expected_revision) != current_revision:
            raise RegionRevisionConflict(
                f'区域配置已更新，请重新加载（当前版本 {current_revision}）'
            )
        task_model_ids = _parse_model_ids(task.model_ids)
        if not task_model_ids or 0 in task_model_ids:
            raise ValueError('该算法任务未配置算法模型列表，无法配置区域检测')

        existing = DeviceDetectionRegion.query.filter_by(task_id=task_id, device_id=device_id).all()
        existing_by_id = {row.id: row for row in existing}
        retained_ids = set()
        seen_region_ids = set()
        saved = []
        for index, raw in enumerate(regions_data):
            if not isinstance(raw, dict):
                raise ValueError('区域配置项必须是对象')
            payload = dict(raw)
            payload['device_id'] = device_id
            normalized = _normalize_region_payload(payload, task, default_sort_order=index)
            raw_id = raw.get('id')
            region_id = int(raw_id) if raw_id is not None else 0
            if region_id > 0:
                if region_id in seen_region_ids:
                    raise ValueError(f'区域 {region_id} 在请求中重复')
                seen_region_ids.add(region_id)
                region = existing_by_id.get(region_id)
                if not region:
                    raise ValueError(f'区域 {region_id} 不属于当前任务和设备')
                retained_ids.add(region_id)
            else:
                region = DeviceDetectionRegion(task_id=task_id, device_id=device_id)
                db.session.add(region)
            for key, value in normalized.items():
                setattr(region, key, value)
            region.updated_at = datetime.utcnow()
            saved.append(region)

        for region in existing:
            if region.id not in retained_ids:
                db.session.delete(region)
        new_revision = _bump_template_revision(task)
        db.session.commit()
        return saved, new_revision
    except Exception:
        db.session.rollback()
        raise


def _validate_task_device(task_id: int, device_id: str) -> AlgorithmTask:
    """校验任务存在且设备属于该任务"""
    task = AlgorithmTask.query.get(task_id)
    if not task:
        raise ValueError(f"算法任务不存在: {task_id}")

    device = Device.query.get(device_id)
    if not device:
        raise ValueError(f"设备不存在: {device_id}")

    task_device_ids = {d.id for d in (task.devices or [])}
    if device_id not in task_device_ids:
        raise ValueError(f"设备 {device_id} 不属于算法任务 {task_id}")

    return task


def get_device_regions(device_id: str, task_id: int) -> List[DeviceDetectionRegion]:
    """获取指定任务下设备的检测区域"""
    try:
        _validate_task_device(task_id, device_id)
        regions = DeviceDetectionRegion.query.filter_by(
            device_id=device_id,
            task_id=task_id,
        ).order_by(DeviceDetectionRegion.sort_order).all()
        return regions
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"获取设备检测区域失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取设备检测区域失败: {str(e)}")


def create_device_region(device_id: str, task_id: int, region_name: str, region_type: str, points: List[Dict],
                        image_id: Optional[int] = None, color: str = '#FF5252', opacity: float = 0.3,
                        is_enabled: bool = True, sort_order: int = 0, model_ids: Optional[List[int]] = None,
                        hit_mode: str = 'center', min_overlap_ratio: float = 0.5) -> DeviceDetectionRegion:
    """创建设备检测区域（绑定到算法任务）"""
    try:
        task = _validate_task_device(task_id, device_id)
        normalized = _normalize_region_payload({
            'device_id': device_id,
            'region_name': region_name,
            'region_type': region_type,
            'points': points,
            'image_id': image_id,
            'color': color,
            'opacity': opacity,
            'is_enabled': is_enabled,
            'sort_order': sort_order,
            'model_scope': 'selected' if model_ids else 'all',
            'model_ids': model_ids,
            'hit_mode': hit_mode,
            'min_overlap_ratio': min_overlap_ratio,
        }, task, default_sort_order=sort_order)

        region = DeviceDetectionRegion(task_id=task_id, device_id=device_id, **normalized)

        db.session.add(region)
        _bump_template_revision(task)
        db.session.commit()

        logger.info(f"创建设备检测区域成功: task_id={task_id}, device_id={device_id}, region_name={region_name}")
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
        if not region.task_id:
            raise ValueError('历史区域未绑定算法任务，不能直接更新')
        task = _validate_task_device(region.task_id, region.device_id)
        try:
            current_points = json.loads(region.points) if region.points else []
        except (TypeError, json.JSONDecodeError):
            current_points = []
        current_model_ids = _parse_model_ids(region.model_ids)
        payload = {
            'device_id': region.device_id,
            'region_name': region.region_name,
            'region_type': region.region_type,
            'points': current_points,
            'image_id': region.image_id,
            'color': region.color,
            'opacity': region.opacity,
            'is_enabled': region.is_enabled,
            'sort_order': region.sort_order,
            'model_scope': 'selected' if current_model_ids else 'all',
            'model_ids': current_model_ids,
            'hit_mode': getattr(region, 'hit_mode', None) or 'center',
            'min_overlap_ratio': (
                getattr(region, 'min_overlap_ratio', None)
                if getattr(region, 'min_overlap_ratio', None) is not None
                else 0.5
            ),
        }
        payload.update(kwargs)
        payload['device_id'] = region.device_id
        if 'model_ids' in kwargs and 'model_scope' not in kwargs:
            payload['model_scope'] = 'selected' if kwargs.get('model_ids') else 'all'
        normalized = _normalize_region_payload(payload, task, default_sort_order=region.sort_order or 0)
        for key, value in normalized.items():
            setattr(region, key, value)

        region.updated_at = datetime.utcnow()
        _bump_template_revision(task)
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

        task = AlgorithmTask.query.get(region.task_id) if region.task_id else None
        db.session.delete(region)
        if task:
            _bump_template_revision(task)
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
