"""算法任务运行时身份与任务级流地址工具。"""
from __future__ import annotations

import hashlib
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit


_SAFE_STREAM_PART_PATTERN = re.compile(r'[^A-Za-z0-9._-]+')
_TASK_STREAM_KEY_PATTERN = re.compile(r'^t([1-9]\d*)_([A-Za-z0-9._-]+)$')


class AmbiguousAlgorithmTaskError(ValueError):
    """告警缺少任务身份且数据库中存在多个候选任务。"""


def normalize_algorithm_task_type(task_type: Optional[str]) -> str:
    """统一算法任务类型，兼容旧版 snapshot 表达。"""
    normalized = str(task_type or 'realtime').strip().lower()
    return 'snap' if normalized == 'snapshot' else normalized


def _safe_device_stream_part(device_id: str) -> str:
    """生成 SRS 可安全使用且不会因清洗产生歧义的设备标识。"""
    original = str(device_id or '').strip()
    if not original:
        raise ValueError('device_id 不能为空')

    safe = _SAFE_STREAM_PART_PATTERN.sub('-', original).strip('-') or 'device'
    if safe == original:
        return safe

    digest = hashlib.sha1(original.encode('utf-8')).hexdigest()[:8]
    return f'{safe}_{digest}'


def build_task_stream_key(task_id: int, device_id: str) -> str:
    """构建任务与摄像头唯一的 SRS stream key。"""
    try:
        normalized_task_id = int(task_id)
    except (TypeError, ValueError) as exc:
        raise ValueError('task_id 必须是整数') from exc
    if normalized_task_id <= 0:
        raise ValueError('task_id 必须大于 0')
    return f't{normalized_task_id}_{_safe_device_stream_part(device_id)}'


def parse_task_stream_key(stream_key: str) -> Tuple[Optional[int], Optional[str]]:
    """解析任务级 SRS stream key，返回任务ID和安全设备片段。"""
    match = _TASK_STREAM_KEY_PATTERN.fullmatch(str(stream_key or '').strip())
    if not match:
        return None, None
    return int(match.group(1)), match.group(2)


def rewrite_task_stream_url(
        base_url: Optional[str],
        task_id: int,
        device_id: str,
) -> Optional[str]:
    """保留现有协议、主机和应用名，将摄像头公共流改写为任务独立流。"""
    raw_url = str(base_url or '').strip()
    if not raw_url:
        return None

    parsed = urlsplit(raw_url)
    stream_key = build_task_stream_key(task_id, device_id)
    path_parts = [part for part in parsed.path.split('/') if part]
    app_name = path_parts[0] if path_parts else 'ai'
    old_stream_name = path_parts[-1] if path_parts else ''
    extension = '.flv' if old_stream_name.lower().endswith('.flv') else ''
    new_path = f'/{app_name}/{stream_key}{extension}'
    return urlunsplit((parsed.scheme, parsed.netloc, new_path, parsed.query, parsed.fragment))


def build_alert_suppression_key(
        task_id: int,
        device_id: str,
        task_type: Optional[str],
        event_identity: Optional[str] = None,
) -> Tuple[str, ...]:
    """构建任务及事件级告警抑制键，防止不同任务或模型事件互相压制。"""
    if task_id is None or str(task_id).strip() == '':
        raise ValueError('task_id 不能为空')
    normalized_device_id = str(device_id or '').strip()
    if not normalized_device_id:
        raise ValueError('device_id 不能为空')
    base_key = (
        str(task_id),
        normalized_device_id,
        normalize_algorithm_task_type(task_type),
    )
    normalized_event_identity = str(event_identity or '').strip().lower()
    if normalized_event_identity:
        return base_key + (normalized_event_identity,)
    return base_key


def build_alert_event_groups(detections) -> Dict[str, List[dict]]:
    """按模型和类别拆分事件，并移除追踪器产生的完全重复目标。"""
    from app.utils.alert_class_filter import normalize_class_name

    groups: Dict[str, List[dict]] = {}
    group_indexes: Dict[str, Dict[Tuple, int]] = {}
    for raw_detection in detections or []:
        if not isinstance(raw_detection, dict):
            continue
        detection = dict(raw_detection)
        model_id = detection.get('model_id')
        try:
            model_identity = str(int(model_id)) if model_id is not None else 'unknown'
        except (TypeError, ValueError):
            model_identity = str(model_id).strip().lower() or 'unknown'
        class_name = normalize_class_name(detection.get('class_name') or 'unknown') or 'unknown'
        event_identity = f'{model_identity}:{class_name}'

        track_id = detection.get('track_id')
        bbox = tuple(detection.get('bbox') or ())
        if track_id not in (None, 0, '0', ''):
            detection_identity = ('track', str(track_id), bbox)
        else:
            detection_identity = ('bbox', bbox)

        group = groups.setdefault(event_identity, [])
        indexes = group_indexes.setdefault(event_identity, {})
        existing_index = indexes.get(detection_identity)
        if existing_index is None:
            indexes[detection_identity] = len(group)
            group.append(detection)
            continue

        # 同一目标同时出现实时结果与缓存结果时，始终保留实时结果。
        existing = group[existing_index]
        if existing.get('is_cached') and not detection.get('is_cached'):
            group[existing_index] = detection
    return groups


def resolve_alert_event_identity(alert_data) -> Optional[str]:
    """从新版或旧版告警消息中解析稳定的模型类别事件身份。"""
    from app.utils.alert_class_filter import normalize_class_name

    if not isinstance(alert_data, dict):
        return None
    explicit = str(alert_data.get('event_identity') or '').strip().lower()
    if explicit:
        return explicit

    groups = build_alert_event_groups(alert_data.get('detections'))
    if groups:
        return '|'.join(groups.keys())

    class_name = normalize_class_name(alert_data.get('object') or '')
    model_ids = alert_data.get('model_ids') or []
    if not isinstance(model_ids, (list, tuple, set)):
        model_ids = [model_ids]
    normalized_model_ids = sorted({str(value).strip() for value in model_ids if str(value).strip()})
    if class_name:
        model_identity = ','.join(normalized_model_ids) if normalized_model_ids else 'unknown'
        return f'{model_identity}:{class_name}'
    return None


def claim_due_alert_event_identities(
        last_times: dict,
        device_id: str,
        event_identities,
        *,
        current_time: float,
        suppress_interval: float,
) -> List[str]:
    """在调用方持锁期间占用到期事件槽，并返回本次成功占用的事件身份。"""
    claimed = []
    for raw_identity in event_identities or []:
        event_identity = str(raw_identity or '').strip().lower()
        if not event_identity:
            continue
        suppression_key = (str(device_id), event_identity)
        last_time = float(last_times.get(suppression_key, 0) or 0)
        if suppress_interval > 0 and current_time - last_time < suppress_interval:
            continue
        last_times[suppression_key] = current_time
        claimed.append(event_identity)
    return claimed


def should_reload_algorithm_models(loaded_model_ids, configured_model_ids) -> bool:
    """判断任务热更新是否需要重新加载算法模型。"""
    loaded = {int(model_id) for model_id in (loaded_model_ids or [])}
    configured = {int(model_id) for model_id in (configured_model_ids or [])}
    return loaded != configured


def select_unique_legacy_alert_task(candidates, device_id: str, task_type: str):
    """旧版告警仅允许从唯一候选任务中恢复任务身份。"""
    candidate_list = list(candidates or [])
    if len(candidate_list) > 1:
        raise AmbiguousAlgorithmTaskError(
            f'设备 {device_id} 存在多个 {task_type} 告警任务，旧版消息缺少 task_id'
        )
    return candidate_list[0] if candidate_list else None
