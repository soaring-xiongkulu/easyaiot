"""
从 SRS/ZLM Hook 数据中解析 device_id。
"""
import logging
import os
from typing import Optional, Tuple

from models import AlgorithmTask, Device
from app.utils.algorithm_task_identity import build_task_stream_key, parse_task_stream_key

logger = logging.getLogger(__name__)


def parse_infer_stream_device_id(stream: str) -> Optional[str]:
    """AI 推理输出流 infer_{device_id}_m{model_suffix} → device_id。"""
    if not stream or not stream.startswith('infer_'):
        return None
    rest = stream[6:]
    sep = rest.find('_m')
    if sep <= 0:
        return None
    device_id = rest[:sep]
    return device_id or None


def parse_task_stream_identity(stream: str) -> Tuple[Optional[int], Optional[str]]:
    """解析任务级画框流，安全设备片段只用于诊断，真实设备需通过任务关联反查。"""
    return parse_task_stream_key(stream)


def _resolve_task_stream_device(stream: str) -> Tuple[Optional[int], Optional[str], Optional[Device]]:
    """通过任务关联反查任务流对应设备，兼容设备 ID 被安全化且不可逆的情况。"""
    task_id, _safe_device_part = parse_task_stream_identity(stream)
    if not task_id:
        return None, None, None
    task = AlgorithmTask.query.get(task_id)
    if not task:
        return task_id, None, None
    for device in task.devices or []:
        if build_task_stream_key(task_id, device.id) == stream:
            return task_id, device.id, device
    return task_id, None, None


def resolve_stream_identity_from_hook(
    stream: str,
    file_path: str = '',
) -> Tuple[Optional[int], Optional[str], Optional[Device]]:
    """返回 ``(task_id, device_id, Device)``，旧设备流的 task_id 为 None。"""
    task_id, device_id, device = _resolve_task_stream_device(stream or '')
    if device:
        return task_id, device_id, device
    path_task_id, path_device_id, path_device = _resolve_task_stream_from_file_path(file_path)
    if path_device:
        return path_task_id, path_device_id, path_device
    resolved_device_id, resolved_device = _resolve_legacy_device_from_hook(stream, file_path)
    return task_id, resolved_device_id, resolved_device


def resolve_device_from_hook(
    stream: str,
    file_path: str = '',
) -> Tuple[Optional[str], Optional[Device]]:
    """返回 (device_id, Device)，未找到时 device 为 None。"""
    _task_id, device_id, device = resolve_stream_identity_from_hook(stream, file_path)
    return device_id, device


def _resolve_legacy_device_from_hook(
    stream: str,
    file_path: str = '',
) -> Tuple[Optional[str], Optional[Device]]:
    """解析旧版设备级或 infer 流。"""
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
        _task_id, task_device_id, task_device = _resolve_task_stream_device(potential_id)
        if task_device:
            return task_device_id, task_device
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


def _resolve_task_stream_from_file_path(
    file_path: str,
) -> Tuple[Optional[int], Optional[str], Optional[Device]]:
    """从 SRS DVR 路径恢复任务流身份，兼容 Hook 缺失 stream 字段。"""
    if not file_path:
        return None, None, None
    try:
        path_parts = [part for part in file_path.replace('\\', '/').split('/') if part]
        if 'playbacks' not in path_parts:
            return None, None, None
        playback_index = path_parts.index('playbacks')
        if playback_index + 2 >= len(path_parts):
            return None, None, None
        return _resolve_task_stream_device(path_parts[playback_index + 2])
    except Exception as exc:
        logger.debug('从录像路径解析任务流失败 file_path=%s error=%s', file_path, exc)
        return None, None, None
