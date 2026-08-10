"""
从 SRS/ZLM Hook 数据中解析 device_id。
"""
import logging
import os
from typing import Optional, Tuple

from models import Device

logger = logging.getLogger(__name__)


def parse_infer_stream_device_id(stream: str) -> Optional[str]:
    """AI 推理输出流 infer_{device_id}_m{model_suffix} → device_id。"""
    if not stream or not stream.startswith('infer_'):
        return None
    rest = stream[6:]
    sep = rest.rfind('_m')
    if sep <= 0:
        return None
    device_id = rest[:sep]
    return device_id or None


def resolve_device_from_hook(
    stream: str,
    file_path: str = '',
) -> Tuple[Optional[str], Optional[Device]]:
    """返回 (device_id, Device)，未找到时 device 为 None。"""
    if not stream and not file_path:
        return None, None

    device_id = stream or ''
    device = Device.query.get(device_id) if device_id else None

    if not device and stream:
        infer_device_id = parse_infer_stream_device_id(stream)
        if infer_device_id:
            device = Device.query.get(infer_device_id)
            if device:
                device_id = infer_device_id

    if not device and stream.startswith('live/'):
        potential_id = stream[5:]
        device = Device.query.get(potential_id)
        if device:
            device_id = potential_id

    if not device and stream:
        patterns = [
            f'live/{stream}',
            stream,
            f'/live/{stream}',
            f'/{stream}',
            f'live/{stream}/',
            f'{stream}/',
        ]
        for pattern in patterns:
            device = Device.query.filter(Device.rtmp_stream.like(f'%{pattern}%')).first()
            if device:
                device_id = device.id
                break

    if not device and file_path:
        device_id, device = _resolve_from_file_path(file_path, device_id)

    return (device_id if device else None), device


def _resolve_from_file_path(file_path: str, fallback_id: str) -> Tuple[Optional[str], Optional[Device]]:
    try:
        path_parts = [p for p in file_path.replace('\\', '/').split('/') if p]
        if 'playbacks' not in path_parts:
            return None, None
        pi = path_parts.index('playbacks')
        if pi + 2 >= len(path_parts):
            return None, None
        potential_id = path_parts[pi + 2]
        infer_device_id = parse_infer_stream_device_id(potential_id)
        if infer_device_id:
            device = Device.query.get(infer_device_id)
            if device:
                return infer_device_id, device
        device = Device.query.get(potential_id)
        if device:
            return potential_id, device
        app_name = path_parts[pi + 1] if pi + 1 < len(path_parts) else ''
        for pattern in [
            f'{app_name}/{potential_id}',
            f'live/{potential_id}',
            potential_id,
            f'/live/{potential_id}',
            f'/{potential_id}',
        ]:
            device = Device.query.filter(Device.rtmp_stream.like(f'%{pattern}%')).first()
            if device:
                return device.id, device
    except Exception as e:
        logger.debug('从文件路径解析设备失败 file_path=%s error=%s', file_path, e)
    return fallback_id or None, None
